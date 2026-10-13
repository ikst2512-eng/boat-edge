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
