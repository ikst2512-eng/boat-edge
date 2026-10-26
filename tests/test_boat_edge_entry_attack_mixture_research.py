"""Synthetic-only verification; does not establish real-race accuracy."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_entry_attack_mixture_research import ATTACKS, rank_scenarios


class EntryAttackMixture(unittest.TestCase):
    def test_all_courses_all_attacks_including_course_two_makuri(self):
        entry = {i: i for i in range(1, 7)}
        scenarios = [{"entry": entry, "attacker": c, "attack": attack,
                      "weight": 1, "strengths": {i: (3 if i == c else 1) for i in entry}}
                     for c in entry for attack in ATTACKS]
        out = rank_scenarios(scenarios)
        self.assertTrue(out["coverage_complete"])
        self.assertIn({"course": 2, "attack": "makuri"}, out["entry_attack_coverage"])
        self.assertEqual(len(out["ranked_120"]), 120)
        self.assertAlmostEqual(math.fsum(r["relative_model_mass"] for r in out["ranked_120"]), 1)
        self.assertFalse(out["calibrated"])
        self.assertFalse(out["formal_fresh_eligible"])

    def test_entry_swap_changes_boat_predictions(self):
        base = {i: i for i in range(1, 7)}
        swap = {1: 2, 2: 1, 3: 3, 4: 4, 5: 5, 6: 6}
        def scenario(entry):
            return [{"entry": entry, "attacker": next(b for b in entry if entry[b] == 1),
                     "attack": "escape", "weight": 1,
                     "strengths": {b: (10 if entry[b] == 1 else 1) for b in entry}}]
        a = rank_scenarios(scenario(base))["ranked_120"][0]["boat_combo"]
        b = rank_scenarios(scenario(swap))["ranked_120"][0]["boat_combo"]
        self.assertEqual(a.split("-")[0], "1")
        self.assertEqual(b.split("-")[0], "2")

    def test_bad_inputs_fail_closed(self):
        entry = {i: i for i in range(1, 7)}
        s = {"entry": entry, "attacker": 2, "attack": "makuri",
             "weight": 1, "strengths": {i: 1 for i in entry}}
        for changed in (dict(s, weight=0), dict(s, attack="unknown"),
                        dict(s, entry={i: 1 for i in entry})):
            with self.assertRaises(ValueError):
                rank_scenarios([changed])


if __name__ == "__main__":
    unittest.main()
