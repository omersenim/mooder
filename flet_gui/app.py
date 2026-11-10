"""Main desktop window for Mooder — Linear/macOS workspace shell with left sidebar navigation."""

import os
import sys
import flet as ft

from core.data import load_data, today_key
from core.weekly import current_streak
from flet_gui.tabs.history_tab import HistoryTab
from flet_gui.tabs.stats_tab import StatsTab
from flet_gui.tabs.sync_tab import SyncTab
from flet_gui.tabs.today_tab import TodayTab
from flet_gui.tabs.weekly_tab import WeeklyTab
from flet_gui.theme import *


# Navigation definitions: (id, label, icon, breadcrumb_label)
NAV_ITEMS = [
    ("today", "Today", ft.Icons.WB_SUNNY_OUTLINED, "Today"),
    ("history", "History & Archive", ft.Icons.FOLDER_OPEN_OUTLINED, "History"),
    ("weekly", "Weekly Review", ft.Icons.AUTO_AWESOME_OUTLINED, "Weekly Review"),
    ("stats", "Stats & Insights", ft.Icons.INSIGHTS_OUTLINED, "Insights"),
    ("sync", "Phone Sync", ft.Icons.PHONELINK_OUTLINED, "Phone Sync"),
]


class MooderApp:
    """Hosts Mooder desktop shell with a sidebar and breadcrumb workspace."""

    def __init__(self, page: ft.Page, server_ref=None):
        self.page = page
        self.server_ref = server_ref
        self.tabs = {}
        self.current_tab_id = "today"
        self.nav_buttons = {}
        self._setup_page()
        self._build()

    # ── Page setup ─────────────────────────────────────────────────

    def _setup_page(self):
        page = self.page
        page.title = "Mooder — Personal Day & Mood Logger"
        page.bgcolor = Colors.BG
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(
            color_scheme_seed=Colors.PRIMARY,
            use_material3=True,
        )

        for attr, value in (
            ("window_width", 1080),
            ("window_height", 800),
            ("window_min_width", 720),
            ("window_min_height", 580),
        ):
            try:
                setattr(page, attr, value)
            except Exception:
                pass
        try:
            page.window.width, page.window.height = 1080, 800
            page.window.min_width, page.window.min_height = 720, 580
            page.window.title_bar_hidden = True
            page.window.title_bar_buttons_hidden = True
            base_dir = getattr(sys, "_MEIPASS", os.getcwd())
            icon_candidate = os.path.join(base_dir, "assets", "icon.ico")
            if os.path.exists(icon_candidate):
                page.window.icon = icon_candidate
            else:
                page.window.icon = "assets/icon.ico"
        except Exception:
            pass

    # ── UI Construction ────────────────────────────────────────────

    def _build(self):
        # Instantiate content tabs
        self.tabs = {
            "today": TodayTab(on_data_change=self._on_data_change),
            "history": HistoryTab(on_data_change=self._on_data_change),
            "weekly": WeeklyTab(on_data_change=self._on_data_change),
            "stats": StatsTab(on_data_change=self._on_data_change),
            "sync": SyncTab(server_ref=self.server_ref, on_data_change=self._on_data_change),
        }

        # Dynamic breadcrumbs
        self.breadcrumb_container = ft.Container(
            content=breadcrumb_bar(["Mooder Workspace", "Today"]),
        )

        # Tab view switcher
        self.switcher = ft.AnimatedSwitcher(
            content=self.tabs["today"],
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=180,
            reverse_duration=90,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            expand=True,
        )

        # Build Sidebar & Main pane
        self.sidebar = self._build_sidebar()
        self.main_content = self._build_main_pane()

        # Root layout: 2-column workspace
        self.page.add(
            ft.SafeArea(
                expand=True,
                content=ft.Row(
                    [
                        self.sidebar,
                        self.main_content,
                    ],
                    spacing=0,
                    expand=True,
                ),
            )
        )

        self.page.on_keyboard_event = self._on_keyboard
        self._refresh_streak_badge()

    # ── Sidebar ────────────────────────────────────────────────────

    def _build_sidebar(self):
        data = load_data()
        today_logged = today_key() in data
        streak = current_streak(data)

        # Workspace Profile Header (Clean, purposeful branding)
        workspace_header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text("M", size=13, weight=ft.FontWeight.BOLD, color=Colors.BG),
                        width=32,
                        height=32,
                        bgcolor=Colors.PRIMARY,
                        border_radius=Radius.SM,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        [
                            ft.Text("Mooder Workspace", size=13, weight=ft.FontWeight.W_600, color=Colors.TEXT),
                            ft.Text(f"🔥 {streak} day streak" if streak > 0 else "Personal Day & Mood Logger", size=11, color=Colors.TEXT_MUTED),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                ],
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.MD, top=Spacing.LG, right=Spacing.MD, bottom=Spacing.MD),
        )

        # Navigation section title
        nav_header = ft.Container(
            content=ft.Text("NAVIGATION", size=10, weight=ft.FontWeight.W_700, color=Colors.TEXT_MUTED),
            padding=ft.Padding(left=Spacing.MD, top=Spacing.SM, right=Spacing.MD, bottom=Spacing.XS),
        )

        # Navigation Links
        nav_controls = []
        for nav_id, label, icon, _ in NAV_ITEMS:
            badge_ctrl = None
            if nav_id == "today" and not today_logged:
                badge_ctrl = ft.Container(
                    width=7, height=7, border_radius=Radius.FULL, bgcolor=Colors.WARNING
                )
            elif nav_id == "sync" and self.server_ref and getattr(self.server_ref, "running", False):
                badge_ctrl = ft.Container(
                    width=7, height=7, border_radius=Radius.FULL, bgcolor=Colors.SUCCESS
                )

            btn = self._build_nav_item(nav_id, label, icon, badge_ctrl)
            self.nav_buttons[nav_id] = btn
            nav_controls.append(btn)

        # Sidebar Footer: Real Vault Info & Shortcut Hints
        sidebar_footer = ft.Container(
            content=ft.Column(
                [
                    ft.Divider(height=1, thickness=1, color=Colors.SIDEBAR_BORDER),
                    ft.Container(height=4),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.STORAGE_ROUNDED, size=13, color=Colors.TEXT_MUTED),
                            ft.Text(f"{len(data)} logs stored locally", size=11, color=Colors.TEXT_MUTED),
                        ],
                        spacing=Spacing.XS,
                    ),
                    ft.Text("Shortcuts: Ctrl+1..5 | F5 Refresh", size=10, color=Colors.TEXT_DISABLED),
                ],
                spacing=Spacing.XS,
            ),
            padding=ft.Padding(left=Spacing.MD, top=0, right=Spacing.MD, bottom=Spacing.MD),
        )

        return ft.Container(
            content=ft.Column(
                [
                    workspace_header,
                    nav_header,
                    ft.Column(nav_controls, spacing=2),
                    ft.Container(expand=True),
                    sidebar_footer,
                ],
                spacing=0,
            ),
            width=240,
            bgcolor=Colors.SIDEBAR,
            border=ft.Border(right=ft.BorderSide(1, Colors.SIDEBAR_BORDER)),
        )

    def _build_nav_item(self, nav_id: str, label: str, icon: str, badge: ft.Control = None):
        is_selected = nav_id == self.current_tab_id
        items = [
            ft.Icon(
                icon,
                size=18,
                color=Colors.PRIMARY if is_selected else Colors.TEXT_SECONDARY,
            ),
            ft.Text(
                label,
                size=13,
                weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400,
                color=Colors.TEXT if is_selected else Colors.TEXT_SECONDARY,
                expand=True,
            ),
        ]
        if badge:
            items.append(badge)

        return ft.Container(
            content=ft.Row(items, spacing=Spacing.MD, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=Colors.SIDEBAR_SELECTED if is_selected else None,
            border_radius=Radius.MD,
            padding=ft.Padding(left=12, top=9, right=12, bottom=9),
            margin=ft.Margin(left=Spacing.MD, top=1, right=Spacing.MD, bottom=1),
            on_click=lambda e, nid=nav_id: self.select_tab(nid),
            ink=True,
            animate=Animation.FAST,
        )

    # ── Main Pane ──────────────────────────────────────────────────

    def _build_main_pane(self):
        # Discord-style Integrated Window Controls
        win_controls = ft.Row(
            [
                window_control_button(
                    ft.Icons.REMOVE_ROUNDED,
                    on_click=self._minimize_window,
                    tooltip="Minimize",
                ),
                window_control_button(
                    ft.Icons.CROP_SQUARE_ROUNDED,
                    on_click=self._maximize_window,
                    tooltip="Maximize / Restore",
                ),
                window_control_button(
                    ft.Icons.CLOSE_ROUNDED,
                    on_click=self._close_window,
                    is_close=True,
                    tooltip="Close",
                ),
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Top breadcrumb line & utility buttons
        top_bar_content = ft.Row(
            [
                self.breadcrumb_container,
                ft.Row(
                    [
                        icon_button(
                            ft.Icons.REFRESH_ROUNDED,
                            tooltip="Refresh (F5)",
                            on_click=lambda e: self._refresh_current(),
                        ),
                        icon_button(
                            ft.Icons.FILE_DOWNLOAD_OUTLINED,
                            tooltip="Export Data",
                            on_click=self._export_dialog,
                        ),
                        ft.Container(
                            width=1,
                            height=18,
                            bgcolor=Colors.CARD_BORDER,
                            margin=ft.Margin(left=4, top=0, right=4, bottom=0),
                        ),
                        win_controls,
                    ],
                    spacing=Spacing.XS,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        top_bar = ft.Container(
            content=ft.WindowDragArea(
                content=top_bar_content,
                expand=True,
            ),
            height=46,
            padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.SM, bottom=0),
            border=ft.Border(bottom=ft.BorderSide(1, Colors.CARD_BORDER)),
            bgcolor=Colors.BG,
        )

        return ft.Container(
            content=ft.Column(
                [
                    top_bar,
                    ft.Container(content=self.switcher, expand=True, bgcolor=Colors.BG),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=Colors.BG,
        )

    def _minimize_window(self, e):
        try:
            self.page.window.minimized = True
            self.page.update()
        except Exception:
            pass

    def _maximize_window(self, e):
        try:
            self.page.window.maximized = not self.page.window.maximized
            self.page.update()
        except Exception:
            pass

    async def _close_window(self, e):
        if self.server_ref:
            try:
                self.server_ref.stop()
            except Exception:
                pass
        try:
            await self.page.window.destroy()
        except Exception:
            try:
                await self.page.window.close()
            except Exception:
                pass

    # ── Navigation & State ─────────────────────────────────────────

    def select_tab(self, tab_id):
        # Support int index or string identifier
        if isinstance(tab_id, int):
            if 0 <= tab_id < len(NAV_ITEMS):
                tab_id = NAV_ITEMS[tab_id][0]
            else:
                return

        if tab_id not in self.tabs:
            return

        self.current_tab_id = tab_id
        # Update breadcrumb label
        matched = next((item for item in NAV_ITEMS if item[0] == tab_id), None)
        breadcrumb_title = matched[3] if matched else tab_id.capitalize()
        self.breadcrumb_container.content = breadcrumb_bar(["Mooder Workspace", breadcrumb_title])
        self.breadcrumb_container.update()

        # Update sidebar nav item highlights
        for nid, btn in self.nav_buttons.items():
            is_sel = nid == tab_id
            btn.bgcolor = Colors.SIDEBAR_SELECTED if is_sel else None
            # Icon & text color
            row = btn.content
            row.controls[0].color = Colors.PRIMARY if is_sel else Colors.TEXT_SECONDARY
            row.controls[1].color = Colors.TEXT if is_sel else Colors.TEXT_SECONDARY
            row.controls[1].weight = ft.FontWeight.W_600 if is_sel else ft.FontWeight.W_400
            btn.update()

        # Switch content
        self.switcher.content = self.tabs[tab_id]
        self.page.update()
        self._refresh_current()

    def _refresh_current(self):
        tab = self.tabs[self.current_tab_id]
        refresh = getattr(tab, "refresh", None)
        if callable(refresh):
            try:
                refresh()
                self.page.update()
            except Exception as ex:
                print(f"[mooder] refresh failed: {ex}")

    def _refresh_streak_badge(self):
        data = load_data()
        current_streak(data)

    def _on_data_change(self):
        for key in ("history", "weekly", "stats"):
            if key == self.current_tab_id:
                continue
            tab = self.tabs[key]
            tab_refresh = getattr(tab, "refresh", None)
            if callable(tab_refresh):
                try:
                    tab_refresh()
                except Exception:
                    pass

    def _on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "F5":
            self._refresh_current()
        elif e.ctrl and e.key in {"1", "2", "3", "4", "5"}:
            idx = int(e.key) - 1
            if 0 <= idx < len(NAV_ITEMS):
                self.select_tab(NAV_ITEMS[idx][0])

    def _export_dialog(self, e=None):
        import json
        data = load_data()
        count = len(data)
        try:
            with open("mooder_backup.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"✓ Exported {count} entries to mooder_backup.json", color=Colors.TEXT),
                    bgcolor=Colors.CARD,
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
            )
            self.page.update()
        except Exception as ex:
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Export failed: {ex}", color=Colors.ERROR),
                    bgcolor=Colors.CARD,
                )
            )


DaylogApp = MooderApp


def main(page: ft.Page, server_ref=None):
    MooderApp(page, server_ref=server_ref)


def run(server_ref=None):
    if hasattr(ft, "run"):
        ft.run(lambda page: main(page, server_ref))
    else:
        ft.app(target=lambda page: main(page, server_ref))


if __name__ == "__main__":
    run()
