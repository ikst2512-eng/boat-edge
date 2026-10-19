import unittest
from scripts.boat_edge_v352_action_pressure import analyze


class Gate1CEventPressure(unittest.TestCase):
    def test_fanout_count_is_metadata_not_duplicate_proof(self):
        raw = {
            "schema": "BOAT_EDGE_01_V352_EVENT_PRESSURE_METADATA_V1",
            "event_filter": "all", "runs": [
                {"run_id": 1, "workflow_name": "BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps",
                 "created_at": "2026-10-19T07:44:04Z",
                 "event": "workflow_run", "conclusion": "skipped"},
                {"run_id": 2, "workflow_name": "BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring",
                 "created_at": "2026-10-19T07:44:12Z",
                 "event": "workflow_run", "conclusion": "cancelled"},
                {"run_id": 3, "workflow_name": "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit",
                 "created_at": "2026-10-19T07:44:22Z",
                 "event": "workflow_run", "conclusion": "success"},
                {"run_id": 4, "workflow_name": "pages build and deployment",
                 "created_at": "2026-10-19T07:44:35Z",
                 "event": "dynamic", "conclusion": "cancelled"},
                {"run_id": 5, "workflow_name": "BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps",
                 "created_at": "2026-10-19T07:50:00Z",
                 "event": "schedule", "conclusion": "success"},
            ]
        }
        report = analyze(raw)
        self.assertEqual(report["run_records"], 5)
        self.assertEqual(report["windows_observed"], 2)
        busiest = report["busiest_five_minute_windows"][0]
        self.assertEqual(busiest["window_start_utc"], "2026-10-19T07:40:00Z")
        self.assertEqual(busiest["run_count"], 4)
        self.assertEqual(busiest["workflow_run_events"], 3)
        self.assertEqual(busiest["capture_owner_skipped"], 1)
        self.assertEqual(busiest["capture_owner_cancelled"], 1)
        self.assertEqual(busiest["cancelled"], 2)
        self.assertFalse(report["run_or_job_duplicate_proven"])
        self.assertFalse(report["capture_source_eligibility_proven"])
        self.assertFalse(report["workflow_disable_authorized"])
        self.assertEqual(report, analyze(raw))

    def test_wrong_schema_and_partial_timestamp_do_not_invent_completeness(self):
        with self.assertRaises(ValueError):
            analyze({"schema": "BOAT_EDGE_01_V348_SCHEDULED_ACTIONS_RUN_METADATA_V1",
                     "event_filter": "schedule", "runs": []})
        report = analyze({"schema": "BOAT_EDGE_01_V352_EVENT_PRESSURE_METADATA_V1",
                          "event_filter": "all",
                          "runs": [{"run_id": 5, "created_at": None}]})
        self.assertEqual(report["unknown_or_missing_created_at"], 1)
        self.assertTrue(report["pagination_may_be_incomplete"])
        self.assertEqual(report["windows_observed"], 0)


if __name__ == "__main__":
    unittest.main()
