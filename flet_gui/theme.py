"""Flet theme configuration for Daylog."""
import flet as ft

# ─── Color Palette ─────────────────────────────────────────────────
class Colors:
    # Deep obsidian dark theme (Linear/macOS workspace style)
    BG = "#0d0e12"
    BG_SECONDARY = "#14151b"
    CARD = "#171821"
    CARD_HOVER = "#1d1f2a"
    CARD_BORDER = "#232634"

    # Workspace & Sidebar layout
    SIDEBAR = "#121319"
    SIDEBAR_HOVER = "#181a22"
    SIDEBAR_SELECTED = "#1e212c"
    SIDEBAR_BORDER = "#1c1e27"
    PILL_BG = "#1f222d"
    PILL_BORDER = "#2b2f3e"

    # Accents matching reference image (Blue folder, Teal, Purple, Amber, Red)
    ACCENT_BLUE = "#3b82f6"
    ACCENT_PURPLE = "#8b5cf6"
    ACCENT_AMBER = "#f59e0b"
    ACCENT_CYAN = "#06b6d4"

    PRIMARY = "#00d4aa"
    PRIMARY_DIM = "#00d4aa26"
    PRIMARY_STRONG = "#00f0c0"

    TEXT = "#f3f4f8"
    TEXT_SECONDARY = "#9da3b4"
    TEXT_MUTED = "#656a7d"
    TEXT_DISABLED = "#3c3f4d"

    # Semantic
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"

    # Star rating
    STAR_FILLED = "#fbbf24"
    STAR_EMPTY = "#242735"

    # Keyword categories
    POSITIVE = "#10b981"
    NEUTRAL = "#656a7d"
    NEGATIVE = "#ef4444"

    # Light theme (future)
    LIGHT_BG = "#fafafa"
    LIGHT_CARD = "#ffffff"
    LIGHT_TEXT = "#1a1a1a"
    LIGHT_TEXT_MUTED = "#888888"
    LIGHT_BORDER = "#e0e0e0"


# ─── Spacing System ────────────────────────────────────────────────
class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


# ─── Border Radius ─────────────────────────────────────────────────
class Radius:
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    FULL = 9999


# ─── Typography ────────────────────────────────────────────────────
class TextStyle:
    @staticmethod
    def display_large():
        return ft.TextStyle(size=32, weight=ft.FontWeight.W_700, color=Colors.TEXT, letter_spacing=-0.5)

    @staticmethod
    def display_medium():
        return ft.TextStyle(size=28, weight=ft.FontWeight.W_700, color=Colors.TEXT, letter_spacing=-0.3)

    @staticmethod
    def display_small():
        return ft.TextStyle(size=24, weight=ft.FontWeight.W_600, color=Colors.TEXT)

    @staticmethod
    def headline_large():
        return ft.TextStyle(size=22, weight=ft.FontWeight.W_600, color=Colors.TEXT)

    @staticmethod
    def headline_medium():
        return ft.TextStyle(size=18, weight=ft.FontWeight.W_600, color=Colors.TEXT)

    @staticmethod
    def headline_small():
        return ft.TextStyle(size=16, weight=ft.FontWeight.W_600, color=Colors.TEXT)

    @staticmethod
    def title_large():
        return ft.TextStyle(size=16, weight=ft.FontWeight.W_500, color=Colors.TEXT)

    @staticmethod
    def title_medium():
        return ft.TextStyle(size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT)

    @staticmethod
    def body_large():
        return ft.TextStyle(size=16, weight=ft.FontWeight.W_400, color=Colors.TEXT)

    @staticmethod
    def body_medium():
        return ft.TextStyle(size=14, weight=ft.FontWeight.W_400, color=Colors.TEXT)

    @staticmethod
    def body_small():
        return ft.TextStyle(size=12, weight=ft.FontWeight.W_400, color=Colors.TEXT_SECONDARY)

    @staticmethod
    def label_large():
        return ft.TextStyle(size=14, weight=ft.FontWeight.W_500, color=Colors.TEXT)

    @staticmethod
    def label_medium():
        return ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=Colors.TEXT_SECONDARY)

    @staticmethod
    def caption():
        return ft.TextStyle(size=11, weight=ft.FontWeight.W_400, color=Colors.TEXT_MUTED)

    @staticmethod
    def muted(style_func):
        """Return a muted version of a text style."""
        style = style_func()
        style.color = Colors.TEXT_MUTED
        return style


# ─── Shadows (Layered 3D Depth) ────────────────────────────────────
class Shadows:
    CARD = ft.BoxShadow(
        spread_radius=0,
        blur_radius=20,
        color="#00000040",
        offset=ft.Offset(0, 4),
    )
    CARD_3D = [
        ft.BoxShadow(spread_radius=0, blur_radius=1, color="#ffffff0f", offset=ft.Offset(0, -1)),
        ft.BoxShadow(spread_radius=0, blur_radius=22, color="#00000085", offset=ft.Offset(0, 10)),
    ]
    ELEVATED_3D = [
        ft.BoxShadow(spread_radius=0, blur_radius=1, color="#ffffff18", offset=ft.Offset(0, -1)),
        ft.BoxShadow(spread_radius=0, blur_radius=30, color="#000000a0", offset=ft.Offset(0, 14)),
    ]
    PILL_3D = [
        ft.BoxShadow(spread_radius=0, blur_radius=1, color="#ffffff12", offset=ft.Offset(0, -1)),
        ft.BoxShadow(spread_radius=0, blur_radius=6, color="#00000060", offset=ft.Offset(0, 3)),
    ]
    POCKET_3D = [
        ft.BoxShadow(spread_radius=0, blur_radius=8, color="#00000080", offset=ft.Offset(0, 4)),
    ]


def border_3d(light="#2d3146", dark="#13141d", sides="#202332"):
    """Create a realistic top-lit beveled border for physical 3D depth."""
    return ft.Border(
        top=ft.BorderSide(1, light),
        bottom=ft.BorderSide(1, dark),
        left=ft.BorderSide(1, sides),
        right=ft.BorderSide(1, sides),
    )


# ─── Animation ─────────────────────────────────────────────────────
class Animation:
    FAST = ft.Animation(150, ft.AnimationCurve.EASE_OUT)
    NORMAL = ft.Animation(250, ft.AnimationCurve.EASE_OUT)
    SLOW = ft.Animation(350, ft.AnimationCurve.EASE_OUT)


# ─── Helper Functions ──────────────────────────────────────────────
def card_container(content, padding=None, margin=None, on_hover=None, **kwargs):
    """Create a consistently styled card container with tactile 3D depth."""
    return ft.Container(
        content=content,
        bgcolor=Colors.CARD,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#171925", "#12131c"],
        ),
        border_radius=Radius.XL,
        border=border_3d(light="#2c3046", dark="#11121a", sides="#1f2231"),
        shadow=Shadows.CARD_3D,
        padding=padding or ft.Padding.all(Spacing.MD),
        margin=margin,
        animate=Animation.NORMAL,
        on_hover=on_hover,
        **kwargs,
    )


def primary_button(text, icon=None, on_click=None, disabled=False, expand=False, **kwargs):
    """Create a consistently styled primary button."""
    return ft.FilledButton(
        content=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: Colors.PRIMARY,
                ft.ControlState.DISABLED: Colors.CARD_BORDER,
                ft.ControlState.HOVERED: Colors.PRIMARY_STRONG,
            },
            color={
                ft.ControlState.DEFAULT: Colors.BG,
                ft.ControlState.DISABLED: Colors.TEXT_DISABLED,
            },
            padding=ft.Padding(left=Spacing.LG, top=Spacing.MD, right=Spacing.LG, bottom=Spacing.MD),
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            text_style=TextStyle.label_large(),
            elevation=0,
            overlay_color=Colors.PRIMARY_DIM,
        ),
        height=48,
        **kwargs,
    )


def secondary_button(text, icon=None, on_click=None, disabled=False, **kwargs):
    """Create a consistently styled secondary button."""
    return ft.OutlinedButton(
        content=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: Colors.PRIMARY,
                ft.ControlState.DISABLED: Colors.TEXT_DISABLED,
                ft.ControlState.HOVERED: Colors.PRIMARY_STRONG,
            },
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, Colors.PRIMARY),
                ft.ControlState.HOVERED: ft.BorderSide(1.5, Colors.PRIMARY_STRONG),
            },
            padding=ft.Padding(left=Spacing.LG, top=Spacing.MD, right=Spacing.LG, bottom=Spacing.MD),
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            text_style=TextStyle.label_large(),
            elevation=0,
        ),
        height=48,
        **kwargs,
    )


def icon_button(icon, on_click=None, tooltip=None, disabled=False, **kwargs):
    """Create a consistently styled icon button."""
    return ft.IconButton(
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        disabled=disabled,
        icon_color=Colors.TEXT_SECONDARY,
        icon_size=20,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.HOVERED: Colors.PRIMARY_DIM},
            color={ft.ControlState.HOVERED: Colors.PRIMARY},
            shape=ft.CircleBorder(),
        ),
        **kwargs,
    )


def text_field(label, hint_text=None, multiline=False, **kwargs):
    """Create a consistently styled text field (kwargs override the defaults)."""
    props = dict(
        label=label,
        hint_text=hint_text,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        max_lines=5 if multiline else 1,
        border_radius=Radius.MD,
        border_color=Colors.CARD_BORDER,
        focused_border_color=Colors.PRIMARY,
        border_width=1,
        focused_border_width=1.5,
        text_style=TextStyle.body_medium(),
        label_style=TextStyle.label_medium(),
        hint_style=TextStyle.caption(),
        bgcolor=Colors.BG_SECONDARY,
        content_padding=ft.Padding(left=16, top=14, right=16, bottom=14),
    )
    props.update(kwargs)
    return ft.TextField(**props)


def divider():
    """Create a subtle divider."""
    return ft.Divider(height=1, thickness=1, color=Colors.CARD_BORDER)


def section_title(text):
    """Create a section title."""
    return ft.Text(text, style=TextStyle.headline_small())


def chip(text, color=Colors.PRIMARY_DIM, text_color=Colors.TEXT, on_click=None, closable=False):
    """Create a styled chip."""
    controls = [ft.Text(text, size=12, weight=ft.FontWeight.W_500, color=text_color)]
    if closable:
        controls.append(ft.Icon(ft.Icons.CLOSE, size=14, color=Colors.TEXT_MUTED))

    return ft.Container(
        content=ft.Row(controls, spacing=Spacing.XS, tight=True),
        bgcolor=color,
        border_radius=Radius.FULL,
        padding=ft.Padding(left=12, top=6, right=8, bottom=6),
        on_click=on_click,
        ink=True,
        border=ft.Border.all(1, Colors.CARD_BORDER),
    )


def badge_pill(text, bg_color=None, text_color=None, icon=None, leading=None):
    """Create a tactile 3D pill badge with top-edge lighting and subtle drop shadow."""
    controls = []
    if leading:
        controls.append(leading)
    elif icon:
        controls.append(ft.Icon(icon, size=12, color=text_color or Colors.TEXT_SECONDARY))
    controls.append(ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=text_color or Colors.TEXT_SECONDARY))

    custom_bg = bg_color is not None
    return ft.Container(
        content=ft.Row(controls, spacing=Spacing.XS, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bg_color if custom_bg else None,
        gradient=None if custom_bg else ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#222537", "#161825"],
        ),
        border=border_3d(light="#363a54", dark="#11121c", sides="#222537"),
        shadow=Shadows.PILL_3D,
        border_radius=Radius.FULL,
        padding=ft.Padding(left=9, top=3, right=9, bottom=3),
    )


def breadcrumb_bar(items: list[str]):
    """Create a sleek breadcrumb navigation line (e.g. Knowledge Base > General)."""
    row_controls = []
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        row_controls.append(
            ft.Text(
                item,
                size=13,
                weight=ft.FontWeight.W_600 if is_last else ft.FontWeight.W_400,
                color=Colors.TEXT if is_last else Colors.TEXT_MUTED,
            )
        )
        if not is_last:
            row_controls.append(
                ft.Text("›", size=14, color=Colors.TEXT_MUTED)
            )
    return ft.Row(row_controls, spacing=Spacing.SM, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def window_control_button(icon, on_click, is_close=False, tooltip=None):
    """Create a sleek Discord/macOS style window control button for frameless topbar."""
    hover_bg = Colors.ERROR if is_close else Colors.SIDEBAR_HOVER
    hover_fg = "#ffffff" if is_close else Colors.TEXT
    return ft.Container(
        content=ft.Icon(icon, size=13, color=Colors.TEXT_MUTED),
        width=32,
        height=32,
        border_radius=Radius.SM,
        alignment=ft.Alignment(0, 0),
        on_click=on_click,
        tooltip=tooltip,
        ink=True,
        animate=Animation.FAST,
    )


def folder_card(title, subtitle, badge_text=None, icon=None, accent_color=None, on_click=None, custom_art=None, gradient=None, expand=True):
    """
    Create a tactile 3D workspace folder card matching the reference design.
    Features layered document sheets peeking from a front frosted pocket,
    top-lit bevel borders, and soft depth shadows. Proportional flex sizing.
    """
    accent = accent_color or Colors.PRIMARY
    badge_widget = badge_pill(badge_text) if badge_text else None

    # Layered 3D folder stack:
    # 1. Base recessed back pocket
    # 2. Peeking translucent document sheets
    # 3. Front frosted pocket with gradient and drop shadow
    peeking_sheets = [
        ft.Container(
            content=ft.Container(
                width=50,
                height=42,
                bgcolor="#ffffff12",
                border_radius=4,
                border=ft.Border.all(1, "#ffffff20"),
            ),
            alignment=ft.Alignment(-0.35, -0.65),
        ),
        ft.Container(
            content=ft.Container(
                width=46,
                height=38,
                bgcolor="#ffffff0a",
                border_radius=4,
                border=ft.Border.all(1, "#ffffff16"),
            ),
            alignment=ft.Alignment(0.25, -0.5),
        ),
    ]

    front_pocket_content = []
    if custom_art:
        front_pocket_content.append(
            ft.Container(content=custom_art, alignment=ft.Alignment(0, 0))
        )
    else:
        front_pocket_content.append(
            ft.Container(
                content=ft.Icon(icon or ft.Icons.FOLDER_ROUNDED, size=42, color=accent),
                alignment=ft.Alignment(0, 0),
            )
        )

    if badge_widget:
        front_pocket_content.append(
            ft.Container(
                content=badge_widget,
                alignment=ft.Alignment(1, 1),
                padding=ft.Padding(right=8, bottom=6),
            )
        )

    pocket_gradient = gradient or ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=["#171926", "#11131e"],
    )

    front_pocket = ft.Container(
        content=ft.Stack(front_pocket_content),
        height=72,
        gradient=pocket_gradient,
        border_radius=ft.BorderRadius(0, 0, Radius.MD, Radius.MD),
        border=ft.Border(
            top=ft.BorderSide(1, "#ffffff22"),
            bottom=ft.BorderSide(1, "#0a0b10"),
            left=ft.BorderSide(1, "#ffffff0d"),
            right=ft.BorderSide(1, "#ffffff0d"),
        ),
        shadow=Shadows.POCKET_3D,
        alignment=ft.Alignment(0, 1),
    )

    folder_graphic = ft.Container(
        content=ft.Stack(
            [
                ft.Container(
                    bgcolor="#0d0e14",
                    border_radius=Radius.MD,
                    border=ft.Border.all(1, "#1c1e2b"),
                ),
                *peeking_sheets,
                ft.Container(content=front_pocket, alignment=ft.Alignment(0, 1)),
            ]
        ),
        height=105,
        border_radius=Radius.MD,
    )

    card_content = ft.Column([
        folder_graphic,
        ft.Container(height=Spacing.XS),
        ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=Colors.TEXT, text_align=ft.TextAlign.CENTER),
        ft.Text(subtitle, size=12, color=Colors.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    return ft.Container(
        content=card_content,
        bgcolor=Colors.CARD,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#181a26", "#12131d"],
        ),
        border=border_3d(light="#2d3148", dark="#101118", sides="#1e2130"),
        border_radius=Radius.LG,
        shadow=Shadows.CARD_3D,
        padding=ft.Padding.all(Spacing.MD),
        on_click=on_click,
        ink=True,
        animate=Animation.NORMAL,
        expand=expand,
    )


def workspace_table(header_row: ft.Control, rows: list[ft.Control]):
    """Create a unified Files/Entries table container matching the reference mockup."""
    table_items = [
        header_row,
        ft.Divider(height=1, thickness=1, color=Colors.CARD_BORDER),
    ]
    if not rows:
        table_items.append(
            ft.Container(
                content=ft.Text("No entries found in this folder", size=13, color=Colors.TEXT_MUTED),
                padding=ft.Padding.all(Spacing.XL),
                alignment=ft.Alignment(0, 0),
            )
        )
    else:
        for i, row in enumerate(rows):
            table_items.append(row)
            if i < len(rows) - 1:
                table_items.append(ft.Divider(height=1, thickness=1, color=Colors.SIDEBAR_BORDER))

    return ft.Container(
        content=ft.Column(table_items, spacing=0),
        bgcolor=Colors.CARD,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#171924", "#12131b"],
        ),
        border=border_3d(light="#2d3148", dark="#101118", sides="#1e2130"),
        border_radius=Radius.LG,
        shadow=Shadows.CARD_3D,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def empty_state(icon, title, subtitle, action_text=None, action_click=None):
    """Create an empty state illustration."""
    controls = [
        ft.Container(
            content=ft.Icon(icon, size=64, color=Colors.TEXT_MUTED),
            margin=ft.Margin(bottom=Spacing.LG),
        ),
        ft.Text(title, style=TextStyle.headline_small(), text_align=ft.TextAlign.CENTER),
        ft.Container(height=Spacing.SM),
        ft.Text(subtitle, style=TextStyle.body_medium(), text_align=ft.TextAlign.CENTER, color=Colors.TEXT_SECONDARY),
    ]
    if action_text and action_click:
        controls.extend([
            ft.Container(height=Spacing.LG),
            primary_button(action_text, on_click=action_click),
        ])

    return ft.Column(
        controls,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def get_page(control):
    """Safely get the page a control belongs to, returning None if unmounted."""
    try:
        return control.page
    except (RuntimeError, AttributeError):
        return None


def safe_update(*controls):
    """Safely update controls only if they are attached to an active page."""
    for c in controls:
        if c is not None and get_page(c) is not None:
            try:
                c.update()
            except Exception:
                pass

