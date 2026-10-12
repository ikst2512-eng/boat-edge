"""V324 all 11 independent readiness gates, never model promotion."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v324_research_gate import REQUIREMENTS, evaluate


class V324EvidenceGate(unittest.TestCase):
    def test_every_missing_gate_is_reported(self):
        all_false = {key: False for key in REQUIREMENTS}
        result = evaluate(all_false)
        self.assertEqual(result["missing"], list(REQUIREMENTS))
        self.assertFalse(result["ready_for_independent_review"])
        self.assertFalse(result["model_promotion_authorized"])
        self.assertFalse(result["result_access_performed"])
        self.assertFalse(result["formal_fresh_access_performed"])

    def test_all_declared_true_is_only_ready_for_review(self):
        all_true = {key: True for key in REQUIREMENTS}
        result = evaluate(all_true)
        self.assertTrue(result["ready_for_independent_review"])
        self.assertEqual(result["missing"], [])
        self.assertFalse(result["source_authenticated_by_this_tool"])
        self.assertFalse(result["model_accuracy_evaluated"])
        self.assertFalse(result["wagers_authorized"])

    def test_bad_types_and_missing_keys_refused(self):
        with self.assertRaises(ValueError):
            evaluate({"baseline_predeadline": True})
        with self.assertRaises(ValueError):
            evaluate({key: (1 if key == "same_race" else True) for key in REQUIREMENTS})
        with self.assertRaises(ValueError):
            evaluate({**{key: True for key in REQUIREMENTS}, "results": True})


if __name__ == "__main__":
    unittest.main()
