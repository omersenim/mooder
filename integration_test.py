"""Headless-ish integration test: mount MooderApp, switch through every tab, exit."""
import asyncio
import flet as ft
from flet_gui.app import MooderApp


async def main(page: ft.Page):
    try:
        app = MooderApp(page)
        for i in range(5):
            app.select_tab(i)
            await asyncio.sleep(0.4)
            print("tab", i, "OK")
        app.tabs["sync"]._start_server()
        await asyncio.sleep(0.3)
        print("sync start OK, running =", app.tabs["sync"].server_running)
        app.tabs["sync"]._stop_server()
        print("ALL OK")
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        await page.window.destroy()


ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
