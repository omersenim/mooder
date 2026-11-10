#!/usr/bin/env python3
"""Day Logging System - Rate your day, add notes, answer a random reflection question."""

import json
import random
from datetime import date, datetime
from pathlib import Path

# Storage file
DATA_FILE = Path("daylog_data.json")

# Pool of reflection questions
QUESTIONS = [
    "What were you most happy about today?",
    "What made you sad or disappointed today?",
    "What's one thing you learned today?",
    "What would you do differently if you could relive today?",
    "Who or what are you grateful for today?",
    "What challenged you today, and how did you handle it?",
    "What's a small win you had today?",
    "Did you take care of yourself today? How?",
    "What made you laugh or smile today?",
    "What's one thing you're looking forward to tomorrow?",
    "How present were you today? What pulled you away?",
    "What drained your energy today? What restored it?",
]

def load_data():
    """Load existing log data."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    """Save log data to file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_today_key():
    """Get today's date as ISO string key."""
    return date.today().isoformat()

def prompt_rating():
    """Get day rating from user (0-5)."""
    while True:
        try:
            rating = input("Rate your day (0-5): ").strip()
            if rating == "":
                return None
            rating = int(rating)
            if 0 <= rating <= 5:
                return rating
            print("Please enter a number between 0 and 5.")
        except ValueError:
            print("Please enter a valid number.")

def prompt_notes():
    """Get optional notes from user."""
    notes = input("Quick notes (optional): ").strip()
    return notes if notes else None

def prompt_question():
    """Ask a random reflection question."""
    question = random.choice(QUESTIONS)
    print(f"\n🤔 Reflection: {question}")
    answer = input("Your answer: ").strip()
    return {"question": question, "answer": answer} if answer else None

def view_history(data):
    """Display past entries."""
    if not data:
        print("No entries yet.")
        return

    print("\n📅 Your Day Log History:")
    print("-" * 50)
    for day_key in sorted(data.keys(), reverse=True):
        entry = data[day_key]
        rating = entry.get("rating", "?")
        stars = "★" * rating + "☆" * (5 - rating) if isinstance(rating, int) else "?"
        notes = entry.get("notes", "")
        reflection = entry.get("reflection", {})

        print(f"{day_key}  [{stars}]  {rating}/5")
        if notes:
            print(f"       📝 {notes}")
        if reflection:
            print(f"       💭 {reflection['question']}")
            print(f"       → {reflection['answer']}")
        print()

def main():
    import sys

    # Non-interactive test mode: python daylog.py --test "4" "notes" "answer"
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_rating = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        test_notes = sys.argv[3] if len(sys.argv) > 3 else "test notes"
        test_answer = sys.argv[4] if len(sys.argv) > 4 else "test answer"

        data = load_data()
        today = get_today_key()

        entry = {
            "rating": test_rating,
            "notes": test_notes,
            "reflection": {
                "question": "What were you most happy about today? (test)",
                "answer": test_answer
            },
            "timestamp": datetime.now().isoformat()
        }
        data[today] = entry
        save_data(data)
        print(f"✅ Test entry saved for {today}")
        view_history(data)
        return

    print("🌅 Day Logging System")
    print("=" * 30)

    data = load_data()
    today = get_today_key()

    # Check if today already logged
    if today in data:
        print(f"Today ({today}) already logged:")
        entry = data[today]
        print(f"  Rating: {entry.get('rating', '?')}/5")
        if entry.get("notes"):
            print(f"  Notes: {entry['notes']}")
        if entry.get("reflection"):
            print(f"  Reflection: {entry['reflection']['question']}")

        overwrite = input("\nOverwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Keeping existing entry.")
            view_history(data)
            return

    # New entry
    print(f"\nLogging for {today}")
    print("-" * 30)

    rating = prompt_rating()
    notes = prompt_notes()
    reflection = prompt_question()

    # Build entry
    entry = {}
    if rating is not None:
        entry["rating"] = rating
    if notes:
        entry["notes"] = notes
    if reflection:
        entry["reflection"] = reflection
    entry["timestamp"] = datetime.now().isoformat()

    data[today] = entry
    save_data(data)

    print(f"\n✅ Saved entry for {today}")

    # Show history
    view_history(data)

if __name__ == "__main__":
    main()