"""Quick Flet prototype - Modern 'Today' tab for Daylog."""
import flet as ft
from datetime import date
from core.data import load_data, save_data, today_key, validate_entry
from core.keywords import suggest_keywords_for_entry, get_all_keywords
import random

QUESTIONS = [
    "What made you smile today?",
    "What were you most proud of today?",
    "What challenged you today, and how did you handle it?",
    "What did you learn today?",
    "What are you grateful for today?",
]

COLORS = {
    "bg": "#0f0f0f",
    "card": "#1a1a1a",
    "card_hover": "#222",
    "primary": "#00d4aa",
    "primary_dim": "#00d4aa33",
    "text": "#f5f5f5",
    "text_muted": "#888",
    "star_filled": "#ffd700",
    "star_empty": "#333",
    "red": "#ff4757",
    "green": "#2ed573",
}

STAR_ICONS = ["☆", "☆", "☆", "☆", "☆"]  # will be replaced by Filled/Outlined


def main(page: ft.Page):
    page.title = "Daylog"
    page.bgcolor = COLORS["bg"]
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 420
    page.window_height = 720
    page.window_resizable = False
    page.padding = 0
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    }
    page.theme = ft.Theme(font_family="Inter")

    # ── State ──────────────────────────────────────────────────────
    rating = {"value": 0}
    reflection_q = random.choice(QUESTIONS)

    # ── Load existing entry ────────────────────────────────────────
    data = load_data()
    today = today_key()
    existing = data.get(today)

    # ── UI Components ──────────────────────────────────────────────
    # Stars
    stars = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER)
    rating_text = ft.Text("Tap a star", size=14, color=COLORS["text_muted"], text_align=ft.TextAlign.CENTER)

    def make_star(i):
        return ft.IconButton(
            icon=ft.Icons.STAR if i < rating["value"] else ft.Icons.STAR_OUTLINE,
            icon_color=COLORS["star_filled"] if i < rating["value"] else COLORS["star_empty"],
            icon_size=28,
            on_click=lambda e, idx=i: set_rating(idx + 1),
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                bgcolor={ft.ControlState.HOVERED: COLORS["primary_dim"]},
            ),
        )

    def rebuild_stars():
        stars.controls = [make_star(i) for i in range(5)]
        rating_text.value = f"{rating['value']}/5" if rating['value'] > 0 else "Tap a star"
        page.update()

    def set_rating(v):
        rating["value"] = v
        rebuild_stars()
        save_btn.disabled = v == 0
        save_btn.update()

    rebuild_stars()

    # Notes
    notes_field = ft.TextField(
        label="Notes (optional)",
        hint_text="What happened today?",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_radius=12,
        border_color=COLORS["primary_dim"],
        focused_border_color=COLORS["primary"],
        border_width=1,
        focused_border_width=1.5,
        text_style=ft.TextStyle(color=COLORS["text"], size=14),
        label_style=ft.TextStyle(color=COLORS["text_muted"]),
        hint_style=ft.TextStyle(color=COLORS["text_muted"]),
        bgcolor=COLORS["card"],
        content_padding=ft.Padding(left=16, top=16, right=16, bottom=16),
    )

    # Reflection
    reflection_text = ft.Text(
        reflection_q,
        size=15,
        color=COLORS["primary"],
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    reflection_field = ft.TextField(
        label="Your answer",
        hint_text="Type your reflection...",
        multiline=True,
        min_lines=2,
        max_lines=3,
        border_radius=12,
        border_color=COLORS["primary_dim"],
        focused_border_color=COLORS["primary"],
        border_width=1,
        focused_border_width=1.5,
        text_style=ft.TextStyle(color=COLORS["text"], size=14),
        label_style=ft.TextStyle(color=COLORS["text_muted"]),
        hint_style=ft.TextStyle(color=COLORS["text_muted"]),
        bgcolor=COLORS["card"],
        content_padding=ft.Padding(left=16, top=16, right=16, bottom=16),
    )

    # Keywords chips
    keyword_chips = ft.Row(spacing=8, wrap=True, alignment=ft.MainAxisAlignment.CENTER)

    def rebuild_keywords():
        keyword_chips.controls.clear()
        entry_for_kw = {"notes": notes_field.value, "reflection": {"answer": reflection_field.value}}
        suggested = suggest_keywords_for_entry(entry_for_kw)
        for kw in suggested:
            chip = ft.Container(
                content=ft.Row([
                    ft.Text(kw, size=12, weight=ft.FontWeight.W_500, color=COLORS["text"]),
                    ft.Icon(ft.Icons.CLOSE, size=14, color=COLORS["text_muted"]),
                ], spacing=4, tight=True),
                bgcolor=COLORS["primary_dim"],
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                on_click=lambda e, k=kw: toggle_keyword(k),
                ink=True,
                border=ft.border.all(1, COLORS["primary_dim"]),
            )
            keyword_chips.controls.append(chip)
        page.update()

    def toggle_keyword(kw):
        # For prototype: just remove on click
        entry_for_kw = {"notes": notes_field.value, "reflection": {"answer": reflection_field.value}}
        suggested = suggest_keywords_for_entry(entry_for_kw)
        if kw in suggested:
            # Can't easily remove from auto-suggest, so just rebuild
            pass
        rebuild_keywords()

    notes_field.on_change = lambda e: rebuild_keywords()
    reflection_field.on_change = lambda e: rebuild_keywords()

    # Save button
    def save_entry(e):
        if rating["value"] == 0:
            return

        entry = {
            "rating": rating["value"],
            "notes": notes_field.value.strip() if notes_field.value else None,
            "reflection": {"question": reflection_q, "answer": reflection_field.value.strip()} if reflection_field.value else None,
        }
        entry["keywords"] = suggest_keywords_for_entry(entry)

        data[today] = validate_entry(entry)
        save_data(data)

        # Success feedback
        page.open(ft.SnackBar(
            content=ft.Text(f"✅ Saved! Rated {rating['value']}/5", color=COLORS["text"]),
            bgcolor=COLORS["card"],
            behavior=ft.SnackBarBehavior.FLOATING,
        ))
        page.update()

    save_btn = ft.FilledButton(
        "Save Entry",
        icon=ft.Icons.SAVE,
        disabled=rating["value"] == 0,
        on_click=save_entry,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: COLORS["primary"], ft.ControlState.DISABLED: COLORS["card"]},
            color={ft.ControlState.DEFAULT: COLORS["bg"], ft.ControlState.DISABLED: COLORS["text_muted"]},
            padding=ft.Padding(left=40, top=16, right=40, bottom=16),
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
        ),
        height=56,
    )

    # Pre-fill if exists
    if existing:
        rating["value"] = existing.get("rating", 0)
        notes_field.value = existing.get("notes", "")
        if existing.get("reflection"):
            reflection_text.value = existing["reflection"].get("question", reflection_q)
            reflection_field.value = existing["reflection"].get("answer", "")
        rebuild_stars()
        rebuild_keywords()

    # ── Layout ─────────────────────────────────────────────────────
    # Consistent spacing system
    SPACING_XS = 8
    SPACING_SM = 12
    SPACING_MD = 16
    SPACING_LG = 24
    SPACING_XL = 32
    CARD_MARGIN = ft.Margin(left=20, top=0, right=20, bottom=0)
    CARD_BORDER = ft.Border.all(1, "#2a2a2a")

    page.add(
        ft.Container(
            content=ft.Column([
                # Header
                ft.Container(height=SPACING_LG),
                ft.Text("Daylog", size=28, weight=ft.FontWeight.W_700, color=COLORS["text"], text_align=ft.TextAlign.CENTER),
                ft.Text(date.today().strftime("%A, %B %d"), size=14, color=COLORS["text_muted"], text_align=ft.TextAlign.CENTER),
                ft.Container(height=SPACING_XL),

                # Rating Card
                ft.Container(
                    content=ft.Column([
                        ft.Text("How was your day?", size=18, weight=ft.FontWeight.W_600, color=COLORS["text"], text_align=ft.TextAlign.CENTER),
                        ft.Container(height=SPACING_MD),
                        stars,
                        ft.Container(height=SPACING_XS),
                        rating_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    bgcolor=COLORS["card"],
                    border_radius=20,
                    padding=ft.Padding(left=24, top=24, right=24, bottom=24),
                    margin=CARD_MARGIN,
                    border=CARD_BORDER,
                ),

                ft.Container(height=SPACING_MD),

                # Notes Card
                ft.Container(
                    content=ft.Column([
                        ft.Text("Notes", size=16, weight=ft.FontWeight.W_600, color=COLORS["text"]),
                        ft.Container(height=SPACING_SM),
                        notes_field,
                    ], spacing=0),
                    bgcolor=COLORS["card"],
                    border_radius=20,
                    padding=ft.Padding(left=20, top=20, right=20, bottom=20),
                    margin=CARD_MARGIN,
                    border=CARD_BORDER,
                ),

                ft.Container(height=SPACING_MD),

                # Reflection Card
                ft.Container(
                    content=ft.Column([
                        ft.Text("Reflection", size=16, weight=ft.FontWeight.W_600, color=COLORS["text"]),
                        ft.Container(height=SPACING_SM),
                        ft.Container(
                            content=reflection_text,
                            bgcolor=COLORS["primary_dim"],
                            border_radius=12,
                            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(height=SPACING_SM),
                        reflection_field,
                    ], spacing=0),
                    bgcolor=COLORS["card"],
                    border_radius=20,
                    padding=ft.Padding(left=20, top=20, right=20, bottom=20),
                    margin=CARD_MARGIN,
                    border=CARD_BORDER,
                ),

                ft.Container(height=SPACING_MD),

                # Keywords
                ft.Container(
                    content=ft.Column([
                        ft.Text("Suggested Keywords", size=16, weight=ft.FontWeight.W_600, color=COLORS["text"]),
                        ft.Container(height=SPACING_SM),
                        ft.Container(
                            content=keyword_chips,
                            alignment=ft.Alignment(0, 0),
                        ),
                    ], spacing=0),
                    bgcolor=COLORS["card"],
                    border_radius=20,
                    padding=ft.Padding(left=20, top=20, right=20, bottom=20),
                    margin=CARD_MARGIN,
                    border=CARD_BORDER,
                ),

                ft.Container(height=SPACING_XL),

                # Save Button - full width
                ft.Container(
                    content=ft.Row([save_btn], alignment=ft.MainAxisAlignment.CENTER),
                    margin=CARD_MARGIN,
                ),

                ft.Container(height=SPACING_XL),
            ], scroll=ft.ScrollMode.AUTO, spacing=0),
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)