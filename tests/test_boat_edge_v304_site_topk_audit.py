"""Synthetic-only regression tests; never access race outcomes or Formal files."""
import unittest
from scripts.boat_edge_v304_site_topk_audit import summarize, reconcile_v235_baseline, ranked_site_baseline_by_day
from scripts.boat_edge_v301_paired_evidence import EvidenceError

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


class V304DayRankBinsTests(unittest.TestCase):
    def test_nonadditive_per_day_rank_bins(self):
        rows = [row("20261011-01-01", PICKS[0], PICKS),
                row("20261011-01-02", PICKS[4], PICKS),
                row("20261012-01-01", PICKS[9], PICKS),
                row("20261012-01-02", "6-5-4", PICKS)]
        result = ranked_site_baseline_by_day(rows)
        self.assertEqual(list(result), ["20261011", "20261012"])
        self.assertEqual(result["20261011"]["races"], 2)
        self.assertEqual(result["20261011"]["rank_bins"],
                         {"top3": 1, "rank4_5": 1, "rank6_10": 0, "outside_top10": 0})
        self.assertEqual(result["20261012"]["rank_bins"],
                         {"top3": 0, "rank4_5": 0, "rank6_10": 1, "outside_top10": 1})
        self.assertEqual(result["20261011"]["baseline_hits"], {"3": 1, "5": 2, "10": 2})
        self.assertEqual(result["20261012"]["baseline_hits"], {"3": 0, "5": 0, "10": 1})
        self.assertEqual(result["20261012"]["miss_leg_partition"]["head_missing"], 1)
        self.assertEqual(sum(v["races"] for v in result.values()), 4)

    def test_empty_not_implied_zero_accuracy(self):
        self.assertEqual(ranked_site_baseline_by_day([]), {})

    def test_wrong_day_and_damaged_ticket_fail_closed(self):
        r = row("20261012-01-01", PICKS[0], PICKS)
        with self.assertRaisesRegex(EvidenceError, "DAY_OR_RANKING"):
            ranked_site_baseline_by_day([dict(r, day="20261011")])
        with self.assertRaisesRegex(EvidenceError, "VALIDATED_RANKING"):
            ranked_site_baseline_by_day([dict(r, baseline=PICKS[:9] + PICKS[0:1])])
        with self.assertRaisesRegex(EvidenceError, "VALIDATED_WINNER"):
            ranked_site_baseline_by_day([dict(r, winning="1-1-1")])


def frozen(key, picks=PICKS):
    return {"race_key":key, "schema":"BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1",
            "scope":"SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
            "model_id":"SITE_REFERENCE_V122",
            "formal_results_seen":False,"formal_gate_unlocked":False,
            "paper_purchases_authorized":False,"real_purchases_authorized":False,
            "top10":list(picks),"top3":list(picks[:3]),"top5":list(picks[:5]),
            "frozen_mode_tickets":{"hit":[{"combo":x} for x in picks]}}

def v241(key, winning, picks=PICKS):
    return {"race_key":key,"date_jst":key[:8],"winning_combo":winning,
            "model_id":"SITE_REFERENCE_V122","post_result_verified":True,
            "head_prediction":picks[0].split("-")[0],
            "top3_hit":winning in picks[:3],"top5_hit":winning in picks[:5],
            "top10_hit":winning in picks}

class V304V235ReconciliationTests(unittest.TestCase):
    """Pure synthetic tests. Does NOT open real results or formal files."""
    def setUp(self):
        self.a = "20261011-01-01"
        self.b = "20261012-01-01"
        self.rows = [v241(self.a,PICKS[0]),v241(self.b,"6-5-4")]
        self.parents = {self.a:frozen(self.a),self.b:frozen(self.b)}
        self.existing_shadow = {self.b:row(self.b,"6-5-4",PICKS)}

    def test_nonadditive_verified_baseline_and_v305_misses(self):
        result = reconcile_v235_baseline(self.rows,self.parents,self.existing_shadow)
        self.assertEqual(result["baseline"]["races"],2)
        self.assertEqual(result["baseline"]["days"],2)
        self.assertEqual(result["baseline"]["baseline_hits"],{"3":1,"5":1,"10":1})
        self.assertEqual(result["additional_unique_outside_v301"],1)
        self.assertEqual(result["miss_leg_partition"]["top10_hit"],1)
        self.assertEqual(result["miss_leg_partition"]["head_missing"],1)
        self.assertIsNone(result["candidate_top3_top5_delta"])
        self.assertTrue(result["by_day_descriptive_only_not_evidence_of_model_improvement"])
        self.assertEqual(result["verified_baseline_by_day"]["20261011"]["rank_bins"]["top3"], 1)
        self.assertEqual(result["verified_baseline_by_day"]["20261012"]["rank_bins"]["outside_top10"], 1)
        self.assertFalse(result["promotion_authorized"])

    def test_reject_duplicate_race_before_counting(self):
        with self.assertRaisesRegex(EvidenceError,"DUPLICATE"):
            reconcile_v235_baseline(self.rows+self.rows[:1],self.parents,self.existing_shadow)

    def test_reject_late_relabelled_rank_or_hit(self):
        mutated = [dict(self.rows[0]),self.rows[1]]
        mutated[0]["top3_hit"]=False
        with self.assertRaisesRegex(EvidenceError,"TOPK_PARITY"):
            reconcile_v235_baseline(mutated,self.parents,self.existing_shadow)

    def test_reject_reordered_pre_result_prefix(self):
        parents={k:dict(v) for k,v in self.parents.items()}
        parents[self.a]["top3"]=PICKS[1:4]
        with self.assertRaisesRegex(EvidenceError,"ORDERED_TOPK"):
            reconcile_v235_baseline(self.rows,parents,self.existing_shadow)

    def test_reject_untrusted_missing_source_cohort(self):
        with self.assertRaisesRegex(EvidenceError,"ORIGINAL_COHORT"):
            reconcile_v235_baseline(self.rows,{self.a:self.parents[self.a]},self.existing_shadow)

    def test_reject_cross_study_overlap_disagreement(self):
        wrong={self.b:row(self.b,"1-2-3",PICKS)}
        with self.assertRaisesRegex(EvidenceError,"OVERLAP_CONFLICT"):
            reconcile_v235_baseline(self.rows,self.parents,wrong)

    def test_reject_unaccounted_shadow_race(self):
        ghost={"20261013-01-01":row("20261013-01-01","1-2-3",PICKS)}
        with self.assertRaisesRegex(EvidenceError,"SHADOW_ROW_NOT_IN_V241"):
            reconcile_v235_baseline(self.rows,self.parents,ghost)

    def test_reject_failed_formal_blind_label(self):
        parents={k:dict(v) for k,v in self.parents.items()}
        parents[self.a]["formal_results_seen"]=True
        with self.assertRaisesRegex(EvidenceError,"ORIGINAL_COHORT"):
            reconcile_v235_baseline(self.rows,parents,self.existing_shadow)

    def test_empty_rows_only_valid_with_no_overlap(self):
        result=reconcile_v235_baseline([],{}, {})
        self.assertEqual(result["baseline"]["races"],0)
        self.assertIsNone(result["baseline"]["baseline_hit_rate"]["3"])

if __name__=="__main__":
    unittest.main()
