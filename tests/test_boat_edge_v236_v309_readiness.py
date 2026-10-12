"""V309 synthetic-only readiness audit tests."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v309_readiness_audit import audit


def example(key="SYNTHETIC-01"):
    return {
        "race_key": key,
        "deadline_jst": "2026-10-13T12:00:00+09:00",
        "frozen_at_jst": "2026-10-13T11:50:00+09:00",
        "source_sha256": "a" * 64,
        "source_verified": True,
        "actual_course_by_boat": {str(i): i for i in range(1, 7)},
        "strength_by_boat": {str(i): 1 for i in range(1, 7)},
    }


class V309Audit(unittest.TestCase):
    def test_accept_reject_and_duplicate(self):
        good = example()
        bad = example("SYNTHETIC-02")
        bad["source_verified"] = False
        result = audit([good, bad, good])
        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(result["rejected_count"], 2)
        self.assertEqual(len(result["accepted"][0]["top10"]), 10)
        self.assertFalse(result["independent_source_authentication"])
        self.assertFalse(result["real_world_accuracy_evaluated"])
        self.assertFalse(result["production_eligible"])
        self.assertFalse(result["formal_results_read"])

    def test_empty_and_invalid(self):
        self.assertEqual(audit([])["accepted_count"], 0)
        with self.assertRaises(ValueError):
            audit({"race_key": "bad"})


if __name__ == "__main__":
    unittest.main()
