"""Synthetic-only A/B: no source reads, results, predictions, payouts or wagers."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from boat_edge_02_entry_marginalized_topk_research import prepare_entry_topk_ablation
from boat_edge_02_joint_entry_permutation_research import digest
from boat_edge_02_matched_ten_pre_result import prepare_matched_ten

KEY = "20261014-12-01"
JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 14, 10, 8, tzinfo=JST)
SCOPE = dict(schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1", race_key=KEY,
  train_end="20261013", first_frozen_at="2026-10-14T10:08:00+09:00",
  deadline_jst="10:20", authorized_training_aggregate=True,
  source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
  reviewed_permission_evidence_sha256="a"*64, source_manifest_sha256="b"*64,
  no_target_outcome=True, formal_fresh_not_used=True)


def cfg():
    observed={b:b for b in range(1,7)}
    strengths={b:float(9-b) for b in range(1,7)}
    factors={b:float(2 if b==1 else 1) for b in range(1,7)}
    return {
        "schema":"BE02_ENTRY_TOPK_PRE_RESULT_CONTEXT_V1",
        "race_key":KEY,
        "target_source_sha256":"c"*64,
        "entry_mapping_sha256":digest(observed),
        "source_permission_evidence_sha256":"a"*64,
        "reference_exhibition_course_by_boat":observed,
        "boat_strength_by_boat":strengths,
        "course_factor_by_course":factors,
        "course_factor_training_end":"20261012",
        "course_factor_manifest_sha256":digest(factors),
        "course_factor_permission_reviewed":True,
        "frozen_pre_result_evidence_only":True,
        "six_active_boats_no_scratch":True,
        "not_using_target_actual_entry":True,
        "not_using_target_outcome":True,
    }


def evidence(uniform=False):
    counts={b:{c:(6 if uniform else 45 if b==c else 1)
               for c in range(1,7)} for b in range(1,7)}
    return {
        "schema":"BE02_JOINT_ENTRY_OBSERVED_COUNTS_V1",
        "source_class":"REVIEWED_AUTHORIZED_OFFICIAL_HISTORICAL_ACTUAL_ENTRY",
        "source_url":"https://boatrace-biwako.jp/example-only-synthetic-no-fetch",
        "venue":12, "historical_period_start":"20260701",
        "historical_period_end":"20260930",
        "same_cohort_six_boat_races_n":36 if uniform else 50,
        "boat_frame_course_observed_counts":counts,
        "counts_sha256":digest(counts),
        "source_manifest_sha256":"b"*64,
        "permission_evidence_sha256":"a"*64,
        "rights_reviewed_for_training":True,
        "first_source_seen_at_jst":"2026-10-14T10:00:00+09:00",
        "source_event_times_before_target":True,
        "six_boats_and_no_scratch_verified":True,
        "actual_target_course_not_used":True,
        "target_result_not_used":True,
    }


def trial(config=None,ev=None):
    return prepare_entry_topk_ablation(KEY,SCOPE,config or cfg(),ev or evidence())


class EntryMarginalizationAblation(unittest.TestCase):
    def test_full120_top3_top5_top10_and_no_accuracy_claim(self):
        out=trial()
        self.assertEqual(out["entry_permutations_considered"],720)
        self.assertEqual(out["entry_permutations_nonzero_weight"],720)
        for side in ("baseline","candidate"):
            doc=out[side+"_ranking_document"]
            rows=doc["ranked_120"]
            self.assertEqual(len(rows),120)
            self.assertEqual(len({r["boat_combo"] for r in rows}),120)
            self.assertAlmostEqual(sum(r["relative_model_mass"] for r in rows),1.0)
            self.assertEqual([r["boat_combo"] for r in rows[:10]],out[side+"_top10"])
            self.assertEqual(len(out[side+"_top3"]),3)
            self.assertEqual(len(out[side+"_top5"]),5)
        self.assertFalse(out["head_top3_top5_top10_improvement_proven"])
        self.assertFalse(out["production_eligible"])
        self.assertFalse(out["actual_results_or_formal_read"])
    def test_same_race_and_ten_tickets_can_use_existing_contract(self):
        c=cfg();out=trial(c)
        pair={
            "scope":"SITE_RESEARCH_PRE_RESULT_NOT_FORMAL",
            "race_key":KEY, "deadline_jst":"10:20",
            "target_source_sha256":c["target_source_sha256"],
            "entry_mapping_sha256":c["entry_mapping_sha256"],
            "source_permission_evidence_sha256":"a"*64,
            "parent_model_id":out["baseline_ranking_document"]["model_id"],
            "candidate_model_id":out["candidate_ranking_document"]["model_id"],
            "parent_training_end":"20261013",
            "candidate_training_end":"20261013",
            "no_target_outcome":True, "no_formal_fresh":True,
        }
        x=prepare_matched_ten(pair,out["baseline_ranking_document"],
                              out["candidate_ranking_document"],NOW)
        self.assertEqual(x["same_ticket_count_each"],10)
        self.assertEqual(x["per_model_virtual_budget_yen"],10000)
        self.assertEqual(x["parent_top10"],out["baseline_top10"])
        self.assertEqual(x["candidate_top10"],out["candidate_top10"])
        self.assertFalse(x["first_git_commit_time_independently_verified"])
    def test_identical_one_multipliers_cannot_invent_entry_signal(self):
        c=cfg()
        c["course_factor_by_course"]={b:1.0 for b in range(1,7)}
        c["course_factor_manifest_sha256"]=digest(c["course_factor_by_course"])
        r=trial(c,evidence(uniform=True))
        self.assertLess(r["mass_l1_research_distance_not_hit_improvement"],1e-10)
        for a,b in zip(r["baseline_ranking_document"]["ranked_120"],
                       r["candidate_ranking_document"]["ranked_120"]):
            self.assertEqual(a["boat_combo"],b["boat_combo"])
            self.assertAlmostEqual(a["relative_model_mass"],b["relative_model_mass"],places=10)
    def test_nontrivial_course_interaction_changes_some_scores_not_proven_hit(self):
        c=cfg()
        c["course_factor_by_course"]={b:float(8 if b==1 else 2 if b==2 else 1)
                                      for b in range(1,7)}
        c["course_factor_manifest_sha256"]=digest(c["course_factor_by_course"])
        r=trial(c,evidence(uniform=True))
        self.assertGreater(r["mass_l1_research_distance_not_hit_improvement"],1e-5)
        self.assertFalse(r["head_top3_top5_top10_improvement_proven"])
    def test_not_permutation_label_leakage(self):
        a=trial()
        self.assertTrue(a["candidate_entry_is_hypothetical_permutation_not_actual"])
        self.assertTrue(a["baseline_entry_is_observed_exhibition_not_actual"])
        self.assertFalse(a["actual_target_course_known"])
    def test_deterministic_and_input_not_mutated(self):
        c,e=cfg(),evidence()
        c_before,e_before=deepcopy(c),deepcopy(e)
        self.assertEqual(trial(c,e),trial(c,e))
        self.assertEqual(c,c_before)
        self.assertEqual(e,e_before)
    def test_wrong_race_or_late_training_is_rejected(self):
        c=cfg();c["race_key"]="20261014-12-02"
        with self.assertRaisesRegex(ValueError,"RACE_SCOPE_MISMATCH"):
            trial(c)
        c=cfg();c["course_factor_training_end"]="20261014"
        with self.assertRaisesRegex(ValueError,"COURSE_FACTOR_TRAINING_AFTER"):
            trial(c)
    def test_invalid_exhibition_permutation_cannot_fill_missing_course(self):
        c=cfg();c["reference_exhibition_course_by_boat"][6]=5
        with self.assertRaisesRegex(ValueError,"EXHIBITION_PERMUTATION_NOT_SIX"):
            trial(c)
    def test_pretarget_course_source_sha_required(self):
        c=cfg();c["entry_mapping_sha256"]="d"*64
        with self.assertRaisesRegex(ValueError,"EXHIBITION_MAPPING_SHA_MISMATCH"):
            trial(c)
        c=cfg();c["course_factor_manifest_sha256"]="d"*64
        with self.assertRaisesRegex(ValueError,"COURSE_FACTOR_CONTENT_SHA_MISMATCH"):
            trial(c)
    def test_no_rights_or_scratches_or_target_actual(self):
        for field in ("course_factor_permission_reviewed",
                      "six_active_boats_no_scratch",
                      "not_using_target_actual_entry",
                      "not_using_target_outcome"):
            c=cfg();c[field]=False
            with self.assertRaisesRegex(ValueError,"RIGHTS_PRE_RESULT_GUARD"):
                trial(c)
    def test_external_entry_source_same_manifest_and_rights(self):
        e=evidence();e["source_manifest_sha256"]="e"*64
        with self.assertRaisesRegex(ValueError,"ENTRY_SOURCE_OR_PERMISSION_SHA_MISMATCH"):
            trial(ev=e)
        e=evidence();e["rights_reviewed_for_training"]=False
        with self.assertRaisesRegex(ValueError,"ENTRY_RIGHTS_OR_PRE_RESULT"):
            trial(ev=e)
    def test_three_arm_controls_separate_factor_effect_from_entry_effect(self):
        out=trial()
        self.assertEqual(out["three_arm_predeclared_ablation"],
                         "A_no_factor__B_fixed_exhibition_with_course_factor__C_joint_entry_with_same_factor")
        for name in ("no_factor_control", "baseline", "candidate"):
            self.assertEqual(len(out[name+"_ranking_document"]["ranked_120"]),120)
            self.assertEqual(out[name+"_top3"],out[name+"_top10"][:3])
            self.assertEqual(out[name+"_top5"],out[name+"_top10"][:5])
        self.assertGreater(out["factor_only_mass_l1_not_hit_improvement"],1e-8)
        self.assertGreaterEqual(out["mass_l1_research_distance_not_hit_improvement"],0)
        self.assertFalse(out["head_top3_top5_top10_improvement_proven"])
    def test_all_course_factors_one_makes_no_factor_and_baseline_identical(self):
        c=cfg(); c["course_factor_by_course"]={i:1.0 for i in range(1,7)}
        c["course_factor_manifest_sha256"]=digest(c["course_factor_by_course"])
        out=trial(c)
        self.assertLess(out["factor_only_mass_l1_not_hit_improvement"],1e-12)
        self.assertEqual(out["no_factor_control_top10"],out["baseline_top10"])
    def test_central_known_formal_days_closed_even_if_caller_claims_safe(self):
        for key in ("20261001-12-01","20261005-12-01","20261013-12-01"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
                    prepare_entry_topk_ablation(key,SCOPE,cfg(),evidence())

    def test_topk_ticket_turnover_is_not_measured_accuracy(self):
        r=trial()
        for comparison in ("a_to_b", "b_to_c"):
            delta=r["topk_membership_"+comparison+"_not_hit_rates"]
            self.assertEqual(set(delta), {"3", "5", "10"})
            for k in (3,5,10):
                row=delta[str(k)]
                self.assertEqual(
                    row["changed_ticket_count_per_side"],
                    len(row["removed_boat_tickets"]))
                self.assertEqual(
                    len(row["added_boat_tickets"]),len(row["removed_boat_tickets"]))
                self.assertLessEqual(row["changed_ticket_count_per_side"], k)
                self.assertEqual(
                    row["ordered_topk_identical"],
                    (r["no_factor_control_top10"] if comparison=="a_to_b" else r["baseline_top10"])[:k] ==
                    (r["baseline_top10"] if comparison=="a_to_b" else r["candidate_top10"])[:k])
        self.assertTrue(r["model_ranking_change_is_not_real_accuracy_gain"])
        self.assertFalse(r["head_top3_top5_top10_improvement_proven"])
    def test_head_masses_are_six_normalized_boat_labels(self):
        r=trial()
        for group in "abc":
            heads=r["head_relative_mass_"+group]
            self.assertEqual(set(heads),set(str(i) for i in range(1,7)))
            self.assertAlmostEqual(sum(heads.values()),1,places=11)
            self.assertIn(r["top_head_boat_"+group],range(1,7))
        self.assertEqual(r["head_top1_change_a_to_b"],
                         r["top_head_boat_a"] != r["top_head_boat_b"])
        self.assertEqual(r["head_top1_change_b_to_c"],
                         r["top_head_boat_b"] != r["top_head_boat_c"])
    def test_negative_control_all_one_course_factors_zero_ticket_turnover(self):
        config=cfg()
        config["course_factor_by_course"]={b:1.0 for b in range(1,7)}
        config["course_factor_manifest_sha256"]=digest(config["course_factor_by_course"])
        r=trial(config,evidence(uniform=True))
        for compare in ("a_to_b","b_to_c"):
            for k in ("3","5","10"):
                self.assertEqual(
                    r["topk_membership_"+compare+"_not_hit_rates"][k]["changed_ticket_count_per_side"],0)
                self.assertTrue(
                    r["topk_membership_"+compare+"_not_hit_rates"][k]["ordered_topk_identical"])
        self.assertFalse(r["head_top1_change_a_to_b"])
        self.assertFalse(r["head_top1_change_b_to_c"])
    def test_large_course_factor_can_change_topk_without_measured_hit(self):
        config=cfg()
        config["course_factor_by_course"]={
            b:float(12 if b==4 else 2 if b==2 else 1) for b in range(1,7)}
        config["course_factor_manifest_sha256"]=digest(config["course_factor_by_course"])
        r=trial(config,evidence(uniform=True))
        self.assertGreater(r["factor_only_mass_l1_not_hit_improvement"],0.01)
        self.assertTrue(r["model_ranking_change_is_not_real_accuracy_gain"])
        self.assertFalse(r["calibration_validated"])

    def test_no_unverified_beneficial_hit_rate_from_mass_distance(self):
        out=trial()
        self.assertGreaterEqual(out["mass_l1_research_distance_not_hit_improvement"],0)
        self.assertNotIn("hit_rate",out)
        self.assertFalse(out["calibration_validated"])


if __name__=="__main__":
    unittest.main()
