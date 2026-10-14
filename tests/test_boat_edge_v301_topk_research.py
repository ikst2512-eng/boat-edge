import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v301_paired_evidence import baseline_topk


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


if __name__ == "__main__":
    unittest.main()
