"""Only SYNTHETIC historical exhibition/final-entry pairs, no real outcomes."""
from copy import deepcopy
from datetime import date, timedelta
import unittest
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from boat_edge_02_exhibition_to_actual_entry_research import (
    estimate_exhibition_conditioned_entry, ID, MIN_NATIONAL, MIN_VENUE,
)
from boat_edge_02_joint_entry_permutation_research import digest

KEY="20261014-12-01"
EXHIB={1:2,2:1,3:3,4:4,5:5,6:6}
SCOPE=dict(schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1",race_key=KEY,
    train_end="20261013",first_frozen_at="2026-10-14T10:08:00+09:00",
    deadline_jst="10:20",authorized_training_aggregate=True,
    source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
    reviewed_permission_evidence_sha256="a"*64,
    source_manifest_sha256="b"*64,no_target_outcome=True,
    formal_fresh_not_used=True)
EVIDENCE=dict(schema="BE02_PAIRED_EXHIBITION_ACTUAL_TRAIN_V1",
    target_race_key=KEY,target_venue=12,target_exhibition_course_by_boat=EXHIB,
    target_exhibition_mapping_sha256=digest(EXHIB),
    target_exhibition_first_seen_jst="2026-10-14T10:04:00+09:00",
    training_source_manifest_sha256="b"*64,permission_evidence_sha256="a"*64,
    rights_reviewed_for_historic_pairs=True,history_cutoff="20261013",
    current_locked_formal_dates=["20261001","20261005","20261013"],
    historic_course_final_is_official=True,historic_exhibition_is_pre_result=True,
    no_target_actual_course_or_outcome=True)


def rows():
    out=[]
    start=date(2026,8,1)
    for i in range(40):
        dt=start+timedelta(days=i)
        d=dt.strftime("%Y%m%d")
        iso=dt.isoformat()
        venue=3 if i%5==0 else 12
        exhibit={b:b for b in range(1,7)}
        final=dict(exhibit)
        if i%4==0:
            final[1],final[2]=2,1
        out.append(dict(
            race_key=f"{d}-{venue:02d}-01",venue=venue,
            exhibition_course_by_boat=exhibit,
            actual_course_by_boat=final,
            exhibition_first_seen_jst=f"{iso}T10:00:00+09:00",
            race_deadline_jst=f"{iso}T11:00:00+09:00",
            final_actual_course_first_seen_jst=f"{iso}T13:00:00+09:00",
            exhibition_source_sha256="c"*64,
            final_course_source_sha256="d"*64,
            has_six_active_boats_no_scratch=True,
            source_licensed_for_research=True))
    return out


def trial(rows_=None, evid=None, scope=None):
    return estimate_exhibition_conditioned_entry(
        KEY,scope or SCOPE,evid or EVIDENCE,rows_ if rows_ is not None else rows())


class PairedExhibitionFinalEntry(unittest.TestCase):
    def test_relative_transition_scopes_and_shrinks_from_real_fake_pairs(self):
        r=trial()
        self.assertEqual(r["model_id"],ID)
        self.assertEqual(r["historical_national_paired_events_n"],40)
        self.assertEqual(r["historical_same_venue_paired_events_n"],32)
        self.assertEqual(r["distinct_national_observed_transition_patterns"],2)
        self.assertEqual(r["distinct_venue_observed_transition_patterns"],2)
        self.assertEqual(len(r["ranked_720"]),720)
        self.assertEqual(r["ranked_720"][0]["course_by_boat"],[2,1,3,4,5,6])
        self.assertAlmostEqual(sum(x["relative_model_mass"] for x in r["ranked_720"]),1)
        self.assertEqual(sum(x["relative_model_mass"]>0 for x in r["ranked_720"]),2)
        self.assertFalse(r["full_conditional_entry_posterior_calibrated"])
        self.assertFalse(r["historic_transition_counts_conditioned_on_exact_exhibition_pattern"])
        self.assertTrue(r["target_exhibition_permutation_used_in_mapping"])
        self.assertFalse(r["production_eligible"])
        self.assertFalse(r["formal_results_read"])
    def test_each_boat_each_course_valid_and_marginals(self):
        r=trial()
        self.assertEqual(len({tuple(v["course_by_boat"]) for v in r["ranked_720"]}),720)
        for row in r["ranked_720"]:
            self.assertEqual(set(row["course_by_boat"]),set(range(1,7)))
        for b in range(1,7):
            self.assertAlmostEqual(sum(r["course_marginal_by_boat"][str(b)].values()),1)
        for c in range(1,7):
            self.assertAlmostEqual(sum(r["course_marginal_by_boat"][str(b)][str(c)]
                                       for b in range(1,7)),1)
    def test_deterministic_sha_and_no_input_mutation(self):
        x=rows()
        orig=deepcopy(x)
        one=trial(x)
        self.assertEqual(one,trial(x))
        self.assertEqual(x,orig)
        self.assertEqual(len(one["observed_paired_counts_sha256"]),64)
    def test_current_exhibition_swap_relabels_all_future_course_but_not_historic(self):
        e=deepcopy(EVIDENCE)
        e["target_exhibition_course_by_boat"]={b:b for b in range(1,7)}
        e["target_exhibition_mapping_sha256"]=digest(e["target_exhibition_course_by_boat"])
        a,b=trial(),trial(evid=e)
        self.assertNotEqual(a["ranked_720"][0]["course_by_boat"],
                            b["ranked_720"][0]["course_by_boat"])
        self.assertEqual(a["observed_paired_counts_sha256"]==b["observed_paired_counts_sha256"],False)
        self.assertEqual(a["historical_national_paired_events_n"],b["historical_national_paired_events_n"])
    def test_no_proof_of_two_distinct_historic_six_boat_orders(self):
        x=rows();x[0]["actual_course_by_boat"][2]=2
        with self.assertRaisesRegex(ValueError,"SIX_ACTUAL_VS_EXHIBITION_PERMUTATION_REQUIRED"):
            trial(x)
        x=rows();x[0]["exhibition_course_by_boat"][6]=None
        with self.assertRaisesRegex(ValueError,"SIX_ACTUAL_VS_EXHIBITION_PERMUTATION_REQUIRED"):
            trial(x)
    def test_reject_scratches_or_unlicensed_old_results(self):
        x=rows();x[0]["has_six_active_boats_no_scratch"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_SCRATCH"):
            trial(x)
        x=rows();x[0]["source_licensed_for_research"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_SCRATCH"):
            trial(x)
    def test_historic_exhibition_must_precede_actual_and_actual_precede_target(self):
        x=rows();x[0]["final_actual_course_first_seen_jst"]="2026-08-01T09:50:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORIC_ASOF_NOT_PROVED"):
            trial(x)
        x=rows();x[-1]["final_actual_course_first_seen_jst"]="2026-10-14T10:09:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORIC_ASOF_NOT_PROVED"):
            trial(x)
    def test_historic_exhibition_predeadline_not_same_day_result_proxy(self):
        x=rows()
        x[0]["exhibition_first_seen_jst"]="2026-08-01T11:01:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORIC_ASOF_NOT_PROVED"):
            trial(x)
        x=rows()
        x[0]["final_actual_course_first_seen_jst"]="2026-08-01T10:59:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORIC_ASOF_NOT_PROVED"):
            trial(x)
    def test_training_history_publication_must_be_before_training_cutoff_date(self):
        x=rows()
        x[0]["final_actual_course_first_seen_jst"]="2026-10-14T00:02:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORIC_ASOF_NOT_PROVED"):
            trial(x)
    def test_deadline_is_required_and_not_inferred(self):
        x=rows();del x[0]["race_deadline_jst"]
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_HISTORIC_ROW_SCHEMA"):
            trial(x)

    def test_bad_jst_offsets_rejected_not_coerced(self):
        x=rows();x[0]["exhibition_first_seen_jst"]="2026-08-01T01:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_JST_OFFSET_REQUIRED"):
            trial(x)
    def test_cannot_include_known_or_dynamic_formal_dates_in_training(self):
        for protected in ("20261001","20261005","20261013"):
            x=rows()
            x[-1]["race_key"]=protected+"-12-01"
            x[-1]["venue"]=12
            with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORIC_RACE"):
                trial(x)
        e=deepcopy(EVIDENCE)
        e["current_locked_formal_dates"].append("20260801")
        x=rows()
        with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORIC_RACE"):
            trial(x,e)
    def test_target_day_result_not_admitted_in_historic_rows(self):
        x=rows();x[-1]["race_key"]="20261014-12-01";x[-1]["venue"]=12
        with self.assertRaisesRegex(ValueError,"HISTORY_TARGET_DAY_LEAK"):
            trial(x)
    def test_historical_pairs_strictly_sorted_and_unique(self):
        x=rows();x[1]=deepcopy(x[0])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNSORTED"):
            trial(x)
        x=rows();x[0],x[1]=x[1],x[0]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_UNSORTED"):
            trial(x)
    def test_no_unseen_venue_claim_from_national_only(self):
        x=rows()
        x=[r for r in x if r["venue"]!=12]
        with self.assertRaisesRegex(ValueError,"COHORT_TOO_SPARSE"):
            trial(x)
    def test_target_exhibition_must_be_present_before_freeze(self):
        e=deepcopy(EVIDENCE)
        e["target_exhibition_first_seen_jst"]="2026-10-14T10:09:00+09:00"
        with self.assertRaisesRegex(ValueError,"TARGET_EXHIBITION_NOT_AVAILABLE"):
            trial(evid=e)
    def test_source_and_rights_manifest_attested_only_not_verified_by_code(self):
        e=deepcopy(EVIDENCE)
        e["permission_evidence_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_SOURCE_SHA_MISMATCH"):
            trial(evid=e)
        e=deepcopy(EVIDENCE)
        e["rights_reviewed_for_historic_pairs"]=False
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_RIGHTS_AND_TEMPORAL"):
            trial(evid=e)
        x=trial()
        self.assertFalse(x["rights_sha_and_first_seen_independently_authenticated"])
    def test_no_additional_target_or_outcome_fields(self):
        e=deepcopy(EVIDENCE)
        e["current_race_actual_course"]={b:b for b in range(1,7)}
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_EXACT_EVIDENCE"):
            trial(evid=e)
        x=rows();x[0]["finish"]="1-2-3"
        with self.assertRaisesRegex(ValueError,"PAIRED_ENTRY_HISTORIC_ROW_SCHEMA"):
            trial(x)
    def test_protected_target_scope_refused(self):
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
            estimate_exhibition_conditioned_entry(
                "20261001-12-01",SCOPE,EVIDENCE,rows())


if __name__=="__main__":
    unittest.main()
