import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v301_paired_evidence import baseline_topk, cross_study_ranked_topk, cross_study_ranked_topk_by_day, compare_10point_modes, EvidenceError


class BaselineTopKTests(unittest.TestCase):
    def test_rank_sensitive_top3_top5_top10(self):
        row = {"winning": "1-4-6", "baseline": [
            "1-2-3", "1-2-4", "1-4-2", "1-3-2",
            "1-4-6", "2-1-3", "2-3-1", "3-1-2", "3-2-1", "4-1-2"]}
        other = {"winning": "6-5-4", "baseline": row["baseline"]}
        r = baseline_topk([row, other])
        self.assertEqual([r[f"top{k}"]["hits"] for k in (3, 5, 10)], [0, 1, 1])
        self.assertEqual(r["top5"]["hit_rate"], 0.5)

    def test_topk_monotonic_on_ranked_frozen_tickets(self):
        rows = [
            {"winning": "1-2-3", "baseline": ["1-2-3", "1-3-2", "2-1-3"]},
            {"winning": "1-3-2", "baseline": ["1-2-3", "1-3-2", "2-1-3"]},
            {"winning": "2-1-3", "baseline": ["1-2-3", "1-3-2", "2-1-3"]},
        ]
        r = baseline_topk(rows)
        self.assertEqual([r[f"top{k}"]["hits"] for k in (3, 5, 10)], [3, 3, 3])
        self.assertTrue(r["top3"]["hits"] <= r["top5"]["hits"] <= r["top10"]["hits"])

    def test_empty_sample_is_not_perfect_accuracy(self):
        r = baseline_topk([])
        for k in (3, 5, 10):
            self.assertEqual(r[f"top{k}"]["races"], 0)
            self.assertEqual(r[f"top{k}"]["hits"], 0)
            self.assertIsNone(r[f"top{k}"]["hit_rate"])



class CrossStudyTopKTests(unittest.TestCase):
    def test_same_race_ranked_topk_changes_only_top10(self):
        baseline = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2",
                    "1-4-3", "2-1-3", "2-1-4", "2-3-1", "2-3-4"]
        candidate = baseline[:9] + ["1-4-6"]
        left = [{"key": "20261013-04-10", "winning": "1-4-6",
                 "baseline": baseline, "ranked_comparators": {"hit10": baseline}}]
        right = [{"key": "20261013-04-10", "winning": "1-4-6",
                  "baseline": baseline,
                  "ranked_comparators": {"third_tail10": candidate}}]
        result = cross_study_ranked_topk(left, right, "hit10", "third_tail10")
        self.assertEqual(result["top3"]["right_only_hits"], 0)
        self.assertEqual(result["top5"]["right_only_hits"], 0)
        self.assertEqual(result["top10"]["right_only_hits"], 1)
        self.assertEqual(result["top10"]["left_only_hits"], 0)
        self.assertEqual(result["top10"]["exact_mcnemar_two_sided_p"], 1.0)
        self.assertFalse(result["top10"]["improvement_proven"])

    def test_by_day_prevents_concealed_day_concentration(self):
        base = ["1-2-3", "1-2-4", "1-3-2", "1-3-4", "1-4-2",
                "1-4-3", "2-1-3", "2-1-4", "2-3-1", "2-3-4"]
        alt = base[:9] + ["1-4-6"]
        left = [{"key": "20261012-04-10", "day": "20261012",
                 "winning": "1-4-6", "baseline": base,
                 "ranked_comparators": {"hit10": base}},
                {"key": "20261013-04-10", "day": "20261013",
                 "winning": "2-3-4", "baseline": base,
                 "ranked_comparators": {"hit10": base}}]
        right = [{**row, "ranked_comparators": {"third_tail10": alt}} for row in left]
        out = cross_study_ranked_topk_by_day(left, right, "hit10", "third_tail10")
        self.assertEqual(out["20261012"]["top10"]["right_only_hits"], 1)
        self.assertEqual(out["20261013"]["top10"]["left_only_hits"], 1)
        self.assertFalse(out["20261012"]["top10"]["improvement_proven"])

    def test_cross_study_mismatched_race_rejected(self):
        left = [{"key": "20261013-04-10", "winning": "1-2-3"}]
        right = [{"key": "20261013-04-11", "winning": "1-2-3"}]
        with self.assertRaises(EvidenceError):
            cross_study_ranked_topk(left, right, "hit10", "hit10")

    def test_cross_study_unequal_length_rejected(self):
        with self.assertRaises(EvidenceError):
            cross_study_ranked_topk([{"key": "20261013-04-10"}], [], "hit10", "hit10")



class PairedTenIdentityTests(unittest.TestCase):
    def row(self):
        return {"key": "20261014-04-01", "day": "20261014",
                "winning": "1-2-3",
                "outcomes": {"hit10": True, "third_tail10": False},
                "modes": {"hit10": 10, "third_tail10": 10}}

    def test_same_race_ten_points_works_without_promotion(self):
        a, b = self.row(), self.row()
        out = compare_10point_modes([a], [b], "hit10", "third_tail10")
        self.assertEqual(out["races"], 1)
        self.assertEqual((out["left_hits"], out["right_hits"]), (1, 0))
        self.assertFalse(out["improvement_proven"])

    def test_mismatch_key_outcome_day_or_ticket_budget_rejected(self):
        for field, value, reason in (
                ("key", "20261014-04-02", "RACE_OR_OUTCOME"),
                ("winning", "1-3-2", "RACE_OR_OUTCOME"),
                ("day", "20261013", "RACE_OR_OUTCOME")):
            with self.subTest(field=field):
                a, b = self.row(), self.row()
                b[field] = value
                with self.assertRaisesRegex(EvidenceError, reason):
                    compare_10point_modes([a], [b], "hit10", "third_tail10")
        a, b = self.row(), self.row()
        b["modes"]["third_tail10"] = 9
        with self.assertRaisesRegex(EvidenceError, "EXACT_TEN"):
            compare_10point_modes([a], [b], "hit10", "third_tail10")

    def test_unequal_race_counts_rejected(self):
        with self.assertRaisesRegex(EvidenceError, "RACE_COUNT_MISMATCH"):
            compare_10point_modes([self.row()], [], "hit10", "hit10")


if __name__ == "__main__":
    unittest.main()
