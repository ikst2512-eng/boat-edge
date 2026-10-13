"""Synthetic only: evidence gates for pre-target rider ST pairs, not race outcomes."""
from copy import deepcopy
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from boat_edge_02_st_distribution_research import derive_st_signals

KEY="20261014-12-01"
SCOPE=dict(schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1",race_key=KEY,
           train_end="20261013",first_frozen_at="2026-10-14T10:08:00+09:00",
           deadline_jst="10:20",authorized_training_aggregate=True,
           source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
           reviewed_permission_evidence_sha256="a"*64,source_manifest_sha256="b"*64,
           no_target_outcome=True,formal_fresh_not_used=True)
EVIDENCE=dict(schema="BE02_ST_PRE_RESULT_PROOF_V1",provenance="b"*64,
              six_boats_verified_no_scratch=True,
              historical_finish_st_is_earlier_than_target=True,
              source_rights_reviewed=True,official_exhibition_only=True,
              race_exhibition_observed_at_jst="2026-10-14T10:05:00+09:00",
              race_exhibition_by_boat={i:0.14 for i in range(1,7)})

def row(n=30,m=25):
    ex=[.12+.01*(i%5) for i in range(m)]
    fin=[.11+.4*(v-.14)+.004*(i%3) for i,v in enumerate(ex)]
    rest=[.16]*(n-m)
    all_fin=fin+rest
    return dict(training_n=n,top_start_count=min(5,n),
                final_st_sum=sum(all_fin),final_st_square_sum=sum(v*v for v in all_fin),
                paired_n=m,paired_ex_sum=sum(ex),paired_final_sum=sum(fin),
                paired_ex_square_sum=sum(v*v for v in ex),
                paired_final_square_sum=sum(v*v for v in fin),
                paired_ex_final_product_sum=sum(x*y for x,y in zip(ex,fin)))

def history():
    return {i:row() for i in range(1,7)}

class STDistributionResearch(unittest.TestCase):
    def test_six_sample_distributions_and_deterministic_regression(self):
        one=derive_st_signals(KEY,SCOPE,EVIDENCE,history())
        self.assertEqual(one,derive_st_signals(KEY,SCOPE,EVIDENCE,history()))
        self.assertEqual(len(one["st_signals"]),6)
        self.assertAlmostEqual(one["st_signals"][0]["top_start_rate_shrunk_prior_one_sixth"],7/42)
        self.assertTrue(math.isfinite(one["st_signals"][0]["regression_slope_shrunk_training_only"]))
        self.assertFalse(one["production_eligible"])
        self.assertFalse(one["actual_race_st_read"])
        self.assertFalse(one["source_rights_and_timestamps_independently_verified_by_code"])
    def test_missing_official_exhibition_never_imputed(self):
        e=deepcopy(EVIDENCE);e["race_exhibition_by_boat"][2]=None
        out=derive_st_signals(KEY,SCOPE,e,history())
        self.assertIsNone(out["st_signals"][1]["conditional_exhibition_st_correction_candidate"])
        self.assertIsNone(out["st_signals"][1]["observed_official_exhibition_st"])
    def test_small_paired_sample_does_not_estimate_slope(self):
        h=history();h[1]=row(n=30,m=5)
        out=derive_st_signals(KEY,SCOPE,EVIDENCE,h)
        self.assertIsNone(out["st_signals"][0]["regression_slope_shrunk_training_only"])
        self.assertIsNone(out["st_signals"][0]["conditional_exhibition_st_correction_candidate"])
    def test_zero_historical_sample_is_missing_not_a_zero_signal(self):
        h=history();h[1]=row(0,0)
        r=derive_st_signals(KEY,SCOPE,EVIDENCE,h)["st_signals"][0]
        self.assertIsNone(r["historical_actual_st_mean"])
        self.assertIsNone(r["top_start_rate_shrunk_prior_one_sixth"])
    def test_unlicensed_or_unproven_full_boat_source_rejected(self):
        e=deepcopy(EVIDENCE);e["source_rights_reviewed"]=False
        with self.assertRaisesRegex(ValueError,"ST_SOURCE_OR_RIGHTS"):
            derive_st_signals(KEY,SCOPE,e,history())
        e=deepcopy(EVIDENCE);e["six_boats_verified_no_scratch"]=False
        with self.assertRaisesRegex(ValueError,"ST_SOURCE_OR_RIGHTS"):
            derive_st_signals(KEY,SCOPE,e,history())
    def test_source_seen_after_freeze_and_wrong_timezone_rejected(self):
        e=deepcopy(EVIDENCE)
        e["race_exhibition_observed_at_jst"]="2026-10-14T10:09:00+09:00"
        with self.assertRaisesRegex(ValueError,"EXHIBITION_NOT_PROVEN"):
            derive_st_signals(KEY,SCOPE,e,history())
        e["race_exhibition_observed_at_jst"]="2026-10-14T01:05:00+00:00"
        with self.assertRaisesRegex(ValueError,"EXHIBITION_NOT_PROVEN"):
            derive_st_signals(KEY,SCOPE,e,history())
    def test_bad_pair_count_or_topcount_rejected(self):
        h=history();h[2]["paired_n"]=50
        with self.assertRaisesRegex(ValueError,"COUNTS_INVALID"):
            derive_st_signals(KEY,SCOPE,EVIDENCE,h)
        h=history();h[2]["top_start_count"]=31
        with self.assertRaisesRegex(ValueError,"COUNTS_INVALID"):
            derive_st_signals(KEY,SCOPE,EVIDENCE,h)
    def test_impossible_negative_variance_and_covariance_rejected(self):
        h=history();h[3]["final_st_square_sum"]=0.
        with self.assertRaisesRegex(ValueError,"INCONSISTENT_ST_MOMENTS"):
            derive_st_signals(KEY,SCOPE,EVIDENCE,h)
        h=history();h[4]["paired_ex_final_product_sum"]=5.
        with self.assertRaisesRegex(ValueError,"INCONSISTENT_ST_COVARIANCE"):
            derive_st_signals(KEY,SCOPE,EVIDENCE,h)
    def test_banned_target_day_and_formal_gate(self):
        s=deepcopy(SCOPE);s["train_end"]="20261014"
        with self.assertRaisesRegex(ValueError,"TRAINING_NOT_EARLIER"):
            derive_st_signals(KEY,s,EVIDENCE,history())
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
            derive_st_signals("20261001-12-01",SCOPE,EVIDENCE,history())
    def test_no_extra_actual_current_st_or_result_fields(self):
        e=deepcopy(EVIDENCE);e["same_race_actual_st"]=.12
        with self.assertRaisesRegex(ValueError,"ST_EVIDENCE_SCHEMA"):
            derive_st_signals(KEY,SCOPE,e,history())
        h=history();h[1]["last_actual_race_result"]="1-2-3"
        with self.assertRaisesRegex(ValueError,"TRAINING_ST_MOMENTS_SCHEMA"):
            derive_st_signals(KEY,SCOPE,EVIDENCE,h)
    def test_invalid_or_missing_exhibition_st_rejected(self):
        e=deepcopy(EVIDENCE);e["race_exhibition_by_boat"][4]=-0.01
        with self.assertRaisesRegex(ValueError,"INVALID_PRE_RESULT"):
            derive_st_signals(KEY,SCOPE,e,history())
        e=deepcopy(EVIDENCE);del e["race_exhibition_by_boat"][4]
        with self.assertRaisesRegex(ValueError,"SIX_BOAT_EXHIBITION"):
            derive_st_signals(KEY,SCOPE,e,history())

if __name__=="__main__":unittest.main()
