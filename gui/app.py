"""Main GUI application — Tkinter window with notebook tabs."""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

from gui.tabs.today import create_today_tab
from gui.tabs.history import create_history_tab
from gui.tabs.weekly import create_weekly_tab
from gui.tabs.stats import create_stats_tab
from gui.tabs.sync import create_sync_tab


class DaylogApp:
    """Main Daylog GUI application."""

    def __init__(self, root, server_ref=None):
        self.root = root
        self.server_ref = server_ref
        self.tabs = {}
        self._build()
        self._center_window()

    def _build(self) -> None:
        # Window setup
        self.root.title("Daylog — Personal Day Logger")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Try to set icon
        try:
            if hasattr(sys, '_MEIPASS'):
                # Running from PyInstaller bundle
                icon_path = os.path.join(sys._MEIPASS, 'assets', 'icon.ico')
            else:
                icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        # Style
        style = ttk.Style()
        style.theme_use('clam')  # More modern look on Windows

        # Configure colors
        style.configure("TNotebook", background="#f5f5f5", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 10), font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
            background=[("selected", "white"), ("active", "#e8e8e8")],
            foreground=[("selected", "#333"), ("active", "#333")]
        )
        style.configure("TLabelFrame", background="white")
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white")

        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Create tabs
        self._create_tabs()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(10, 5))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Menu bar
        self._create_menu()

    def _create_tabs(self) -> None:
        """Create all 5 tabs."""
        # Today tab
        self.tabs['today'] = create_today_tab(self.notebook, on_data_change=self._on_data_change)
        self.notebook.add(self.tabs['today'], text="  🌅 Today  ")

        # History tab
        self.tabs['history'] = create_history_tab(self.notebook, on_data_change=self._on_data_change)
        self.notebook.add(self.tabs['history'], text="  📅 History  ")

        # Weekly tab
        self.tabs['weekly'] = create_weekly_tab(self.notebook, on_data_change=self._on_data_change)
        self.notebook.add(self.tabs['weekly'], text="  📊 Weekly  ")

        # Stats tab
        self.tabs['stats'] = create_stats_tab(self.notebook, on_data_change=self._on_data_change)
        self.notebook.add(self.tabs['stats'], text="  📈 Stats  ")

        # Sync tab
        self.tabs['sync'] = create_sync_tab(self.notebook, server_ref=self.server_ref)
        self.notebook.add(self.tabs['sync'], text="  📱 Sync  ")

    def _create_menu(self) -> None:
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data...", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Current Tab", command=self._refresh_current_tab, accelerator="F5")

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)

        # Bind F5
        self.root.bind("<F5>", lambda e: self._refresh_current_tab())

    def _on_tab_change(self, event) -> None:
        """Called when user switches tabs."""
        tab_id = self.notebook.select()
        if not tab_id:
            return
        tab_widget = self.notebook.nametowidget(tab_id)
        tab_name = self.notebook.tab(tab_widget, "text").strip()

        # Refresh the tab that became active
        if hasattr(tab_widget, 'refresh'):
            tab_widget.refresh()

        self.status_var.set(f"Viewing: {tab_name}")

    def _on_data_change(self) -> None:
        """Called when data changes in any tab — refresh all tabs."""
        for tab in self.tabs.values():
            if hasattr(tab, 'refresh'):
                tab.refresh()
        self.status_var.set("Data updated — all tabs refreshed")

    def _refresh_current_tab(self) -> None:
        """Refresh the currently active tab."""
        tab_id = self.notebook.select()
        if tab_id:
            tab_widget = self.root.nametowidget(tab_id)
            if hasattr(tab_widget, 'refresh'):
                tab_widget.refresh()
                self.status_var.set("Refreshed")

    def _export_data(self) -> None:
        """Export data to JSON file."""
        from tkinter import filedialog
        from core.data import load_data
        import json

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Daylog Data"
        )
        if filepath:
            data = load_data()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Exported {len(data)} entries to:\n{filepath}")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About Daylog",
            "Daylog v1.0\n\n"
            "Personal day logging with ratings, notes, reflections, and keyword tagging.\n\n"
            "Features:\n"
            "• Daily 0-5 star ratings with notes & reflection questions\n"
            "• Weekly review with best/worst day analysis\n"
            "• Statistics dashboard with trends & keyword correlations\n"
            "• Local WiFi sync to phone via PWA\n"
            "• No cloud, no accounts — your data stays yours\n\n"
            "Built with Python, Tkinter, FastAPI"
        )

    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts."""
        shortcuts = (
            "Keyboard Shortcuts:\n\n"
            "F5           Refresh current tab\n"
            "Ctrl+S       Save (in Today tab)\n"
            "Ctrl+Q       Quit\n"
            "Tab          Navigate between fields\n"
            "Enter        Activate buttons\n\n"
            "Today Tab:\n"
            "  Click stars to rate (1-5)\n"
            "  Type notes, reflection answer\n"
            "  Click keywords to add/remove\n"
            "  Press Enter in keyword field to add\n\n"
            "History Tab:\n"
            "  Click calendar day to view details\n"
            "  Use filter dropdown to filter by keyword\n"
            "  Click Edit/Delete to modify entries\n\n"
            "Weekly Tab:\n"
            "  ◀ Prev / Next ▶ to navigate weeks\n"
            "  Type reflections, click Save\n\n"
            "Sync Tab:\n"
            "  Start Server to enable phone sync\n"
            "  Scan QR code with phone camera"
        )
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _center_window(self) -> None:
        """Center window on screen."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def set_server_ref(self, server_ref) -> None:
        """Update server reference (called after server starts)."""
        self.server_ref = server_ref
        if 'sync' in self.tabs:
            self.tabs['sync'].set_server_ref(server_ref)


def run_gui(server_ref=None) -> None:
    """Entry point to run the GUI application."""
    root = tk.Tk()
    app = DaylogApp(root, server_ref=server_ref)
    root.mainloop()


if __name__ == "__main__":
    run_gui()