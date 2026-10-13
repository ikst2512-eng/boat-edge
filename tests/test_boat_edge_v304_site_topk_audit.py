"""Synthetic-only regression tests; never access race outcomes or Formal files."""
import unittest
from scripts.boat_edge_v304_site_topk_audit import summarize

def row(key, winning, picks):
    return {"key":key,"day":key[:8],"winning":winning,"baseline":picks}

PICKS=["1-2-3","1-2-4","1-3-2","1-3-4","1-4-2",
       "1-4-3","2-1-3","2-1-4","2-3-1","2-3-4"]

class V304TopKTests(unittest.TestCase):
    def test_nested_prefixes_and_denominator(self):
        rows=[row("20261012-01-01",PICKS[1],PICKS),
              row("20261012-01-02",PICKS[4],PICKS),
              row("20261013-01-01",PICKS[9],PICKS),
              row("20261013-01-02","6-5-4",PICKS)]
        got=summarize(rows)
        self.assertEqual(got["races"],4)
        self.assertEqual(got["days"],2)
        self.assertEqual(got["baseline_hits"],{"3":1,"5":2,"10":3})
        self.assertEqual(got["baseline_hit_rate"],{"3":.25,"5":.5,"10":.75})
        self.assertIsNone(got["new_model_delta"])
    def test_zero_rows_not_zero_accuracy(self):
        got=summarize([])
        self.assertEqual(got["races"],0)
        self.assertEqual(got["baseline_hits"],{"3":0,"5":0,"10":0})
        self.assertEqual(got["baseline_hit_rate"],{"3":None,"5":None,"10":None})
    def test_no_candidate_lift_claim(self):
        got=summarize([row("20261012-01-01",PICKS[0],PICKS)])
        self.assertTrue(got["candidate_top3_top5_unavailable"])
        self.assertIsNone(got["new_model_delta"])

if __name__=="__main__":
    unittest.main()
