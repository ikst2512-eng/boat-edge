"""Offline regression for exact GitHub Actions starts in missed C-1 windows."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from scripts.boat_edge_01_gate1c_actions_window_audit import audit, deadline_for, window_runs

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 19, 21, 15, tzinfo=JST)
DAY = "20261019"


def entry(run_id, name, created, conclusion="success", event="schedule"):
    return {"id": run_id, "name": name, "created_at": created, "event": event,
            "status": "completed", "conclusion": conclusion}


class C1MissedWindowAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        observations = {
            "20261019-18-07": {"deadline": "11:22", "source_gaps_seen": [],
                                  "reasons_seen": ["snapshot_missing"]},
            "20261019-12-05": {"deadline": "17:01", "source_gaps_seen": [],
                                  "reasons_seen": ["snapshot_missing"]},
            "20261019-01-12": {"deadline": "20:45", "source_gaps_seen": ["beforeinfo_not_ok"],
                                  "reasons_seen": ["snapshot_missing"]},
        }
        p = self.root / "data/site_paper_sim/readiness_history_v215" / (DAY + ".json")
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({
            "schema": "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1",
            "day_jst": DAY, "observations": observations,
        }), encoding="utf-8")
        # Existing snapshot means no missing-freeze audit regardless of earlier
        # snapshot_missing observation.
        s = self.root / "data/site_prediction_snapshots/20261019-01-12.json"
        s.parent.mkdir(parents=True)
        s.write_text("{}", encoding="utf-8")

    def test_no_run_starts_does_not_falsely_prove_source_ready(self):
        def fetch(start, end, page):
            self.assertEqual(page, 1)
            self.assertEqual((end - start).total_seconds(), 8 * 60)
            return {"total_count": 0, "workflow_runs": []}
        data = audit(self.root, DAY, NOW, fetch)
        self.assertEqual(data["observed_matured_missing_snapshots"], 2)
        self.assertEqual(data["observed_matured_with_existing_snapshot"], 1)
        self.assertEqual(data["complete_window_queries"], 2)
        self.assertEqual(data["incomplete_window_queries"], 0)
        self.assertEqual(set(x["race_key"] for x in data["races"]),
                         {"20261019-18-07", "20261019-12-05"})
        for row in data["races"]:
            self.assertEqual(row["classification"], "NO_CAPTURE_OWNER_START_IN_WINDOW")
            self.assertFalse(row["independent_source_eligibility_proven"])
            self.assertFalse(row["no_prior_active_run_proven"])
            self.assertTrue(row["first_git_save_absent_in_current_tree"])
        self.assertIsNone(data["independently_source_eligible_denominator"])
        self.assertIsNone(data["eligible_save_rate_percent"])
        self.assertFalse(data["automated_recovery_or_formal_unlock_authorized"])

    def test_v229_starts_and_v216_starts_never_confused_with_successful_freeze(self):
        def fetch(start, end, page):
            key = "18" if start.hour < 4 else "12"
            if key == "18":
                return {"total_count": 1, "workflow_runs": [entry(11,
                    "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit",
                    "2026-10-19T02:17:00Z", "skipped", "workflow_run")]}
            return {"total_count": 1, "workflow_runs": [entry(12,
                "BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps",
                "2026-10-19T07:54:00Z")]}
        rows = {x["race_key"]: x for x in audit(self.root, DAY, NOW, fetch)["races"]}
        self.assertEqual(rows["20261019-18-07"]["classification"],
                         "V229_ALL_RUNS_SKIPPED_NO_EXECUTED_FREEZE_PROVEN")
        self.assertEqual(rows["20261019-12-05"]["classification"],
                         "V216_START_WITHOUT_V229_START")
        self.assertEqual(rows["20261019-18-07"]["capture_owner_starts"][0]["conclusion"],
                         "skipped")

    def test_cancelled_v229_does_not_prove_writer_executed(self):
        name = "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit"
        def fetch(start, end, page):
            return {"total_count": 1, "workflow_runs": [
                entry(61, name, "2026-10-19T02:17:00Z", "cancelled"),
            ]} if start.hour == 2 else {"total_count": 0, "workflow_runs": []}
        rows = {r["race_key"]: r for r in audit(
            self.root, DAY, NOW, fetch)["races"]}
        row = rows["20261019-18-07"]
        self.assertEqual(row["classification"],
                         "V229_ONLY_SKIPPED_OR_CANCELLED_EXECUTION_UNVERIFIED")
        self.assertFalse(row["v229_execution_proven_by_run_metadata"])

    def test_completed_v229_start_still_does_not_prove_snapshot(self):
        name = "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit"
        def fetch(start, end, page):
            return {"total_count": 1, "workflow_runs": [
                entry(62, name, "2026-10-19T02:17:00Z", "success"),
            ]} if start.hour == 2 else {"total_count": 0, "workflow_runs": []}
        rows = {r["race_key"]: r for r in audit(
            self.root, DAY, NOW, fetch)["races"]}
        row = rows["20261019-18-07"]
        self.assertEqual(row["classification"],
                         "V229_START_RECORDED_SNAPSHOT_MISSING")
        self.assertFalse(row["v229_execution_proven_by_run_metadata"])

    def test_v125_only_independent_schedule_is_a_possible_v229_wake(self):
        v125 = "BOAT EDGE V125 Revision Safe FINAL15M Audit"
        def fetch(start, end, page):
            if start.hour == 2:
                return {"total_count": 2, "workflow_runs": [
                    entry(31, v125, "2026-10-19T02:17:00Z", "success", "schedule"),
                    entry(32, v125, "2026-10-19T02:18:00Z", "success", "workflow_run"),
                ]}
            return {"total_count": 1, "workflow_runs": [
                entry(33, v125, "2026-10-19T07:54:00Z", "success", "workflow_run"),
            ]}
        rows = {r["race_key"]: r for r in audit(
            self.root, DAY, NOW, fetch)["races"]}
        candidate = rows["20261019-18-07"]
        self.assertEqual(candidate["classification"],
                         "V125_SCHEDULE_STARTED_WITHOUT_V229_START")
        self.assertEqual(candidate["capture_owner_starts"][0]["owner"],
                         "v125_schedule")
        self.assertEqual(len(candidate["capture_owner_starts"]), 1)
        self.assertEqual(candidate["v125_completion_only_audit_starts_ignored"], 1)
        self.assertFalse(candidate["independent_source_eligibility_proven"])
        self.assertFalse(candidate["no_prior_active_run_proven"])
        passive = rows["20261019-12-05"]
        self.assertEqual(passive["classification"],
                         "NO_CAPTURE_OWNER_START_IN_WINDOW")
        self.assertEqual(passive["capture_owner_starts"], [])
        self.assertEqual(passive["v125_completion_only_audit_starts_ignored"], 1)
        self.assertEqual(passive["all_actions_starts_in_window"], 1)

    def test_status_api_failure_and_truncation_cannot_be_interpreted_as_zero(self):
        def broken(start, end, page):
            raise OSError("rate limited")
        r = audit(self.root, DAY, NOW, broken)
        self.assertEqual(r["incomplete_window_queries"], 2)
        self.assertTrue(all(x["classification"] == "RUN_HISTORY_UNVERIFIED"
                            for x in r["races"]))
        now_utc = NOW.astimezone(timezone.utc)
        many = [entry(i, "noise", "2026-10-19T12:00:00Z")
                for i in range(100)]
        # Use a synthetic window containing the returned timestamps.
        start, end = now_utc - timedelta(minutes=20), now_utc
        self.assertEqual(len(many), 100)
        records, complete, error = window_runs(
            lambda start, end, page: {"total_count": 100, "workflow_runs": many}, start, end, max_pages=1)
        self.assertTrue(complete)
        self.assertIsNone(error)
        self.assertEqual(len(records), 100)

    def test_total_count_missing_or_incomplete_is_unverified(self):
        start = datetime(2026, 10, 19, 2, 12, tzinfo=timezone.utc)
        end = start + timedelta(minutes=8)
        records, complete, error = window_runs(
            lambda a, b, page: {"total_count": 2, "workflow_runs": [
                entry(99, "noise", "2026-10-19T02:17:00Z")]}, start, end)
        self.assertEqual((records, complete, error), ([], False, "RUN_TOTAL_COUNT_MISMATCH"))
        records, complete, error = window_runs(
            lambda a, b, page: {"workflow_runs": []}, start, end)
        self.assertFalse(complete)
        self.assertIn("RUN_TOTAL_COUNT_UNVERIFIED", error)

    def test_excess_short_page_fails_closed(self):
        start = datetime(2026, 10, 19, 2, 12, tzinfo=timezone.utc)
        end = start + timedelta(minutes=8)
        runs, complete, error = window_runs(
            lambda a, b, page: {"total_count": 0, "workflow_runs": [
                entry(1001, "noise", "2026-10-19T02:17:00Z")]}, start, end)
        self.assertEqual((runs, complete, error), ([], False, "RUN_TOTAL_COUNT_MISMATCH"))

    def test_changed_total_between_pages_fails_closed(self):
        start = datetime(2026, 10, 19, 2, 12, tzinfo=timezone.utc)
        end = start + timedelta(minutes=8)
        first = [entry(i, "noise", "2026-10-19T02:17:00Z") for i in range(100)]
        def fetch(a, b, page):
            if page == 1:
                return {"total_count": 101, "workflow_runs": first}
            return {"total_count": 102, "workflow_runs": [
                entry(100, "noise", "2026-10-19T02:18:00Z")]}
        runs, complete, error = window_runs(fetch, start, end)
        self.assertFalse(complete)
        self.assertIn("RUN_TOTAL_COUNT_CHANGED_BETWEEN_PAGES", error)

    def test_prospective_deadline_and_untrusted_history_fail_closed(self):
        early = datetime(2026, 10, 19, 10, 30, tzinfo=JST)
        d = audit(self.root, DAY, early, lambda s, e, p: {"total_count": 0, "workflow_runs": []})
        self.assertEqual(d["observed_matured_missing_snapshots"], 0)
        self.assertIsNone(deadline_for("20261019-18-07", "99:99"))
        with self.assertRaises(ValueError):
            audit(self.root, "20261018", NOW, lambda s, e, p: {"total_count": 0, "workflow_runs": []})
        with self.assertRaises(ValueError):
            audit(self.root, "../bad", NOW, lambda s, e, p: {"total_count": 0, "workflow_runs": []})


if __name__ == "__main__":
    unittest.main()
