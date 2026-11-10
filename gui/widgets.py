"""Reusable Tkinter widgets for daylog GUI."""

import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
from typing import Callable, Optional
import calendar


# ──────────────────────────────────────────────────────────────────────
# StarRating — Clickable 0-5 stars
# ──────────────────────────────────────────────────────────────────────

class StarRating(ttk.Frame):
    """Clickable star rating widget (0-5)."""

    def __init__(self, parent, value: int = 0, command: Callable[[int], None] | None = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.value = value
        self.command = command
        self.stars: list[ttk.Label] = []
        self._build()

    def _build(self) -> None:
        for i in range(5):
            lbl = ttk.Label(self, text="★", font=("Segoe UI Emoji", 24), cursor="hand2")
            lbl.grid(row=0, column=i, padx=2)
            lbl.bind("<Enter>", lambda e, idx=i: self._hover(idx))
            lbl.bind("<Leave>", lambda e: self._refresh())
            lbl.bind("<Button-1>", lambda e, idx=i: self._click(idx))
            self.stars.append(lbl)
        self.bind("<Leave>", lambda e: self._refresh())
        self._refresh()

    def _hover(self, idx: int) -> None:
        for i, lbl in enumerate(self.stars):
            lbl.config(text="★" if i <= idx else "☆", foreground="gold" if i <= idx else "gray")

    def _refresh(self) -> None:
        for i, lbl in enumerate(self.stars):
            lbl.config(text="★" if i < self.value else "☆", foreground="gold" if i < self.value else "gray")

    def _click(self, idx: int) -> None:
        self.value = idx + 1
        self._refresh()
        if self.command:
            self.command(self.value)

    def get(self) -> int:
        return self.value

    def set(self, value: int) -> None:
        self.value = max(0, min(5, value))
        self._refresh()


# ──────────────────────────────────────────────────────────────────────
# CalendarHeatmap — Month view with colored days
# ──────────────────────────────────────────────────────────────────────

class CalendarHeatmap(ttk.Frame):
    """Month calendar with color-coded day ratings."""

    def __init__(
        self,
        parent,
        ratings: dict[str, int],  # {YYYY-MM-DD: rating}
        on_day_click: Callable[[date], None] | None = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.ratings = ratings
        self.on_day_click = on_day_click
        self.current_month = date.today().replace(day=1)
        self.day_buttons: dict[int, ttk.Button] = {}
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Header with month navigation
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(header, text="◀", width=3, command=self._prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(header, text="", font=("Segoe UI", 11, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(header, text="▶", width=3, command=self._next_month).pack(side=tk.RIGHT)

        # Day names
        days_frame = ttk.Frame(self)
        days_frame.pack(fill=tk.X)
        for i, name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
            ttk.Label(days_frame, text=name, width=4, anchor=tk.CENTER, font=("Segoe UI", 8)).grid(row=0, column=i, padx=1, pady=1)

        # Calendar grid
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

    def _prev_month(self) -> None:
        if self.current_month.month == 1:
            self.current_month = self.current_month.replace(year=self.current_month.year - 1, month=12)
        else:
            self.current_month = self.current_month.replace(month=self.current_month.month - 1)
        self.refresh()

    def _next_month(self) -> None:
        if self.current_month.month == 12:
            self.current_month = self.current_month.replace(year=self.current_month.year + 1, month=1)
        else:
            self.current_month = self.current_month.replace(month=self.current_month.month + 1)
        self.refresh()

    def _rating_color(self, rating: int) -> str:
        """Return hex color for rating 0-5."""
        # Green to red gradient
        colors = {
            5: "#2e7d32",  # dark green
            4: "#66bb6a",  # green
            3: "#ffeb3b",  # yellow
            2: "#ffa726",  # orange
            1: "#ef5350",  # red
            0: "#b71c1c",  # dark red
        }
        return colors.get(rating, "#757575")

    def refresh(self, ratings: dict[str, int] | None = None) -> None:
        """Update with new ratings data."""
        if ratings is not None:
            self.ratings = ratings

        # Clear existing buttons
        for btn in self.day_buttons.values():
            btn.destroy()
        self.day_buttons.clear()

        # Update month label
        self.month_label.config(text=self.current_month.strftime("%B %Y"))

        # Calculate calendar
        cal = calendar.monthcalendar(self.current_month.year, self.current_month.month)
        # calendar.monthcalendar returns weeks starting Monday; we want Sunday start
        # Adjust: shift each week so Sunday is first column
        adjusted_cal = []
        for week in cal:
            # week = [Mon, Tue, Wed, Thu, Fri, Sat, Sun] (0=Mon, 6=Sun)
            # We want [Sun, Mon, Tue, Wed, Thu, Fri, Sat]
            adjusted_cal.append([week[6]] + week[:6])

        # Create buttons
        for r, week in enumerate(adjusted_cal):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    # Empty cell (previous/next month)
                    lbl = ttk.Label(self.grid_frame, text="", width=4)
                    lbl.grid(row=r, column=c, padx=1, pady=1)
                else:
                    d = date(self.current_month.year, self.current_month.month, day_num)
                    key = d.isoformat()
                    rating = self.ratings.get(key)

                    if rating is not None:
                        color = self._rating_color(rating)
                        text = str(day_num)
                        style = "CalendarDay.Rated.TButton"
                    else:
                        color = "#e0e0e0"
                        text = str(day_num)
                        style = "CalendarDay.Empty.TButton"

                    btn = ttk.Button(
                        self.grid_frame,
                        text=text,
                        width=4,
                        style=style,
                        command=lambda dt=d: self._on_click(dt)
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1)
                    # Store rating as attribute for tooltip
                    btn.rating = rating
                    self.day_buttons[day_num] = btn

        # Configure styles
        style = ttk.Style()
        style.configure("CalendarDay.Rated.TButton", font=("Segoe UI", 9, "bold"))
        style.configure("CalendarDay.Empty.TButton", font=("Segoe UI", 9), foreground="#999")

    def _on_click(self, d: date) -> None:
        if self.on_day_click:
            self.on_day_click(d)

    def update_ratings(self, ratings: dict[str, int]) -> None:
        """Update ratings without changing month."""
        self.ratings = ratings
        self.refresh()


# ──────────────────────────────────────────────────────────────────────
# KeywordCloud — Clickable keyword tags
# ──────────────────────────────────────────────────────────────────────

class KeywordCloud(ttk.Frame):
    """Flow layout of clickable keyword tags with category colors."""

    CATEGORY_COLORS = {
        "positive": ("#e8f5e9", "#2e7d32"),   # light bg, dark fg
        "neutral": ("#f5f5f5", "#616161"),
        "negative": ("#fdecea", "#c62828"),
    }

    def __init__(
        self,
        parent,
        keywords: list[str],
        get_category: Callable[[str], str | None],
        on_add: Callable[[str], None] | None = None,
        on_remove: Callable[[str], None] | None = None,
        editable: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.keywords = keywords[:]
        self.get_category = get_category
        self.on_add = on_add
        self.on_remove = on_remove
        self.editable = editable
        self.tag_labels: dict[str, ttk.Label] = {}
        self._build()

    def _build(self) -> None:
        self.canvas = tk.Canvas(self, highlightthickness=0, height=80)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.inner = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_configure(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfig(self.canvas_window, height=event.height)

    def refresh(self, keywords: list[str] | None = None) -> None:
        if keywords is not None:
            self.keywords = keywords[:]

        # Clear
        for lbl in self.tag_labels.values():
            lbl.destroy()
        self.tag_labels.clear()

        # Rebuild
        for kw in self.keywords:
            self._add_tag(kw)

    def _add_tag(self, kw: str) -> None:
        cat = self.get_category(kw) or "neutral"
        bg, fg = self.CATEGORY_COLORS.get(cat, self.CATEGORY_COLORS["neutral"])

        frame = ttk.Frame(self.inner)
        frame.pack(side=tk.LEFT, padx=4, pady=4)

        lbl = tk.Label(
            frame,
            text=kw,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9),
            padx=8,
            pady=3,
            cursor="hand2",
            relief=tk.RAISED,
            bd=1,
        )
        lbl.pack(side=tk.LEFT)
        lbl.bind("<Button-1>", lambda e, k=kw: self._on_click(k))
        self.tag_labels[kw] = lbl

        if self.editable and self.on_remove:
            # Small × button
            btn = tk.Label(frame, text="×", bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=2)
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, k=kw: self._on_remove(k))

    def _on_click(self, kw: str) -> None:
        if self.editable and self.on_remove:
            self._on_remove(kw)
        # Non-editable: just visual feedback

    def _on_remove(self, kw: str) -> None:
        if kw in self.keywords:
            self.keywords.remove(kw)
            if self.on_remove:
                self.on_remove(kw)
            self.refresh()

    def add_keyword(self, kw: str) -> None:
        if kw not in self.keywords:
            self.keywords.append(kw)
            self._add_tag(kw)
            if self.on_add:
                self.on_add(kw)

    def get_keywords(self) -> list[str]:
        return self.keywords[:]


# ──────────────────────────────────────────────────────────────────────
# Tooltip helper
# ──────────────────────────────────────────────────────────────────────

class ToolTip:
    """Simple tooltip for any widget."""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None) -> None:
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("Segoe UI", 8), padx=6, pady=3
        )
        label.pack()

    def hide(self, event=None) -> None:
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def add_tooltip(widget, text: str) -> ToolTip:
    """Attach a tooltip to a widget."""
    return ToolTip(widget, text)