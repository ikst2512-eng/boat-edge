import unittest
from scripts.boat_edge_v305_site_miss_attribution import category, summarize

PICKS=["1-2-3","1-2-4","1-3-2","1-3-4","1-4-2",
       "1-4-3","2-1-3","2-1-4","2-3-1","2-3-4"]
def row(win):
    return {"winning":win,"baseline":PICKS}

class V305MissTests(unittest.TestCase):
    def test_exhaustive_leg_categories(self):
        self.assertEqual(category(row("1-2-3")),"top10_hit")
        self.assertEqual(category(row("6-1-2")),"head_missing")
        self.assertEqual(category(row("1-5-2")),"second_missing_given_head")
        self.assertEqual(category(row("1-2-5")),"third_missing_given_head_second")
    def test_denominator_and_no_entry_claim(self):
        result=summarize([row(x) for x in ("1-2-3","6-1-2","1-5-2","1-2-5")])
        self.assertEqual(result["races"],4)
        self.assertEqual(result["misses"],3)
        self.assertEqual(list(result["counts"].values()),[1,1,1,1])
        self.assertTrue(result["entry_attribution_unavailable"])
        self.assertTrue(result["scenario_attribution_unavailable"])
        self.assertFalse(result["model_improvement_proven"])

if __name__=="__main__":
    unittest.main()
