import unittest
from scripts.boat_edge_v349_schedule_run_overlap import analyze


class V349TemporalHints(unittest.TestCase):
    def test_same_start_never_proves_concurrency(self):
        data = {"schema": "BOAT_EDGE_01_V348_SCHEDULED_ACTIONS_RUN_METADATA_V1",
                "runs": [
                    {"run_id": 1, "event": "schedule", "workflow_name": "a",
                     "run_started_at": "2026-10-13T00:00:00Z", "updated_at": "2026-10-13T00:05:00Z"},
                    {"run_id": 2, "event": "schedule", "workflow_name": "b",
                     "run_started_at": "2026-10-13T00:00:00Z", "updated_at": "2026-10-13T00:10:00Z"},
                    {"run_id": 3, "event": "pull_request"}]}
        result = analyze(data)
        self.assertEqual(result["scheduled_run_records"], 2)
        self.assertEqual(len(result["same_start_candidate_pairs"]), 1)
        self.assertEqual(result["concurrent_runs_proven"], 0)
        self.assertEqual(result["duplicate_writes_proven"], 0)
        self.assertFalse(result["workflow_disable_authorized"])
        self.assertEqual(result, analyze(data))

    def test_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            analyze({"schema": "wrong", "runs": []})

    def test_missing_times_do_not_become_overlap(self):
        result = analyze({"schema": "BOAT_EDGE_01_V348_SCHEDULED_ACTIONS_RUN_METADATA_V1",
                          "runs": [{"run_id": 1, "event": "schedule"},
                                   {"run_id": 2, "event": "schedule"}]})
        self.assertEqual(result["same_start_candidate_pairs"], [])


if __name__ == "__main__":
    unittest.main()
