"""Smoke test: instantiate every Flet tab off-page."""
import traceback

from flet_gui.tabs.today_tab import TodayTab
from flet_gui.tabs.history_tab import HistoryTab
from flet_gui.tabs.weekly_tab import WeeklyTab
from flet_gui.tabs.stats_tab import StatsTab
from flet_gui.tabs.sync_tab import SyncTab

failed = 0
for cls in (TodayTab, HistoryTab, WeeklyTab, StatsTab, SyncTab):
    try:
        cls()
        print(f"OK   {cls.__name__}")
    except Exception:
        failed += 1
        print(f"FAIL {cls.__name__}")
        traceback.print_exc()
raise SystemExit(failed)
