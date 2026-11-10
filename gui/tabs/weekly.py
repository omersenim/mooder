"""Weekly tab — Weekly review with best/worst day analysis."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from core.data import load_data, save_data
from core.weekly import (
    week_start_sunday, week_end_saturday,
    current_week_start, previous_week_start,
    analyze_week, get_weekly_reflection_prompt,
    save_weekly_reflection, current_streak, longest_streak
)


class WeeklyTab(ttk.Frame):
    """Weekly tab: Shows week analysis, best/worst day, reflection prompts."""

    def __init__(self, parent, on_data_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_data_change = on_data_change
        self.current_week_start = current_week_start()
        self.analysis = None
        self.reflection_entries = {}  # date_key -> answer
        self._build()
        self.refresh()

    def _build(self) -> None:
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Toolbar ────────────────────────────────────────────────────
        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(toolbar, text="📊 Weekly Review", font=("Segoe UI", 18, "bold")).pack(side=tk.LEFT)

        # Week navigation
        nav_frame = ttk.Frame(toolbar)
        nav_frame.pack(side=tk.RIGHT)

        ttk.Button(nav_frame, text="◀ Prev", command=self._prev_week).pack(side=tk.LEFT, padx=5)
        self.week_label = ttk.Label(nav_frame, text="", font=("Segoe UI", 11, "bold"), width=20)
        self.week_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text="Next ▶", command=self._next_week).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="This Week", command=self._this_week).pack(side=tk.LEFT, padx=5)

        # ── Week Summary ───────────────────────────────────────────────
        self.summary_frame = ttk.LabelFrame(main, text="Week Summary", padding=15)
        self.summary_frame.pack(fill=tk.X, pady=(0, 20))

        self.summary_text = ttk.Label(self.summary_frame, text="", font=("Segoe UI", 11), justify=tk.LEFT)
        self.summary_text.pack(anchor=tk.W)

        # ── Best/Worst Day Cards ───────────────────────────────────────
        cards_frame = ttk.Frame(main)
        cards_frame.pack(fill=tk.X, pady=(0, 20))

        # Best day card
        self.best_frame = ttk.LabelFrame(cards_frame, text="🌟 Best Day", padding=15)
        self.best_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.best_label = ttk.Label(self.best_frame, text="No data", font=("Segoe UI", 14, "bold"), foreground="#2e7d32")
        self.best_label.pack(anchor=tk.W)
        self.best_prompt = ttk.Label(self.best_frame, text="", font=("Segoe UI", 10), wraplength=250)
        self.best_prompt.pack(anchor=tk.W, pady=(10, 0))
        self.best_answer = tk.Text(self.best_frame, height=3, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.best_answer.pack(fill=tk.X, pady=(5, 0))

        # Worst day card
        self.worst_frame = ttk.LabelFrame(cards_frame, text="😔 Worst Day", padding=15)
        self.worst_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.worst_label = ttk.Label(self.worst_frame, text="No data", font=("Segoe UI", 14, "bold"), foreground="#c62828")
        self.worst_label.pack(anchor=tk.W)
        self.worst_prompt = ttk.Label(self.worst_frame, text="", font=("Segoe UI", 10), wraplength=250)
        self.worst_prompt.pack(anchor=tk.W, pady=(10, 0))
        self.worst_answer = tk.Text(self.worst_frame, height=3, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        self.worst_answer.pack(fill=tk.X, pady=(5, 0))

        # ── Other Days ─────────────────────────────────────────────────
        other_frame = ttk.LabelFrame(main, text="Other Days This Week", padding=15)
        other_frame.pack(fill=tk.X, pady=(0, 20))

        self.other_text = tk.Text(other_frame, height=6, wrap=tk.WORD, font=("Consolas", 9), relief=tk.SOLID, bd=1, state=tk.DISABLED)
        self.other_text.pack(fill=tk.X)

        # ── Reflection Prompts ─────────────────────────────────────────
        reflect_frame = ttk.LabelFrame(main, text="💭 Weekly Reflections", padding=15)
        reflect_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.prompts_frame = ttk.Frame(reflect_frame)
        self.prompts_frame.pack(fill=tk.BOTH, expand=True)

        # ── Save Button ────────────────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        self.save_btn = ttk.Button(btn_frame, text="💾 Save Reflections", command=self._save_reflections, style="Accent.TButton")
        self.save_btn.pack(side=tk.RIGHT)

        self.streak_label = ttk.Label(btn_frame, text="", font=("Segoe UI", 10))
        self.streak_label.pack(side=tk.LEFT)

        # Style
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=(20, 10))

    def _this_week(self) -> None:
        self.current_week_start = current_week_start()
        self.refresh()

    def _prev_week(self) -> None:
        self.current_week_start -= timedelta(weeks=1)
        self.refresh()

    def _next_week(self) -> None:
        # Don't go beyond current week
        if self.current_week_start < current_week_start():
            self.current_week_start += timedelta(weeks=1)
            self.refresh()

    def refresh(self) -> None:
        """Reload week analysis."""
        data = load_data()
        self.analysis = analyze_week(data, self.current_week_start)

        # Update week label
        ws = self.current_week_start
        we = week_end_saturday(ws)
        self.week_label.config(text=f"{ws.strftime('%b %d')} – {we.strftime('%b %d, %Y')}")

        if not self.analysis:
            self._show_empty()
            return

        # Update summary
        a = self.analysis
        summary = (
            f"📅 {a['week_label']}   |   "
            f"📈 Average: {a['average']:.1f}/5   |   "
            f"📝 Days logged: {a['count']}/7"
        )
        self.summary_text.config(text=summary)

        # Best day
        best = a['best']
        self.best_label.config(text=f"{best['date']}  —  {best['rating']}/5 ★")
        self.best_prompt.config(text=f"Why was {date.fromisoformat(best['date']).strftime('%A')} your best day?")
        self.best_answer.delete("1.0", tk.END)
        existing = self.reflection_entries.get(best['date'], "")
        self.best_answer.insert("1.0", existing)

        # Worst day
        worst = a['worst']
        self.worst_label.config(text=f"{worst['date']}  —  {worst['rating']}/5 ★")
        self.worst_prompt.config(text=f"What made {date.fromisoformat(worst['date']).strftime('%A')} difficult?")
        self.worst_answer.delete("1.0", tk.END)
        existing = self.reflection_entries.get(worst['date'], "")
        self.worst_answer.insert("1.0", existing)

        # Other days
        self._populate_other_days()

        # Reflection prompts (auto-generated)
        self._build_prompts()

        # Streaks
        self.streak_label.config(text=f"🔥 Current streak: {current_streak(data)} days  |  🏆 Longest: {longest_streak(data)} days")

    def _show_empty(self) -> None:
        self.summary_text.config(text="No rated entries for this week.")
        self.best_label.config(text="No data")
        self.best_prompt.config(text="")
        self.best_answer.delete("1.0", tk.END)
        self.worst_label.config(text="No data")
        self.worst_prompt.config(text="")
        self.worst_answer.delete("1.0", tk.END)
        self.other_text.config(state=tk.NORMAL)
        self.other_text.delete("1.0", tk.END)
        self.other_text.config(state=tk.DISABLED)
        self._clear_prompts()
        self.streak_label.config(text="")

    def _populate_other_days(self) -> None:
        """Show all days in the week with their ratings."""
        if not self.analysis:
            return

        data = load_data()
        ws = self.current_week_start

        lines = []
        for i in range(7):
            d = ws + timedelta(days=i)
            day_key = d.isoformat()
            entry = data.get(day_key, {})
            rating = entry.get("rating")

            day_name = d.strftime("%a")
            if rating is not None:
                stars = "★" * rating + "☆" * (5 - rating)
                lines.append(f"  {day_name} {day_key}: {stars}  ({rating}/5)")
            else:
                lines.append(f"  {day_name} {day_key}: —  (not logged)")

        self.other_text.config(state=tk.NORMAL)
        self.other_text.delete("1.0", tk.END)
        self.other_text.insert("1.0", "\n".join(lines))
        self.other_text.config(state=tk.DISABLED)

    def _clear_prompts(self) -> None:
        for widget in self.prompts_frame.winfo_children():
            widget.destroy()

    def _build_prompts(self) -> None:
        """Build reflection prompt widgets from analysis."""
        self._clear_prompts()

        if not self.analysis:
            return

        prompts = get_weekly_reflection_prompt(self.analysis)

        for p in prompts:
            frame = ttk.Frame(self.prompts_frame)
            frame.pack(fill=tk.X, pady=8)

            ttk.Label(frame, text=p["question"], font=("Segoe UI", 10), wraplength=500).pack(anchor=tk.W)

            answer_text = tk.Text(frame, height=2, wrap=tk.WORD, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
            answer_text.pack(fill=tk.X, pady=(4, 0))
            answer_text.insert("1.0", self.reflection_entries.get(p["date"], ""))

            # Store reference for saving
            answer_text.prompt_date = p["date"]
            self.reflection_entries[p["date"]] = answer_text

    def _save_reflections(self) -> None:
        """Save all reflection answers."""
        if not self.analysis:
            messagebox.showinfo("Nothing to Save", "No weekly analysis available.")
            return

        data = load_data()
        reflections = {}

        # Best/worst day answers
        best_date = self.analysis['best']['date']
        worst_date = self.analysis['worst']['date']

        best_ans = self.best_answer.get("1.0", tk.END).strip()
        worst_ans = self.worst_answer.get("1.0", tk.END).strip()

        if best_ans:
            reflections[best_date] = best_ans
        if worst_ans:
            reflections[worst_date] = worst_ans

        # Other prompts
        for widget in self.prompts_frame.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Text) and hasattr(child, 'prompt_date'):
                    ans = child.get("1.0", tk.END).strip()
                    if ans:
                        reflections[child.prompt_date] = ans

        if not reflections:
            messagebox.showinfo("Nothing to Save", "No reflections entered.")
            return

        save_weekly_reflection(data, self.current_week_start, reflections)
        save_data(data)

        messagebox.showinfo("Saved", "Weekly reflections saved!")
        if self.on_data_change:
            self.on_data_change()


def create_weekly_tab(parent, on_data_change=None) -> WeeklyTab:
    """Factory function for Weekly tab."""
    return WeeklyTab(parent, on_data_change=on_data_change)