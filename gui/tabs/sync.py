"""Sync tab — Local WiFi sync with QR code for phone PWA."""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time

from gui.widgets import add_tooltip


class SyncTab(ttk.Frame):
    """Sync tab: Shows LAN IP, QR code, server status, connected devices."""

    def __init__(self, parent, server_ref=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.server_ref = server_ref  # Reference to server thread/object
        self.server_running = False
        self.server_port = 8000
        self.local_ip = self._get_local_ip()
        self.qr_image = None
        self._build()
        self._start_status_poll()

    def _get_local_ip(self) -> str:
        """Get the local LAN IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _build(self) -> None:
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Title ──────────────────────────────────────────────────────
        ttk.Label(main, text="📱 Phone Sync (Local WiFi)", font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(0, 20))

        # ── Server Status ──────────────────────────────────────────────
        status_frame = ttk.LabelFrame(main, text="Server Status", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))

        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(status_frame, text="Server: Stopped", font=("Segoe UI", 11))
        self.status_label.pack(side=tk.LEFT)
        self._draw_status_circle(False)

        self.url_label = ttk.Label(status_frame, text="", font=("Consolas", 10), foreground="#0066cc", cursor="hand2")
        self.url_label.pack(side=tk.LEFT, padx=(20, 0))
        self.url_label.bind("<Button-1>", self._copy_url)

        # Buttons
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(side=tk.RIGHT)

        self.start_btn = ttk.Button(btn_frame, text="▶ Start Server", command=self._toggle_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 Copy URL", command=self._copy_url).pack(side=tk.LEFT, padx=5)

        # ── Connection Info ────────────────────────────────────────────
        info_frame = ttk.LabelFrame(main, text="Connection Info", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        grid = ttk.Frame(info_frame)
        grid.pack(fill=tk.X)

        ttk.Label(grid, text="🌐 LAN IP:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.ip_label = ttk.Label(grid, text=self.local_ip, font=("Consolas", 11))
        self.ip_label.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(grid, text="🔌 Port:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.port_label = ttk.Label(grid, text=str(self.server_port), font=("Consolas", 11))
        self.port_label.grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(grid, text="📱 Phone URL:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.phone_url = f"http://{self.local_ip}:{self.server_port}"
        self.phone_url_label = ttk.Label(grid, text=self.phone_url, font=("Consolas", 11), foreground="#0066cc", cursor="hand2")
        self.phone_url_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.phone_url_label.bind("<Button-1>", self._copy_url)

        ttk.Label(grid, text="📋 Instructions:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.NW, padx=(0, 10), pady=(10, 5))
        instructions = (
            "1. Connect phone to same WiFi\n"
            "2. Scan QR code below or open URL above\n"
            "3. Tap 'Install' to add to home screen\n"
            "4. Log days from phone — syncs automatically"
        )
        ttk.Label(grid, text=instructions, font=("Segoe UI", 9), justify=tk.LEFT).grid(row=3, column=1, sticky=tk.W, pady=(10, 5))

        # ── QR Code ────────────────────────────────────────────────────
        qr_frame = ttk.LabelFrame(main, text="📷 QR Code (Scan with Phone)", padding=15)
        qr_frame.pack(fill=tk.X, pady=(0, 20))

        self.qr_canvas = tk.Canvas(qr_frame, width=200, height=200, highlightthickness=1, highlightbackground="#ccc", bg="white")
        self.qr_canvas.pack()
        self._draw_qr_placeholder()

        ttk.Button(qr_frame, text="🔄 Refresh QR", command=self._generate_qr).pack(pady=(10, 0))

        # ── Connected Devices ──────────────────────────────────────────
        devices_frame = ttk.LabelFrame(main, text="📱 Connected Devices", padding=15)
        devices_frame.pack(fill=tk.BOTH, expand=True)

        self.devices_tree = ttk.Treeview(devices_frame, columns=("IP", "Last Seen", "User Agent"), show="headings", height=6)
        self.devices_tree.heading("IP", text="IP Address")
        self.devices_tree.heading("Last Seen", text="Last Seen")
        self.devices_tree.heading("User Agent", text="User Agent")
        self.devices_tree.column("IP", width=120)
        self.devices_tree.column("Last Seen", width=150)
        self.devices_tree.column("User Agent", width=300)
        self.devices_tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(devices_frame, orient=tk.VERTICAL, command=self.devices_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.devices_tree.configure(yscrollcommand=scrollbar.set)

        # Empty state
        self.devices_tree.insert("", "end", values=("—", "No devices connected", "—"))

        # ── Troubleshooting ────────────────────────────────────────────
        trouble_frame = ttk.LabelFrame(main, text="🔧 Troubleshooting", padding=15)
        trouble_frame.pack(fill=tk.X, pady=(20, 0))

        trouble_text = (
            "• Phone and computer must be on the SAME WiFi network\n"
            "• Windows Firewall: Allow Python on Private networks\n"
            "• If QR doesn't work, manually type the URL in phone browser\n"
            "• PWA works offline — changes sync when back on WiFi\n"
            "• No cloud, no accounts — data stays on your devices"
        )
        ttk.Label(trouble_frame, text=trouble_text, font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor=tk.W)

    def _draw_status_circle(self, running: bool) -> None:
        c = self.status_indicator
        c.delete("all")
        color = "#2e7d32" if running else "#c62828"
        c.create_oval(2, 2, 18, 18, fill=color, outline="")
        self.status_label.config(text="Server: Running" if running else "Server: Stopped")

    def _draw_qr_placeholder(self) -> None:
        c = self.qr_canvas
        c.delete("all")
        c.create_rectangle(10, 10, 190, 190, fill="#f5f5f5", outline="#ddd")
        c.create_text(100, 100, text="QR Code\n(Start server)", fill="#999", font=("Segoe UI", 12), justify=tk.CENTER)

    def _generate_qr(self) -> None:
        """Generate QR code for the phone URL."""
        try:
            import qrcode
            from PIL import Image, ImageTk

            url = f"http://{self.local_ip}:{self.server_port}"
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((180, 180), Image.Resampling.LANCZOS)

            self.qr_image = ImageTk.PhotoImage(img)

            c = self.qr_canvas
            c.delete("all")
            c.create_image(100, 100, image=self.qr_image)

        except ImportError:
            messagebox.showwarning("Missing Dependency", "qrcode and pillow required for QR generation.\nRun: pip install qrcode pillow")
        except Exception as e:
            messagebox.showerror("QR Error", f"Failed to generate QR: {e}")

    def _toggle_server(self) -> None:
        """Start or stop the background server."""
        if self.server_running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self) -> None:
        """Start the FastAPI server in background thread."""
        # This will be called from main.py which has the actual server
        if self.server_ref and hasattr(self.server_ref, 'start'):
            self.server_ref.start()
            self.server_running = True
            self._draw_status_circle(True)
            self.start_btn.config(text="⏹ Stop Server")
            self._generate_qr()
            messagebox.showinfo("Server Started", f"Server running at:\n{self.phone_url}")
        else:
            # Fallback: show manual instructions
            self.server_running = True
            self._draw_status_circle(True)
            self.start_btn.config(text="⏹ Stop Server")
            self._generate_qr()
            messagebox.showinfo("Server Started",
                f"Server would start at:\n{self.phone_url}\n\n"
                "Note: Actual server integration happens in main.py")

    def _stop_server(self) -> None:
        """Stop the background server."""
        if self.server_ref and hasattr(self.server_ref, 'stop'):
            self.server_ref.stop()
        self.server_running = False
        self._draw_status_circle(False)
        self.start_btn.config(text="▶ Start Server")
        self._draw_qr_placeholder()

    def _copy_url(self, event=None) -> None:
        """Copy phone URL to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.phone_url)
        messagebox.showinfo("Copied", f"URL copied to clipboard:\n{self.phone_url}")

    def _start_status_poll(self) -> None:
        """Periodically update device list from server."""
        def poll():
            while True:
                time.sleep(5)
                if self.server_running and self.server_ref and hasattr(self.server_ref, 'get_connected_devices'):
                    devices = self.server_ref.get_connected_devices()
                    self.after(0, lambda: self._update_devices(devices))
        threading.Thread(target=poll, daemon=True).start()

    def _update_devices(self, devices: list) -> None:
        """Update connected devices tree."""
        self.devices_tree.delete(*self.devices_tree.get_children())
        if not devices:
            self.devices_tree.insert("", "end", values=("—", "No devices connected", "—"))
        else:
            for d in devices:
                self.devices_tree.insert("", "end", values=(d.get('ip', '?'), d.get('last_seen', '?'), d.get('ua', '?')[:50]))

    def set_server_ref(self, server_ref) -> None:
        """Set reference to server object (called from main.py)."""
        self.server_ref = server_ref

    def refresh(self) -> None:
        """Refresh the tab (called when tab becomes active)."""
        self.local_ip = self._get_local_ip()
        self.phone_url = f"http://{self.local_ip}:{self.server_port}"
        self.ip_label.config(text=self.local_ip)
        self.phone_url_label.config(text=self.phone_url)
        if self.server_running:
            self._generate_qr()


def create_sync_tab(parent, server_ref=None) -> SyncTab:
    """Factory function for Sync tab."""
    return SyncTab(parent, server_ref=server_ref)