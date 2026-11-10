"""Today tab — Linear/Workspace layout with overview cards, rating, notes, reflection, and keywords."""

from datetime import date
import random
import flet as ft

from core.data import load_data, save_data, today_key, validate_entry
from core.keywords import suggest_keywords_for_entry
from core.weekly import current_streak
from flet_gui.theme import *

# Predefined reflection questions
QUESTIONS = [
    "What made you smile today?",
    "What were you most proud of today?",
    "What challenged you today, and how did you handle it?",
    "What did you learn today?",
    "What are you grateful for today?",
    "If you could redo one moment today, what would it be?",
    "What gave you energy today? What drained you?",
    "Who or what made a positive impact on your day?",
    "What progress did you make on something important?",
    "How did you take care of yourself today?",
    "What would you tell your morning self?",
    "What's one thing you want to remember about today?",
]


class TodayTab(ft.Column):
    """Today tab with workspace layout matching Linear/macOS design."""

    def __init__(self, on_data_change=None):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        self.on_data_change = on_data_change

        # State
        self.rating = {"value": 0}
        self.reflection_question = random.choice(QUESTIONS)
        self.selected_keywords = set()

        # Load existing entry
        self._load_existing_entry()

        # Build UI
        self._build()

    def _load_existing_entry(self):
        """Load today's existing entry if any."""
        data = load_data()
        today = today_key()
        existing = data.get(today)
        if existing:
            self.rating["value"] = existing.get("rating", 0)
            self.notes_value = existing.get("notes", "") or ""
            if existing.get("reflection"):
                self.reflection_question = existing["reflection"].get("question", self.reflection_question)
                self.reflection_value = existing["reflection"].get("answer", "") or ""
            else:
                self.reflection_value = ""
            self.selected_keywords = set(existing.get("keywords", []))
        else:
            self.notes_value = ""
            self.reflection_value = ""
            self.selected_keywords = set()

    def _build(self):
        """Build the focused daily logging workspace."""
        self.controls = [
            ft.Container(height=Spacing.LG),
            self._build_header(),
            ft.Container(height=Spacing.MD),

            # Main Daily Log Document
            ft.Container(
                content=self._build_document_editor(),
                padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=Spacing.XL),
            ),
        ]

    def _build_header(self):
        today_str = date.today().strftime("%A, %B %d, %Y")
        data = load_data()
        is_logged = today_key() in data
        streak = current_streak(data)

        status_badge = (
            badge_pill("Logged", bg_color=Colors.PRIMARY_DIM, text_color=Colors.PRIMARY, icon=ft.Icons.CHECK_CIRCLE)
            if is_logged
            else badge_pill("Pending Log", bg_color=Colors.PILL_BG, text_color=Colors.WARNING, icon=ft.Icons.PENDING)
        )

        streak_badge = badge_pill(f"🔥 {streak} days", text_color=Colors.WARNING) if streak > 0 else ft.Container()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Today's Entry", style=TextStyle.display_small()),
                            ft.Text(today_str, style=TextStyle.body_small(), color=Colors.TEXT_MUTED),
                        ],
                        spacing=Spacing.XS,
                    ),
                    ft.Row([streak_badge, status_badge], spacing=Spacing.SM),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=0),
        )

    def _shuffle_question(self):
        self.reflection_question = random.choice(QUESTIONS)
        if hasattr(self, "question_display"):
            self.question_display.value = self.reflection_question
            safe_update(self.question_display)

    # ── Section 2: Document Editor ─────────────────────────────────

    def _build_document_editor(self):
        # 1. Rating Selector Row
        self.stars_row = ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.rating_pill_display = badge_pill("Select rating", text_color=Colors.TEXT_MUTED)
        self._rebuild_stars()

        rating_block = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("HOW WAS TODAY?", style=TextStyle.caption(), color=Colors.TEXT_MUTED),
                            ft.Container(height=4),
                            self.stars_row,
                        ],
                        spacing=0,
                    ),
                    self.rating_pill_display,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colors.BG_SECONDARY,
            border_radius=Radius.MD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            padding=ft.Padding.all(Spacing.MD),
        )

        # 2. Notes editor
        self.notes_field = text_field(
            label="Daily Notes & Highlights",
            hint_text="Write what happened today... Accomplishments, thoughts, experiences, takeaways",
            multiline=True,
            min_lines=4,
            max_lines=8,
            value=self.notes_value,
            on_change=lambda e: self._on_text_change(),
        )

        # 3. Reflection Callout Block
        self.question_display = ft.Text(
            self.reflection_question,
            size=13,
            weight=ft.FontWeight.W_600,
            color=Colors.TEXT,
        )

        reflection_header = ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=16, color=Colors.ACCENT_PURPLE),
                        self.question_display,
                    ],
                    spacing=Spacing.SM,
                    expand=True,
                ),
                icon_button(
                    ft.Icons.SHUFFLE_ROUNDED,
                    tooltip="Shuffle prompt question",
                    on_click=lambda e: self._shuffle_question(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.reflection_field = text_field(
            label="Your reflection",
            hint_text="Your honest thoughts on today's prompt...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            value=self.reflection_value,
            on_change=lambda e: self._on_text_change(),
        )

        reflection_block = ft.Container(
            content=ft.Column(
                [
                    reflection_header,
                    ft.Container(height=4),
                    self.reflection_field,
                ],
                spacing=Spacing.SM,
            ),
            bgcolor=Colors.BG_SECONDARY,
            border_radius=Radius.MD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            padding=ft.Padding.all(Spacing.MD),
        )

        # 4. Keywords Container
        self.keywords_chips_row = ft.Row([], spacing=6, wrap=True)
        self._rebuild_keywords()

        keywords_block = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("KEYWORDS & TAGS", style=TextStyle.caption(), color=Colors.TEXT_MUTED),
                        ft.Text("Click to toggle", style=TextStyle.caption(), color=Colors.TEXT_MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=4),
                self.keywords_chips_row,
            ],
            spacing=Spacing.XS,
        )

        # 5. Actions Footer
        self.save_btn = primary_button(
            text="Save Today's Entry",
            icon=ft.Icons.CHECK_ROUNDED,
            on_click=self._save_entry,
            disabled=self.rating["value"] == 0,
        )

        actions_footer = ft.Row(
            [
                ft.Text("Rate your day (1-5 stars) to enable saving", size=12, color=Colors.TEXT_MUTED),
                self.save_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Unified Document Box
        return ft.Container(
            content=ft.Column(
                [
                    rating_block,
                    ft.Container(height=Spacing.SM),
                    self.notes_field,
                    ft.Container(height=Spacing.SM),
                    reflection_block,
                    ft.Container(height=Spacing.SM),
                    keywords_block,
                    ft.Container(height=Spacing.MD),
                    ft.Divider(height=1, thickness=1, color=Colors.CARD_BORDER),
                    ft.Container(height=Spacing.SM),
                    actions_footer,
                ],
                spacing=0,
            ),
            bgcolor=Colors.CARD,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            border_radius=Radius.LG,
            padding=ft.Padding.all(Spacing.LG),
        )

    # ── Star rating interaction ────────────────────────────────────

    def _rebuild_stars(self):
        self.stars_row.controls = []
        cur_val = self.rating["value"]
        labels = {1: "Tough", 2: "Rough", 3: "Average", 4: "Good", 5: "Great!"}

        for i in range(1, 6):
            filled = i <= cur_val
            btn = ft.IconButton(
                icon=ft.Icons.STAR_ROUNDED if filled else ft.Icons.STAR_OUTLINE_ROUNDED,
                icon_color=Colors.STAR_FILLED if filled else Colors.STAR_EMPTY,
                icon_size=28,
                tooltip=f"Rate {i} / 5",
                on_click=lambda e, val=i: self._set_rating(val),
                style=ft.ButtonStyle(
                    shape=ft.CircleBorder(),
                    bgcolor={ft.ControlState.HOVERED: Colors.PRIMARY_DIM},
                ),
            )
            self.stars_row.controls.append(btn)

        if cur_val > 0:
            badge_label = f"{cur_val} / 5 · {labels.get(cur_val, '')}"
            self.rating_pill_display.content.controls[0].value = badge_label
            self.rating_pill_display.content.controls[0].color = Colors.STAR_FILLED
        else:
            self.rating_pill_display.content.controls[0].value = "Tap a star to rate"
            self.rating_pill_display.content.controls[0].color = Colors.TEXT_MUTED

        safe_update(self.stars_row, self.rating_pill_display)

    def _set_rating(self, val: int):
        self.rating["value"] = val
        self._rebuild_stars()
        self.save_btn.disabled = val == 0
        safe_update(self.save_btn)

    # ── Keywords handling ──────────────────────────────────────────

    def _on_text_change(self):
        self._rebuild_keywords()

    def _rebuild_keywords(self):
        entry_mock = {
            "notes": self.notes_field.value if hasattr(self, "notes_field") else self.notes_value,
            "reflection": {"answer": self.reflection_field.value if hasattr(self, "reflection_field") else self.reflection_value},
        }
        suggested = suggest_keywords_for_entry(entry_mock)
        all_tags = sorted(list(self.selected_keywords.union(suggested)))

        self.keywords_chips_row.controls.clear()
        if not all_tags:
            self.keywords_chips_row.controls.append(
                ft.Text("Keywords will appear automatically as you write notes...", size=12, color=Colors.TEXT_MUTED)
            )
        else:
            for tag in all_tags:
                is_selected = tag in self.selected_keywords
                bg = Colors.PRIMARY_DIM if is_selected else Colors.BG_SECONDARY
                tc = Colors.PRIMARY if is_selected else Colors.TEXT_SECONDARY
                self.keywords_chips_row.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"#{tag}", size=11, weight=ft.FontWeight.W_500, color=tc),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=bg,
                        border=ft.Border.all(1, Colors.PRIMARY if is_selected else Colors.CARD_BORDER),
                        border_radius=Radius.FULL,
                        padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                        on_click=lambda e, t=tag: self._toggle_tag(t),
                        ink=True,
                    )
                )

        safe_update(self.keywords_chips_row)

    def _toggle_tag(self, tag: str):
        if tag in self.selected_keywords:
            self.selected_keywords.remove(tag)
        else:
            self.selected_keywords.add(tag)
        self._rebuild_keywords()

    # ── Save handling ──────────────────────────────────────────────

    def _save_entry(self, e=None):
        if self.rating["value"] == 0:
            return

        entry = {
            "rating": self.rating["value"],
            "notes": self.notes_field.value.strip() if self.notes_field.value else None,
            "reflection": {
                "question": self.reflection_question,
                "answer": self.reflection_field.value.strip()
            } if self.reflection_field.value and self.reflection_field.value.strip() else None,
        }

        # Combine selected keywords and auto-suggested keywords
        auto_tags = suggest_keywords_for_entry(entry)
        combined_tags = sorted(list(self.selected_keywords.union(auto_tags)))
        entry["keywords"] = combined_tags

        data = load_data()
        data[today_key()] = validate_entry(entry)
        save_data(data)

        # Notify parent & refresh
        if self.on_data_change:
            self.on_data_change()

        # Visual confirmation
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"✓ Saved today's log ({self.rating['value']}/5 ★)", color=Colors.TEXT),
                bgcolor=Colors.CARD,
                behavior=ft.SnackBarBehavior.FLOATING,
            )
        )
        self.page.update()

    def refresh(self):
        """Called when user navigates to this tab."""
        self._load_existing_entry()
        self._rebuild_stars()
        if hasattr(self, "notes_field"):
            self.notes_field.value = self.notes_value
        if hasattr(self, "reflection_field"):
            self.reflection_field.value = self.reflection_value
        if hasattr(self, "question_display"):
            self.question_display.value = self.reflection_question
        self._rebuild_keywords()
        if hasattr(self, "save_btn"):
            self.save_btn.disabled = self.rating["value"] == 0
        safe_update(self)
