"""History tab — Calendar heatmap with day editing."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta
from typing import Optional

from core.data import (
    load_data, save_data, get_entry, delete_entry, validate_entry
)
from core.keywords import get_keyword_category, extract_keywords

from gui.widgets import CalendarHeatmap, KeywordCloud, add_tooltip, StarRating


class HistoryTab(ttk.Frame):
    """History tab: Calendar heatmap, click to view/edit entries, filter by keyword."""

    def __init__(self, parent, on_data_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_data_change = on_data_change
        self.selected_date: Optional[date] = None
        self.filter_keyword: Optional[str] = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self, padding=10)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="📅 History", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)

        # Filter by keyword
        ttk.Label(toolbar, text="Filter:").pack(side=tk.LEFT, padx=(20, 5))
        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, width=20, state="readonly")
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)
        ttk.Button(toolbar, text="Clear", command=self._clear_filter).pack(side=tk.LEFT)

        # Main content: Calendar on left, detail on right
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # ── Left: Calendar Heatmap ─────────────────────────────────────
        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.calendar = CalendarHeatmap(
            left,
            ratings={},
            on_day_click=self._on_day_click,
        )
        self.calendar.pack(fill=tk.BOTH, expand=True)

        # ── Right: Day Detail Panel ────────────────────────────────────
        right = ttk.LabelFrame(content, text="Day Details", padding=15)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right.configure(width=350)

        self.detail_date_label = ttk.Label(right, text="Click a day", font=("Segoe UI", 12, "bold"))
        self.detail_date_label.pack(anchor=tk.W, pady=(0, 15))

        # Rating display
        ttk.Label(right, text="Rating:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.detail_stars = StarRating(right, value=0)
        self.detail_stars.pack(anchor=tk.W, pady=(0, 10))

        # Notes
        ttk.Label(right, text="Notes:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.detail_notes = tk.Text(right, height=4, width=35, wrap=tk.WORD, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        self.detail_notes.pack(fill=tk.X, pady=(0, 10))

        # Reflection
        ttk.Label(right, text="Reflection:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.detail_reflection = tk.Text(right, height=3, width=35, wrap=tk.WORD, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        self.detail_reflection.pack(fill=tk.X, pady=(0, 10))

        # Keywords
        ttk.Label(right, text="Keywords:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.detail_keywords = KeywordCloud(
            right,
            keywords=[],
            get_category=get_keyword_category,
            on_add=self._on_detail_kw_add,
            on_remove=self._on_detail_kw_remove,
            editable=True,
        )
        self.detail_keywords.pack(fill=tk.X, pady=(0, 15))

        # Action buttons
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=tk.X)
        self.edit_btn = ttk.Button(btn_frame, text="✏️ Edit", command=self._edit_day, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.delete_btn = ttk.Button(btn_frame, text="🗑️ Delete", command=self._delete_day, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT)

        # Legend
        legend = ttk.Frame(self, padding=(10, 0))
        legend.pack(fill=tk.X)
        ttk.Label(legend, text="Legend:").pack(side=tk.LEFT)
        colors = [
            ("🟢 5", "#2e7d32"), ("🟢 4", "#66bb6a"), ("🟡 3", "#ffeb3b"),
            ("🟠 2", "#ffa726"), ("🔴 1", "#ef5350"), ("⚫ 0", "#b71c1c"), ("⚪ None", "#e0e0e0"),
        ]
        for label, color in colors:
            frm = ttk.Frame(legend)
            frm.pack(side=tk.LEFT, padx=8)
            canvas = tk.Canvas(frm, width=16, height=16, highlightthickness=0)
            canvas.create_rectangle(2, 2, 14, 14, fill=color, outline="#999")
            canvas.pack(side=tk.LEFT)
            ttk.Label(frm, text=label, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(4, 0))

    def refresh(self) -> None:
        """Reload data and update calendar."""
        data = load_data()

        # Build ratings dict for calendar
        ratings = {}
        all_keywords = set()
        for day_key, entry in data.items():
            if isinstance(entry.get("rating"), int):
                ratings[day_key] = entry["rating"]
            for kw in entry.get("keywords", []):
                all_keywords.add(kw)

        # Apply filter
        if self.filter_keyword:
            filtered_ratings = {}
            for day_key, rating in ratings.items():
                entry = data.get(day_key, {})
                if self.filter_keyword in entry.get("keywords", []):
                    filtered_ratings[day_key] = rating
            ratings = filtered_ratings

        self.calendar.update_ratings(ratings)

        # Update filter dropdown
        kw_list = ["All"] + sorted(all_keywords)
        self.filter_combo["values"] = kw_list
        if not self.filter_keyword:
            self.filter_var.set("All")

        # Clear detail panel
        self._clear_detail()

    def _clear_detail(self) -> None:
        self.selected_date = None
        self.detail_date_label.config(text="Click a day")
        self.detail_stars.set(0)
        self.detail_notes.delete("1.0", tk.END)
        self.detail_reflection.delete("1.0", tk.END)
        self.detail_keywords.refresh([])
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

    def _on_day_click(self, d: date) -> None:
        """Show details for clicked day."""
        self.selected_date = d
        day_key = d.isoformat()
        data = load_data()
        entry = data.get(day_key)

        self.detail_date_label.config(text=d.strftime("%A, %B %d, %Y"))

        if entry:
            rating = entry.get("rating", 0)
            self.detail_stars.set(rating)

            self.detail_notes.delete("1.0", tk.END)
            if entry.get("notes"):
                self.detail_notes.insert("1.0", entry["notes"])

            self.detail_reflection.delete("1.0", tk.END)
            if entry.get("reflection"):
                r = entry["reflection"]
                self.detail_reflection.insert("1.0", f"Q: {r.get('question', '')}\nA: {r.get('answer', '')}")

            self.detail_keywords.refresh(entry.get("keywords", []))

            self.edit_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)
        else:
            self.detail_stars.set(0)
            self.detail_notes.delete("1.0", tk.END)
            self.detail_reflection.delete("1.0", tk.END)
            self.detail_keywords.refresh([])
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)

    def _on_filter_change(self, event=None) -> None:
        val = self.filter_var.get()
        self.filter_keyword = None if val == "All" else val
        self.refresh()

    def _clear_filter(self) -> None:
        self.filter_var.set("All")
        self.filter_keyword = None
        self.refresh()

    def _on_detail_kw_add(self, kw: str) -> None:
        if self.selected_date:
            self._update_day_keywords(kw, add=True)

    def _on_detail_kw_remove(self, kw: str) -> None:
        if self.selected_date:
            self._update_day_keywords(kw, add=False)

    def _update_day_keywords(self, kw: str, add: bool) -> None:
        if not self.selected_date:
            return
        day_key = self.selected_date.isoformat()
        data = load_data()
        entry = data.get(day_key, {})
        keywords = entry.get("keywords", [])[:]

        if add and kw not in keywords:
            keywords.append(kw)
        elif not add and kw in keywords:
            keywords.remove(kw)

        entry["keywords"] = keywords
        data[day_key] = validate_entry(entry)
        save_data(data)
        self.refresh()
        if self.on_data_change:
            self.on_data_change()

    def _edit_day(self) -> None:
        if not self.selected_date:
            return
        day_key = self.selected_date.isoformat()
        data = load_data()
        entry = data.get(day_key, {})

        # Create edit dialog
        dialog = EditDayDialog(self, day_key, entry)
        self.wait_window(dialog)
        if dialog.result:
            data[day_key] = validate_entry(dialog.result)
            save_data(data)
            self.refresh()
            if self.on_data_change:
                self.on_data_change()

    def _delete_day(self) -> None:
        if not self.selected_date:
            return
        day_key = self.selected_date.isoformat()
        if messagebox.askyesno("Delete Entry", f"Delete entry for {day_key}?"):
            data = load_data()
            if day_key in data:
                delete_entry(data, day_key)
                save_data(data)
                self.refresh()
                if self.on_data_change:
                    self.on_data_change()


class EditDayDialog(tk.Toplevel):
    """Dialog to edit a day's entry."""

    def __init__(self, parent, day_key: str, entry: dict):
        super().__init__(parent)
        self.title(f"Edit {day_key}")
        self.geometry("450x550")
        self.resizable(False, False)
        self.day_key = day_key
        self.result = None

        self.transient(parent)
        self.grab_set()

        self._build(entry)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build(self, entry: dict) -> None:
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Rating
        ttk.Label(main, text="Rating:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        self.star_rating = StarRating(main, value=entry.get("rating", 0))
        self.star_rating.pack(anchor=tk.W, pady=(0, 15))

        # Notes
        ttk.Label(main, text="Notes:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        self.notes_text = tk.Text(main, height=5, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.notes_text.pack(fill=tk.X, pady=(0, 15))
        if entry.get("notes"):
            self.notes_text.insert("1.0", entry["notes"])

        # Reflection
        ttk.Label(main, text="Reflection:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        self.reflection_text = tk.Text(main, height=4, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.reflection_text.pack(fill=tk.X, pady=(0, 15))
        if entry.get("reflection"):
            r = entry["reflection"]
            self.reflection_text.insert("1.0", f"Q: {r.get('question', '')}\nA: {r.get('answer', '')}")

        # Keywords
        ttk.Label(main, text="Keywords (comma-separated):", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        self.kw_entry = ttk.Entry(main, font=("Segoe UI", 10))
        self.kw_entry.pack(fill=tk.X, pady=(0, 20))
        if entry.get("keywords"):
            self.kw_entry.insert(0, ", ".join(entry["keywords"]))

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Save", command=self._on_save, style="Accent.TButton").pack(side=tk.RIGHT)

    def _on_save(self) -> None:
        rating = self.star_rating.get()
        if rating == 0:
            messagebox.showwarning("Missing Rating", "Please select a rating (1-5 stars).", parent=self)
            return

        notes = self.notes_text.get("1.0", tk.END).strip()
        reflection_text = self.reflection_text.get("1.0", tk.END).strip()
        kw_text = self.kw_entry.get().strip()

        # Parse reflection if present
        reflection = None
        if reflection_text:
            lines = reflection_text.split("\n", 1)
            q = lines[0].replace("Q: ", "").strip()
            a = lines[1].replace("A: ", "").strip() if len(lines) > 1 else ""
            if q and a:
                reflection = {"question": q, "answer": a}

        keywords = [k.strip().lower() for k in kw_text.split(",") if k.strip()] if kw_text else []

        self.result = {"rating": rating}
        if notes:
            self.result["notes"] = notes
        if reflection:
            self.result["reflection"] = reflection
        if keywords:
            self.result["keywords"] = keywords

        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def create_history_tab(parent, on_data_change=None) -> HistoryTab:
    """Factory function for History tab."""
    return HistoryTab(parent, on_data_change=on_data_change)