"""Today tab — Main day logging interface."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import random

from core.data import (
    load_data, save_data, today_key, validate_entry, get_entry
)
from core.keywords import (
    extract_keywords, suggest_keywords_for_entry, get_keyword_category
)
from core.data import QUESTIONS

from gui.widgets import StarRating, KeywordCloud, add_tooltip


class TodayTab(ttk.Frame):
    """Today tab: log today's rating, notes, reflection, and keywords."""

    def __init__(self, parent, on_data_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_data_change = on_data_change
        self.current_question = None
        self.selected_keywords = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Main container with padding
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Title ──────────────────────────────────────────────────────
        ttk.Label(main, text="🌅 How was your day?", font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(0, 20))

        # ── Star Rating ────────────────────────────────────────────────
        rating_frame = ttk.LabelFrame(main, text="Rating (0-5)", padding=15)
        rating_frame.pack(fill=tk.X, pady=(0, 15))

        self.star_rating = StarRating(rating_frame, value=0, command=self._on_rating_change)
        self.star_rating.pack(anchor=tk.W)

        self.rating_label = ttk.Label(rating_frame, text="Click stars to rate", font=("Segoe UI", 10), foreground="#666")
        self.rating_label.pack(anchor=tk.W, pady=(5, 0))

        # ── Notes ──────────────────────────────────────────────────────
        notes_frame = ttk.LabelFrame(main, text="Notes (optional)", padding=15)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.bind("<KeyRelease>", self._on_notes_change)

        # ── Reflection Question ────────────────────────────────────────
        reflect_frame = ttk.LabelFrame(main, text="💭 Daily Reflection", padding=15)
        reflect_frame.pack(fill=tk.X, pady=(0, 15))

        self.question_label = ttk.Label(reflect_frame, text="", font=("Segoe UI", 11, "italic"), wraplength=500)
        self.question_label.pack(anchor=tk.W, pady=(0, 10))

        self.reflection_text = tk.Text(reflect_frame, height=3, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.reflection_text.pack(fill=tk.X)

        ttk.Button(reflect_frame, text="🔄 New Question", command=self._new_question).pack(anchor=tk.E, pady=(8, 0))

        # ── Keywords ───────────────────────────────────────────────────
        kw_frame = ttk.LabelFrame(main, text="🏷️ Keywords (auto-suggested, click to edit)", padding=15)
        kw_frame.pack(fill=tk.X, pady=(0, 15))

        # Auto-suggested keywords (clickable cloud)
        self.keyword_cloud = KeywordCloud(
            kw_frame,
            keywords=[],
            get_category=get_keyword_category,
            on_add=self._on_keyword_add,
            on_remove=self._on_keyword_remove,
            editable=True,
        )
        self.keyword_cloud.pack(fill=tk.X)

        # Manual keyword entry
        manual_frame = ttk.Frame(kw_frame)
        manual_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(manual_frame, text="Add custom:").pack(side=tk.LEFT, padx=(0, 8))
        self.kw_entry = ttk.Entry(manual_frame, width=30)
        self.kw_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.kw_entry.bind("<Return>", lambda e: self._add_manual_keyword())
        ttk.Button(manual_frame, text="Add", command=self._add_manual_keyword).pack(side=tk.LEFT)

        # Category hint
        hint = ttk.Label(kw_frame, text="🟢 Positive  ⚪ Neutral  🔴 Negative", font=("Segoe UI", 8), foreground="#888")
        hint.pack(anchor=tk.W, pady=(5, 0))

        # ── Save Button ────────────────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.save_btn = ttk.Button(btn_frame, text="💾 Save Entry", command=self._save, style="Accent.TButton")
        self.save_btn.pack(side=tk.RIGHT)

        self.status_label = ttk.Label(btn_frame, text="", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.RIGHT, padx=(0, 20))

        # Style for accent button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=(20, 10))

    def _on_rating_change(self, value: int) -> None:
        labels = {0: "😞 Terrible", 1: "😕 Bad", 2: "😐 Meh", 3: "🙂 Okay", 4: "😊 Good", 5: "😍 Amazing"}
        self.rating_label.config(text=labels.get(value, ""))

    def _on_notes_change(self, event=None) -> None:
        # Auto-suggest keywords as user types (debounced)
        self.after(500, self._update_keyword_suggestions)

    def _update_keyword_suggestions(self) -> None:
        entry = {
            "notes": self.notes_text.get("1.0", tk.END).strip(),
            "reflection": {"answer": self.reflection_text.get("1.0", tk.END).strip()} if self.reflection_text.get("1.0", tk.END).strip() else None,
        }
        suggested = suggest_keywords_for_entry(entry)
        # Merge with manually added keywords
        all_kws = list(dict.fromkeys(suggested + self.selected_keywords))  # preserve order, dedupe
        self.keyword_cloud.refresh(all_kws)

    def _new_question(self) -> None:
        self.current_question = random.choice(QUESTIONS)
        self.question_label.config(text=self.current_question)

    def _on_keyword_add(self, kw: str) -> None:
        if kw not in self.selected_keywords:
            self.selected_keywords.append(kw)

    def _on_keyword_remove(self, kw: str) -> None:
        if kw in self.selected_keywords:
            self.selected_keywords.remove(kw)

    def _add_manual_keyword(self) -> None:
        kw = self.kw_entry.get().strip().lower()
        if kw and kw not in self.selected_keywords:
            self.selected_keywords.append(kw)
            self.keyword_cloud.add_keyword(kw)
            self.kw_entry.delete(0, tk.END)

    def refresh(self) -> None:
        """Reload today's entry if exists."""
        data = load_data()
        today = today_key()
        entry = data.get(today)

        # Pick a random question
        self.current_question = random.choice(QUESTIONS)
        self.question_label.config(text=self.current_question)

        if entry:
            # Populate existing entry
            self.star_rating.set(entry.get("rating", 0))
            self._on_rating_change(entry.get("rating", 0))

            if entry.get("notes"):
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", entry["notes"])

            if entry.get("reflection"):
                self.reflection_text.delete("1.0", tk.END)
                self.reflection_text.insert("1.0", entry["reflection"].get("answer", ""))

            # Load keywords
            self.selected_keywords = entry.get("keywords", [])[:]
        else:
            # Clear form
            self.star_rating.set(0)
            self._on_rating_change(0)
            self.notes_text.delete("1.0", tk.END)
            self.reflection_text.delete("1.0", tk.END)
            self.selected_keywords = []

        # Update keyword cloud
        self.keyword_cloud.refresh(self.selected_keywords)
        self._update_save_button_state()

    def _update_save_button_state(self) -> None:
        data = load_data()
        today = today_key()
        if today in data:
            self.save_btn.config(text="💾 Update Entry")
            self.status_label.config(text="✓ Already logged today", foreground="green")
        else:
            self.save_btn.config(text="💾 Save Entry")
            self.status_label.config(text="")

    def _save(self) -> None:
        rating = self.star_rating.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        reflection_answer = self.reflection_text.get("1.0", tk.END).strip()

        if rating == 0:
            messagebox.showwarning("Missing Rating", "Please select a rating (1-5 stars).")
            return

        entry = {"rating": rating}
        if notes:
            entry["notes"] = notes
        if reflection_answer and self.current_question:
            entry["reflection"] = {"question": self.current_question, "answer": reflection_answer}

        # Keywords: merge suggested + manual
        entry["keywords"] = list(dict.fromkeys(self.selected_keywords + self.keyword_cloud.get_keywords()))

        data = load_data()
        data[today_key()] = validate_entry(entry)
        save_data(data)

        messagebox.showinfo("Saved", f"Entry saved for {today_key()}!")
        self.refresh()

        if self.on_data_change:
            self.on_data_change()


def create_today_tab(parent, on_data_change=None) -> TodayTab:
    """Factory function for Today tab."""
    return TodayTab(parent, on_data_change=on_data_change)