"""Mooder — Unified application entry point.

Spawns the background FastAPI server on 0.0.0.0:8000 (serving the mobile PWA)
and launches the Flet desktop GUI. Exiting the desktop app cleanly stops the server.
"""

import sys
import io

# In windowed / no-console mode (PyInstaller/flet pack), sys.stdout and sys.stderr are None.
# Redirect them to dummy buffers so libraries (like uvicorn or print calls) don't crash.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import flet as ft
from flet_gui.app import MooderApp
from server.api import BackgroundServer


def main():
    # 1. Initialize and start the background server
    server = BackgroundServer(host="0.0.0.0", port=8000)
    server.start()
    print("🌅 Mooder background server running at http://0.0.0.0:8000")

    # 2. Main Flet window entry point
    async def app_main(page: ft.Page):
        # Cleanly stop server when window is closed
        async def on_window_event(e):
            if e.data == "close":
                server.stop()
                await page.window.destroy()

        page.window.prevent_close = True
        page.window.on_event = on_window_event

        # Mount Mooder with server reference
        MooderApp(page, server_ref=server)

    try:
        if hasattr(ft, "run"):
            ft.run(app_main)
        else:
            ft.app(target=app_main)
    finally:
        server.stop()
        print("Mooder server stopped cleanly.")


if __name__ == "__main__":
    main()
