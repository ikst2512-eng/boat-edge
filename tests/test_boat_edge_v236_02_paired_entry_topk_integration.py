"""Paired exhibition-to-final experimental 720→120 ablation, synthetic only."""
from copy import deepcopy
import unittest
from pathlib import Path
import sys

TESTS=Path(__file__).resolve().parent
sys.path.insert(0,str(TESTS))
sys.path.insert(0,str(TESTS.parent/"scripts"))

from test_boat_edge_v236_02_entry_marginalized_topk import (
    cfg, SCOPE, KEY, NOW,
)
from test_boat_edge_v236_02_exhibition_to_actual_entry import (
    EVIDENCE as TRAIN_EVIDENCE, rows as training_rows,
)
from boat_edge_02_entry_marginalized_topk_research import prepare_entry_topk_ablation
from boat_edge_02_joint_entry_permutation_research import digest
from boat_edge_02_matched_ten_pre_result import prepare_matched_ten


def proof(config=None):
    c=config or cfg()
    e=deepcopy(TRAIN_EVIDENCE)
    e["target_exhibition_course_by_boat"]=deepcopy(c["reference_exhibition_course_by_boat"])
    e["target_exhibition_mapping_sha256"]=c["entry_mapping_sha256"]
    return e


def paired(config=None, evidence=None, data=None):
    c=config or cfg()
    e=evidence or proof(c)
    return prepare_entry_topk_ablation(
        KEY,SCOPE,c,entry_evidence=None,
        paired_history_evidence=e,
        paired_history_rows=training_rows() if data is None else data)


class PairedEntryTopK(unittest.TestCase):
    def test_paired_input_runs_existing_720_to_120_code(self):
        out=paired()
        self.assertEqual(out["entry_research_source_kind"],
                         "PAIRED_EXHIBITION_TO_FINAL_RELATIVE_TRANSITION")
        self.assertTrue(out["historic_start_exhibition_to_actual_entry_pairs_used"])
        self.assertEqual(out["entry_permutations_considered"],720)
        self.assertEqual(out["entry_permutations_nonzero_weight"],2)
        for label in ("no_factor_control","baseline","candidate"):
            doc=out[label+"_ranking_document"]
            self.assertEqual(len(doc["ranked_120"]),120)
            self.assertEqual(len(set(r["boat_combo"] for r in doc["ranked_120"])),120)
            self.assertAlmostEqual(sum(row["relative_model_mass"] for row in doc["ranked_120"]),1,places=10)
        self.assertFalse(out["production_eligible"])
        self.assertFalse(out["head_top3_top5_top10_improvement_proven"])
        self.assertFalse(out["actual_results_or_formal_read"])
    def test_without_course_factor_historic_transition_does_not_invent_effect(self):
        c=cfg()
        c["course_factor_by_course"]={i:1. for i in range(1,7)}
        c["course_factor_manifest_sha256"]=digest(c["course_factor_by_course"])
        r=paired(c)
        self.assertLess(r["factor_only_mass_l1_not_hit_improvement"],1e-12)
        self.assertLess(r["mass_l1_research_distance_not_hit_improvement"],1e-10)
        self.assertEqual(r["no_factor_control_top10"],r["candidate_top10"])
        for comparison in ("a_to_b","b_to_c"):
            for k in ("3","5","10"):
                self.assertEqual(r["topk_membership_"+comparison+"_not_hit_rates"][k]["changed_ticket_count_per_side"],0)
    def test_existing_exact_ten_contract_accepts_paired_shadow_not_score(self):
        c=cfg();out=paired(c)
        parent=out["baseline_ranking_document"]
        candidate=out["candidate_ranking_document"]
        scope=dict(
            scope="SITE_RESEARCH_PRE_RESULT_NOT_FORMAL",
            race_key=KEY,deadline_jst="10:20",
            target_source_sha256=c["target_source_sha256"],
            entry_mapping_sha256=c["entry_mapping_sha256"],
            source_permission_evidence_sha256="a"*64,
            parent_model_id=parent["model_id"],
            candidate_model_id=candidate["model_id"],
            parent_training_end="20261013",
            candidate_training_end="20261013",
            no_target_outcome=True,no_formal_fresh=True)
        result=prepare_matched_ten(scope,parent,candidate,NOW)
        self.assertEqual(result["same_ticket_count_each"],10)
        self.assertEqual(result["parent_top10"],out["baseline_top10"])
        self.assertEqual(result["candidate_top10"],out["candidate_top10"])
        self.assertFalse(result["scoring_authorized"])
        self.assertFalse(result["first_git_commit_time_independently_verified"])
    def test_cannot_silently_mix_unconditional_and_historic_paired_sources(self):
        with self.assertRaisesRegex(ValueError,"EXACT_ONE_ENTRY_EVIDENCE_MODE_REQUIRED"):
            prepare_entry_topk_ablation(
                KEY,SCOPE,cfg(),entry_evidence={"source":"bad"},
                paired_history_evidence=proof(),
                paired_history_rows=training_rows())
    def test_paired_source_requires_both_explicit_proof_and_rows(self):
        with self.assertRaisesRegex(ValueError,"EXACT_ONE_ENTRY_EVIDENCE_MODE_REQUIRED"):
            prepare_entry_topk_ablation(
                KEY,SCOPE,cfg(),entry_evidence=None,
                paired_history_evidence=proof())
        with self.assertRaisesRegex(ValueError,"ENTRY_SOURCE_EVIDENCE_REQUIRED"):
            prepare_entry_topk_ablation(KEY,SCOPE,cfg())
    def test_target_exhibition_mapping_must_match_predeclared_120_source(self):
        e=deepcopy(TRAIN_EVIDENCE)
        # The training fixture target exhibition has 1/2 swapped while cfg()
        # asserts today 1..6 identity. The two sources must not be joined.
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_RESEARCH_ONLY_INVARIANTS"):
            paired(evidence=e)
    def test_no_training_records_does_not_fall_back_to_old_frame_prior(self):
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_HISTORY_NOT_SUPPLIED"):
            paired(data=[])
    def test_paired_hist_source_missing_permissions_fails_closed(self):
        e=proof();e["rights_reviewed_for_historic_pairs"]=False
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_RIGHTS_AND_TEMPORAL_GUARD"):
            paired(evidence=e)
    def test_target_day_and_formal_training_cannot_enter_paired_rows(self):
        r=training_rows()
        r[-1]["race_key"]="20261001-12-01"
        r[-1]["venue"]=12
        with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORIC_RACE"):
            paired(data=r)
    def test_source_semantics_distinguish_pooled_transitions_from_exact_posterior(self):
        r=paired()
        self.assertEqual(
            r["entry_weight_semantics"],
            "POOLED_HISTORICAL_EXHIBITION_TO_FINAL_TRANSITIONS_NOT_EXACT_EXHIBITION_POSTERIOR")
        self.assertFalse(r["live_exhibition_conditioned_entry_transition_learned"])
        self.assertTrue(r["entry_720_relative_weights_are_not_calibrated_posterior"])
        self.assertFalse(r["source_rights_and_first_git_time_independently_verified"])


if __name__=="__main__":
    unittest.main()
