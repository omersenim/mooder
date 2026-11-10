# Mooder — Personal Day & Mood Logging System

## Vision
A single `mooder.exe` you double-click. Log your day & mood (rating 0-5, notes, reflection question). See weekly reviews, stats, keyword trends. Sync to phone via local WiFi — no cloud, no server management.

---

## Architecture: One Exe, Two Modes

```
mooder.exe
│
├── 🖱️  GUI MODE (default, double-click)
│   ├── Flet / Material 3 frameless tactile desktop app
│   ├── Tabs: Today | History | Weekly | Stats | Sync
│   └── Background: FastAPI server on localhost:8000
│
└── ⌨️  CLI MODE (optional)
    ├── mooder.exe log      → Quick terminal entry
    ├── mooder.exe review   → Weekly review in terminal
    └── mooder.exe stats    → Monthly averages
```

**Single process.** GUI starts → spawns server thread → serves PWA to phone. Close GUI → server stops. No separate executables.

---

## Data Model

```json
{
  "2026-11-10": {
    "rating": 4,
    "notes": "finished the project",
    "reflection": {
      "question": "What were you most happy about today?",
      "answer": "deployed the feature"
    },
    "keywords": ["productive", "great"],
    "timestamp": "2026-11-10T20:34:12.000Z"
  }
}
```

- **File**: `daylog_data.json` (same folder as exe)
- **Week boundary**: Sunday–Saturday (ISO week, `date.isocalendar()`)
- **Conflict resolution**: Last write wins (per-day key)

---

## GUI Tabs

| Tab | Features |
|-----|----------|
| **Today** | Big 0-5 star rating, notes textarea, random reflection Q, Save button, "Already logged" indicator |
| **History** | Calendar heatmap (Sun-Sat rows), color by rating, click day → edit inline, filter by keyword |
| **Weekly** | Auto-detect best/worst day of current week → "Why was Tuesday (5) your best?" / "Why Thursday (1)?" → saves as weekly reflection |
| **Stats** | Month avg, 7/30-day rolling avg, streak (consecutive logged days), keyword frequency cloud |
| **Sync** | Shows LAN IP + port (`http://192.168.1.47:8000`), QR code, "Install PWA" button, connected devices list |

---

## Phone PWA (served by background FastAPI)

- **Static files** embedded in exe (extracted to temp on first run)
- **Service Worker** → offline-capable, caches all assets
- **IndexedDB** → local queue when offline, auto-sync when laptop reachable
- **Manifest** → "Add to Home Screen" → feels native
- **API**: `GET/POST /api/day/{date}`, `GET /api/week/{iso_week}`, `POST /api/sync`

---

## Keyword Tagging System

**Predefined emotional keywords** (user-extendable):

| Positive | Neutral | Negative |
|----------|---------|----------|
| amazing, awesome, great, productive, wonderful | meh, okay, average, normal, routine | terrible, awful, worst, exhausted, draining, anxious |

- **Extraction**: Regex scan notes + reflection answer → suggest tags
- **Manual**: Click to add/remove in Today/History tabs
- **Stats**: Frequency chart, correlation with rating

---

## Weekly Review Logic

```python
def weekly_review(data, week_start_sunday):
    week_entries = {d: e for d, e in data.items() if is_in_week(d, week_start_sunday)}
    if not week_entries: return None
    
    rated = {d: e["rating"] for d, e in week_entries.items() if "rating" in e}
    if not rated: return None
    
    best_day = max(rated, key=rated.get)
    worst_day = min(rated, key=rated.get)
    
    return {
        "week": week_start_sunday.isoformat(),
        "best": {"date": best_day, "rating": rated[best_day]},
        "worst": {"date": worst_day, "rating": rated[worst_day]},
        "avg": sum(rated.values()) / len(rated)
    }
```

- Runs automatically on Weekly tab open
- Prompts "Why?" → saves as `weekly_reflection` in data

---

## File Structure

```
ilkprojem/
├── main.py              # Entry point: GUI + background server (TODO)
├── gui/
│   ├── __init__.py
│   ├── app.py           # ✅ Main Tkinter window + tabs
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── today.py     # ✅ Star rating, notes, reflection, keywords, save
│   │   ├── history.py   # ✅ Calendar heatmap, day details, edit/delete, filter
│   │   ├── weekly.py    # ✅ Week analysis, best/worst cards, reflection prompts
│   │   ├── stats.py     # ✅ Overall, rolling, streaks, keywords, charts
│   │   └── sync.py      # ✅ LAN IP, QR code, server controls, devices
│   └── widgets.py       # ✅ StarRating, CalendarHeatmap, KeywordCloud, ToolTip
├── server/
│   ├── __init__.py      # TODO
│   ├── api.py           # FastAPI routes (TODO)
│   └── static/          # PWA files (embedded via PyInstaller) (TODO)
│       ├── index.html
│       ├── app.js
│       ├── sw.js        # Service Worker
│       ├── manifest.json
│       └── style.css
├── core/
│   ├── __init__.py
│   ├── data.py          # ✅ load/save, validation, query helpers
│   ├── keywords.py      # ✅ extraction, suggestions, custom keywords
│   ├── weekly.py        # ✅ week boundaries, review, streaks
│   └── stats.py         # ✅ overall/monthly/rolling, keyword analytics, series
├── cli.py               # ✅ Terminal: log/history/today/weekly/stats/keywords/export
├── build_exe.py         # PyInstaller spec builder (TODO)
├── requirements.txt     # TODO
└── daylog_data.json     # Created at runtime
```

---

## Dependencies

```txt
# requirements.txt
fastapi==0.115.*
uvicorn==0.30.*
qrcode==7.4.*
pillow==10.*        # QR code generation
pyinstaller==6.11.* # Build exe
# tkinter, json, datetime, pathlib, re, sqlite3 — all stdlib
```

---

## Build Process

```bash
# One-time setup
pip install -r requirements.txt

# Build single exe
python build_exe.py
# → dist/daylog.exe (~15-25 MB)
```

**PyInstaller config**:
- `--onefile` + `--windowed` (no console)
- `--add-data "server/static/*;server/static"` (embed PWA)
- `--hidden-import=tkinter` (ensure included)
- `--icon=assets/icon.ico` (optional)

---

## Sync Protocol (Local WiFi)

```
Laptop (server)                    Phone (PWA client)
─────────────────                  ──────────────────
GET  /api/day/2026-11-10    ←──────  Fetch today
POST /api/day/2026-11-10    ──────→  Save entry
GET  /api/sync?since=...    ←──────  Incremental pull
POST /api/sync              ──────→  Batch push (offline queue)
```

- **Discovery**: Phone scans QR → opens `http://<laptop-ip>:8000`
- **CORS**: `allow_origins=["*"]` (local LAN only)
- **No auth** — trusted home network

---

## Milestones

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Core data layer (`core/data.py`, `core/keywords.py`, `core/weekly.py`, `core/stats.py`) + CLI (`cli.py`) | ✅ **DONE** |
| 2 | Desktop GUI widgets & styling (`flet_gui/theme.py`, `gui/widgets.py`) | ✅ **DONE** |
| 3 | Full desktop app with 5 tabs (`flet_gui/tabs/` + `flet_gui/app.py`) | ✅ **DONE** |
| 4 | FastAPI server + PWA static files (`server/api.py`, `server/static/`) | ✅ **DONE** |
| 5 | Background thread integration in `main.py` (GUI + server) | ✅ **DONE** |
| 6 | PyInstaller build script → `daylog.exe` (`build_exe.py`) | 🔄 **NEXT** |
| 7 | Test on Windows → verify phone sync works | ⏳ Pending |

---

## Non-Goals (v1)

- Cloud sync / accounts
- Multiple users
- Encryption (local file only)
- Mobile app store build (PWA is enough)
- Plugin system
- Themes beyond light/dark

---

## Start Command

```bash
cd D:\CLAUDECODE\ilkprojem
python main.py          # Dev: runs GUI + server (TODO)
# or
python cli.py log       # Dev: terminal only ✅ WORKS
python cli.py log --test 4 "had a good day" "finished the project"  # ✅ Non-interactive test mode
python cli.py history
python cli.py stats
```

**Build exe when ready:**
```bash
python build_exe.py
# → dist/daylog.exe
```

---

## Testing Notes (Phase 1)

- ✅ `core/data.py` — load/save, validation, query helpers tested
- ✅ `core/keywords.py` — extraction (single words + multi-word phrases like "awesome sauce"), suggestions, custom keyword management
- ✅ `core/weekly.py` — week boundaries (Sun-Sat), analysis, reflection prompts, streaks
- ✅ `core/stats.py` — overall/monthly/rolling, keyword frequency/correlation, series, day-of-week patterns
- ✅ `cli.py` — all commands work; `--test` mode avoids PowerShell `input()` EOFError
- ✅ `gui/widgets.py` — StarRating, CalendarHeatmap, KeywordCloud, ToolTip implemented

## Testing Notes (Phase 2 - GUI Tabs)

- ✅ `gui/tabs/today.py` — Star rating (clickable), notes textarea, random reflection Q, keyword cloud (editable), save/update
- ✅ `gui/tabs/history.py` — Calendar heatmap (Sun-Sat), click day → detail panel, edit/delete dialog, keyword filter dropdown
- ✅ `gui/tabs/weekly.py` — Week navigation, best/worst day cards with prompts, other days list, reflection prompts, save
- ✅ `gui/tabs/stats.py` — Overall cards, rolling averages, streaks, keyword cloud + list + correlation, weekly/monthly/DOW charts
- ✅ `gui/tabs/sync.py` — LAN IP detection, QR code generation, server start/stop buttons, device list, troubleshooting
- ✅ `gui/app.py` — Main window with notebook, menu bar, status bar, tab-change refresh, F5 shortcut, export/about dialogs