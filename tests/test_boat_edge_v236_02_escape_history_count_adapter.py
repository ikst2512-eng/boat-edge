"""Only fabricated historical race rows: no actual records or result endpoints."""
from copy import deepcopy
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from boat_edge_02_escape_history_count_adapter import build_historical_escape_counts
from boat_edge_02_escape_second_third_research import estimate_escape_second_third

KEY="20261014-12-01"
SCOPE={
    "schema":"BE02_RESEARCH_AGGREGATE_SCOPE_V1", "race_key":KEY,
    "train_end":"20261013", "first_frozen_at":"2026-10-14T10:08:00+09:00",
    "deadline_jst":"10:20", "authorized_training_aggregate":True,
    "source_class":"REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
    "reviewed_permission_evidence_sha256":"a"*64, "source_manifest_sha256":"b"*64,
    "no_target_outcome":True, "formal_fresh_not_used":True,
}
TARGET={
    "schema":"BE02_HISTORICAL_ESCAPE_TRAINING_CONTEXT_V1",
    "scope":"RESEARCH_ONLY_PRE_RESULT", "race_key":KEY, "target_venue":12,
    "target_c1_racer":"r6", "target_c1_motor_epoch":"m6:2026-09",
    "locked_formal_dates":["20261013"], "rights_reviewed_for_historical_training":True,
    "historical_raw_manifest_sha256":"b"*64, "permission_evidence_sha256":"a"*64,
    "training_data_first_git_commit_sha":"c"*40,
    "training_data_first_git_server_time_jst":"2026-10-13T23:10:00+09:00",
    "all_events_are_c1_nige_with_official_final_course":True,
}
MAP={1:6,2:2,3:3,4:4,5:5,6:1}
RACERS={i:f"r{i}" for i in range(1,7)}
MOTORS={i:f"m{i}:2026-09" for i in range(1,7)}


def records():
    out=[]
    cases=[
        ("20260925-12-01",2,3),("20260926-12-02",3,2),
        ("20260927-03-01",4,2),("20260928-12-03",5,2),
        ("20260929-12-04",6,2),("20260930-12-05",2,4),
        ("20261012-12-01",3,4),
    ]
    for key,second,third in cases:
        remaining=[x for x in range(1,7) if x not in (1,second,third)]
        order=[MAP[x] for x in (1,second,third,*remaining)]
        out.append({
            "race_key":key, "venue":int(key.split("-")[1]),
            "official_kimarite":"nige",
            "source_kind":"OFFICIAL_AUTHORIZED_HISTORICAL_FINISH_KIMARITE_AND_ACTUAL_ENTRY",
            "final_actual_course_to_boat":MAP.copy(),
            "official_full_finish_boats":order,
            "racer_id_by_boat":RACERS.copy(), "motor_epoch_by_boat":MOTORS.copy(),
            "result_first_available_at_jst": f"{key[:4]}-{key[4:6]}-{key[6:8]}T22:00:00+09:00",
            "source_raw_sha256":"d"*64,
        })
    return out


def future_evidence(agg):
    return {
        "schema":"BE02_ESCAPE_COURSE1_HISTORY_AND_ENTRY_SCOPE_V1",
        "historical_population":"RESULT_CONFIRMED_ACTUAL_COURSE1_ESCAPE_ONLY",
        "historical_finish_basis":"OFFICIAL_CONFIRMED_KIMARITE_NIGE_AND_ALL_THREE_FINISHERS",
        "pre_result_entry_basis":"OFFICIAL_START_EXHIBITION_PROJECTION_NOT_ACTUAL_ENTRY",
        "predicted_course_to_boat":MAP.copy(),
        "source_snapshot_sha256":"e"*64,
        "historical_count_manifest_sha256":agg["training_count_derivation_sha256"],
        "historical_count_rights_reviewed":True, "historical_cutoff":"20261013",
        "no_target_day_history":True, "six_active_boats_no_scratch":True,
    }


class HistoricalCourseOneNigeAdapter(unittest.TestCase):
    def test_seven_fake_rows_aggregate_and_deterministic_sha(self):
        a=build_historical_escape_counts(SCOPE,TARGET,records())
        self.assertEqual(a,build_historical_escape_counts(SCOPE,TARGET,records()))
        self.assertEqual(a["historical_events_verified_by_code"],7)
        self.assertEqual(a["layer_event_n"],{"national":7,"venue":6,"racer":6,"motor":6})
        self.assertEqual(sum(a["conditional_counts"]["second_by_actual_course"]["national"].values()),7)
        self.assertFalse(a["formal_results_touched"])
        self.assertFalse(a["event_rights_and_first_git_clock_independently_attested_by_code"])
    def test_can_feed_existing_20_way_conditional_no_duplicate_model(self):
        a=build_historical_escape_counts(SCOPE,TARGET,records())
        r=estimate_escape_second_third(KEY,SCOPE,future_evidence(a),a["conditional_counts"])
        self.assertEqual(r["historical_national_escape_event_n"],7)
        self.assertEqual(len(r["conditional_20"]),20)
        self.assertTrue(all(x["boat_combo"].startswith("6-") for x in r["conditional_20"]))
        self.assertFalse(r["full_120_ready"])
        self.assertFalse(r["fresh_accuracy_proven"])
    def test_boat_1_is_not_same_as_course_1_head(self):
        r=records()[0]
        self.assertEqual(r["official_full_finish_boats"][0],6)
        self.assertEqual(r["final_actual_course_to_boat"][1],6)
        self.assertEqual(build_historical_escape_counts(SCOPE,TARGET,records())["historical_events_verified_by_code"],7)
    def test_duplicate_historical_key_rejected(self):
        x=records();x.insert(1,deepcopy(x[0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_HISTORICAL_RACE"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_out_of_order_historical_key_rejected(self):
        x=records();x[0],x[1]=x[1],x[0]
        with self.assertRaisesRegex(ValueError,"HISTORICAL_COHORT_NOT_CANONICALLY_ORDERED"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_formal_result_date_current_and_old_never_accepted(self):
        for date in ("20261001","20261005","20261013"):
            x=records();x[0]["race_key"]=date+"-12-01"
            x.sort(key=lambda row:row["race_key"])
            with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORICAL_EVENT"):
                build_historical_escape_counts(SCOPE,TARGET,x)
    def test_other_formal_day_dynamic_block(self):
        t=deepcopy(TARGET);t["locked_formal_dates"].append("20260926")
        with self.assertRaisesRegex(ValueError,"PROTECTED_FORMAL_HISTORICAL_EVENT"):
            build_historical_escape_counts(SCOPE,t,records())
    def test_false_nige_and_provisional_exhibition_not_accepted_as_actual(self):
        for field,val in [("official_kimarite","sashi"),("source_kind","EXHIBITION_ONLY")]:
            x=records();x[0][field]=val
            with self.assertRaisesRegex(ValueError,"NOT_OFFICIALLY_VERIFIED_COURSE_ONE_NIGE"):
                build_historical_escape_counts(SCOPE,TARGET,x)
    def test_winner_became_boat_one_not_actual_course_one_rejected(self):
        x=records();x[0]["official_full_finish_boats"]=[1,2,3,4,5,6]
        with self.assertRaisesRegex(ValueError,"NIGE_WINNER_NOT_CONFIRMED_ACTUAL_COURSE_ONE"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_invalid_actual_entry_and_bad_finish_not_inferred(self):
        x=records();x[0]["final_actual_course_to_boat"][6]=6
        with self.assertRaisesRegex(ValueError,"ACTUAL_ENTRY_NOT_SIX_PERMUTATION"):
            build_historical_escape_counts(SCOPE,TARGET,x)
        x=records();x[0]["official_full_finish_boats"]=x[0]["official_full_finish_boats"][:3]
        with self.assertRaisesRegex(ValueError,"HISTORICAL_FINISH_NOT_SIX_PERMUTATION"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_historical_source_must_be_available_before_freeze(self):
        x=records();x[-1]["result_first_available_at_jst"]="2026-10-14T10:09:00+09:00"
        with self.assertRaisesRegex(ValueError,"HISTORICAL_EVENT_NOT_AVAILABLE_PRE_FREEZE"):
            build_historical_escape_counts(SCOPE,TARGET,x)
        x=records();x[-1]["result_first_available_at_jst"]="2026-10-12T13:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"PUBLICATION_MUST_HAVE_JST_OFFSET"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_training_source_first_git_pub_also_before_freeze(self):
        t=deepcopy(TARGET);t["training_data_first_git_server_time_jst"]="2026-10-14T10:09:00+09:00"
        with self.assertRaisesRegex(ValueError,"TRAINING_NOT_PUBLISHED_BEFORE_FREEZE"):
            build_historical_escape_counts(SCOPE,t,records())
    def test_disallow_historical_after_training_cutoff(self):
        x=records();x[-1]["race_key"]="20261014-12-01"
        with self.assertRaisesRegex(ValueError,"HISTORICAL_EVENT_AFTER_TRAINING_CUTOFF"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_permission_provenance_and_rights_hard_fail(self):
        t=deepcopy(TARGET);t["permission_evidence_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"PERMISSION_PROVENANCE_MISMATCH"):
            build_historical_escape_counts(SCOPE,t,records())
        t=deepcopy(TARGET);t["rights_reviewed_for_historical_training"]=False
        with self.assertRaisesRegex(ValueError,"HISTORICAL_RIGHTS"):
            build_historical_escape_counts(SCOPE,t,records())
    def test_missing_racer_and_motor_layers_stay_missing(self):
        t=deepcopy(TARGET);t["target_c1_racer"]=None;t["target_c1_motor_epoch"]=None
        x=build_historical_escape_counts(SCOPE,t,records())
        self.assertIsNone(x["conditional_counts"]["second_by_actual_course"]["racer"])
        self.assertIsNone(x["conditional_counts"]["second_by_actual_course"]["motor"])
    def test_motor_requires_racer_and_target_venue_matches_race(self):
        t=deepcopy(TARGET);t["target_c1_racer"]=None
        with self.assertRaisesRegex(ValueError,"MOTOR_LAYER_REQUIRES_RACER"):
            build_historical_escape_counts(SCOPE,t,records())
        t=deepcopy(TARGET);t["target_venue"]=13
        with self.assertRaisesRegex(ValueError,"TARGET_VENUE_AND_RACE_KEY_MISMATCH"):
            build_historical_escape_counts(SCOPE,t,records())
    def test_missing_fields_never_imputed(self):
        x=records();del x[0]["final_actual_course_to_boat"]
        with self.assertRaisesRegex(ValueError,"EXACT_HISTORICAL_ROW_SCHEMA"):
            build_historical_escape_counts(SCOPE,TARGET,x)
        x=records();del x[0]["motor_epoch_by_boat"][6]
        with self.assertRaisesRegex(ValueError,"SIX_IDENTITIES_REQUIRED"):
            build_historical_escape_counts(SCOPE,TARGET,x)
    def test_empty_history_does_not_generate_pseudocounts(self):
        with self.assertRaisesRegex(ValueError,"AUTHORIZED_HISTORICAL_COHORT_EMPTY"):
            build_historical_escape_counts(SCOPE,TARGET,[])
    def test_current_target_not_formal(self):
        t=deepcopy(TARGET);t["race_key"]="20261001-12-01"
        with self.assertRaisesRegex(ValueError,"FORMAL_FRESH_EXCLUDED"):
            build_historical_escape_counts(SCOPE,t,records())
    def test_unobserved_national_second_course_rejected_not_imputed(self):
        x=[r for r in records() if r["official_full_finish_boats"][1] != MAP[6]]
        with self.assertRaisesRegex(ValueError,"UNOBSERVED_SECOND_COURSE_THIRD_DISTRIBUTION"):
            build_historical_escape_counts(SCOPE,TARGET,x)


if __name__ == "__main__":
    unittest.main()
