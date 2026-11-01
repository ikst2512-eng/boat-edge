import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "wake", Path(__file__).resolve().parents[1] /
    "scripts" / "fresh_nov01_source_wake_audit.py")
wake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wake)

class SourceWakeAuditTests(unittest.TestCase):
    def test_window_classification_and_event_types(self):
        def get_json(url, token):
            self.assertIn("created=2026-11-01..2026-11-01", url)
            return {"workflow_runs": [
                {"id": 1, "created_at": "2026-11-01T01:39:00Z",
                 "event": "schedule", "conclusion": "success"},
                {"id": 2, "created_at": "2026-11-01T01:40:00Z",
                 "event": "schedule", "conclusion": "failure"},
                {"id": 3, "created_at": "2026-11-01T06:20:00Z",
                 "event": "workflow_dispatch", "conclusion": "cancelled"},
                {"id": 4, "created_at": "2026-11-01T06:21:00Z",
                 "event": "schedule", "conclusion": "success"}]}
        report = wake.audit("owner/repo", "test", get_json)
        self.assertTrue(report["complete"])
        self.assertFalse(report["results_accessed"])
        for entry in report["workflows"].values():
            self.assertEqual([x["id"] for x in entry["runs"]], [2, 3])
            self.assertEqual(entry["scheduled_created"], 1)
            self.assertEqual(entry["failed"], 1)
            self.assertEqual(entry["cancelled"], 1)

    def test_truncated_pagination_never_complete(self):
        def get_json(url, token):
            return {"workflow_runs": [
                {"id": i, "created_at": "2026-11-01T02:00:00Z",
                 "event": "schedule"} for i in range(100)]}
        self.assertFalse(wake.audit("owner/repo", "test", get_json,
                                    max_pages=1)["complete"])

    def test_missing_credentials_and_malformed_response_fail_closed(self):
        with self.assertRaises(ValueError):
            wake.audit("owner/repo", "", lambda *x: {})
        with self.assertRaises(ValueError):
            wake.audit("owner/repo", "test", lambda *x: {"no_runs": []})

if __name__ == "__main__":
    unittest.main()
