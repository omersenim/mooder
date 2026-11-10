"""Statistics and analytics calculations."""

from collections import Counter
from datetime import date, timedelta
from typing import Any

from .data import get_month_entries, iter_rated_entries, get_week_entries
from .weekly import week_start_sunday, current_week_start


# ──────────────────────────────────────────────────────────────────────
# Basic stats
# ──────────────────────────────────────────────────────────────────────

def overall_stats(data: dict[str, Any]) -> dict[str, Any]:
    """Overall statistics across all time."""
    rated = [(d, r) for d, r in iter_rated_entries(data)]
    if not rated:
        return {"total_days": 0, "avg_rating": 0, "best_day": None, "worst_day": None}

    ratings = [r for _, r in rated]
    best = max(rated, key=lambda x: x[1])
    worst = min(rated, key=lambda x: x[1])

    return {
        "total_days": len(rated),
        "avg_rating": sum(ratings) / len(ratings),
        "best_day": {"date": best[0].isoformat(), "rating": best[1]},
        "worst_day": {"date": worst[0].isoformat(), "rating": worst[1]},
        "rating_distribution": Counter(ratings),
    }


def monthly_stats(data: dict[str, Any], year: int, month: int) -> dict[str, Any]:
    """Statistics for a specific month."""
    entries = get_month_entries(data, year, month)
    # entries keys are strings like "2026-11-10", convert to date for consistency
    rated = [(date.fromisoformat(d), e["rating"]) for d, e in entries.items() if isinstance(e.get("rating"), int)]

    if not rated:
        return {"year": year, "month": month, "days_logged": 0, "avg_rating": 0}

    ratings = [r for _, r in rated]
    best = max(rated, key=lambda x: x[1])
    worst = min(rated, key=lambda x: x[1])

    return {
        "year": year,
        "month": month,
        "days_logged": len(rated),
        "avg_rating": sum(ratings) / len(ratings),
        "best_day": {"date": best[0].isoformat(), "rating": best[1]},
        "worst_day": {"date": worst[0].isoformat(), "rating": worst[1]},
        "rating_distribution": Counter(ratings),
    }


def rolling_average(data: dict[str, Any], days: int) -> float | None:
    """Average rating over the last N days (including today if logged)."""
    cutoff = date.today() - timedelta(days=days - 1)
    rated = [(d, r) for d, r in iter_rated_entries(data) if d >= cutoff]
    if not rated:
        return None
    return sum(r for _, r in rated) / len(rated)


# ──────────────────────────────────────────────────────────────────────
# Keyword analytics
# ──────────────────────────────────────────────────────────────────────

def keyword_frequency(data: dict[str, Any]) -> Counter:
    """Count of each keyword across all entries."""
    freq = Counter()
    for entry in data.values():
        for kw in entry.get("keywords", []):
            freq[kw] += 1
    return freq


def keyword_rating_correlation(data: dict[str, Any]) -> dict[str, dict[str, float]]:
    """
    Average rating for days tagged with each keyword.
    Returns {keyword: {"avg": float, "count": int}}.
    """
    kw_ratings: dict[str, list[int]] = {}
    for entry in data.values():
        rating = entry.get("rating")
        if not isinstance(rating, int):
            continue
        for kw in entry.get("keywords", []):
            kw_ratings.setdefault(kw, []).append(rating)

    result = {}
    for kw, ratings in kw_ratings.items():
        result[kw] = {
            "avg": sum(ratings) / len(ratings),
            "count": len(ratings),
        }
    return result


def top_keywords(data: dict[str, Any], n: int = 10) -> list[tuple[str, int]]:
    """Top N most used keywords."""
    return keyword_frequency(data).most_common(n)


# ──────────────────────────────────────────────────────────────────────
# Weekly/Monthly series for charts
# ──────────────────────────────────────────────────────────────────────

def weekly_series(data: dict[str, Any], weeks: int = 12) -> list[dict[str, Any]]:
    """
    Last N weeks: [{week_start, avg, best, worst, count}, ...]
    Most recent first.
    """
    today = date.today()
    current_ws = week_start_sunday(today)
    series = []

    for i in range(weeks):
        ws = current_ws - timedelta(weeks=i)
        analysis = analyze_week_data(data, ws)
        if analysis:
            series.append(analysis)
    return series


def analyze_week_data(data: dict[str, Any], week_start: date) -> dict[str, Any] | None:
    """Internal: compute week stats (reused from weekly.py logic)."""
    entries = get_week_entries(data, week_start)
    rated = {k: v["rating"] for k, v in entries.items() if isinstance(v.get("rating"), int)}
    if not rated:
        return None

    best_day = max(rated, key=rated.get)
    worst_day = min(rated, key=rated.get)
    ratings = list(rated.values())

    return {
        "week_start": week_start.isoformat(),
        "week_label": week_start.strftime("%b %d"),
        "avg": sum(ratings) / len(ratings),
        "best": {"date": best_day, "rating": rated[best_day]},
        "worst": {"date": worst_day, "rating": rated[worst_day]},
        "count": len(ratings),
    }


def monthly_series(data: dict[str, Any], months: int = 12) -> list[dict[str, Any]]:
    """Last N months: [{year, month, avg, count}, ...] Most recent first."""
    today = date.today()
    series = []
    y, m = today.year, today.month

    for _ in range(months):
        stats = monthly_stats(data, y, m)
        if stats["days_logged"] > 0:
            series.append({
                "year": y,
                "month": m,
                "label": date(y, m, 1).strftime("%b %Y"),
                "avg": stats["avg_rating"],
                "count": stats["days_logged"],
            })
        # Previous month
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1

    return series


# ──────────────────────────────────────────────────────────────────────
# Day-of-week patterns
# ──────────────────────────────────────────────────────────────────────

def day_of_week_pattern(data: dict[str, Any]) -> dict[int, dict[str, float]]:
    """
    Average rating by day of week (0=Mon ... 6=Sun).
    Returns {dow: {"avg": float, "count": int}}.
    """
    dow_ratings: dict[int, list[int]] = {i: [] for i in range(7)}
    for d, r in iter_rated_entries(data):
        dow_ratings[d.weekday()].append(r)

    result = {}
    for dow, ratings in dow_ratings.items():
        if ratings:
            result[dow] = {"avg": sum(ratings) / len(ratings), "count": len(ratings)}
    return result


DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def best_worst_days_of_week(data: dict[str, Any]) -> tuple[int | None, int | None]:
    """Return (best_dow, worst_dow) by average rating, or (None, None) if insufficient data."""
    pattern = day_of_week_pattern(data)
    if len(pattern) < 2:
        return None, None
    best = max(pattern.items(), key=lambda x: x[1]["avg"])[0]
    worst = min(pattern.items(), key=lambda x: x[1]["avg"])[0]
    return best, worst