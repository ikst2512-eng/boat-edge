"""V319 paired shadow/baseline test, no outcomes or scoring."""
from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v319_pre_result_pair import compare

TICKETS = [
    "1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
    "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3",
]


def fixture():
    key = "20261013-22-12"
    shadow = {
        "model_id": "BOAT_EDGE_V318_SHADOW_FREEZE_RESEARCH_ONLY",
        "race_key": key,
        "deadline_jst": "2026-10-13T16:40:00+09:00",
        "frozen_at_jst": "2026-10-13T16:20:00+09:00",
        "candidate_model_id": "V312_TEST",
        "research_top10_by_mode": {
            "national_only": TICKETS.copy(),
            "national_motor": TICKETS[1:] + ["2-1-3"],
        },
        "results_read": False, "formal_fresh_read": False,
    }
    baseline = {
        "model_id": "SITE_BASELINE_SYNTHETIC",
        "race_key": key,
        "frozen_at_jst": "2026-10-13T16:21:00+09:00",
        "entry_basis": "BOAT_NUMBER",
        "top10_boat": TICKETS.copy(),
        "results_read": False, "formal_fresh_read": False,
    }
    return shadow, baseline


class V319PairedPreResult(unittest.TestCase):
    def test_same_race_overlap_does_not_claim_improvement(self):
        shadow, baseline = fixture()
        result = compare(shadow, baseline)
        self.assertEqual(result["overlap_by_mode"]["national_only"]["overlap_count"], 10)
        self.assertEqual(result["overlap_by_mode"]["national_motor"]["overlap_count"], 9)
        self.assertEqual(result["overlap_by_mode"]["national_motor"]["research_only_tickets"], ["2-1-3"])
        self.assertFalse(result["prediction_accuracy_evaluated"])
        self.assertFalse(result["performance_improvement_proven"])
        self.assertFalse(result["model_promotion_authorized"])
        self.assertFalse(result["results_read"])

    def test_late_baseline_or_shadow_rejected(self):
        shadow, baseline = fixture()
        baseline["frozen_at_jst"] = "2026-10-13T16:41:00+09:00"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)
        shadow, baseline = fixture()
        shadow["frozen_at_jst"] = "2026-10-13T16:40:00+09:00"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)

    def test_cross_race_wrong_basis_and_bad_tickets_rejected(self):
        shadow, baseline = fixture()
        baseline["race_key"] = "20261013-22-11"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)
        shadow, baseline = fixture()
        baseline["entry_basis"] = "COURSE"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)
        shadow, baseline = fixture()
        baseline["top10_boat"][0] = "1-1-2"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)
        shadow, baseline = fixture()
        shadow["research_top10_by_mode"]["national_only"][0] = "1-2-4"
        with self.assertRaises(ValueError):
            compare(shadow, baseline)

    def test_results_guard_required(self):
        shadow, baseline = fixture()
        shadow["results_read"] = True
        with self.assertRaises(ValueError):
            compare(shadow, baseline)
        shadow, baseline = fixture()
        baseline["formal_fresh_read"] = True
        with self.assertRaises(ValueError):
            compare(shadow, baseline)


if __name__ == "__main__":
    unittest.main()
