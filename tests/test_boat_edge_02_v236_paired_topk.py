"""Unit tests for site-only paired TopK evaluation; no formal Fresh access."""
import importlib.util
import json
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

    @staticmethod
    def _write_formal(root, guards=None, cohort=None):
        p = root / "data/formal_status.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "guards": guards if guards is not None else {
                "results_seen": False, "unlock": False,
                "scoring": False, "RESULT_UNLOCK_TOKEN": None
            },
            "formalFirst100": cohort if cohort is not None else {"races": 0}
        }), encoding="utf-8")

    def test_empty_site_cohort_never_claims_proven_accuracy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._write_formal(root)
            result = mod.evaluate(root)
        self.assertEqual(result["races"], 0)
        self.assertIs(result["promotion_authorized"], False)
        self.assertIs(result["production_model_changed"], False)
        self.assertIs(result["post_hoc_exploration_not_predeadline_evidence"]["promotion_authorized"], False)

    def test_formal_gate_rejects_missing_active_and_unknown_before_site_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaisesRegex(RuntimeError, "FORMAL_GATE"):
                mod.evaluate(root)
            blocked = [
                ({"results_seen": True, "unlock": False, "scoring": False, "RESULT_UNLOCK_TOKEN": None}, {"races": 0}),
                ({"results_seen": False, "unlock": False, "scoring": False, "RESULT_UNLOCK_TOKEN": None}, {"races": 1}),
                ({"results_seen": False, "unlock": False, "scoring": False}, {"races": 0}),
                ({"results_seen": False, "unlock": False, "scoring": False, "RESULT_UNLOCK_TOKEN": None}, {}),
                ({"results_seen": False, "unlock": False, "scoring": False, "RESULT_UNLOCK_TOKEN": None}, {"races": False}),
            ]
            for guards, cohort in blocked:
                with self.subTest(guards=guards, cohort=cohort):
                    self._write_formal(root, guards, cohort)
                    with self.assertRaisesRegex(RuntimeError, "FORMAL_GATE"):
                        mod.evaluate(root)
            # Only a definitely closed and empty cohort may proceed.
            self._write_formal(root)
            self.assertEqual(mod.evaluate(root)["races"], 0)

    def test_exact_paired_uncertainty_on_declared_comparators(self):
        self.assertIsNone(mod.paired_exact_p(0, 0))
        self.assertEqual(mod.paired_exact_p(2, 1), 1.0)
        self.assertEqual(mod.paired_exact_p(5, 0), 0.0625)
        self.assertEqual(mod.paired_exact_p(6, 0), 0.03125)


if __name__ == "__main__":
    unittest.main()
