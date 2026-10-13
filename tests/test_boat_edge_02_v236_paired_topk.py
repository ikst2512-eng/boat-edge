"""Unit tests for site-only paired TopK evaluation; no formal Fresh access."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/boat_edge_02_v236_paired_topk_readonly.py"
spec = importlib.util.spec_from_file_location("paired_topk", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PairedTopKTests(unittest.TestCase):
    def test_miss_cause(self):
        tickets = ["1-2-3", "1-2-4", "2-1-3"]
        self.assertEqual(mod.cause(tickets, "1-2-3"), "hit")
        self.assertEqual(mod.cause(tickets, "4-2-3"), "head_absent")
        self.assertEqual(mod.cause(tickets, "1-3-4"), "second_absent_given_head")
        self.assertEqual(mod.cause(tickets, "1-2-5"), "third_absent_given_head_second")

    def test_exploratory_head_diversification_keeps_unique_original_tickets(self):
        ranked = ["1-2-3", "1-2-4", "1-3-2", "1-3-4",
                  "2-1-3", "3-1-2", "4-1-2", "2-3-1", "5-1-2", "6-1-2"]
        for k, keep in ((3, 2), (5, 3)):
            changed = mod.rank_head_diversified(ranked, k, keep)
            self.assertEqual(len(changed), k)
            self.assertEqual(len(set(changed)), k)
            self.assertEqual(changed[:keep], ranked[:keep])
            self.assertTrue(set(changed).issubset(set(ranked)))
            self.assertNotEqual(changed, ranked[:k])

    def test_empty_site_cohort_never_claims_proven_accuracy(self):
        with tempfile.TemporaryDirectory() as d:
            result = mod.evaluate(Path(d))
        self.assertEqual(result["races"], 0)
        self.assertIs(result["promotion_authorized"], False)
        self.assertIs(result["production_model_changed"], False)
        self.assertIs(result["post_hoc_exploration_not_predeadline_evidence"]["promotion_authorized"], False)


if __name__ == "__main__":
    unittest.main()
