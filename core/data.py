"""Core data layer: load, save, validate, and access daylog entries."""

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

DATA_FILENAME = "daylog_data.json"

# Predefined reflection questions
QUESTIONS = [
    "What made you smile today?",
    "What were you most proud of today?",
    "What challenged you today, and how did you handle it?",
    "What did you learn today?",
    "What are you grateful for today?",
    "If you could redo one moment today, what would it be?",
    "What gave you energy today? What drained you?",
    "Who or what made a positive impact on your day?",
    "What progress did you make on something important?",
    "How did you take care of yourself today?",
    "What would you tell your morning self?",
    "What's one thing you want to remember about today?",
]

# Predefined emotional keywords (user can extend at runtime)
DEFAULT_KEYWORDS = {
    "positive": [
        "amazing", "awesome", "great", "productive", "wonderful",
        "fantastic", "excellent", "brilliant", "joyful", "energized",
        "motivated", "accomplished", "proud", "grateful", "blessed",
    ],
    "neutral": [
        "meh", "okay", "average", "normal", "routine", "standard",
        "typical", "uneventful", "steady", "balanced",
    ],
    "negative": [
        "terrible", "awful", "worst", "exhausted", "draining", "anxious",
        "stressed", "overwhelmed", "burned out", "miserable", "depressed",
        "frustrated", "angry", "sad", "lonely", "hopeless",
    ],
}

ALL_KEYWORDS = set()
for cat in DEFAULT_KEYWORDS.values():
    ALL_KEYWORDS.update(cat)

# ──────────────────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────────────────

def get_data_path() -> Path:
    """
    Return the path to daylog_data.json.
    When frozen (PyInstaller), use the folder containing the exe.
    Otherwise use the current working directory.
    """
    if hasattr(__import__("sys"), "frozen"):  # PyInstaller
        base = Path(__import__("sys").executable).parent
    else:
        base = Path.cwd()
    return base / DATA_FILENAME


# ──────────────────────────────────────────────────────────────────────
# Load / Save
# ──────────────────────────────────────────────────────────────────────

def load_data() -> dict[str, dict[str, Any]]:
    """Load all entries from JSON file. Returns empty dict if missing/corrupt."""
    path = get_data_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Validate structure: must be dict of date_key -> entry
        if not isinstance(data, dict):
            return {}
        # Ensure each entry is a dict
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data: dict[str, dict[str, Any]]) -> None:
    """Atomically write data to JSON file."""
    path = get_data_path()
    # Atomic write: write to temp, then replace
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


# ──────────────────────────────────────────────────────────────────────
# Entry helpers
# ──────────────────────────────────────────────────────────────────────

def today_key() -> str:
    """Today's date as ISO string (YYYY-MM-DD)."""
    return date.today().isoformat()


def validate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize an entry dict.
    Returns cleaned entry with only known fields.
    """
    clean: dict[str, Any] = {}

    # Rating: int 0-5
    if "rating" in entry:
        try:
            r = int(entry["rating"])
            if 0 <= r <= 5:
                clean["rating"] = r
        except (ValueError, TypeError):
            pass

    # Notes: non-empty string
    if entry.get("notes"):
        notes = str(entry["notes"]).strip()
        if notes:
            clean["notes"] = notes

    # Reflection: dict with question + answer
    if entry.get("reflection"):
        refl = entry["reflection"]
        if isinstance(refl, dict):
            q = str(refl.get("question", "")).strip()
            a = str(refl.get("answer", "")).strip()
            if q and a:
                clean["reflection"] = {"question": q, "answer": a}

    # Keywords: list of strings from known set (case-insensitive match)
    if entry.get("keywords"):
        kws = entry["keywords"]
        if isinstance(kws, list):
            matched = []
            for kw in kws:
                if isinstance(kw, str):
                    kl = kw.strip().lower()
                    if kl in ALL_KEYWORDS:
                        matched.append(kl)
            if matched:
                clean["keywords"] = matched

    # Weekly reflection: free text
    if entry.get("weekly_reflection"):
        wr = str(entry["weekly_reflection"]).strip()
        if wr:
            clean["weekly_reflection"] = wr

    # Timestamp: always set to now if missing
    clean["timestamp"] = entry.get("timestamp") or datetime.now().isoformat()

    return clean


def get_entry(data: dict, day_key: str) -> dict[str, Any] | None:
    """Get entry for a specific day, or None."""
    return data.get(day_key)


def set_entry(data: dict, day_key: str, entry: dict) -> None:
    """Add or update an entry (validated)."""
    data[day_key] = validate_entry(entry)


def delete_entry(data: dict, day_key: str) -> bool:
    """Delete entry for a day. Returns True if existed."""
    if day_key in data:
        del data[day_key]
        return True
    return False


# ──────────────────────────────────────────────────────────────────────
# Query helpers
# ──────────────────────────────────────────────────────────────────────

def get_entries_in_range(
    data: dict, start: date, end: date
) -> dict[str, dict[str, Any]]:
    """Return entries with date keys between start and end (inclusive)."""
    result = {}
    for k, v in data.items():
        try:
            d = date.fromisoformat(k)
            if start <= d <= end:
                result[k] = v
        except ValueError:
            continue
    return result


def get_week_entries(data: dict, week_start: date) -> dict[str, dict[str, Any]]:
    """Return entries for the week starting on given Sunday."""
    week_end = date.fromordinal(week_start.toordinal() + 6)
    return get_entries_in_range(data, week_start, week_end)


def get_month_entries(data: dict, year: int, month: int) -> dict[str, dict[str, Any]]:
    """Return entries for a specific month."""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)
    return get_entries_in_range(data, start, end)


def iter_rated_entries(data: dict) -> list[tuple[date, int]]:
    """Return list of (date, rating) for all entries with a rating, sorted by date."""
    result = []
    for k, v in data.items():
        try:
            d = date.fromisoformat(k)
            r = v.get("rating")
            if isinstance(r, int):
                result.append((d, r))
        except ValueError:
            continue
    result.sort(key=lambda x: x[0])
    return result
    return result