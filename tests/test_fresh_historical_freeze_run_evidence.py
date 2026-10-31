import importlib.util
import unittest
from datetime import timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "audit", Path(__file__).resolve().parents[1] / "scripts" /
    "fresh_historical_freeze_run_evidence.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class HistoricalFreezeRunEvidenceTests(unittest.TestCase):
    def test_precise_windows(self):
        self.assertEqual(audit.window("2026-10-31", "11:01")[0].strftime("%H:%M"), "10:51")
        self.assertEqual(audit.window("2026-10-31", "19:14")[1].strftime("%H:%M"), "19:12")

    def test_utc_cron_opportunities_not_dispatch_proof(self):
        for key, expected in (
            ("20261031-23-06", {"v229": ["10:51", "10:56"], "v216": ["10:54", "10:59"]}),
            ("20261031-24-09", {"v229": ["19:06", "19:11"], "v216": ["19:04", "19:09"]}),
        ):
            start, end = audit.window(*audit.RACES[key])
            for workflow in ("v229", "v216"):
                slots = audit.configured_schedule_slots(start, end, workflow)
                self.assertEqual([v[11:16] for v in slots], expected[workflow])

    def test_actual_start_not_creation_or_completion(self):
        def fake(url, token):
            self.assertIn("created=", url)
            return {"workflow_runs": [
                {"id": 1, "run_started_at": "2026-10-31T01:53:00Z",
                 "created_at": "2026-10-31T01:40:00Z",
                 "status": "completed", "conclusion": "success"},
                {"id": 2, "run_started_at": "2026-10-31T01:49:00Z",
                 "status": "completed"},
                {"id": 3, "run_started_at": "2026-10-31T02:00:00Z",
                 "status": "completed"}]}
        out = audit.collect("owner/repo", "test-token", "20261031-23-06", fake)
        self.assertEqual(
            [x["id"] for x in out["workflows"]["v229"]["runs_started_in_window"]], [1])
        self.assertTrue(out["evidence_complete"])
        self.assertFalse(out["workflows"]["v229"]["no_run_proven"])
        self.assertFalse(out["formal_unlock_authorized"])

    def test_cross_window_uses_updated_at_only_as_candidate(self):
        def fake(url, token):
            return {"workflow_runs": [
                {"id": 11, "run_started_at": "2026-10-31T01:40:00Z",
                 "updated_at": "2026-10-31T01:55:00Z"},
                {"id": 12, "run_started_at": "2026-10-31T01:40:00Z",
                 "updated_at": "2026-10-31T01:45:00Z"},
                {"id": 13, "run_started_at": "2026-10-31T01:40:00Z"}]}
        out = audit.collect("owner/repo", "token", "20261031-23-06", fake)
        v = out["workflows"]["v229"]
        self.assertEqual([x["id"] for x in v["possible_overlaps_by_updated_at"]], [11])
        self.assertEqual([x["id"] for x in v["uncertain_without_updated_at"]], [13])
        self.assertFalse(v["overlap_is_confirmed_by_job_times"])

    def test_nearby_run_starts_are_not_misclassified_as_window_starts(self):
        def fake(url, token):
            return {"workflow_runs": [
                {"id": 21, "run_started_at": "2026-10-31T01:45:00Z",
                 "updated_at": "2026-10-31T01:47:00Z", "event": "schedule"},
                {"id": 22, "run_started_at": "2026-10-31T02:06:00Z",
                 "updated_at": "2026-10-31T02:08:00Z", "event": "schedule"}]}
        out = audit.collect("owner/repo", "token", "20261031-23-06", fake)
        v = out["workflows"]["v229"]
        self.assertEqual([x["id"] for x in v["nearby_starts_plus_minus_20m"]], [21, 22])
        self.assertEqual(v["runs_started_in_window"], [])

    def test_truncated_page_fails_closed(self):
        def fake(url, token):
            return {"workflow_runs": [{"id": i} for i in range(100)]}
        out = audit.collect("owner/repo", "token", "20261031-24-09", fake, pages=1)
        self.assertFalse(out["evidence_complete"])
        self.assertFalse(out["workflows"]["v216"]["pagination_exhausted"])

    def test_missing_credentials_and_bad_key(self):
        with self.assertRaises(ValueError):
            audit.collect("owner/repo", "", "20261031-23-06", lambda *x: {})
        with self.assertRaises(ValueError):
            audit.collect("owner/repo", "token", "20261031-23-07", lambda *x: {})

if __name__ == "__main__":
    unittest.main()
