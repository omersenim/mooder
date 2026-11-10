"""Sync tab - Local WiFi sync with QR code for the phone PWA (Flet port of gui/tabs/sync.py)."""
import base64
import inspect
import socket
import struct
import threading
import zlib

import flet as ft

from flet_gui.theme import *


DEFAULT_PORT = 8000
POLL_INTERVAL_SECONDS = 5
QR_DISPLAY_SIZE = 200
# 1x1 transparent PNG used until a real QR code is generated
_BLANK_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


# ─── Helpers ───────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Get the local LAN IP address (falls back to loopback)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return "127.0.0.1"


def _matrix_to_png_base64(matrix, scale: int = 6, border: int = 2) -> str:
    """Encode a QR boolean matrix as a base64 grayscale PNG (no Pillow needed)."""
    size = (len(matrix) + border * 2) * scale
    rows = bytearray()
    for y in range(size):
        rows.append(0)  # PNG filter type: None
        my = y // scale - border
        for x in range(size):
            mx = x // scale - border
            dark = 0 <= my < len(matrix) and 0 <= mx < len(matrix) and matrix[my][mx]
            rows.append(0 if dark else 255)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode("ascii")


class SyncTab(ft.Column):
    """Sync tab: shows LAN IP, QR code, server status and connected devices."""

    def __init__(self, server_ref=None, on_data_change=None):
        super().__init__(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        self.server_ref = server_ref  # Object exposing start/stop/get_connected_devices
        self.on_data_change = on_data_change

        self.server_running = False
        self.server_port = DEFAULT_PORT
        self.local_ip = get_local_ip()
        self.phone_url = self._make_url()
        self._qr_b64 = None
        self._stop_poll = threading.Event()
        self._poll_thread = None

        self._build()

    # ── URL ────────────────────────────────────────────────────────

    def _make_url(self) -> str:
        return f"http://{self.local_ip}:{self.server_port}"

    # ── UI construction ────────────────────────────────────────────

    def _build(self):
        # Status widgets
        is_running = bool(self.server_ref and getattr(self.server_ref, "running", False))
        self.server_running = is_running
        self.status_dot = ft.Container(
            width=12, height=12, border_radius=Radius.FULL,
            bgcolor=Colors.SUCCESS if is_running else Colors.ERROR,
            animate=Animation.NORMAL,
        )
        self.status_text = ft.Text("Server: Running" if is_running else "Server: Stopped", style=TextStyle.title_large())
        self.toggle_btn = primary_button(
            "Stop Server" if is_running else "Start Server",
            ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW,
            on_click=self._toggle_server,
        )
        self.copy_btn = secondary_button("Copy URL", ft.Icons.CONTENT_COPY, on_click=self._copy_url)

        # Connection info widgets
        self.ip_text = ft.Text(self.local_ip, style=TextStyle.body_large(), selectable=True)
        self.port_text = ft.Text(str(self.server_port), style=TextStyle.body_large(), selectable=True)
        self.url_text = ft.Text(
            self.phone_url, style=TextStyle.body_large(), color=Colors.PRIMARY, selectable=True,
        )

        # QR widgets
        self.qr_image = ft.Image(
            src=_BLANK_PNG_B64, width=QR_DISPLAY_SIZE - 20, height=QR_DISPLAY_SIZE - 20,
            fit=ft.BoxFit.CONTAIN, visible=False,
        )
        self.qr_placeholder = ft.Column(
            [
                ft.Icon(ft.Icons.QR_CODE_2, size=56, color=Colors.TEXT_MUTED),
                ft.Text("QR Code", style=TextStyle.title_medium(), color=Colors.TEXT_MUTED),
                ft.Text("(Start server)", style=TextStyle.caption()),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.XS,
        )
        self.qr_box = ft.Container(
            content=ft.Stack(
                [
                    ft.Container(content=self.qr_placeholder, alignment=ft.Alignment(0, 0)),
                    ft.Container(content=self.qr_image, alignment=ft.Alignment(0, 0)),
                ],
                width=QR_DISPLAY_SIZE, height=QR_DISPLAY_SIZE,
            ),
            width=QR_DISPLAY_SIZE,
            height=QR_DISPLAY_SIZE,
            bgcolor=Colors.BG_SECONDARY,
            border_radius=Radius.LG,
            border=ft.Border.all(1, Colors.CARD_BORDER),
            padding=ft.Padding.all(Spacing.SM),
        )
        self.refresh_qr_btn = secondary_button(
            "Refresh QR", ft.Icons.REFRESH, on_click=lambda e: self._generate_qr(notify=True),
        )

        # Devices
        self.devices_column = ft.Column(spacing=Spacing.SM)
        self._render_devices([])

        left_col = ft.Column(
            [
                self._build_status_card(),
                self._build_info_card(),
            ],
            spacing=Spacing.MD,
            expand=1,
        )

        right_col = ft.Column(
            [
                self._build_qr_card(),
                self._build_devices_card(),
                self._build_troubleshooting_card(),
            ],
            spacing=Spacing.MD,
            expand=1,
        )

        self.controls = [
            ft.Container(height=Spacing.LG),
            self._build_header(),
            ft.Container(height=Spacing.MD),
            ft.Container(
                content=ft.Row(
                    [left_col, right_col],
                    spacing=Spacing.MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=Spacing.XL),
            ),
        ]

    @staticmethod
    def _card_margin():
        return None

    def _build_header(self):
        is_running = bool(self.server_ref and getattr(self.server_ref, "running", False))
        status_pill = (
            badge_pill("Online", bg_color=Colors.PRIMARY_DIM, text_color=Colors.PRIMARY, icon=ft.Icons.WIFI)
            if is_running
            else badge_pill("Offline", bg_color=Colors.PILL_BG, text_color=Colors.TEXT_MUTED, icon=ft.Icons.WIFI_OFF)
        )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Phone Sync", style=TextStyle.display_small()),
                            ft.Text(
                                "Sync with your phone or tablet over local WiFi",
                                style=TextStyle.body_small(),
                                color=Colors.TEXT_MUTED,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    status_pill,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=Spacing.LG, top=0, right=Spacing.LG, bottom=0),
        )

    def _build_status_card(self):
        return card_container(
            content=ft.Column(
                [
                    section_title("Server Status"),
                    ft.Container(height=Spacing.MD),
                    ft.Row(
                        [self.status_dot, self.status_text],
                        spacing=Spacing.SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=Spacing.MD),
                    ft.Row([self.toggle_btn, self.copy_btn], spacing=Spacing.MD),
                ],
                spacing=0,
            ),
            margin=self._card_margin(),
        )

    def _info_row(self, icon, label, value_control):
        return ft.Row(
            [
                ft.Icon(icon, size=18, color=Colors.TEXT_SECONDARY),
                ft.Text(label, style=TextStyle.label_large(), width=110),
                value_control,
            ],
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_info_card(self):
        instructions = (
            "1. Connect phone to the same WiFi\n"
            "2. Scan the QR code below or open the URL above\n"
            "3. Tap 'Install' to add it to your home screen\n"
            "4. Log days from your phone - syncs automatically"
        )
        return card_container(
            content=ft.Column(
                [
                    section_title("Connection Info"),
                    ft.Container(height=Spacing.MD),
                    self._info_row(ft.Icons.LANGUAGE, "LAN IP", self.ip_text),
                    self._info_row(ft.Icons.SETTINGS_ETHERNET, "Port", self.port_text),
                    self._info_row(ft.Icons.PHONE_ANDROID, "Phone URL", self.url_text),
                    ft.Container(height=Spacing.SM),
                    divider(),
                    ft.Container(height=Spacing.SM),
                    ft.Text(instructions, style=TextStyle.body_small()),
                ],
                spacing=Spacing.SM,
            ),
            margin=self._card_margin(),
        )

    def _build_qr_card(self):
        return card_container(
            content=ft.Column(
                [
                    section_title("QR Code (Scan with Phone)"),
                    ft.Container(height=Spacing.MD),
                    self.qr_box,
                    ft.Container(height=Spacing.MD),
                    self.refresh_qr_btn,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            margin=self._card_margin(),
        )

    def _build_devices_card(self):
        return card_container(
            content=ft.Column(
                [
                    section_title("Connected Devices"),
                    ft.Container(height=Spacing.MD),
                    self.devices_column,
                ],
                spacing=0,
            ),
            margin=self._card_margin(),
        )

    def _build_troubleshooting_card(self):
        tips = [
            "Phone and computer must be on the SAME WiFi network",
            "Windows Firewall: allow Python on Private networks",
            "If the QR doesn't work, type the URL into your phone browser",
            "The PWA works offline - changes sync when back on WiFi",
            "No cloud, no accounts - data stays on your devices",
        ]
        return card_container(
            content=ft.Column(
                [
                    section_title("Troubleshooting"),
                    ft.Container(height=Spacing.MD),
                    *[
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=Colors.TEXT_MUTED),
                                ft.Text(t, style=TextStyle.body_small(), expand=True),
                            ],
                            spacing=Spacing.SM,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        )
                        for t in tips
                    ],
                ],
                spacing=Spacing.SM,
            ),
            margin=self._card_margin(),
        )

    # ── Device list ────────────────────────────────────────────────

    def _render_devices(self, devices):
        """Rebuild the connected devices list."""
        if not devices:
            self.devices_column.controls = [
                ft.Container(
                    content=empty_state(
                        ft.Icons.DEVICES_OTHER, "No devices connected",
                        "Devices appear here once they reach the server",
                    ),
                    padding=ft.Padding.all(Spacing.MD),
                )
            ]
            return

        rows = []
        for d in devices:
            ua = str(d.get("ua", "?"))
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SMARTPHONE, size=20, color=Colors.PRIMARY),
                            ft.Column(
                                [
                                    ft.Text(str(d.get("ip", "?")), style=TextStyle.title_medium()),
                                    ft.Text(ua[:50], style=TextStyle.caption()),
                                ],
                                spacing=0, expand=True,
                            ),
                            ft.Text(str(d.get("last_seen", "?")), style=TextStyle.body_small()),
                        ],
                        spacing=Spacing.MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.all(Spacing.SM),
                    bgcolor=Colors.BG_SECONDARY,
                    border_radius=Radius.MD,
                    border=ft.Border.all(1, Colors.CARD_BORDER),
                )
            )
        self.devices_column.controls = rows

    def _update_devices(self, devices):
        self._render_devices(devices)
        self._safe_update(self.devices_column)

    # ── State rendering ────────────────────────────────────────────

    def _set_running(self, running: bool):
        self.server_running = running
        self.status_dot.bgcolor = Colors.SUCCESS if running else Colors.ERROR
        self.status_text.value = "Server: Running" if running else "Server: Stopped"
        self.toggle_btn.content = "Stop Server" if running else "Start Server"
        self.toggle_btn.icon = ft.Icons.STOP if running else ft.Icons.PLAY_ARROW
        self._safe_update(self.status_dot, self.status_text, self.toggle_btn)

    def _show_qr_placeholder(self):
        self._qr_b64 = None
        self.qr_image.visible = False
        self.qr_placeholder.visible = True
        self._safe_update(self.qr_image, self.qr_placeholder)

    def _generate_qr(self, notify: bool = False):
        """Generate the QR code for the phone URL (needs only `qrcode`)."""
        try:
            import qrcode
        except ImportError:
            self._snack("qrcode is required for QR generation. Run: pip install qrcode pillow", error=True)
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(self.phone_url)
            qr.make(fit=True)
            self._qr_b64 = _matrix_to_png_base64(qr.get_matrix(), scale=6, border=2)  # light quiet zone keeps it scannable on dark UI
        except Exception as ex:
            self._snack(f"Failed to generate QR: {ex}", error=True)
            return

        self.qr_image.src = self._qr_b64
        self.qr_image.visible = True
        self.qr_placeholder.visible = False
        self._safe_update(self.qr_image, self.qr_placeholder)
        if notify:
            self._snack("QR code refreshed")

    # ── Event handlers ─────────────────────────────────────────────

    def _toggle_server(self, e=None):
        if self.server_running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        """Start the server through server_ref (if provided)."""
        try:
            if self.server_ref and hasattr(self.server_ref, "start"):
                self.server_ref.start()
                note = f"Server running at {self.phone_url}"
            else:
                note = f"Server would start at {self.phone_url} (integration happens in main.py)"
        except Exception as ex:
            self._snack(f"Could not start server: {ex}", error=True)
            return

        self._set_running(True)
        self._generate_qr()
        self._snack(note)

    def _stop_server(self):
        try:
            if self.server_ref and hasattr(self.server_ref, "stop"):
                self.server_ref.stop()
        except Exception as ex:
            self._snack(f"Error while stopping server: {ex}", error=True)
        self._set_running(False)
        self._show_qr_placeholder()
        self._update_devices([])

    async def _copy_url(self, e=None):
        page = self._get_page()
        if page is None:
            return
        try:
            await ft.Clipboard().set(self.phone_url)
        except Exception as ex:
            self._snack(f"Could not copy: {ex}", error=True)
            return
        self._snack(f"URL copied: {self.phone_url}")

    # ── Polling (connected devices) ────────────────────────────────

    def did_mount(self):
        self._stop_poll.clear()
        if self.server_ref and getattr(self.server_ref, "running", False):
            self._set_running(True)
            self._generate_qr()
        if self._poll_thread is None or not self._poll_thread.is_alive():
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

    def will_unmount(self):
        self._stop_poll.set()

    def _poll_loop(self):
        while not self._stop_poll.wait(POLL_INTERVAL_SECONDS):
            ref = self.server_ref
            if self.server_running and ref and hasattr(ref, "get_connected_devices"):
                try:
                    devices = ref.get_connected_devices()
                except Exception:
                    continue
                self._update_devices(devices)

    # ── Public API ─────────────────────────────────────────────────

    def set_server_ref(self, server_ref):
        """Set reference to the server object (called from main.py)."""
        self.server_ref = server_ref

    def refresh(self):
        """Refresh IP/URL (called when the tab becomes active)."""
        self.local_ip = get_local_ip()
        self.phone_url = self._make_url()
        self.ip_text.value = self.local_ip
        self.url_text.value = self.phone_url
        if self.server_ref and getattr(self.server_ref, "running", False):
            self._set_running(True)
            self._generate_qr()
        self._safe_update(self.ip_text, self.url_text)

    # ── Utilities ──────────────────────────────────────────────────

    def _get_page(self):
        try:
            return self.page
        except Exception:
            return None

    def _safe_update(self, *controls):
        """Update controls only when mounted on a page."""
        if self._get_page() is None:
            return
        for c in controls:
            try:
                c.update()
            except Exception:
                pass

    def _snack(self, message: str, error: bool = False):
        page = self._get_page()
        if page is None:
            return
        bar = ft.SnackBar(
            content=ft.Text(message, color=Colors.TEXT),
            bgcolor=Colors.CARD if not error else Colors.ERROR,
        )
        try:
            page.show_dialog(bar)
        except Exception:
            pass
