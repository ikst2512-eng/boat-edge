"""Fixture-only exact historic exhibition-pattern 720→120 study.

No real results/locked Formal, scraping, odds, network or I/O.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import sys
from pathlib import Path
import unittest

TESTS=Path(__file__).resolve().parent
sys.path.insert(0,str(TESTS))
sys.path.insert(0,str(TESTS.parent/"scripts"))

from test_boat_edge_v236_02_exhibition_to_actual_entry import (
    KEY, EVIDENCE, SCOPE, rows as historic_rows,
)
from test_boat_edge_v236_02_entry_marginalized_topk import cfg
from boat_edge_02_exhibition_to_actual_entry_research import (
    estimate_exhibition_conditioned_entry, EXACT_ID, EXACT_MODE,
)
from boat_edge_02_entry_marginalized_topk_research import (
    prepare_entry_topk_ablation, EXACT_CANDIDATE, PAIRED_CANDIDATE,
)
from boat_edge_02_joint_entry_permutation_research import digest
from boat_edge_02_matched_ten_pre_result import prepare_matched_ten
from test_boat_edge_v236_02_entry_marginalized_topk import NOW


def target_identity():
    evidence=deepcopy(EVIDENCE)
    evidence["target_exhibition_course_by_boat"]={b:b for b in range(1,7)}
    evidence["target_exhibition_mapping_sha256"]=digest(
        evidence["target_exhibition_course_by_boat"])
    return evidence


def two_patterns():
    # Earlier 40 fabricated races: start exhibition swap, final all identity.
    # Later 40 fabricated races: exhibition identity and mostly final identity.
    # All racing dates/source first-seen and deadlines are fake test fixtures.
    extra=[]
    start=date(2026,6,1)
    for i in range(40):
        item=deepcopy(historic_rows()[0])
        today=start+timedelta(days=i)
        dt=today.isoformat()
        v=3 if i%5==0 else 12
        item["race_key"]=f"{today.strftime('%Y%m%d')}-{v:02d}-01"
        item["venue"]=v
        item["exhibition_course_by_boat"]={1:2,2:1,3:3,4:4,5:5,6:6}
        item["actual_course_by_boat"]={b:b for b in range(1,7)}
        item["exhibition_first_seen_jst"]=dt+"T10:00:00+09:00"
        item["race_deadline_jst"]=dt+"T11:00:00+09:00"
        item["final_actual_course_first_seen_jst"]=dt+"T13:00:00+09:00"
        extra.append(item)
    return extra+historic_rows()


class ExactPatternTransitions(unittest.TestCase):
    def test_absent_exact_exhibition_population_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"EXACT_EXHIBITION_PATTERN_SUPPORT_TOO_SPARSE"):
            estimate_exhibition_conditioned_entry(
                KEY,SCOPE,EVIDENCE,historic_rows(),conditioning_mode=EXACT_MODE)
    def test_exact_pattern_histogram_and_720_normalization(self):
        ev=target_identity()
        got=estimate_exhibition_conditioned_entry(
            KEY,SCOPE,ev,two_patterns(),conditioning_mode=EXACT_MODE)
        self.assertEqual(got["model_id"],EXACT_ID)
        self.assertEqual(got["historical_national_paired_events_n"],80)
        self.assertEqual(got["historical_same_venue_paired_events_n"],64)
        self.assertEqual(got["historical_exact_exhibition_pattern_national_n"],40)
        self.assertEqual(got["historical_exact_exhibition_pattern_venue_n"],32)
        self.assertTrue(got["historic_transition_counts_conditioned_on_exact_exhibition_pattern"])
        self.assertFalse(got["full_conditional_entry_posterior_calibrated"])
        self.assertFalse(got["production_eligible"])
        self.assertFalse(got["formal_results_read"])
        self.assertEqual(len(got["ranked_720"]),720)
        self.assertAlmostEqual(sum(x["relative_model_mass"] for x in got["ranked_720"]),1,places=11)
    def test_exact_subgroup_can_change_mass_without_any_hit_claim(self):
        ev=target_identity()
        pooled=estimate_exhibition_conditioned_entry(KEY,SCOPE,ev,two_patterns())
        exact=estimate_exhibition_conditioned_entry(
            KEY,SCOPE,ev,two_patterns(),conditioning_mode=EXACT_MODE)
        self.assertEqual(pooled["historic_transition_counts_conditioned_on_exact_exhibition_pattern"],False)
        self.assertNotEqual(pooled["observed_paired_counts_sha256"],
                            exact["observed_paired_counts_sha256"])
        p={tuple(r["course_by_boat"]):r["relative_model_mass"] for r in pooled["ranked_720"]}
        q={tuple(r["course_by_boat"]):r["relative_model_mass"] for r in exact["ranked_720"]}
        self.assertGreater(sum(abs(p[k]-q[k]) for k in p),0.1)
        self.assertFalse(exact["top3_top5_top10_improvement_proven"])
    def test_exact_mode_uses_existing_full120_aggregator_with_new_candidate_id(self):
        c=cfg()
        e=target_identity()
        out=prepare_entry_topk_ablation(
            KEY,SCOPE,c,paired_history_evidence=e,
            paired_history_rows=two_patterns(),paired_history_mode=EXACT_MODE)
        self.assertEqual(out["candidate_ranking_document"]["model_id"],EXACT_CANDIDATE)
        self.assertTrue(out["exact_exhibition_pattern_conditioning_requested"])
        self.assertTrue(out["historic_transition_counts_conditioned_on_exact_exhibition_pattern"])
        self.assertEqual(out["historical_exact_exhibition_pattern_national_n"],40)
        self.assertEqual(len(out["candidate_ranking_document"]["ranked_120"]),120)
        for name in ("no_factor_control","baseline","candidate"):
            self.assertEqual(len(out[name+"_top3"]),3)
            self.assertEqual(len(out[name+"_top5"]),5)
            self.assertEqual(len(out[name+"_top10"]),10)
        self.assertFalse(out["head_top3_top5_top10_improvement_proven"])
        self.assertFalse(out["production_eligible"])
    def test_old_pooled_model_keeps_separate_id(self):
        c=cfg()
        ev=target_identity()
        out=prepare_entry_topk_ablation(
            KEY,SCOPE,c,paired_history_evidence=ev,paired_history_rows=two_patterns())
        self.assertEqual(out["candidate_ranking_document"]["model_id"],PAIRED_CANDIDATE)
        self.assertFalse(out["exact_exhibition_pattern_conditioning_requested"])
        self.assertFalse(out["historic_transition_counts_conditioned_on_exact_exhibition_pattern"])
    def test_exact_conditioning_does_not_create_signal_with_all_course_factors_one(self):
        c=cfg()
        c["course_factor_by_course"]={b:1.0 for b in range(1,7)}
        c["course_factor_manifest_sha256"]=digest(c["course_factor_by_course"])
        out=prepare_entry_topk_ablation(
            KEY,SCOPE,c,paired_history_evidence=target_identity(),
            paired_history_rows=two_patterns(),paired_history_mode=EXACT_MODE)
        self.assertLess(out["factor_only_mass_l1_not_hit_improvement"],1e-10)
        self.assertLess(out["mass_l1_research_distance_not_hit_improvement"],1e-10)
        self.assertFalse(out["head_top3_top5_top10_improvement_proven"])
        self.assertFalse(out["calibration_validated"])
    def test_exact_conditioning_integrates_existing_equal_ten_without_scoring(self):
        c=cfg()
        out=prepare_entry_topk_ablation(
            KEY,SCOPE,c,paired_history_evidence=target_identity(),
            paired_history_rows=two_patterns(),paired_history_mode=EXACT_MODE)
        b,candidate=out["baseline_ranking_document"],out["candidate_ranking_document"]
        evidence=dict(
            scope="SITE_RESEARCH_PRE_RESULT_NOT_FORMAL",
            race_key=KEY,deadline_jst="10:20",
            target_source_sha256=c["target_source_sha256"],
            entry_mapping_sha256=c["entry_mapping_sha256"],
            source_permission_evidence_sha256="a"*64,
            parent_model_id=b["model_id"],
            candidate_model_id=candidate["model_id"],
            parent_training_end="20261013",
            candidate_training_end="20261013",
            no_target_outcome=True,no_formal_fresh=True)
        m=prepare_matched_ten(evidence,b,candidate,NOW)
        self.assertEqual(m["same_ticket_count_each"],10)
        self.assertEqual(m["parent_top10"],out["baseline_top10"])
        self.assertEqual(m["candidate_top10"],out["candidate_top10"])
        self.assertFalse(m["first_git_commit_time_independently_verified"])
        self.assertFalse(m["scoring_authorized"])
        self.assertFalse(m["accuracy_improvement_proven"])
    def test_declared_mode_is_required_and_cannot_silently_fallback(self):
        ev=target_identity()
        with self.assertRaisesRegex(ValueError,"UNDECLARED_EXHIBITION_CONDITIONING_MODE"):
            estimate_exhibition_conditioned_entry(
                KEY,SCOPE,ev,two_patterns(),conditioning_mode="AUTO")
        with self.assertRaisesRegex(ValueError,"ENTRY_CONDITIONING_MODE_INVALID"):
            prepare_entry_topk_ablation(
                KEY,SCOPE,cfg(),paired_history_evidence=ev,
                paired_history_rows=two_patterns(),paired_history_mode="AUTO")
        with self.assertRaisesRegex(ValueError,"EXACT_ENTRY_MODE_REQUIRES_PAIRED_HISTORY"):
            prepare_entry_topk_ablation(
                KEY,SCOPE,cfg(),entry_evidence={},paired_history_mode=EXACT_MODE)
    def test_both_modes_reject_target_day_and_protected_formal_records(self):
        data=two_patterns()
        data[-1]["race_key"]="20261001-12-01"
        data[-1]["venue"]=12
        for mode in ("POOLED",EXACT_MODE):
            with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORIC_RACE"):
                estimate_exhibition_conditioned_entry(
                    KEY,SCOPE,target_identity(),data,conditioning_mode=mode)
    def test_unobserved_exact_population_must_not_be_pseudocount_filled(self):
        data=two_patterns()
        for r in data:
            if r["exhibition_course_by_boat"] == {b:b for b in range(1,7)}:
                r["exhibition_course_by_boat"]={1:2,2:1,3:3,4:4,5:5,6:6}
        with self.assertRaisesRegex(ValueError,"EXACT_EXHIBITION_PATTERN_SUPPORT_TOO_SPARSE"):
            estimate_exhibition_conditioned_entry(
                KEY,SCOPE,target_identity(),data,conditioning_mode=EXACT_MODE)


if __name__=="__main__":
    unittest.main()
