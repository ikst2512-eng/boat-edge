import unittest
from scripts.boat_edge_v348_actions_run_export import export_runs


class V348RunExport(unittest.TestCase):
    def test_schedule_filter_and_no_false_changed_paths(self):
        calls = []
        def fetch(page):
            calls.append(page)
            return {"workflow_runs": [
                {"id": 12, "event": "schedule", "name": "writer", "head_sha": "abc"},
                {"id": 13, "event": "pull_request", "name": "CI"},
            ]}
        report = export_runs(fetch)
        self.assertEqual(calls, [1])
        self.assertEqual(report["run_count"], 1)
        self.assertIsNone(report["runs"][0]["changed_paths"])
        self.assertFalse(report["runs"][0]["changed_paths_proven"])
        self.assertFalse(report["workflow_disable_authorized"])

    def test_all_events_preserves_skipped_cancelled_without_inventing_jobs(self):
        def fetch(page):
            return {"workflow_runs": [
                {"id": 10, "event": "workflow_run", "conclusion": "skipped",
                 "created_at": "2026-10-19T07:44:15Z", "name": "V216"},
                {"id": 11, "event": "workflow_run", "conclusion": "cancelled",
                 "created_at": "2026-10-19T07:44:22Z", "name": "V235"},
                {"id": 12, "event": "schedule", "conclusion": "success",
                 "created_at": "2026-10-19T07:44:25Z", "name": "V229"},
            ]}
        all_events = export_runs(fetch, event_filter="all")
        self.assertEqual(all_events["run_count"], 3)
        self.assertEqual(all_events["event_filter"], "all")
        self.assertEqual(all_events["schema"], "BOAT_EDGE_01_V352_EVENT_PRESSURE_METADATA_V1")
        self.assertFalse(any(r["runtime_duplicate_proven"] for r in all_events["runs"]))
        self.assertEqual(export_runs(fetch, event_filter="workflow_run")["run_count"], 2)
        self.assertEqual(export_runs(fetch)["run_count"], 1)
        with self.assertRaises(ValueError):
            export_runs(fetch, event_filter="unspecified")

    def test_pagination_and_bounds(self):
        pages = []
        def fetch(page):
            pages.append(page)
            return {"workflow_runs": [{"id": i, "event": "schedule"} for i in range(100)]}
        report = export_runs(fetch, max_pages=2)
        self.assertEqual(pages, [1, 2])
        self.assertEqual(report["run_count"], 200)
        with self.assertRaises(ValueError):
            export_runs(fetch, max_pages=21)


if __name__ == "__main__":
    unittest.main()
