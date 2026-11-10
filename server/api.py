"""FastAPI server and background runner for Mooder mobile PWA sync."""

import os
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.data import (
    QUESTIONS,
    delete_entry,
    get_entry,
    load_data,
    save_data,
    today_key,
    validate_entry,
)
from core.keywords import get_all_keywords, suggest_keywords_for_entry
from core.weekly import analyze_week, current_week_start, week_start_sunday


# ──────────────────────────────────────────────────────────────────────
# Device Tracker
# ──────────────────────────────────────────────────────────────────────

class DeviceTracker:
    """Thread-safe tracker for connected client devices."""

    def __init__(self):
        self._lock = threading.Lock()
        self._devices: Dict[str, Dict[str, Any]] = {}

    def record(self, ip: str, user_agent: str) -> None:
        key = f"{ip}_{user_agent}"
        with self._lock:
            self._devices[key] = {
                "ip": ip,
                "ua": user_agent or "Unknown Device",
                "last_seen_epoch": time.time(),
                "last_seen": datetime.now().strftime("%H:%M:%S"),
            }

    def get_devices(self) -> List[Dict[str, Any]]:
        with self._lock:
            # Sort by most recently seen
            devs = list(self._devices.values())
            devs.sort(key=lambda d: d["last_seen_epoch"], reverse=True)
            return devs


device_tracker = DeviceTracker()


# ──────────────────────────────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────────────────────────────

class ReflectionModel(BaseModel):
    question: str
    answer: str


class DayEntryModel(BaseModel):
    rating: Optional[int] = Field(None, ge=0, le=5)
    notes: Optional[str] = None
    reflection: Optional[ReflectionModel] = None
    keywords: Optional[List[str]] = None
    timestamp: Optional[str] = None


class SyncPushModel(BaseModel):
    entries: Dict[str, Dict[str, Any]]


# ──────────────────────────────────────────────────────────────────────
# Static files directory helper
# ──────────────────────────────────────────────────────────────────────

def get_static_dir() -> Path:
    """Return path to static directory, supporting PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "server" / "static"
    return Path(__file__).resolve().parent / "static"


# ──────────────────────────────────────────────────────────────────────
# FastAPI App Factory
# ──────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Mooder API",
        version="1.0.0",
        description="Local WiFi API for Mooder Phone PWA",
    )

    # Allow all origins for local Wi-Fi sync
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware to record client devices
    @app.middleware("http")
    async def track_devices_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        # Filter out internal/loopback health checks from device list if preferred, but record LAN devices
        if client_ip != "unknown":
            device_tracker.record(client_ip, user_agent)
        return await call_next(request)

    # ── API Endpoints ─────────────────────────────────────────────────

    @app.get("/api/ping")
    def ping():
        return {"status": "ok", "time": datetime.now().isoformat()}

    @app.get("/api/day/{day_key}")
    def get_day(day_key: str):
        data = load_data()
        entry = get_entry(data, day_key)
        if entry is None:
            return {"date": day_key, "exists": False, "entry": None}
        return {"date": day_key, "exists": True, "entry": entry}

    @app.post("/api/day/{day_key}")
    def save_day(day_key: str, payload: DayEntryModel):
        try:
            date.fromisoformat(day_key)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        data = load_data()
        entry_dict = payload.model_dump(exclude_none=True)
        # Suggest keywords if not provided
        if not entry_dict.get("keywords"):
            entry_dict["keywords"] = suggest_keywords_for_entry(entry_dict)

        data[day_key] = validate_entry(entry_dict)
        save_data(data)
        return {"status": "saved", "date": day_key, "entry": data[day_key]}

    @app.delete("/api/day/{day_key}")
    def remove_day(day_key: str):
        data = load_data()
        if delete_entry(data, day_key):
            save_data(data)
            return {"status": "deleted", "date": day_key}
        raise HTTPException(status_code=404, detail="Entry not found")

    @app.get("/api/today")
    def get_today():
        tk = today_key()
        data = load_data()
        return {
            "date": tk,
            "exists": tk in data,
            "entry": data.get(tk),
            "questions": QUESTIONS,
        }

    @app.get("/api/questions")
    def get_questions():
        return {"questions": QUESTIONS}

    @app.get("/api/keywords")
    def get_keywords():
        return get_all_keywords()

    @app.get("/api/week")
    def get_week(start: Optional[str] = None):
        data = load_data()
        if start:
            try:
                target_start = date.fromisoformat(start)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD")
        else:
            target_start = current_week_start()

        # Ensure we align to Sunday
        week_sunday = week_start_sunday(target_start)
        analysis = analyze_week(data, week_sunday)
        return {
            "week_start": week_sunday.isoformat(),
            "analysis": analysis,
        }

    @app.get("/api/sync")
    def sync_pull():
        """Pull full data for mobile client."""
        data = load_data()
        return {"data": data, "timestamp": datetime.now().isoformat()}

    @app.post("/api/sync")
    def sync_push(payload: SyncPushModel):
        """Batch push offline entries from mobile device (Last write wins)."""
        data = load_data()
        updated_count = 0
        for day_key, entry in payload.entries.items():
            try:
                date.fromisoformat(day_key)
                data[day_key] = validate_entry(entry)
                updated_count += 1
            except (ValueError, TypeError):
                continue

        if updated_count > 0:
            save_data(data)
        return {"status": "synced", "updated": updated_count}

    @app.get("/api/devices")
    def get_devices():
        return {"devices": device_tracker.get_devices()}

    # ── Static PWA Hosting ───────────────────────────────────────────

    static_path = get_static_dir()
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

        @app.get("/")
        async def serve_index():
            index_file = static_path / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return {"message": "Mooder PWA index.html not found"}

        @app.get("/sw.js")
        async def serve_sw():
            sw_file = static_path / "sw.js"
            if sw_file.exists():
                return FileResponse(sw_file, media_type="application/javascript")
            raise HTTPException(status_code=404, detail="Service worker not found")

        @app.get("/manifest.json")
        async def serve_manifest():
            manifest_file = static_path / "manifest.json"
            if manifest_file.exists():
                return FileResponse(manifest_file, media_type="application/json")
            raise HTTPException(status_code=404, detail="Manifest not found")

    return app


# ──────────────────────────────────────────────────────────────────────
# Background Server Runner (Controlled by GUI)
# ──────────────────────────────────────────────────────────────────────

class BackgroundServer:
    """
    Manages Uvicorn running in a background daemon thread.
    Exposes start(), stop(), and get_connected_devices() for SyncTab integration.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = create_app()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self.running = False

    def start(self) -> None:
        if self.running:
            return

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            log_config=None,
            loop="asyncio",
        )
        self._server = uvicorn.Server(config)

        def run_srv():
            self._server.run()

        self._thread = threading.Thread(target=run_srv, daemon=True, name="MooderFastAPIServer")
        self._thread.start()
        self.running = True

    def stop(self) -> None:
        if not self.running:
            return

        if self._server:
            self._server.should_exit = True
        self.running = False

    def get_connected_devices(self) -> List[Dict[str, Any]]:
        return device_tracker.get_devices()
