import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

spec=importlib.util.spec_from_file_location("gap", Path(__file__).resolve().parents[1]/"scripts/fresh_collector_run_gap_monitor.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class GapMonitorTests(unittest.TestCase):
    def test_missing_run_is_alert_not_formal(self):
        now=datetime(2026,10,26,6,0,tzinfo=timezone.utc)
        runs=[{"created_at":(now-timedelta(minutes=55)).isoformat()},
              {"created_at":(now-timedelta(minutes=4)).isoformat()}]
        out=mod.classify(runs,now)
        self.assertTrue(out["possible_schedule_gap"])
        self.assertTrue(out["no_scheduled_run_in_window"])
        self.assertTrue(out["scheduled_run_count_below_three_in_90m"])
        self.assertGreater(out["largest_run_start_gap_seconds"],1200)
    def test_normal_runs(self):
        now=datetime(2026,10,26,6,0,tzinfo=timezone.utc)
        runs=[{"created_at":(now-timedelta(minutes=i)).isoformat()} for i in [12,7,2]]
        self.assertFalse(mod.classify(runs,now)["possible_schedule_gap"])
        self.assertTrue(mod.classify(runs,now)["no_scheduled_run_in_window"])
    def test_schedule_event_is_distinguished_from_manual(self):
        now=datetime(2026,10,26,6,0,tzinfo=timezone.utc)
        runs=[{"created_at":(now-timedelta(minutes=5)).isoformat(), "event":"schedule"},
              {"created_at":(now-timedelta(minutes=2)).isoformat(), "event":"workflow_dispatch"}]
        out=mod.classify(runs,now)
        self.assertEqual(out["scheduled_runs_in_window"],1)
        self.assertTrue(out["scheduled_run_count_below_three_in_90m"])
        self.assertFalse(out["no_scheduled_run_in_window"])
if __name__=="__main__": unittest.main()
