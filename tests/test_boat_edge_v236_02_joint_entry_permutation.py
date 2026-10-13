"""Fabricated six-by-six historic entry counts; zero outcomes or provider fetches."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_02_joint_entry_permutation_research import joint_entry_distribution, digest

KEY = "20261014-12-01"
SCOPE = dict(
    schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1", race_key=KEY,
    train_end="20261013", first_frozen_at="2026-10-14T10:08:00+09:00",
    deadline_jst="10:20", authorized_training_aggregate=True,
    source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
    reviewed_permission_evidence_sha256="a"*64,
    source_manifest_sha256="b"*64,
    no_target_outcome=True, formal_fresh_not_used=True,
)


def evidence():
    # A doubly balanced, entirely fabricated 50-event 6x6 contingency.
    counts = {b: {c: (45 if b == c else 1) for c in range(1,7)}
              for b in range(1,7)}
    return dict(
        schema="BE02_JOINT_ENTRY_OBSERVED_COUNTS_V1",
        source_class="REVIEWED_AUTHORIZED_OFFICIAL_HISTORICAL_ACTUAL_ENTRY",
        source_url="https://www.boatrace.jp/example-only-not-a-real-dataset",
        venue=12, historical_period_start="20260701",
        historical_period_end="20260930", same_cohort_six_boat_races_n=50,
        boat_frame_course_observed_counts=counts, counts_sha256=digest(counts),
        source_manifest_sha256="b"*64, permission_evidence_sha256="a"*64,
        rights_reviewed_for_training=True, first_source_seen_at_jst="2026-10-14T10:05:00+09:00",
        source_event_times_before_target=True, six_boats_and_no_scratch_verified=True,
        actual_target_course_not_used=True, target_result_not_used=True,
    )


class JointSixEntryResearch(unittest.TestCase):
    def test_exact_720_ranked_entry_with_normalized_marginals(self):
        x=joint_entry_distribution(KEY,SCOPE,evidence())
        self.assertEqual(x["distinct_full_entry_permutations"],720)
        self.assertEqual(len(x["ranked_720"]),720)
        self.assertEqual(len(x["top10_provisional_course_assignments"]),10)
        self.assertAlmostEqual(sum(r["relative_model_mass"] for r in x["ranked_720"]),1)
        self.assertEqual(x["ranked_720"][0]["course_by_boat"],[1,2,3,4,5,6])
        self.assertEqual(
            len({tuple(r["course_by_boat"]) for r in x["ranked_720"]}),720)
        self.assertFalse(x["production_eligible"])
        self.assertFalse(x["full_120_trifecta_ready"])
        self.assertFalse(x["source_permission_and_first_seen_authenticated_by_function"])
    def test_each_boat_one_course_and_each_course_one_boat_marginals(self):
        x=joint_entry_distribution(KEY,SCOPE,evidence())
        for b in range(1,7):
            self.assertAlmostEqual(sum(x["course_marginal_by_boat"][str(b)].values()),1)
        for c in range(1,7):
            self.assertAlmostEqual(sum(x["course_marginal_by_boat"][str(b)][str(c)]
                                   for b in range(1,7)),1)
        for row in x["ranked_720"]:
            self.assertEqual(set(row["course_by_boat"]), set(range(1,7)))
    def test_deterministic_non_mutation_and_count_hash(self):
        ev=evidence(); original=deepcopy(ev)
        a=joint_entry_distribution(KEY,SCOPE,ev)
        self.assertEqual(a,joint_entry_distribution(KEY,SCOPE,ev))
        self.assertEqual(ev,original)
        self.assertEqual(a["source_count_sha256"],ev["counts_sha256"])
    def test_doubly_balanced_rows_required(self):
        ev=evidence();ev["boat_frame_course_observed_counts"][1][1]+=1
        ev["counts_sha256"]=digest(ev["boat_frame_course_observed_counts"])
        with self.assertRaisesRegex(ValueError,"ROWS_NOT_SAME"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_doubly_balanced_columns_required(self):
        ev=evidence()
        ev["boat_frame_course_observed_counts"][1][1]-=1
        ev["boat_frame_course_observed_counts"][1][2]+=1
        ev["counts_sha256"]=digest(ev["boat_frame_course_observed_counts"])
        with self.assertRaisesRegex(ValueError,"COLUMNS_NOT_SAME"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_absent_counts_cannot_be_filled_by_prior(self):
        ev=evidence();del ev["boat_frame_course_observed_counts"][1][6]
        with self.assertRaisesRegex(ValueError,"SIX_COURSE_COLUMNS_REQUIRED"):
            joint_entry_distribution(KEY,SCOPE,ev)
        ev=evidence();ev["boat_frame_course_observed_counts"][1][6]=None
        with self.assertRaisesRegex(ValueError,"NONNEGATIVE_INTEGER_COUNTS"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_bogus_count_sha_is_refused(self):
        ev=evidence();ev["counts_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"COUNT_CONTENT_HASH_MISMATCH"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_small_eligible_sample_cannot_be_called_valid(self):
        ev=evidence()
        ev["same_cohort_six_boat_races_n"]=29
        with self.assertRaisesRegex(ValueError,"MINIMUM_N"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_no_data_after_training_end(self):
        ev=evidence();ev["historical_period_end"]="20261014"
        with self.assertRaisesRegex(ValueError,"HISTORICAL_PERIOD_FUTURE"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_no_source_after_first_freeze(self):
        ev=evidence();ev["first_source_seen_at_jst"]="2026-10-14T10:10:00+09:00"
        with self.assertRaisesRegex(ValueError,"NOT_PROVEN_PRE_FREEZE"):
            joint_entry_distribution(KEY,SCOPE,ev)
        ev["first_source_seen_at_jst"]="2026-10-14T01:05:00+00:00"
        with self.assertRaisesRegex(ValueError,"NOT_PROVEN_PRE_FREEZE"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_source_rights_and_actual_target_semantics_fail_closed(self):
        ev=evidence();ev["rights_reviewed_for_training"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_PRE_RESULT"):
            joint_entry_distribution(KEY,SCOPE,ev)
        ev=evidence();ev["actual_target_course_not_used"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_PRE_RESULT"):
            joint_entry_distribution(KEY,SCOPE,ev)
        ev=evidence();ev["target_result_not_used"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_PRE_RESULT"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_model_does_not_read_formal_locked_target(self):
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
            joint_entry_distribution("20261001-12-01",SCOPE,evidence())
    def test_site_specific_historic_counts_not_other_venue(self):
        ev=evidence();ev["venue"]=16
        with self.assertRaisesRegex(ValueError,"VENUE_MISMATCH"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_no_undocumented_fields_esp_current_result(self):
        ev=evidence();ev["current_result"]="1-2-3"
        with self.assertRaisesRegex(ValueError,"EXACT_EVIDENCE_SCHEMA"):
            joint_entry_distribution(KEY,SCOPE,ev)
    def test_uniform_counts_returns_uniform_entry_mass(self):
        ev=evidence()
        ev["boat_frame_course_observed_counts"]={
            b:{c:6 for c in range(1,7)} for b in range(1,7)}
        ev["same_cohort_six_boat_races_n"]=36
        ev["counts_sha256"]=digest(ev["boat_frame_course_observed_counts"])
        r=joint_entry_distribution(KEY,SCOPE,ev)
        self.assertAlmostEqual(r["ranked_720"][0]["relative_model_mass"],1/720)
        self.assertEqual(r["top10_provisional_course_assignments"][0],[1,2,3,4,5,6])


if __name__=="__main__":
    unittest.main()
