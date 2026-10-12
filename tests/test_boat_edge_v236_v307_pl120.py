"""V307 synthetic-only validation. Matches existing Development CI v23* glob."""
import importlib.util
import math
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts/boat_edge_v307_pl120_research.py"
spec = importlib.util.spec_from_file_location("v307", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class V307ResearchOnly(unittest.TestCase):
    def test_uniform_has_120_normalized_tickets(self):
        x = m.research_report({i: 1 for i in range(1, 7)})
        self.assertEqual(len(x["ranked_120"]), 120)
        self.assertEqual(len(set(row["course_combo"] for row in x["ranked_120"])), 120)
        self.assertAlmostEqual(sum(row["relative_model_mass"] for row in x["ranked_120"]), 1)
        self.assertTrue(all(math.isclose(row["relative_model_mass"], 1/120)
                            for row in x["ranked_120"]))
        self.assertTrue(all(math.isclose(x["head_mass"][str(i)], 1/6)
                            for i in range(1, 7)))
        self.assertFalse(x["calibrated"])
        self.assertFalse(x["promotion_authorized"])
        self.assertFalse(x["wagers_authorized"])

    def test_strength_affects_head_not_odds(self):
        x = m.research_report({1: 10, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})
        self.assertAlmostEqual(x["head_mass"]["1"], 10/15)
        self.assertTrue(all(row["course_combo"].startswith("1-") for row in x["ranked_120"][:10]))
        self.assertEqual(len(x["top10"]), 10)

    def test_scale_invariant_and_position_hypothesis(self):
        a = m.rank_120({i: i for i in range(1, 7)})
        b = m.rank_120({i: i * 7 for i in range(1, 7)})
        self.assertEqual([x for x, _ in a], [x for x, _ in b])
        for (_, p), (_, q) in zip(a, b):
            self.assertAlmostEqual(p, q)
        altered = m.rank_120({i: 1 for i in range(1, 7)},
                             {i: (1.0 if i == 3 else 0.0) for i in range(1, 7)})
        self.assertAlmostEqual(sum(p for _, p in altered), 1.0)
        self.assertGreater(sum(p for x, p in altered if x.split("-")[1] == "3"), 1/6)

    def test_fail_closed_on_bad_inputs(self):
        valid = {i: 1 for i in range(1, 7)}
        for bad in ({1: 1}, {**valid, 7: 1}, {**valid, 1: 0},
                    {**valid, 1: float("nan")}, {**valid, 1: True}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                m.rank_120(bad)
        with self.assertRaises(ValueError):
            m.rank_120(valid, {1: 0.1})


if __name__ == "__main__":
    unittest.main()
