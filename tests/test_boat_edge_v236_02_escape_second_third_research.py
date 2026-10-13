"""Only fabricated aggregate counts: no actual race/result/data files are opened."""
from __future__ import annotations

from copy import deepcopy
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_02_escape_second_third_research import estimate_escape_second_third

KEY = "20261014-12-01"
SCOPE = dict(
    schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1",
    race_key=KEY, train_end="20261013",
    first_frozen_at="2026-10-14T10:00:00+09:00", deadline_jst="10:20",
    authorized_training_aggregate=True,
    source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
    reviewed_permission_evidence_sha256="a"*64,
    source_manifest_sha256="b"*64,
    no_target_outcome=True, formal_fresh_not_used=True,
)
EVIDENCE = dict(
    schema="BE02_ESCAPE_COURSE1_HISTORY_AND_ENTRY_SCOPE_V1",
    historical_population="RESULT_CONFIRMED_ACTUAL_COURSE1_ESCAPE_ONLY",
    historical_finish_basis="OFFICIAL_CONFIRMED_KIMARITE_NIGE_AND_ALL_THREE_FINISHERS",
    pre_result_entry_basis="OFFICIAL_START_EXHIBITION_PROJECTION_NOT_ACTUAL_ENTRY",
    predicted_course_to_boat={i: i for i in range(1,7)},
    source_snapshot_sha256="c"*64,
    historical_count_manifest_sha256="d"*64,
    historical_count_rights_reviewed=True,
    historical_cutoff="20261013",
    no_target_day_history=True,
    six_active_boats_no_scratch=True,
)


def synthetic_counts():
    """Internally consistent fake cohort with 5 course-2..6 second outcomes."""
    national={2:30,3:20,4:10,5:7,6:3}
    venue={2:6,3:4,4:2,5:1,6:1}
    second=dict(national=national,venue=venue,racer=None,motor=None)
    third={}
    for s in range(2,7):
        target = next(t for t in range(2,7) if t!=s)
        third[s]={}
        for layer in ("national","venue"):
            counts=second[layer]
            third[s][layer]={t:(counts[s] if t==target else 0) for t in range(2,7) if t!=s}
        third[s]["racer"]=None
        third[s]["motor"]=None
    return {"second_by_actual_course":second,"third_by_actual_course_given_second":third}


class CourseOneEscapeResearch(unittest.TestCase):
    def test_escape_is_twenty_conditional_outcomes_not_fake_120(self):
        r=estimate_escape_second_third(KEY,SCOPE,EVIDENCE,synthetic_counts())
        self.assertEqual(len(r["conditional_20"]),20)
        self.assertEqual(len(r["conditional_top10"]),10)
        self.assertAlmostEqual(sum(x["conditional_relative_mass"] for x in r["conditional_20"]),1)
        self.assertEqual(r["historical_national_escape_event_n"],70)
        self.assertFalse(r["full_120_ready"])
        self.assertIsNone(r["world_prior_probability"])
        self.assertFalse(r["promote_to_site"])
    def test_start_exhibition_projection_not_boat1(self):
        e=deepcopy(EVIDENCE)
        e["predicted_course_to_boat"]={1:6,2:2,3:3,4:4,5:5,6:1}
        r=estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
        self.assertEqual(r["conditional_head_boat_projection"],6)
        self.assertTrue(all(x["boat_combo"].startswith("6-") for x in r["conditional_20"]))
        self.assertTrue(r["entry_is_provisional_not_verified_actual"])
    def test_reproducible_without_data_access(self):
        a=estimate_escape_second_third(KEY,SCOPE,EVIDENCE,synthetic_counts())
        b=estimate_escape_second_third(KEY,SCOPE,EVIDENCE,synthetic_counts())
        self.assertEqual(a,b)
        self.assertEqual(len({x["boat_combo"] for x in a["conditional_20"]}),20)
    def test_lose_actual_course_proof_is_rejected(self):
        e=deepcopy(EVIDENCE)
        e["historical_population"]="BOAT1_WIN_INSTEAD_OF_COURSE1_ESCAPE"
        with self.assertRaisesRegex(ValueError,"ESCAPE_KIMARITE"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
        e=deepcopy(EVIDENCE)
        e["historical_finish_basis"]="WIN_METHOD_UNVERIFIED"
        with self.assertRaisesRegex(ValueError,"ESCAPE_KIMARITE"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
    def test_start_exhibition_never_marked_actual(self):
        e=deepcopy(EVIDENCE)
        e["pre_result_entry_basis"]="ACTUAL_COURSE"
        with self.assertRaisesRegex(ValueError,"ENTRY_SEMANTICS"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
    def test_incomplete_six_entrant_mapping_and_scratch(self):
        e=deepcopy(EVIDENCE)
        e["predicted_course_to_boat"]={1:1,2:2,3:3,4:4,5:5,6:5}
        with self.assertRaisesRegex(ValueError,"SIX_PERMUTATION"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
        e=deepcopy(EVIDENCE)
        e["six_active_boats_no_scratch"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_PRE_RESULT"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
    def test_denominators_must_match_second_and_third(self):
        c=synthetic_counts()
        c["third_by_actual_course_given_second"][2]["national"][3]-=1
        with self.assertRaisesRegex(ValueError,"DENOMINATOR"):
            estimate_escape_second_third(KEY,SCOPE,EVIDENCE,c)
    def test_missing_some_layer_is_not_imputed(self):
        c=synthetic_counts()
        c["second_by_actual_course"]["venue"]=None
        for s in range(2,7):
            c["third_by_actual_course_given_second"][s]["venue"]=None
        r=estimate_escape_second_third(KEY,SCOPE,EVIDENCE,c)
        self.assertEqual(r["used_layers"]["second"],["national"])
        self.assertEqual(r["used_layers"]["third_by_second_course"]["2"],["national"])
    def test_no_national_cohort_rejected(self):
        c=synthetic_counts()
        c["second_by_actual_course"]["national"]=None
        for s in range(2,7):
            c["third_by_actual_course_given_second"][s]["national"]=None
        with self.assertRaisesRegex(ValueError,"NATIONAL_ESCAPE_COHORT"):
            estimate_escape_second_third(KEY,SCOPE,EVIDENCE,c)
    def test_target_day_history_and_rights_rejected(self):
        e=deepcopy(EVIDENCE);e["historical_cutoff"]="20261014"
        with self.assertRaisesRegex(ValueError,"HISTORICAL_CUTOFF"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
        e=deepcopy(EVIDENCE);e["historical_count_rights_reviewed"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS_OR_PRE_RESULT"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
        e=deepcopy(EVIDENCE);e["historical_count_manifest_sha256"]="no"
        with self.assertRaisesRegex(ValueError,"SHA_REQUIRED"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())
    def test_formal_100_blocked_by_common_scope(self):
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
            estimate_escape_second_third("20261001-12-01",SCOPE,EVIDENCE,synthetic_counts())
    def test_missing_third_cohort_is_not_silently_completed(self):
        c=synthetic_counts()
        c["third_by_actual_course_given_second"][2]["venue"]=None
        with self.assertRaisesRegex(ValueError,"DENOMINATOR"):
            estimate_escape_second_third(KEY,SCOPE,EVIDENCE,c)
    def test_no_extra_data_fields_even_if_result_metadata(self):
        e=deepcopy(EVIDENCE);e["result"]="1-2-3"
        with self.assertRaisesRegex(ValueError,"EXPLICIT_ESCAPING_COURSE_PROOF"):
            estimate_escape_second_third(KEY,SCOPE,e,synthetic_counts())


if __name__=="__main__":
    unittest.main()
