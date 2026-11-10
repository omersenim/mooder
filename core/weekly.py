"""Weekly review logic: best/worst day detection, prompts, aggregation."""

from datetime import date, timedelta
from typing import Any

from .data import get_week_entries, iter_rated_entries


# ──────────────────────────────────────────────────────────────────────
# Week boundaries (Sunday–Saturday)
# ──────────────────────────────────────────────────────────────────────

def week_start_sunday(d: date) -> date:
    """
    Return the Sunday (week start) for a given date.
    Monday=0 ... Sunday=6 in Python weekday(), so:
    - If Sunday (6): return same day
    - Otherwise: subtract (weekday + 1) days
    """
    wd = d.weekday()  # Mon=0, Sun=6
    if wd == 6:
        return d
    return d - timedelta(days=wd + 1)


def week_end_saturday(week_start: date) -> date:
    """Return Saturday (week end) for a given week start (Sunday)."""
    return week_start + timedelta(days=6)


def current_week_start() -> date:
    """Week start (Sunday) for today."""
    return week_start_sunday(date.today())


def previous_week_start() -> date:
    """Week start (Sunday) for last week."""
    return week_start_sunday(date.today() - timedelta(days=7))


def week_label(week_start: date) -> str:
    """Human-readable label: 'Week of Nov 10'."""
    return f"Week of {week_start.strftime('%b %d')}"


# ──────────────────────────────────────────────────────────────────────
# Weekly analysis
# ──────────────────────────────────────────────────────────────────────

def analyze_week(data: dict[str, Any], week_start: date) -> dict[str, Any] | None:
    """
    Analyze a week's entries.
    Returns dict with best/worst day, average, count, or None if no rated entries.
    """
    entries = get_week_entries(data, week_start)

    # Filter to entries with rating
    rated = {}
    for day_key, entry in entries.items():
        r = entry.get("rating")
        if isinstance(r, int):
            rated[day_key] = r

    if not rated:
        return None

    best_day = max(rated, key=rated.get)
    worst_day = min(rated, key=rated.get)
    ratings = list(rated.values())

    return {
        "week_start": week_start.isoformat(),
        "week_label": week_label(week_start),
        "best": {"date": best_day, "rating": rated[best_day]},
        "worst": {"date": worst_day, "rating": rated[worst_day]},
        "average": sum(ratings) / len(ratings),
        "count": len(ratings),
        "days_logged": len(entries),
    }


def get_weekly_reflection_prompt(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """
    Generate reflection questions for best/worst day.
    Returns list of {date, rating, question} dicts.
    """
    prompts = []

    best = analysis["best"]
    worst = analysis["worst"]

    prompts.append({
        "date": best["date"],
        "rating": str(best["rating"]),
        "type": "best",
        "question": f"🌟 {best['date']} was your best day this week ({best['rating']}/5). What made it great?",
    })

    if worst["date"] != best["date"]:
        prompts.append({
            "date": worst["date"],
            "rating": str(worst["rating"]),
            "type": "worst",
            "question": f"😔 {worst['date']} was your toughest day ({worst['rating']}/5). What happened?",
        })

    return prompts


def save_weekly_reflection(
    data: dict[str, Any], week_start: date, reflections: dict[str, str]
) -> None:
    """
    Save weekly reflection answers to the week's entries.
    reflections: {date_key: "answer text"}
    """
    for day_key, answer in reflections.items():
        if day_key in data:
            entry = data[day_key]
            if "weekly_reflections" not in entry:
                entry["weekly_reflections"] = {}
            entry["weekly_reflections"][week_start.isoformat()] = answer


# ──────────────────────────────────────────────────────────────────────
# Streak calculation
# ──────────────────────────────────────────────────────────────────────

def current_streak(data: dict[str, Any]) -> int:
    """
    Consecutive days logged (with rating) up to today.
    Returns 0 if today not logged.
    """
    today = date.today()
    today_key = today.isoformat()

    if today_key not in data or "rating" not in data[today_key]:
        return 0

    streak = 1
    check = today - timedelta(days=1)
    while True:
        key = check.isoformat()
        if key in data and "rating" in data[key]:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


def longest_streak(data: dict[str, Any]) -> int:
    """Longest consecutive logging streak in entire history."""
    rated_dates = {d for d, _ in iter_rated_entries(data)}
    if not rated_dates:
        return 0

    max_streak = 1
    current = 1
    sorted_dates = sorted(rated_dates)

    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1

    return max_streak