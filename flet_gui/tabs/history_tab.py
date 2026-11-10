"""History tab — Linear/Knowledge-base style with folder highlights and entry table."""

from calendar import monthrange
from datetime import date, timedelta, datetime
import flet as ft

from core.data import delete_entry, load_data, save_data, today_key, validate_entry
from flet_gui.theme import *


class HistoryTab(ft.Column):
    """History tab with workspace folder cards and daily entries table."""

    def __init__(self, on_data_change=None):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        self.on_data_change = on_data_change
        self.current_month = date.today().replace(day=1)
        self.selected_date = None
        self.data = {}
        self.view_mode = "table"  # "table" or "calendar"
        self.filter_month = None
        self.filter_label = None
        self.highlights_only = False
        self.search_query = ""
        self._build()

    def _build(self):
        self.data = load_data()

        # Monthly folders row — expands evenly across the deck
        self.folders_row = ft.Row(
            self._build_month_folders(),
            spacing=Spacing.MD,
        )

        # Main table / calendar content container
        self.content_container = ft.Container(
            content=self._build_table_view() if self.view_mode == "table" else self._build_calendar_view(),
            expand=True,
        )

        self.controls = [
            ft.Container(height=Spacing.LG),
            self._build_header(),
            ft.Container(height=Spacing.MD),

            # Section: Folders (Month Cards)
            self._section_header("Folders", "Monthly collections and archives"),
            ft.Container(
                content=self.folders_row,
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.MD),
            ),

            ft.Container(height=Spacing.MD),

            # Section: Files / Entries
            self._section_header("Entries", "Daily log files and reflections", show_view_toggle=True),
            ft.Container(
                content=self.content_container,
                padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.XL),
            ),
        ]

    def _build_header(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("History & Archive", style=TextStyle.display_small()),
                    ft.Text(
                        "Browse past logs, monthly summaries, and reflections",
                        style=TextStyle.body_small(),
                        color=Colors.TEXT_MUTED,
                    ),
                ],
                spacing=Spacing.XS,
            ),
            padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=0),
        )

    def _section_header(self, title: str, subtitle: str, show_view_toggle: bool = False):
        actions = []
        if show_view_toggle:
            # Active filter pill with clear button
            if self.filter_label:
                actions.append(
                    ft.Row(
                        [
                            badge_pill(self.filter_label, bg_color=Colors.PRIMARY_DIM, text_color=Colors.PRIMARY),
                            ft.IconButton(
                                ft.Icons.CLOSE_ROUNDED,
                                icon_size=14,
                                icon_color=Colors.TEXT_MUTED,
                                tooltip="Clear active filter",
                                on_click=lambda e: self._clear_filter(),
                            ),
                        ],
                        spacing=2,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )

            # Real, working search bar
            actions.append(
                ft.TextField(
                    hint_text="Search logs, notes, #tags...",
                    prefix_icon=ft.Icons.SEARCH,
                    height=34,
                    text_size=12,
                    value=self.search_query,
                    bgcolor=Colors.BG_SECONDARY,
                    border_color=Colors.CARD_BORDER,
                    border_radius=Radius.MD,
                    content_padding=ft.Padding(left=10, top=0, right=10, bottom=0),
                    on_change=self._on_search_change,
                    width=220,
                )
            )

            # View mode toggle (Table vs Calendar Heatmap)
            actions.append(
                icon_button(
                    ft.Icons.TABLE_ROWS if self.view_mode == "calendar" else ft.Icons.CALENDAR_MONTH,
                    tooltip="Switch to " + ("Table view" if self.view_mode == "calendar" else "Calendar heatmap"),
                    on_click=self._toggle_view_mode,
                )
            )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(title, style=TextStyle.headline_small()),
                            ft.Text(subtitle, style=TextStyle.caption(), color=Colors.TEXT_MUTED),
                        ],
                        spacing=2,
                    ),
                    ft.Row(actions, spacing=Spacing.SM, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=Spacing.MD, right=Spacing.LG, bottom=Spacing.XS),
        )

    def _toggle_view_mode(self, e=None):
        self.view_mode = "calendar" if self.view_mode == "table" else "table"
        self._rebuild_all()

    def _clear_filter(self):
        self.filter_month = None
        self.filter_label = None
        self.highlights_only = False
        self._rebuild_all()

    def _on_search_change(self, e):
        self.search_query = e.control.value or ""
        self._rebuild_all()

    # ── Folders (Monthly Highlights) ───────────────────────────────

    def _build_month_folders(self):
        self.data = load_data()
        today = date.today()
        folders = []

        # Current Month folder (Cyan/Teal gradient pocket)
        cur_year, cur_month = today.year, today.month
        cur_entries = [e for k, e in self.data.items() if k.startswith(f"{cur_year}-{cur_month:02d}")]
        cur_rated = [e["rating"] for e in cur_entries if isinstance(e.get("rating"), int)]
        cur_avg = f"{sum(cur_rated)/len(cur_rated):.1f}★" if cur_rated else "No ratings"

        folders.append(
            folder_card(
                title=today.strftime("%B %Y"),
                subtitle=f"{len(cur_entries)} logs · {cur_avg}",
                badge_text="Active",
                icon=ft.Icons.FOLDER_ROUNDED,
                accent_color=Colors.PRIMARY,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#0c2622", "#133f38"],
                ),
                expand=True,
                on_click=lambda e: self._filter_to_month(today.year, today.month),
            )
        )

        # Previous Month folder (Sapphire Blue gradient pocket)
        prev_month_date = today.replace(day=1) - timedelta(days=1)
        prev_year, prev_month = prev_month_date.year, prev_month_date.month
        prev_entries = [e for k, e in self.data.items() if k.startswith(f"{prev_year}-{prev_month:02d}")]
        prev_rated = [e["rating"] for e in prev_entries if isinstance(e.get("rating"), int)]
        prev_avg = f"{sum(prev_rated)/len(prev_rated):.1f}★" if prev_rated else "—"

        folders.append(
            folder_card(
                title=prev_month_date.strftime("%B %Y"),
                subtitle=f"{len(prev_entries)} logs · {prev_avg}",
                badge_text="Archive",
                icon=ft.Icons.FOLDER_SPECIAL_ROUNDED,
                accent_color=Colors.ACCENT_BLUE,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#0e1c36", "#162e59"],
                ),
                expand=True,
                on_click=lambda e: self._filter_to_month(prev_year, prev_month),
            )
        )

        # All-time Archive folder (Charcoal / Slate gradient pocket)
        folders.append(
            folder_card(
                title="Vault Archive",
                subtitle=f"{len(self.data)} total files · JSON",
                badge_text=f"ZIP · {len(self.data)} logs",
                icon=ft.Icons.ARCHIVE_ROUNDED,
                accent_color=Colors.TEXT_MUTED,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#181924", "#242637"],
                ),
                expand=True,
                on_click=lambda e: self._filter_to_month(None, None),
            )
        )

        # Favorites / 5-Star Highlights (Amethyst Purple gradient pocket)
        five_stars = [e for e in self.data.values() if e.get("rating") == 5]
        folders.append(
            folder_card(
                title="Top Highlights",
                subtitle=f"{len(five_stars)} perfect 5★ days",
                badge_text="Highlights",
                icon=ft.Icons.STAR_ROUNDED,
                accent_color=Colors.ACCENT_PURPLE,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=["#291338", "#421b5a"],
                ),
                expand=True,
                on_click=lambda e: self._filter_to_highlights(),
            )
        )

        return folders

    def _filter_to_month(self, year, month):
        if year and month:
            self.filter_month = f"{year}-{month:02d}"
            self.filter_label = date(year, month, 1).strftime("%B %Y")
            self.current_month = date(year, month, 1)
        else:
            self.filter_month = None
            self.filter_label = None
        self.highlights_only = False
        self._rebuild_all()

    def _filter_to_highlights(self):
        self.highlights_only = not getattr(self, "highlights_only", False)
        self.filter_month = None
        self.filter_label = "5★ Highlights" if self.highlights_only else None
        self._rebuild_all()

    # ── Table View (Files List) ────────────────────────────────────

    def _build_table_view(self):
        sorted_keys = sorted(self.data.keys(), reverse=True)
        if getattr(self, "highlights_only", False):
            sorted_keys = [k for k in sorted_keys if self.data[k].get("rating") == 5]
        elif getattr(self, "filter_month", None):
            sorted_keys = [k for k in sorted_keys if k.startswith(self.filter_month)]

        # Search query filter (matches date, notes, reflection, and keywords)
        if getattr(self, "search_query", None) and self.search_query.strip():
            q = self.search_query.strip().lower()
            filtered = []
            for k in sorted_keys:
                entry = self.data[k]
                notes = (entry.get("notes") or "").lower()
                refl = (entry.get("reflection", {}).get("answer") or "").lower() if entry.get("reflection") else ""
                kws = " ".join(entry.get("keywords") or []).lower()
                if q in k.lower() or q in notes or q in refl or q in kws:
                    filtered.append(k)
            sorted_keys = filtered

        if not sorted_keys:
            empty_msg = "No entries matching your filter or search" if (self.filter_label or self.search_query) else "No log entries yet"
            return card_container(
                content=empty_state(
                    ft.Icons.NOTE_ADD_ROUNDED,
                    empty_msg,
                    "Try clearing filters or search, or record today's reflection in the Today tab!",
                )
            )

        # Table Header with balanced proportions
        header_row = ft.Container(
            content=ft.Row(
                [
                    ft.Text("DATE & ENTRY", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=220),
                    ft.Text("RATING & MOOD", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=150),
                    ft.Text("TOPICS & TAGS", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=160),
                    ft.Text("DAILY REFLECTION & NOTES", style=TextStyle.caption(), color=Colors.TEXT_MUTED, expand=True),
                    ft.Text("ACTIONS", style=TextStyle.caption(), color=Colors.TEXT_MUTED, width=80),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=Spacing.SM, right=Spacing.LG, bottom=Spacing.SM),
            border=ft.Border(bottom=ft.BorderSide(1, Colors.CARD_BORDER)),
        )

        # Mood map for rating labels and colors
        mood_map = {
            5: ("★ 5.0", "Exceptional", Colors.SUCCESS),
            4: ("★ 4.0", "Good Day", Colors.SUCCESS),
            3: ("★ 3.0", "Mixed / Routine", Colors.WARNING),
            2: ("★ 2.0", "Rough Day", Colors.ERROR),
            1: ("★ 1.0", "Tough Day", Colors.ERROR),
        }

        # Entry rows with punchy lockups and left accent strip
        rows = []
        today_date = date.today()

        for day_key in sorted_keys:
            entry = self.data[day_key]
            rating = entry.get("rating")
            star_label, mood_label, rating_color = mood_map.get(
                rating, ("—", "Unrated", Colors.TEXT_MUTED)
            )

            # Date Tile Lockup (Notion / Apple Journal style)
            try:
                d = datetime.strptime(day_key, "%Y-%m-%d").date()
                day_name = d.strftime("%A")
                month_abbr = d.strftime("%b").upper()
                day_num = d.strftime("%d")
                if d == today_date:
                    rel_badge_text = "Today"
                    rel_color = Colors.PRIMARY
                elif d == today_date - timedelta(days=1):
                    rel_badge_text = "Yesterday"
                    rel_color = Colors.TEXT_SECONDARY
                else:
                    diff = (today_date - d).days
                    rel_badge_text = f"{diff}d ago"
                    rel_color = Colors.TEXT_MUTED
            except Exception:
                day_name = "Journal Entry"
                month_abbr = "LOG"
                day_num = "—"
                rel_badge_text = day_key
                rel_color = Colors.TEXT_MUTED

            date_tile = ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Text(month_abbr, size=8, weight=ft.FontWeight.W_800, color=rating_color),
                            bgcolor=rating_color + "22",
                            alignment=ft.Alignment(0, 0),
                            height=14,
                            border_radius=ft.BorderRadius(Radius.SM, Radius.SM, 0, 0),
                        ),
                        ft.Container(
                            content=ft.Text(day_num, size=15, weight=ft.FontWeight.BOLD, color=Colors.TEXT),
                            alignment=ft.Alignment(0, 0),
                            expand=True,
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=40,
                height=42,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1),
                    end=ft.Alignment(0, 1),
                    colors=["#1c1e2b", "#12141e"],
                ),
                border_radius=Radius.SM,
                border=border_3d(light="#383c54", dark="#11121c"),
                shadow=Shadows.PILL_3D,
            )

            date_lockup = ft.Row(
                [
                    date_tile,
                    ft.Column(
                        [
                            ft.Text(f"{day_name}, {month_abbr.title()} {day_num}", size=13, weight=ft.FontWeight.W_600, color=Colors.TEXT),
                            ft.Row(
                                [
                                    badge_pill(rel_badge_text, bg_color=Colors.PILL_BG, text_color=rel_color),
                                    ft.Text(day_key, size=11, color=Colors.TEXT_MUTED),
                                ],
                                spacing=Spacing.XS,
                            ),
                        ],
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                width=220,
            )

            # Rating & Mood Column
            rating_mood_cell = ft.Column(
                [
                    badge_pill(star_label, text_color=rating_color, icon=ft.Icons.STAR_ROUNDED if rating else None),
                    ft.Text(mood_label, size=11, color=Colors.TEXT_MUTED),
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                width=150,
            )

            # Tags Column
            kws = entry.get("keywords", [])
            if kws:
                kw_chips = [badge_pill(f"#{k}", bg_color=Colors.PILL_BG, text_color=Colors.PRIMARY) for k in kws[:2]]
                tags_cell = ft.Container(content=ft.Row(kw_chips, spacing=4, wrap=False), width=160)
            else:
                tags_cell = ft.Container(content=ft.Text("—", size=12, color=Colors.TEXT_MUTED), width=160)

            # Notes preview with quote styling
            notes = entry.get("notes") or ""
            refl = entry.get("reflection", {}).get("answer") if entry.get("reflection") else ""
            if notes:
                notes_preview_ctrl = ft.Row(
                    [
                        ft.Icon(ft.Icons.FORMAT_QUOTE_ROUNDED, size=14, color=Colors.TEXT_MUTED),
                        ft.Text(f'"{notes}"' if len(notes) <= 70 else f'"{notes[:70]}..."', size=13, color=Colors.TEXT, italic=True, expand=True),
                    ],
                    spacing=Spacing.XS,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            elif refl:
                notes_preview_ctrl = ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=13, color=Colors.ACCENT_PURPLE),
                        ft.Text(refl if len(refl) <= 70 else f"{refl[:70]}...", size=13, color=Colors.TEXT_SECONDARY, expand=True),
                    ],
                    spacing=Spacing.XS,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            else:
                notes_preview_ctrl = ft.Text("No notes recorded", size=12, color=Colors.TEXT_DISABLED)

            # Row container with 3px Left Rating Accent Strip and subtle glassmorphic hover
            row = ft.Container(
                content=ft.Row(
                    [
                        date_lockup,
                        rating_mood_cell,
                        tags_cell,
                        ft.Container(content=notes_preview_ctrl, expand=True),
                        ft.Row(
                            [
                                icon_button(
                                    ft.Icons.EDIT_OUTLINED,
                                    tooltip="Edit entry",
                                    on_click=lambda e, dk=day_key, en=entry: self._edit_entry(dk, en),
                                ),
                                icon_button(
                                    ft.Icons.DELETE_OUTLINE,
                                    tooltip="Delete entry",
                                    on_click=lambda e, dk=day_key: self._confirm_delete(dk),
                                ),
                            ],
                            spacing=2,
                            width=80,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=Spacing.LG, top=10, right=Spacing.LG, bottom=10),
                bgcolor=Colors.CARD,
                border=ft.Border(
                    left=ft.BorderSide(3, rating_color if rating else Colors.CARD_BORDER),
                    bottom=ft.BorderSide(1, Colors.SIDEBAR_BORDER),
                ),
                animate=Animation.FAST,
            )
            rows.append(row)

        return ft.Container(
            content=ft.Column([header_row, *rows], spacing=0),
            bgcolor=Colors.CARD,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=["#171925", "#12131c"],
            ),
            border=border_3d(light="#2c3046", dark="#101118", sides="#1e2130"),
            border_radius=Radius.LG,
            shadow=Shadows.CARD_3D,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    # ── Calendar View ──────────────────────────────────────────────

    def _build_calendar_view(self):
        self.month_label = ft.Text(
            self.current_month.strftime("%B %Y"),
            style=TextStyle.headline_medium(),
        )

        month_nav = ft.Row(
            [
                icon_button(ft.Icons.CHEVRON_LEFT, on_click=lambda e: self._change_month(-1), tooltip="Previous month"),
                ft.Container(content=self.month_label, expand=True, alignment=ft.Alignment(0, 0)),
                icon_button(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self._change_month(1), tooltip="Next month"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        calendar_grid = self._render_calendar_grid()

        return card_container(
            content=ft.Column(
                [
                    month_nav,
                    ft.Container(height=Spacing.MD),
                    calendar_grid,
                ],
                spacing=0,
            ),
        )

    def _change_month(self, delta):
        year = self.current_month.year
        month = self.current_month.month + delta
        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1
        self.current_month = date(year, month, 1)
        self._rebuild_all()

    def _render_calendar_grid(self):
        _, days_in_month = monthrange(self.current_month.year, self.current_month.month)
        first_day_weekday = self.current_month.weekday()
        first_day_col = (first_day_weekday + 1) % 7

        header_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(d, style=TextStyle.label_medium(), color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                )
                for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            ],
            spacing=Spacing.XS,
        )

        rows = [header_row, ft.Container(height=Spacing.XS)]
        week = []

        for _ in range(first_day_col):
            week.append(ft.Container(expand=True, height=44))

        for day in range(1, days_in_month + 1):
            day_date = date(self.current_month.year, self.current_month.month, day)
            day_key = day_date.isoformat()
            is_today = day_key == today_key()
            entry = self.data.get(day_key)
            rating = entry.get("rating") if entry else None

            bg = Colors.BG_SECONDARY
            if rating is not None:
                intensity = rating / 5.0
                bg = ft.Colors.with_opacity(0.3 + intensity * 0.4, Colors.POSITIVE) if rating >= 4 else (
                    ft.Colors.with_opacity(0.3, Colors.NEUTRAL) if rating == 3 else ft.Colors.with_opacity(0.3 + (5 - rating) * 0.1, Colors.NEGATIVE)
                )

            border = ft.Border.all(2, Colors.PRIMARY) if is_today else ft.Border.all(1, Colors.CARD_BORDER)

            cell = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(str(day), size=12, weight=ft.FontWeight.W_600 if is_today else ft.FontWeight.W_400),
                        ft.Text(f"{rating}★" if rating is not None else "", size=10, color=Colors.STAR_FILLED)
                    ],
                    spacing=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                height=44,
                bgcolor=bg,
                border_radius=Radius.SM,
                border=border,
                alignment=ft.Alignment(0, 0),
                on_click=lambda e, dk=day_key, en=entry: self._edit_entry(dk, en or {}),
                ink=True,
            )
            week.append(cell)

            if len(week) == 7:
                rows.append(ft.Row(week, spacing=Spacing.XS))
                week = []

        if week:
            while len(week) < 7:
                week.append(ft.Container(expand=True, height=44))
            rows.append(ft.Row(week, spacing=Spacing.XS))

        return ft.Column(rows, spacing=Spacing.XS)

    # ── Edit / Delete Dialogs ──────────────────────────────────────

    def _edit_entry(self, day_key, entry):
        rating_field = ft.Dropdown(
            label="Rating",
            options=[ft.dropdown.Option(str(i)) for i in range(6)],
            value=str(entry.get("rating", 4)),
            width=200,
        )
        notes_field = text_field("Notes", "What happened today?", multiline=True, value=entry.get("notes", ""), min_lines=3, max_lines=5)
        refl_answer = entry.get("reflection", {}).get("answer", "") if entry.get("reflection") else ""
        refl_question = entry.get("reflection", {}).get("question", "What challenged you today?") if entry.get("reflection") else "What challenged you today?"
        reflection_field = text_field(refl_question, "Your answer...", multiline=True, value=refl_answer, min_lines=2, max_lines=3)

        def save_edit(e):
            new_entry = {
                "rating": int(rating_field.value) if rating_field.value else 0,
                "notes": notes_field.value.strip() if notes_field.value else None,
                "reflection": {"question": refl_question, "answer": reflection_field.value.strip()} if reflection_field.value else None,
                "keywords": entry.get("keywords", []),
            }
            self.data[day_key] = validate_entry(new_entry)
            save_data(self.data)
            self.page.pop_dialog()
            self._rebuild_all()
            if self.on_data_change:
                self.on_data_change()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit Log — {day_key}", style=TextStyle.headline_small()),
            content=ft.Column([rating_field, notes_field, reflection_field], tight=True, spacing=Spacing.MD, width=440),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()),
                primary_button("Save Changes", on_click=save_edit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    def _confirm_delete(self, day_key):
        def do_delete(e):
            delete_entry(self.data, day_key)
            save_data(self.data)
            self.page.pop_dialog()
            self._rebuild_all()
            if self.on_data_change:
                self.on_data_change()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Entry?", style=TextStyle.headline_small()),
            content=ft.Text(f"Are you sure you want to delete the log for {day_key}?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()),
                ft.FilledButton(
                    content="Delete",
                    on_click=do_delete,
                    style=ft.ButtonStyle(bgcolor=Colors.ERROR),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    def _rebuild_all(self):
        self.data = load_data()
        self.folders_row.controls = self._build_month_folders()
        self.content_container.content = self._build_table_view() if self.view_mode == "table" else self._build_calendar_view()
        safe_update(self.folders_row, self.content_container)

    def refresh(self):
        self._rebuild_all()
