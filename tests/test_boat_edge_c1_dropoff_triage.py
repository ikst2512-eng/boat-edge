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

    def test_day_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "DAY_MISMATCH"):
            classify(report_observed([]), report_actions([], "20261021"))


if __name__ == "__main__":
    unittest.main()
