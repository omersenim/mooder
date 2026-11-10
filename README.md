# 🌅 Mooder

> **A tactile, distraction-free personal day & mood logger.**  
> Native desktop workspace with local Wi-Fi mobile PWA sync. Zero cloud, zero subscriptions, 100% private.

---

## ✨ Features

- **🖥️ Frameless Tactile Desktop UI**  
  Built with Flutter-powered [Flet](https://flet.dev) in Python. Features a Discord-style unified top bar, top-lit beveled card depths, and desk calendar date tiles (`[ NOV | 11 ]`).
- **📱 Zero-Config Phone Sync (Local PWA)**  
  Embedded background [FastAPI](https://fastapi.tiangolo.com) server. Scan the on-screen QR code from your phone on the same Wi-Fi network to install the mobile PWA to your home screen. Log from your phone, sync instantly to your desktop.
- **📅 Daily Journaling & Reflections**  
  Quick 1–5 mood star ratings, daily thought capture, and dynamic reflection prompts to spark mindfulness.
- **📊 Analytics & Insights**  
  Rolling 7/30/90-day averages, weekday mood distribution patterns, streak tracking, and keyword trend heatmaps.
- **⌨️ Direct Terminal CLI**  
  Log entries, review summaries, or view statistics without opening the GUI: `python cli.py log`, `python cli.py stats`.
- **🔒 100% Local & Future-Proof Data**  
  All entries are saved locally in a clean, human-readable JSON format. One-click backup export to JSON.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/mooder.git
cd mooder

# Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Mooder

Launch the desktop app and background mobile sync server with a single command:

```bash
python main.py
```

---

## 📱 Mobile Phone Sync

1. Open the **Phone Sync** tab inside the desktop app.
2. Ensure your phone is connected to the same Wi-Fi network.
3. Scan the QR code with your phone camera.
4. Tap **Add to Home Screen** in your mobile browser to install Mooder as a standalone native-feeling PWA.
5. Entries logged from your phone will immediately sync to your desktop database.

---

## ⌨️ Command Line Usage

Mooder includes a complete terminal interface for fast keyboard-only workflows:

```bash
# Quick interactive day entry
python cli.py log

# View streaks, averages, and day-of-week patterns
python cli.py stats

# Weekly reflection and review
python cli.py review

# Keyword management
python cli.py keywords list
```

---

## 📁 Project Structure

```
Mooder/
├── assets/                 # App icons (.ico multi-res, .png master)
├── core/                   # Pure business logic (data store, stats, streak calculator)
├── flet_gui/               # Modern desktop workspace UI
│   ├── tabs/               # Today, History, Weekly, Stats, Phone Sync views
│   ├── app.py              # Frameless shell, navigation & window controls
│   └── theme.py            # Design tokens, 3D shadows, colors & cards
├── server/                 # FastAPI local Wi-Fi sync server
│   ├── static/             # Mobile PWA assets (HTML, CSS, JS, manifest, icons)
│   └── api.py              # Endpoints & background runner
├── main.py                 # Unified desktop + server entry point
├── cli.py                  # Terminal logging interface
└── requirements.txt        # Python dependencies
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
