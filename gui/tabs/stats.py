"""Stats tab — Analytics dashboard with charts and trends."""

import tkinter as tk
from tkinter import ttk
from datetime import date
from collections import Counter

from core.data import load_data
from core.stats import (
    overall_stats, monthly_stats, rolling_average,
    keyword_frequency, keyword_rating_correlation, top_keywords,
    weekly_series, monthly_series, day_of_week_pattern, best_worst_days_of_week
)
from core.weekly import current_streak, longest_streak

from gui.widgets import KeywordCloud, add_tooltip


class StatsTab(ttk.Frame):
    """Stats tab: Overall stats, rolling averages, keyword analysis, trends."""

    def __init__(self, parent, on_data_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_data_change = on_data_change
        self._build()
        self.refresh()

    def _build(self) -> None:
        # Scrollable canvas
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.content = ttk.Frame(canvas, padding=20)
        canvas_window = canvas.create_window((0, 0), window=self.content, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        self.content.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── Title ──────────────────────────────────────────────────────
        ttk.Label(self.content, text="📈 Statistics & Trends", font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(0, 20))

        # ── Overall Stats Cards ────────────────────────────────────────
        self.overall_frame = ttk.LabelFrame(self.content, text="Overall", padding=15)
        self.overall_frame.pack(fill=tk.X, pady=(0, 15))

        self.overall_grid = ttk.Frame(self.overall_frame)
        self.overall_grid.pack(fill=tk.X)

        # ── Rolling Averages ───────────────────────────────────────────
        self.rolling_frame = ttk.LabelFrame(self.content, text="Rolling Averages", padding=15)
        self.rolling_frame.pack(fill=tk.X, pady=(0, 15))

        self.rolling_grid = ttk.Frame(self.rolling_frame)
        self.rolling_grid.pack(fill=tk.X)

        # ── Streaks ────────────────────────────────────────────────────
        self.streak_frame = ttk.LabelFrame(self.content, text="🔥 Streaks", padding=15)
        self.streak_frame.pack(fill=tk.X, pady=(0, 15))

        self.streak_label = ttk.Label(self.streak_frame, text="", font=("Segoe UI", 12))
        self.streak_label.pack(anchor=tk.W)

        # ── Keyword Frequency ──────────────────────────────────────────
        kw_frame = ttk.LabelFrame(self.content, text="🏷️ Keyword Frequency", padding=15)
        kw_frame.pack(fill=tk.X, pady=(0, 15))

        self.keyword_cloud = KeywordCloud(
            kw_frame,
            keywords=[],
            get_category=lambda kw: self._get_kw_category(kw),
        )
        self.keyword_cloud.pack(fill=tk.X, pady=(0, 10))

        self.keyword_list = tk.Text(kw_frame, height=8, wrap=tk.WORD, font=("Consolas", 9), relief=tk.SOLID, bd=1)
        self.keyword_list.pack(fill=tk.X)

        # ── Keyword ↔ Rating Correlation ───────────────────────────────
        corr_frame = ttk.LabelFrame(self.content, text="📊 Keyword ↔ Rating Correlation", padding=15)
        corr_frame.pack(fill=tk.X, pady=(0, 15))

        self.corr_text = tk.Text(corr_frame, height=6, wrap=tk.WORD, font=("Consolas", 9), relief=tk.SOLID, bd=1)
        self.corr_text.pack(fill=tk.X)

        # ── Weekly Trend ───────────────────────────────────────────────
        week_frame = ttk.LabelFrame(self.content, text="📅 Weekly Trend (Last 12 Weeks)", padding=15)
        week_frame.pack(fill=tk.X, pady=(0, 15))

        self.week_canvas = tk.Canvas(week_frame, height=120, highlightthickness=1, highlightbackground="#ddd")
        self.week_canvas.pack(fill=tk.X)

        # ── Monthly Trend ──────────────────────────────────────────────
        month_frame = ttk.LabelFrame(self.content, text="📅 Monthly Trend (Last 12 Months)", padding=15)
        month_frame.pack(fill=tk.X, pady=(0, 15))

        self.month_canvas = tk.Canvas(month_frame, height=120, highlightthickness=1, highlightbackground="#ddd")
        self.month_canvas.pack(fill=tk.X)

        # ── Day of Week Pattern ────────────────────────────────────────
        dow_frame = ttk.LabelFrame(self.content, text="📅 Day of Week Pattern", padding=15)
        dow_frame.pack(fill=tk.X, pady=(0, 15))

        self.dow_canvas = tk.Canvas(dow_frame, height=100, highlightthickness=1, highlightbackground="#ddd")
        self.dow_canvas.pack(fill=tk.X)

    def _get_kw_category(self, kw: str) -> str:
        positive = {"amazing", "awesome", "great", "productive", "wonderful", "fantastic", "excellent",
                    "brilliant", "joyful", "energized", "motivated", "accomplished", "proud", "grateful", "blessed",
                    "happy", "good", "nice", "love", "best", "perfect", "super", "cool", "fun", "relaxed", "peaceful"}
        negative = {"terrible", "awful", "worst", "exhausted", "draining", "anxious", "stressed", "overwhelmed",
                    "burned out", "miserable", "depressed", "frustrated", "angry", "sad", "lonely", "hopeless",
                    "bad", "horrible", "hate", "pain", "tired", "sick", "upset", "worried", "bored"}
        if kw in positive:
            return "positive"
        if kw in negative:
            return "negative"
        return "neutral"

    def refresh(self) -> None:
        """Reload all stats and redraw."""
        data = load_data()

        if not data:
            self._show_empty()
            return

        # ── Overall Stats ──────────────────────────────────────────────
        ov = overall_stats(data)
        self._clear_frame(self.overall_grid)

        cards = [
            ("📅 Total Days", str(ov['total_days'])),
            ("⭐ Avg Rating", f"{ov['avg_rating']:.2f}/5"),
            ("🌟 Best Day", f"{ov['best_day']['date']} ({ov['best_day']['rating']}/5)" if ov['best_day'] else "—"),
            ("😔 Worst Day", f"{ov['worst_day']['date']} ({ov['worst_day']['rating']}/5)" if ov['worst_day'] else "—"),
        ]
        for i, (label, value) in enumerate(cards):
            card = ttk.Frame(self.overall_grid, relief=tk.RAISED, borderwidth=1, padding=15)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.overall_grid.columnconfigure(i, weight=1)
            ttk.Label(card, text=label, font=("Segoe UI", 9), foreground="#666").pack()
            ttk.Label(card, text=value, font=("Segoe UI", 14, "bold")).pack()

        # ── Rolling Averages ───────────────────────────────────────────
        self._clear_frame(self.rolling_grid)

        periods = [
            ("Last 7 days", 7),
            ("Last 30 days", 30),
            ("Last 90 days", 90),
        ]
        for i, (label, days) in enumerate(periods):
            ra = rolling_average(data, days)
            card = ttk.Frame(self.rolling_grid, relief=tk.RAISED, borderwidth=1, padding=15)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.rolling_grid.columnconfigure(i, weight=1)
            ttk.Label(card, text=label, font=("Segoe UI", 9), foreground="#666").pack()
            ttk.Label(card, text=f"{ra:.2f}/5" if ra else "—", font=("Segoe UI", 14, "bold")).pack()

        # ── Streaks ────────────────────────────────────────────────────
        self.streak_label.config(text=f"Current streak: {current_streak(data)} days  |  Longest streak: {longest_streak(data)} days")

        # ── Keyword Frequency ──────────────────────────────────────────
        kw_freq = keyword_frequency(data)
        top_kws = top_keywords(data, 20)
        self.keyword_cloud.refresh([kw for kw, _ in top_kws])

        self.keyword_list.config(state=tk.NORMAL)
        self.keyword_list.delete("1.0", tk.END)
        lines = []
        for kw, count in top_kws:
            cat = self._get_kw_category(kw)
            emoji = "🟢" if cat == "positive" else "🔴" if cat == "negative" else "⚪"
            # Get correlation
            corr = keyword_rating_correlation(data).get(kw, {})
            avg = f" (avg {corr['avg']:.1f}/5)" if corr else ""
            lines.append(f"{emoji} {kw:<20} {count:>3}x{avg}")
        self.keyword_list.insert("1.0", "\n".join(lines))
        self.keyword_list.config(state=tk.DISABLED)

        # ── Keyword Correlation ────────────────────────────────────────
        corr = keyword_rating_correlation(data)
        self.corr_text.config(state=tk.NORMAL)
        self.corr_text.delete("1.0", tk.END)
        if corr:
            lines = ["Keywords with most positive/negative correlation to rating:\n"]
            sorted_corr = sorted(corr.items(), key=lambda x: x[1]['avg'], reverse=True)
            # Top 5 positive
            lines.append("🟢 Most Positive:")
            for kw, info in sorted_corr[:5]:
                lines.append(f"   {kw:<20} → avg {info['avg']:.2f}/5 ({info['count']} days)")
            lines.append("")
            # Top 5 negative
            lines.append("🔴 Most Negative:")
            for kw, info in sorted_corr[-5:]:
                lines.append(f"   {kw:<20} → avg {info['avg']:.2f}/5 ({info['count']} days)")
            self.corr_text.insert("1.0", "\n".join(lines))
        else:
            self.corr_text.insert("1.0", "No keyword data yet.")
        self.corr_text.config(state=tk.DISABLED)

        # ── Weekly Trend Chart ─────────────────────────────────────────
        self._draw_weekly_chart(data)

        # ── Monthly Trend Chart ────────────────────────────────────────
        self._draw_monthly_chart(data)

        # ── Day of Week Chart ──────────────────────────────────────────
        self._draw_dow_chart(data)

    def _show_empty(self) -> None:
        self._clear_frame(self.overall_grid)
        ttk.Label(self.overall_grid, text="No data yet. Log some days first!").pack(pady=20)
        self._clear_frame(self.rolling_grid)
        self.streak_label.config(text="")
        self.keyword_cloud.refresh([])
        self.keyword_list.config(state=tk.NORMAL)
        self.keyword_list.delete("1.0", tk.END)
        self.keyword_list.insert("1.0", "No keywords yet.")
        self.keyword_list.config(state=tk.DISABLED)
        self.corr_text.config(state=tk.NORMAL)
        self.corr_text.delete("1.0", tk.END)
        self.corr_text.insert("1.0", "No data.")
        self.corr_text.config(state=tk.DISABLED)
        self.week_canvas.delete("all")
        self.month_canvas.delete("all")
        self.dow_canvas.delete("all")

    def _clear_frame(self, frame: ttk.Frame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()

    def _draw_weekly_chart(self, data: dict) -> None:
        """Draw simple bar chart for weekly averages."""
        c = self.week_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 600
        h = c.winfo_height() or 120

        series = weekly_series(data, 12)
        if not series:
            c.create_text(w//2, h//2, text="No weekly data", fill="#999", font=("Segoe UI", 10))
            return

        # Reverse to show oldest first
        series = list(reversed(series))
        n = len(series)
        bar_w = max(20, (w - 40) // n - 10)
        gap = 10
        max_val = 5.0

        for i, week in enumerate(series):
            avg = week['avg']
            x0 = 20 + i * (bar_w + gap)
            x1 = x0 + bar_w
            y0 = h - 20
            y1 = h - 20 - int((avg / max_val) * (h - 40))

            color = self._rating_color(avg)
            c.create_rectangle(x0, y1, x1, y0, fill=color, outline="")
            c.create_text((x0 + x1) // 2, y1 - 10, text=f"{avg:.1f}", font=("Segoe UI", 7), fill="#333")
            c.create_text((x0 + x1) // 2, h - 5, text=week['week_label'], font=("Segoe UI", 7), fill="#666", angle=45)

        # Y axis labels
        for v in [1, 2, 3, 4, 5]:
            y = h - 20 - int((v / max_val) * (h - 40))
            c.create_line(15, y, w - 10, y, fill="#eee")
            c.create_text(12, y, text=str(v), font=("Segoe UI", 7), fill="#999", anchor=tk.E)

    def _draw_monthly_chart(self, data: dict) -> None:
        """Draw simple bar chart for monthly averages."""
        c = self.month_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 600
        h = c.winfo_height() or 120

        series = monthly_series(data, 12)
        if not series:
            c.create_text(w//2, h//2, text="No monthly data", fill="#999", font=("Segoe UI", 10))
            return

        series = list(reversed(series))
        n = len(series)
        bar_w = max(25, (w - 40) // n - 10)
        gap = 10
        max_val = 5.0

        for i, month in enumerate(series):
            avg = month['avg']
            x0 = 20 + i * (bar_w + gap)
            x1 = x0 + bar_w
            y0 = h - 20
            y1 = h - 20 - int((avg / max_val) * (h - 40))

            color = self._rating_color(avg)
            c.create_rectangle(x0, y1, x1, y0, fill=color, outline="")
            c.create_text((x0 + x1) // 2, y1 - 10, text=f"{avg:.1f}", font=("Segoe UI", 7), fill="#333")
            c.create_text((x0 + x1) // 2, h - 5, text=month['label'], font=("Segoe UI", 7), fill="#666", angle=45)

        for v in [1, 2, 3, 4, 5]:
            y = h - 20 - int((v / max_val) * (h - 40))
            c.create_line(15, y, w - 10, y, fill="#eee")
            c.create_text(12, y, text=str(v), font=("Segoe UI", 7), fill="#999", anchor=tk.E)

    def _draw_dow_chart(self, data: dict) -> None:
        """Draw day-of-week pattern chart."""
        c = self.dow_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 600
        h = c.winfo_height() or 100

        dow = day_of_week_pattern(data)
        if not dow:
            c.create_text(w//2, h//2, text="No day-of-week data", fill="#999", font=("Segoe UI", 10))
            return

        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        bar_w = 40
        gap = 20
        start_x = (w - (7 * bar_w + 6 * gap)) // 2
        max_val = 5.0

        best_dow, worst_dow = best_worst_days_of_week(data)

        for i in range(7):
            x0 = start_x + i * (bar_w + gap)
            x1 = x0 + bar_w
            y0 = h - 20

            if i in dow:
                avg = dow[i]['avg']
                y1 = h - 20 - int((avg / max_val) * (h - 40))
                color = self._rating_color(avg)
                if i == best_dow:
                    color = "#1b5e20"  # darker green
                elif i == worst_dow:
                    color = "#b71c1c"  # darker red
                c.create_rectangle(x0, y1, x1, y0, fill=color, outline="")
                c.create_text((x0 + x1) // 2, y1 - 10, text=f"{avg:.1f}", font=("Segoe UI", 8, "bold"), fill="#333")
            else:
                y1 = y0
                c.create_rectangle(x0, y1 - 10, x1, y0, fill="#e0e0e0", outline="#ccc", dash=(2, 2))

            c.create_text((x0 + x1) // 2, h - 2, text=names[i], font=("Segoe UI", 9), fill="#333")

        # Legend
        if best_dow is not None:
            c.create_text(w - 10, 15, text=f"🟢 Best: {names[best_dow]}  🔴 Worst: {names[worst_dow]}",
                         font=("Segoe UI", 8), fill="#666", anchor=tk.NE)

    def _rating_color(self, rating: float) -> str:
        if rating >= 4.5: return "#2e7d32"
        if rating >= 3.5: return "#4caf50"
        if rating >= 2.5: return "#ffeb3b"
        if rating >= 1.5: return "#ffa726"
        return "#ef5350"


def create_stats_tab(parent, on_data_change=None) -> StatsTab:
    """Factory function for Stats tab."""
    return StatsTab(parent, on_data_change=on_data_change)