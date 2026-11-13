import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_paired120_significance import exact_mcnemar, paired_significance


class PairedSignificance(unittest.TestCase):
    def test_exact_binomial(self):
        self.assertEqual(exact_mcnemar(0, 0), 1)
        self.assertAlmostEqual(exact_mcnemar(5, 0), 0.0625)
        self.assertAlmostEqual(exact_mcnemar(2, 2), 1)
        self.assertTrue(0 <= exact_mcnemar(1000, 300) <= 1)

    def test_paired_direction(self):
        tickets = ["1-2-3", "2-1-3", "3-1-2"]
        a = [{"race_key": "x", "actual_trifecta": "1-2-3",
              "ranked_120": [{"boat_combo": t} for t in tickets]}]
        b = [{"race_key": "x", "actual_trifecta": "1-2-3",
              "ranked_120": [{"boat_combo": t} for t in tickets[::-1]]}]
        out = paired_significance(a, b)["paired_topk"]["1"]
        self.assertEqual(out["baseline_only_hits"], 1)
        self.assertEqual(out["candidate_only_hits"], 0)
        self.assertEqual(out["difference"], -1)

    def test_unmatched_races_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXACT_SAME"):
            paired_significance([{"race_key": "a", "ranked_120": [{"boat_combo": "1-2-3"}], "actual_trifecta": "1-2-3"}], [])
