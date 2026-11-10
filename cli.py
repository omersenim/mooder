#!/usr/bin/env python3
"""CLI interface for daylog — quick terminal logging and review."""

import sys
from datetime import date

from core.data import (
    load_data, save_data, today_key, validate_entry, get_entry,
    get_week_entries, iter_rated_entries
)
from core.keywords import extract_keywords, suggest_keywords_for_entry, get_all_keywords
from core.weekly import (
    current_week_start, previous_week_start, analyze_week,
    get_weekly_reflection_prompt, save_weekly_reflection, current_streak, longest_streak
)
from core.stats import (
    overall_stats, monthly_stats, rolling_average,
    keyword_frequency, keyword_rating_correlation, top_keywords,
    weekly_series, monthly_series, day_of_week_pattern, best_worst_days_of_week
)

from core.data import QUESTIONS
import random


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def print_entry(day_key: str, entry: dict) -> None:
    """Pretty-print a single entry."""
    rating = entry.get("rating", "?")
    stars = "★" * rating + "☆" * (5 - rating) if isinstance(rating, int) else "?"
    print(f"\n📅 {day_key}  [{stars}]  {rating}/5")
    if entry.get("notes"):
        print(f"   📝 {entry['notes']}")
    if entry.get("reflection"):
        r = entry["reflection"]
        print(f"   💭 {r['question']}")
        print(f"      → {r['answer']}")
    if entry.get("keywords"):
        print(f"   🏷️  {', '.join(entry['keywords'])}")
    if entry.get("weekly_reflections"):
        for wk, ans in entry["weekly_reflections"].items():
            print(f"   📋 Week {wk}: {ans}")


def prompt_rating() -> int | None:
    while True:
        try:
            s = input("Rate your day (0-5): ").strip()
            if not s:
                return None
            r = int(s)
            if 0 <= r <= 5:
                return r
            print("  Please enter 0-5.")
        except ValueError:
            print("  Invalid number.")


def prompt_notes() -> str | None:
    s = input("Notes (optional): ").strip()
    return s or None


def prompt_reflection() -> dict | None:
    q = random.choice(QUESTIONS)
    print(f"\n🤔 {q}")
    a = input("Your answer: ").strip()
    return {"question": q, "answer": a} if a else None


# ──────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────

def cmd_log(args: list[str]) -> int:
    """Log today's entry."""
    data = load_data()
    today = today_key()

    # Check for --test mode (non-interactive)
    if "--test" in args:
        idx = args.index("--test")
        test_rating = int(args[idx + 1]) if idx + 1 < len(args) else 3
        test_notes = args[idx + 2] if idx + 2 < len(args) else "test notes"
        test_answer = args[idx + 3] if idx + 3 < len(args) else "test answer"

        entry = {
            "rating": test_rating,
            "notes": test_notes,
            "reflection": {"question": QUESTIONS[0], "answer": test_answer},
        }
        # Add suggested keywords
        entry["keywords"] = suggest_keywords_for_entry(entry)
        data[today] = validate_entry(entry)
        save_data(data)
        print(f"✅ Test entry saved for {today}")
        print_entry(today, data[today])
        return 0

    # Interactive mode
    if today in data:
        print(f"Today ({today}) already logged:")
        print_entry(today, data[today])
        if input("\nOverwrite? (y/n): ").strip().lower() != "y":
            print("Keeping existing entry.")
            return 0

    print(f"\n🌅 Logging for {today}")
    print("-" * 30)

    rating = prompt_rating()
    notes = prompt_notes()
    reflection = prompt_reflection()

    entry = {}
    if rating is not None:
        entry["rating"] = rating
    if notes:
        entry["notes"] = notes
    if reflection:
        entry["reflection"] = reflection

    # Auto-suggest keywords from notes + reflection
    entry["keywords"] = suggest_keywords_for_entry(entry)
    if entry["keywords"]:
        print(f"\n🏷️  Suggested keywords: {', '.join(entry['keywords'])}")
        if input("Keep these? (y/n): ").strip().lower() != "y":
            entry["keywords"] = []

    data[today] = validate_entry(entry)
    save_data(data)
    print(f"\n✅ Saved entry for {today}")
    print_entry(today, data[today])
    return 0


def cmd_history(args: list[str]) -> int:
    """Show all history."""
    data = load_data()
    if not data:
        print("No entries yet.")
        return 0

    limit = None
    if args and args[0].isdigit():
        limit = int(args[0])

    print("\n📅 Day Log History")
    print("=" * 50)
    for day_key in sorted(data.keys(), reverse=True)[:limit]:
        print_entry(day_key, data[day_key])
    return 0


def cmd_today(args: list[str]) -> int:
    """Show today's entry."""
    data = load_data()
    today = today_key()
    entry = data.get(today)
    if entry:
        print_entry(today, entry)
    else:
        print(f"No entry for {today} yet.")
    return 0


def cmd_weekly(args: list[str]) -> int:
    """Weekly review for current or previous week."""
    data = load_data()

    # Determine which week
    if args and args[0] == "prev":
        ws = previous_week_start()
    else:
        ws = current_week_start()

    analysis = analyze_week(data, ws)
    if not analysis:
        print(f"No rated entries for {week_label(ws)}.")
        return 0

    print(f"\n📊 {analysis['week_label']}")
    print(f"   Average: {analysis['average']:.1f}/5  ({analysis['count']} days logged)")
    print(f"   🌟 Best:  {analysis['best']['date']} ({analysis['best']['rating']}/5)")
    print(f"   😔 Worst: {analysis['worst']['date']} ({analysis['worst']['rating']}/5)")

    # Reflection prompts
    prompts = get_weekly_reflection_prompt(analysis)
    reflections = {}

    for p in prompts:
        print(f"\n{p['question']}")
        ans = input("> ").strip()
        if ans:
            reflections[p["date"]] = ans

    if reflections:
        save_weekly_reflection(data, ws, reflections)
        save_data(data)
        print("\n✅ Weekly reflections saved.")

    return 0


def week_label(ws: date) -> str:
    return f"Week of {ws.strftime('%b %d')}"


def cmd_stats(args: list[str]) -> int:
    """Show statistics."""
    data = load_data()
    if not data:
        print("No data yet.")
        return 0

    # Overall
    ov = overall_stats(data)
    print("\n📈 Overall Stats")
    print(f"   Total days logged: {ov['total_days']}")
    print(f"   Average rating:    {ov['avg_rating']:.2f}/5")
    if ov['best_day']:
        print(f"   Best day:          {ov['best_day']['date']} ({ov['best_day']['rating']}/5)")
    if ov['worst_day']:
        print(f"   Worst day:         {ov['worst_day']['date']} ({ov['worst_day']['rating']}/5)")

    # Streaks
    print(f"\n🔥 Current streak:  {current_streak(data)} days")
    print(f"   Longest streak:  {longest_streak(data)} days")

    # Rolling averages
    print("\n📊 Rolling Averages")
    for days in [7, 30, 90]:
        ra = rolling_average(data, days)
        if ra is not None:
            print(f"   Last {days} days: {ra:.2f}/5")

    # Keywords
    kw_freq = keyword_frequency(data)
    if kw_freq:
        print("\n🏷️  Top Keywords")
        for kw, cnt in top_keywords(data, 10):
            cat = "🟢" if kw in ["amazing","awesome","great","productive","wonderful","fantastic","excellent","brilliant","joyful","energized","motivated","accomplished","proud","grateful","blessed"] else \
                  "🔴" if kw in ["terrible","awful","worst","exhausted","draining","anxious","stressed","overwhelmed","burned out","miserable","depressed","frustrated","angry","sad","lonely","hopeless"] else "⚪"
            print(f"   {cat} {kw}: {cnt}x")

    # Keyword correlation
    corr = keyword_rating_correlation(data)
    if corr:
        print("\n📊 Keyword ↔ Rating")
        for kw, info in sorted(corr.items(), key=lambda x: x[1]["avg"], reverse=True)[:5]:
            print(f"   {kw}: avg {info['avg']:.1f}/5 ({info['count']} days)")

    # Day of week
    dow = day_of_week_pattern(data)
    if dow:
        print("\n📅 Day of Week Pattern")
        names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        for i in range(7):
            if i in dow:
                print(f"   {names[i]}: {dow[i]['avg']:.1f}/5 ({dow[i]['count']} days)")

    best_dow, worst_dow = best_worst_days_of_week(data)
    if best_dow is not None:
        names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        print(f"\n   Best day:  {names[best_dow]}")
        print(f"   Worst day: {names[worst_dow]}")

    return 0


def cmd_keywords(args: list[str]) -> int:
    """Manage keywords."""
    if not args or args[0] == "list":
        cats = get_all_keywords()
        for cat, kws in cats.items():
            emoji = {"positive": "🟢", "neutral": "⚪", "negative": "🔴"}[cat]
            print(f"\n{emoji} {cat.capitalize()}: {', '.join(kws)}")
        return 0

    if args[0] == "add" and len(args) >= 3:
        kw = args[1]
        cat = args[2]
        from core.keywords import add_custom_keyword
        if add_custom_keyword(kw, cat):
            print(f"✅ Added '{kw}' to {cat}")
        else:
            print("❌ Failed (invalid category or already exists)")
        return 0

    if args[0] == "remove" and len(args) >= 2:
        from core.keywords import remove_keyword
        if remove_keyword(args[1]):
            print(f"✅ Removed '{args[1]}'")
        else:
            print("❌ Not found")
        return 0

    print("Usage: daylog keywords [list|add <kw> <cat>|remove <kw>]")
    return 1


def cmd_export(args: list[str]) -> int:
    """Export data to JSON file."""
    import json
    data = load_data()
    out = args[0] if args else "daylog_export.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported {len(data)} entries to {out}")
    return 0


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

COMMANDS = {
    "log": cmd_log,
    "history": cmd_history,
    "today": cmd_today,
    "weekly": cmd_weekly,
    "stats": cmd_stats,
    "keywords": cmd_keywords,
    "export": cmd_export,
}

def main() -> int:
    if len(sys.argv) < 2:
        print("Daylog CLI — Personal day logging")
        print("\nUsage: daylog <command> [args...]")
        print("\nCommands:")
        print("  log [--test RATING NOTES ANSWER]   Log today's entry")
        print("  history [N]                         Show last N entries")
        print("  today                               Show today's entry")
        print("  weekly [prev]                       Weekly review (current or previous week)")
        print("  stats                               Show statistics")
        print("  keywords [list|add|remove]          Manage keywords")
        print("  export [file.json]                  Export data")
        return 0

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        return 1

    return COMMANDS[cmd](args)


if __name__ == "__main__":
    sys.exit(main())