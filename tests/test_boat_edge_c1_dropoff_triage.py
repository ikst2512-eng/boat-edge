import unittest
from scripts.boat_edge_c1_dropoff_triage import classify


def report_observed(rows, day="20261020"):
    return {"schema": "BOAT_EDGE_C1_OBSERVED_FIRST_GIT_ACCOUNTING_V1",
            "day_jst": day, "races": rows}


def report_actions(rows, day="20261020"):
    return {"schema": "BOAT_EDGE_C1_MISSING_FREEZE_ACTIONS_WINDOW_V1",
            "day_jst": day, "races": rows}


class C1DropoffTriageTests(unittest.TestCase):
    def test_no_denominator_inferred_from_proven_saves(self):
        value = classify(report_observed([
            {"race_key": "20261020-01-01", "status": "PROVEN_FIRST_GIT_BEFORE_DEADLINE"},
            {"race_key": "20261020-01-02", "status": "UNPROVEN_AFTER_DEADLINE"}
        ]), report_actions([]))
        self.assertEqual(value["union_rows"], 2)
        self.assertIsNone(value["formal_save_rate_percent"])
        self.assertIsNone(value["independently_source_eligible_denominator"])
        self.assertFalse(value["c1_passed"])
        self.assertEqual(value["stage_counts"]["FIRST_GIT_RECEIPT_PROVEN"], 1)

    def test_cancelled_actions_not_mislabeled_as_proven_save_failure(self):
        value = classify(report_observed([]), report_actions([
            {"race_key": "20261020-01-03",
             "run_history_complete_for_window": True,
             "classification": "V229_ONLY_SKIPPED_OR_CANCELLED_EXECUTION_UNVERIFIED"}
        ]))
        row = value["races"][0]
        self.assertEqual(row["stage"], "V229_EXECUTION_UNVERIFIED")
        self.assertFalse(row["first_git_save_failure_proven"])
        self.assertFalse(row["historic_source_eligibility_proven"])

    def test_duplicate_observed_race_rejected(self):
        row = {"race_key": "20261020-01-01", "status": "UNPROVEN_AFTER_DEADLINE"}
        with self.assertRaisesRegex(ValueError, "OBSERVED_DUPLICATE_RACE_KEY"):
            classify(report_observed([row, row]), report_actions([]))

    def test_duplicate_actions_race_rejected(self):
        row = {"race_key": "20261020-01-01", "classification": "UNKNOWN"}
        with self.assertRaisesRegex(ValueError, "ACTIONS_DUPLICATE_RACE_KEY"):
            classify(report_observed([]), report_actions([row, row]))

    def test_historical_catalog_only_race_is_not_silently_dropped(self):
        catalog = {"date": "2026-10-20", "venues": [
            {"races": [{"race_key": "20261020-03-12"}]}]}
        result = classify(report_observed([]), report_actions([]), catalog)
        self.assertEqual(result["catalog_only_races"], 1)
        self.assertEqual(result["races"][0]["stage"], "CATALOG_RACE_WITHOUT_AUDIT_EVIDENCE")
        self.assertIsNone(result["formal_save_rate_percent"])

    def test_catalog_wrong_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "CATALOG_INVALID"):
            classify(report_observed([]), report_actions([]),
                     {"date": "2026-10-21", "venues": []})

    def test_catalog_duplicate_rejected(self):
        catalog = {"date": "20261020", "venues": [
            {"races": [{"race_key": "20261020-03-12"},
                       {"race_key": "20261020-03-12"}]}]}
        with self.assertRaisesRegex(ValueError, "CATALOG_RACE_KEY_INVALID_OR_DUPLICATE"):
            classify(report_observed([]), report_actions([]), catalog)

    def test_v215_observation_does_not_prove_a_save(self):
        history = {"schema": "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1",
                   "day_jst": "20261020",
                   "observations": {"20261020-01-02": {
                       "reason": "verified_shadow_ready", "source_gaps": []}}}
        result = classify(report_observed([
            {"race_key": "20261020-01-02", "status": "UNPROVEN_AFTER_DEADLINE"}
        ]), report_actions([]), history=history)
        self.assertEqual(result["v215_final_reasons"]["verified_shadow_ready"], 1)
        self.assertTrue(result["races"][0]["v215_reason_not_proof_of_git_save"])
        self.assertFalse(result["races"][0]["first_git_save_failure_proven"])
        self.assertIsNone(result["formal_save_rate_percent"])

    def test_v215_wrong_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "V215_HISTORY_INVALID"):
            classify(report_observed([]), report_actions([]), history={
                "schema": "BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1",
                "day_jst": "20261021", "observations": {}})

    def test_day_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "DAY_MISMATCH"):
            classify(report_observed([]), report_actions([], "20261021"))


if __name__ == "__main__":
    unittest.main()
