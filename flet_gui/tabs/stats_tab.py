"""Stats tab — Workspace layout with overview folder cards and analytical breakdown."""

from datetime import date
from collections import Counter
import flet as ft

from core.data import load_data, iter_rated_entries
from core.keywords import get_keyword_category
from core.stats import (
    overall_stats, rolling_average, top_keywords, day_of_week_pattern,
    best_worst_days_of_week
)
from core.weekly import current_streak, longest_streak
from flet_gui.theme import *


class StatsTab(ft.Column):
    """Stats tab with workspace layout matching Linear/macOS design."""

    def __init__(self, on_data_change=None):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        self.on_data_change = on_data_change
        self.data = {}
        self._build()

    def _build(self):
        self.data = load_data()
        ov = overall_stats(self.data)

        self.controls = [
            ft.Container(height=Spacing.LG),
            self._build_header(),
            ft.Container(height=Spacing.MD),

            # Section 1: Overview Cards ("Folders" style)
            self._section_header("Overview Metrics", "Key performance indicators across all logs"),
            ft.Container(
                content=self._build_overview_cards(ov),
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.MD),
            ),

            ft.Container(height=Spacing.MD),

            # Section 2: Analytical Breakdown Panels
            self._section_header("Detailed Analytics", "Rating distribution, day of week patterns, and keyword cloud"),
            ft.Container(
                content=self._build_analytics_panels(ov),
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.XL),
            ),
        ]

    def _build_header(self):
        total_logs = len(self.data)
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Stats & Insights", style=TextStyle.display_small()),
                            ft.Text("Deep dive into your habits, ratings, and emotional trends", style=TextStyle.body_small(), color=Colors.TEXT_MUTED),
                        ],
                        spacing=Spacing.XS,
                    ),
                    badge_pill(f"{total_logs} Total Entries", bg_color=Colors.PILL_BG, text_color=Colors.PRIMARY, icon=ft.Icons.BAR_CHART_ROUNDED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=0),
        )

    def _section_header(self, title: str, subtitle: str):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, style=TextStyle.headline_small()),
                    ft.Text(subtitle, style=TextStyle.caption(), color=Colors.TEXT_MUTED),
                ],
                spacing=2,
            ),
            padding=ft.Padding(left=Spacing.LG, top=Spacing.MD, right=Spacing.LG, bottom=Spacing.XS),
        )

    # ── Section 1: Overview Cards ──────────────────────────────────

    def _build_overview_cards(self, ov):
        curr_strk = current_streak(self.data)
        long_strk = longest_streak(self.data)
        avg = f"{ov['avg_rating']:.2f}★" if ov["total_days"] > 0 else "—"

        best_dow, worst_dow = best_worst_days_of_week(self.data)
        dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        best_day_str = dow_names[best_dow] if best_dow is not None else "—"

        card_total = folder_card(
            title="Total Logs",
            subtitle=f"{ov['total_days']} entries recorded",
            badge_text="Archive",
            icon=ft.Icons.AUTO_STORIES_ROUNDED,
            accent_color=Colors.ACCENT_CYAN,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#0c232e", "#133748"],
            ),
            expand=True,
        )

        card_rating = folder_card(
            title="Avg Score",
            subtitle=f"{avg} all-time average",
            badge_text=avg,
            icon=ft.Icons.STAR_ROUNDED,
            accent_color=Colors.STAR_FILLED,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#291f0c", "#3d2e12"],
            ),
            expand=True,
        )

        card_streak = folder_card(
            title="Current Streak",
            subtitle=f"{curr_strk} days (Best: {long_strk}d)",
            badge_text=f"🔥 {curr_strk} days",
            icon=ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            accent_color=Colors.WARNING,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#2b150a", "#421f0e"],
            ),
            expand=True,
        )

        card_peak = folder_card(
            title="Peak Weekday",
            subtitle=f"{best_day_str} is your best day",
            badge_text="Peak Rhythm",
            icon=ft.Icons.TRENDING_UP_ROUNDED,
            accent_color=Colors.ACCENT_PURPLE,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#221233", "#381c54"],
            ),
            expand=True,
        )

        return ft.Row(
            [card_total, card_rating, card_streak, card_peak],
            spacing=Spacing.MD,
        )

    # ── Section 2: Detailed Analytics Panels ───────────────────────

    def _build_analytics_panels(self, ov):
        if ov["total_days"] == 0:
            return card_container(
                content=empty_state(
                    ft.Icons.INSIGHTS_ROUNDED,
                    "No logs available yet",
                    "Start logging in the Today tab to unlock analytics and trends",
                )
            )

        # 1. Rating Distribution Card
        rating_dist_panel = self._build_rating_distribution(ov)

        # 2. Day of Week Patterns Card
        dow_panel = self._build_dow_panel()

        # 3. Rolling Averages Card
        rolling_panel = self._build_rolling_panel()

        # 4. Keyword Frequency Card
        keywords_panel = self._build_keywords_cloud()

        return ft.Column(
            [
                ft.Row([rating_dist_panel, rolling_panel], spacing=Spacing.MD),
                ft.Container(height=Spacing.SM),
                dow_panel,
                ft.Container(height=Spacing.SM),
                keywords_panel,
            ],
            spacing=0,
        )

    def _build_rating_distribution(self, ov):
        dist = ov.get("rating_distribution", {})
        total = max(ov["total_days"], 1)

        bars = []
        for r in range(5, 0, -1):
            count = dist.get(r, 0)
            pct = count / total
            bars.append(
                ft.Row(
                    [
                        ft.Text(f"{r} ★", size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_SECONDARY, width=32),
                        ft.ProgressBar(value=pct, color=Colors.STAR_FILLED if r >= 4 else (Colors.WARNING if r == 3 else Colors.ERROR), bgcolor=Colors.BG_SECONDARY, height=8, expand=True),
                        ft.Text(f"{count} ({int(pct*100)}%)", size=12, color=Colors.TEXT_MUTED, width=65, text_align=ft.TextAlign.RIGHT),
                    ],
                    spacing=Spacing.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Rating Distribution", style=TextStyle.headline_small()),
                            badge_pill("All-time", text_color=Colors.TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Column(bars, spacing=Spacing.SM),
                ],
                spacing=0,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.MD),
            expand=True,
        )

    def _build_rolling_panel(self):
        periods = [(7, "Last 7 Days"), (30, "Last 30 Days"), (90, "Last 90 Days")]
        items = []

        for days, label in periods:
            ra = rolling_average(self.data, days)
            val_str = f"{ra:.2f}★" if ra is not None else "—"
            items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(label, size=13, color=Colors.TEXT_SECONDARY),
                            badge_pill(val_str, bg_color=Colors.BG_SECONDARY, text_color=Colors.PRIMARY),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding(left=Spacing.SM, top=8, right=Spacing.SM, bottom=8),
                    border_radius=Radius.MD,
                    bgcolor=Colors.BG_SECONDARY,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Rolling Averages", style=TextStyle.headline_small()),
                            badge_pill("Pacing", text_color=Colors.TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Column(items, spacing=Spacing.SM),
                ],
                spacing=0,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.MD),
            expand=True,
        )

    def _build_dow_panel(self):
        dow_data = day_of_week_pattern(self.data)
        days_order = [("Mon", 0), ("Tue", 1), ("Wed", 2), ("Thu", 3), ("Fri", 4), ("Sat", 5), ("Sun", 6)]

        cols = []
        for name, idx in days_order:
            info = dow_data.get(idx, {"count": 0, "avg": 0.0})
            avg_str = f"{info['avg']:.1f}★" if info["count"] > 0 else "—"
            cols.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(name, size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=4),
                            ft.Text(avg_str, size=13, weight=ft.FontWeight.BOLD, color=Colors.PRIMARY if info['count'] > 0 else Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                            ft.Text(f"{info['count']}d", size=10, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=1,
                    ),
                    bgcolor=Colors.BG_SECONDARY,
                    border_radius=Radius.MD,
                    border=ft.Border.all(1, Colors.CARD_BORDER),
                    padding=ft.Padding(left=6, top=10, right=6, bottom=10),
                    expand=True,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Day of Week Rhythm", style=TextStyle.headline_small()),
                            badge_pill("Weekly Pattern", text_color=Colors.TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Row(cols, spacing=Spacing.SM),
                ],
                spacing=0,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.MD),
        )

    def _build_keywords_cloud(self):
        top_kws = top_keywords(self.data, n=12)

        chips = []
        if not top_kws:
            chips.append(ft.Text("No keyword tags recorded yet", size=12, color=Colors.TEXT_MUTED))
        else:
            for kw, count in top_kws:
                cat = get_keyword_category(kw)
                cat_color = Colors.POSITIVE if cat == "positive" else (Colors.ERROR if cat == "negative" else Colors.ACCENT_BLUE)
                chips.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"#{kw}", size=12, weight=ft.FontWeight.W_500, color=cat_color),
                                badge_pill(str(count), bg_color=Colors.PILL_BG, text_color=Colors.TEXT_SECONDARY),
                            ],
                            spacing=Spacing.XS,
                            tight=True,
                        ),
                        bgcolor=Colors.BG_SECONDARY,
                        border=ft.Border.all(1, Colors.CARD_BORDER),
                        border_radius=Radius.FULL,
                        padding=ft.Padding(left=10, top=4, right=8, bottom=4),
                    )
                )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Frequent Keywords & Emotional Tags", style=TextStyle.headline_small()),
                            badge_pill("Topic Cloud", text_color=Colors.TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Row(chips, spacing=Spacing.SM, wrap=True),
                ],
                spacing=0,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.MD),
        )

    def refresh(self):
        """Called when user switches to stats tab or data changes."""
        self.data = load_data()
        self._build()
        safe_update(self)
