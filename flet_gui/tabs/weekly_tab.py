"""Weekly review tab — Workspace layout with week folder cards and daily reflection breakdown."""

from datetime import date, timedelta
import flet as ft

from core.data import load_data, save_data
from core.weekly import (
    current_week_start, previous_week_start, week_label, analyze_week,
    get_weekly_reflection_prompt, save_weekly_reflection
)
from flet_gui.theme import *


class WeeklyTab(ft.Column):
    """Weekly review tab with workspace layout matching Linear/macOS design."""

    def __init__(self, on_data_change=None):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        self.on_data_change = on_data_change
        self.current_week_start = current_week_start()
        self.data = {}
        self.analysis = None
        self.reflection_fields = {}
        self._build()

    def _build(self):
        self.data = load_data()
        self.analysis = analyze_week(self.data, self.current_week_start)

        self.controls = [
            ft.Container(height=Spacing.LG),
            self._build_header(),
            ft.Container(height=Spacing.MD),

            # Section 1: Overview Cards ("Folders" style)
            self._section_header("Week Highlights", "Pulse, peak performance, and challenges of this week"),
            ft.Container(
                content=self._build_overview_cards(),
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.MD),
            ),

            ft.Container(height=Spacing.MD),

            # Section 2: Detailed Days & Reflection Documents
            self._section_header("Week Breakdown & Reflections", "Daily entries in this week and reflection prompts"),
            ft.Container(
                content=self._build_breakdown_section(),
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.XL),
            ),
        ]

    def _build_header(self):
        label_text = week_label(self.current_week_start) if self.analysis else "No data for this week"
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Weekly Review", style=TextStyle.display_small()),
                            ft.Text(label_text, style=TextStyle.body_small(), color=Colors.TEXT_MUTED),
                        ],
                        spacing=Spacing.XS,
                    ),
                    ft.Row(
                        [
                            icon_button(
                                ft.Icons.CHEVRON_LEFT_ROUNDED,
                                tooltip="Previous week",
                                on_click=lambda e: self._change_week(-1),
                            ),
                            icon_button(
                                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                                tooltip="Next week",
                                on_click=lambda e: self._change_week(1),
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
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

    def _change_week(self, delta):
        self.current_week_start += timedelta(weeks=delta)
        self.refresh()

    # ── Section 1: Overview Cards ──────────────────────────────────

    def _build_overview_cards(self):
        if not self.analysis:
            card_empty = folder_card(
                title="No Data",
                subtitle="No logs for this week yet",
                badge_text="Empty",
                icon=ft.Icons.EVENT_BUSY_ROUNDED,
                accent_color=Colors.TEXT_MUTED,
            )
            return ft.Row([card_empty], spacing=Spacing.MD)

        avg_str = f"{self.analysis['average']:.1f}★"
        best = self.analysis["best"]
        worst = self.analysis["worst"]

        card_summary = folder_card(
            title="Week Average",
            subtitle=f"{self.analysis['count']} days logged this week",
            badge_text=avg_str,
            icon=ft.Icons.CALENDAR_VIEW_WEEK_ROUNDED,
            accent_color=Colors.ACCENT_CYAN,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#0c232e", "#133748"],
            ),
            expand=True,
        )

        card_best = folder_card(
            title="Best Day",
            subtitle=f"{best['date']} · {best['rating']}/5★",
            badge_text="Peak",
            icon=ft.Icons.EMOJI_EVENTS_ROUNDED,
            accent_color=Colors.SUCCESS,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#0c261e", "#123b30"],
            ),
            expand=True,
        )

        card_worst = folder_card(
            title="Toughest Day",
            subtitle=f"{worst['date']} · {worst['rating']}/5★",
            badge_text="Challenge",
            icon=ft.Icons.SENTIMENT_DISSATISFIED_ROUNDED,
            accent_color=Colors.WARNING,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#2b150a", "#421f0e"],
            ),
            expand=True,
        )

        return ft.Row(
            [card_summary, card_best, card_worst],
            spacing=Spacing.MD,
        )

    # ── Section 2: Detailed Breakdown & Reflection ─────────────────

    def _build_breakdown_section(self):
        if not self.analysis:
            return card_container(
                content=empty_state(
                    ft.Icons.WEEKEND_ROUNDED,
                    "No entries found for this week",
                    "Navigate to another week or log your days in the Today tab",
                )
            )

        days_items = []
        for i in range(7):
            day_d = self.current_week_start + timedelta(days=i)
            day_k = day_d.isoformat()
            day_name = day_d.strftime("%A")
            month_abbr = day_d.strftime("%b").upper()
            day_num = day_d.strftime("%d")
            entry = self.data.get(day_k)

            rating = entry.get("rating", 0) if entry else None
            rating_color = Colors.STAR_FILLED if rating and rating >= 4 else (Colors.WARNING if rating == 3 else Colors.TEXT_MUTED)

            date_tile = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(month_abbr, size=8, weight=ft.FontWeight.W_700, color=rating_color if entry else Colors.TEXT_MUTED),
                        ft.Text(day_num, size=13, weight=ft.FontWeight.BOLD, color=Colors.TEXT if entry else Colors.TEXT_MUTED),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                width=34,
                height=34,
                bgcolor=Colors.BG_SECONDARY,
                border_radius=Radius.SM,
                border=ft.Border.all(1, Colors.CARD_BORDER),
            )

            date_lockup = ft.Row(
                [
                    date_tile,
                    ft.Column(
                        [
                            ft.Text(f"{day_name}, {month_abbr.title()} {day_num}", size=13, weight=ft.FontWeight.W_600 if entry else ft.FontWeight.W_400, color=Colors.TEXT if entry else Colors.TEXT_MUTED),
                            ft.Text(day_k, size=10, color=Colors.TEXT_MUTED),
                        ],
                        spacing=1,
                    ),
                ],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                width=200,
            )

            if entry:
                stars_label = f"★ {rating}.0" if rating else "Unrated"
                notes_preview = entry.get("notes") or ""
                refl = entry.get("reflection", {}).get("answer") if entry.get("reflection") else ""
                preview_text = f'"{notes_preview}"' if notes_preview else (refl or "—")
                if len(preview_text) > 60:
                    preview_text = preview_text[:60] + "..."
                kws = entry.get("keywords", [])
                if kws:
                    kw_pills = [badge_pill(f"#{k}", bg_color=Colors.PILL_BG, text_color=Colors.PRIMARY) for k in kws[:2]]
                else:
                    kw_pills = [badge_pill("Logged", bg_color=Colors.BG_SECONDARY, text_color=Colors.TEXT_MUTED)]

                row = ft.Container(
                    content=ft.Row(
                        [
                            date_lockup,
                            ft.Container(
                                content=badge_pill(stars_label, text_color=rating_color),
                                width=100,
                            ),
                            ft.Container(
                                content=ft.Row(kw_pills, spacing=4),
                                width=160,
                            ),
                            ft.Text(preview_text, size=12, color=Colors.TEXT_SECONDARY, italic=bool(notes_preview), expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=Spacing.LG, top=10, right=Spacing.LG, bottom=10),
                    bgcolor=Colors.CARD,
                    border=ft.Border(
                        left=ft.BorderSide(3, rating_color),
                        bottom=ft.BorderSide(1, Colors.SIDEBAR_BORDER),
                    ),
                )
            else:
                row = ft.Container(
                    content=ft.Row(
                        [
                            date_lockup,
                            ft.Container(
                                content=badge_pill("—", text_color=Colors.TEXT_DISABLED),
                                width=100,
                            ),
                            ft.Container(
                                content=badge_pill("No entry", bg_color=Colors.BG_SECONDARY, text_color=Colors.TEXT_DISABLED),
                                width=160,
                            ),
                            ft.Text("Not recorded yet", size=12, color=Colors.TEXT_DISABLED, expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=Spacing.LG, top=10, right=Spacing.LG, bottom=10),
                    bgcolor=Colors.CARD,
                    border=ft.Border(
                        left=ft.BorderSide(3, Colors.CARD_BORDER),
                        bottom=ft.BorderSide(1, Colors.SIDEBAR_BORDER),
                    ),
                )
            days_items.append(row)

        table_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("DATE / DAY", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=200),
                    ft.Text("RATING", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=100),
                    ft.Text("KEYWORDS", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=160),
                    ft.Text("NOTES PREVIEW", style=TextStyle.caption(), color=Colors.TEXT_MUTED, expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.SM),
            border=ft.Border(bottom=ft.BorderSide(1, Colors.CARD_BORDER)),
        )

        table_box = workspace_table(table_header, days_items)

        # Reflection prompts
        prompts = get_weekly_reflection_prompt(self.analysis)
        prompt_cards = []
        if prompts:
            for p in prompts:
                is_best = p["type"] == "best"
                color = Colors.POSITIVE if is_best else Colors.WARNING
                icon = ft.Icons.STAR_ROUNDED if is_best else ft.Icons.SENTIMENT_DISSATISFIED_ROUNDED
                label = f"Reflecting on {p['date']} ({'Best Day' if is_best else 'Toughest Day'})"

                prompt_cards.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(icon, size=18, color=color),
                                        ft.Text(label, size=13, weight=ft.FontWeight.W_600, color=color),
                                    ],
                                    spacing=Spacing.SM,
                                ),
                                ft.Text(p.get("question", ""), size=12, color=Colors.TEXT_SECONDARY),
                            ],
                            spacing=Spacing.XS,
                        ),
                        bgcolor=Colors.BG_SECONDARY,
                        border_radius=Radius.MD,
                        border=ft.Border.all(1, Colors.CARD_BORDER),
                        padding=ft.Padding.all(Spacing.MD),
                    )
                )

        reflection_box = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Weekly Reflection Prompts", style=TextStyle.headline_small()),
                    ft.Container(height=4),
                    ft.Column(prompt_cards, spacing=Spacing.SM) if prompt_cards else ft.Text("No specific reflections generated for this week", size=12, color=Colors.TEXT_MUTED),
                ],
                spacing=Spacing.XS,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.MD),
        )

        return ft.Column(
            [
                table_box,
                ft.Container(height=Spacing.MD),
                reflection_box,
            ],
            spacing=0,
        )

    def refresh(self):
        """Called when data changes or user switches week."""
        self.data = load_data()
        self.analysis = analyze_week(self.data, self.current_week_start)
        self._build()
        safe_update(self)
