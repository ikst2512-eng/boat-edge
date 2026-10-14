"""Fixture-only pre-result parity and fail-closed evidence checks.

No file/network reads, authorized outcome inputs, or formal Fresh tests.
"""
import copy
from datetime import datetime, timezone, timedelta
import itertools
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_02_matched_ten_pre_result import prepare_matched_ten

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 14, 10, 8, tzinfo=JST)
KEY = "20261014-12-01"
CONTEXT = {
    "scope": "SITE_RESEARCH_PRE_RESULT_NOT_FORMAL",
    "race_key": KEY,
    "deadline_jst": "10:20",
    "target_source_sha256": "a"*64,
    "entry_mapping_sha256": "b"*64,
    "source_permission_evidence_sha256": "c"*64,
    "parent_model_id": "FIXTURE_PARENT",
    "candidate_model_id": "FIXTURE_CANDIDATE",
    "parent_training_end": "20261013",
    "candidate_training_end": "20261013",
    "no_target_outcome": True,
    "no_formal_fresh": True,
}


FORMAL_STATUS = {
    "schema_version": "boat-edge-formal-status-v2",
    "asOf": "2026-10-14T10:00:00+09:00",
    "target_date": "2026-10-15",
    "last_cohort": {"date": "2026-10-05"},
    "formalFirst100": {"races": 0},
    "guards": {"results_seen": False, "unlock": False,
               "scoring": False, "RESULT_UNLOCK_TOKEN": None},
}


def paired_checked(context, parent, candidate, when, formal_status=None):
    return prepare_matched_ten(
        context, parent, candidate, when,
        FORMAL_STATUS if formal_status is None else formal_status)


def documents():
    combos = ["-".join(map(str, p)) for p in itertools.permutations(range(1, 7), 3)]
    def doc(model, reverse=False):
        vals = {combo: (i+1 if reverse else 120-i) for i, combo in enumerate(combos)}
        total = sum(vals.values())
        ordered = sorted(vals, key=lambda x: (-vals[x], x))
        return {
            "model_id": model, "race_key": KEY,
            "target_source_sha256": CONTEXT["target_source_sha256"],
            "entry_mapping_sha256": CONTEXT["entry_mapping_sha256"],
            "ranked_120": [
                {"boat_combo": combo, "relative_model_mass": vals[combo]/total}
                for combo in ordered
            ],
        }
    return doc("FIXTURE_PARENT"), doc("FIXTURE_CANDIDATE", True)


class MatchedTenPreResult(unittest.TestCase):
    def test_two_models_exactly_ten_same_budget_and_deterministic(self):
        parent,candidate = documents()
        one = paired_checked(CONTEXT, parent,candidate,NOW)
        two = paired_checked(CONTEXT, parent,candidate,NOW)
        self.assertEqual(one,two)
        self.assertEqual(len(one["parent_top10"]), 10)
        self.assertEqual(len(one["candidate_top10"]), 10)
        for name, ranked in (("parent", parent), ("candidate", candidate)):
            original = [r["boat_combo"] for r in ranked["ranked_120"]]
            self.assertEqual(one[name + "_top3"], original[:3])
            self.assertEqual(one[name + "_top5"], original[:5])
            self.assertEqual(one[name + "_top10"], original[:10])
            self.assertEqual(one[name + "_top3"], one[name + "_top5"][:3])
            self.assertEqual(one[name + "_top5"], one[name + "_top10"][:5])
        self.assertNotEqual(one["parent_top10"], one["candidate_top10"])
        self.assertEqual(one["per_model_virtual_budget_yen"], 10000)
        self.assertFalse(one["scoring_authorized"])
        self.assertFalse(one["production_eligible"])
        self.assertFalse(one["first_git_commit_time_independently_verified"])
    def test_all_120_required_no_legacy_top10_padding(self):
        p,c=documents();p["ranked_120"]=p["ranked_120"][:10]
        with self.assertRaisesRegex(ValueError,"REQUIRE_FULL_120"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_exact_same_race_and_data_and_entry_sha(self):
        p,c=documents();c["target_source_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"PAIRED_SOURCE_MISMATCH"):
            paired_checked(CONTEXT,p,c,NOW)
        p,c=documents();c["entry_mapping_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"PAIRED_SOURCE_MISMATCH"):
            paired_checked(CONTEXT,p,c,NOW)
        p,c=documents();p["race_key"]="20261014-12-02"
        with self.assertRaisesRegex(ValueError,"PAIRED_SOURCE_MISMATCH"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_no_duplicate_ticket(self):
        p,c=documents();c["ranked_120"][1] = copy.deepcopy(c["ranked_120"][0])
        with self.assertRaisesRegex(ValueError,"INVALID_OR_REPEATED_BOAT_COMBO"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_total_not_one_or_negative_mass(self):
        p,c=documents();c["ranked_120"][0]["relative_model_mass"]+=0.2
        with self.assertRaisesRegex(ValueError,"NON_NORMALIZED"):
            paired_checked(CONTEXT,p,c,NOW)
        p,c=documents();c["ranked_120"][0]["relative_model_mass"]=-0.1
        with self.assertRaisesRegex(ValueError,"INVALID_MASS"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_sorted_probability_ranking_required(self):
        p,c=documents();c["ranked_120"][:2]=c["ranked_120"][1::-1]
        with self.assertRaisesRegex(ValueError,"RANK_ORDER"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_outcome_odds_and_extra_keys_are_forbidden(self):
        p,c=documents();c["race_result"]="1-2-3"
        with self.assertRaisesRegex(ValueError,"DOCUMENT_SCHEMA"):
            paired_checked(CONTEXT,p,c,NOW)
        p,c=documents();c["ranked_120"][0]["odds"]=30.0
        with self.assertRaisesRegex(ValueError,"ROW_SCHEMA"):
            paired_checked(CONTEXT,p,c,NOW)
    def test_after_deadline_and_less_than_two_minutes_rejected(self):
        p,c=documents()
        for when in (datetime(2026,10,14,10,21,tzinfo=JST),
                     datetime(2026,10,14,10,19,tzinfo=JST),
                     datetime(2026,10,14,10,1,tzinfo=JST)):
            with self.assertRaisesRegex(ValueError,"NO_LIVE_FINAL_WINDOW"):
                paired_checked(CONTEXT,p,c,when)
    def test_bad_timezone_and_train_leakage(self):
        p,c=documents()
        with self.assertRaisesRegex(ValueError,"NO_LIVE_FINAL_WINDOW"):
            paired_checked(CONTEXT,p,c,NOW.astimezone(timezone.utc))
        d=copy.deepcopy(CONTEXT);d["candidate_training_end"]="20261014"
        with self.assertRaisesRegex(ValueError,"TRAINING_LEAKS"):
            paired_checked(d,p,c,NOW)
    def test_formal_race_never_admitted(self):
        p,c=documents()
        # Conservative fixed denial is intentionally earlier than clock and
        # document validation; no protected target can pass this pure contract.
        for day in ("20261001", "20261005", "20261013"):
            with self.subTest(day=day):
                d=copy.deepcopy(CONTEXT);d["race_key"]=day+"-12-01"
                with self.assertRaisesRegex(ValueError,"FORMAL_TARGET_EXCLUDED"):
                    paired_checked(d,p,c,NOW)
    def test_live_formal_date_and_previous_cohort_cannot_be_relabelled_site(self):
        p,c = documents()
        for date_field in ("target_date", "last_cohort"):
            status = copy.deepcopy(FORMAL_STATUS)
            if date_field == "target_date":
                status["target_date"] = "2026-10-14"
            else:
                status["last_cohort"]["date"] = "2026-10-14"
            with self.subTest(field=date_field):
                with self.assertRaisesRegex(ValueError, "CURRENT_FORMAL_TARGET_DATE_EXCLUDED"):
                    paired_checked(CONTEXT,p,c,NOW,status)

    def test_stale_or_unlocked_current_formal_state_is_not_a_valid_site_shadow(self):
        p,c = documents()
        for patch, expected in (
                ({"asOf": "2026-10-13T23:59:00+09:00"}, "NOT_ASOF_TARGET_DAY"),
                ({"asOf": "2026-10-14T10:09:00+09:00"}, "NOT_ASOF_TARGET_DAY"),
                ({"target_date": "nonsense"}, "PROTECTED_DATES_INVALID"),
                ({"last_cohort": {}}, "PROTECTED_DATES_INVALID"),
                ({"formalFirst100": {"races": 1}}, "FORMAL_LOCK_NOT_CONFIRMED"),
                ({"guards": {"results_seen": True, "unlock": False,
                             "scoring": False, "RESULT_UNLOCK_TOKEN": None}},
                 "FORMAL_LOCK_NOT_CONFIRMED"),
        ):
            status = copy.deepcopy(FORMAL_STATUS)
            status.update(patch)
            with self.subTest(patch=patch):
                with self.assertRaisesRegex(ValueError, expected):
                    paired_checked(CONTEXT,p,c,NOW,status)
        with self.assertRaisesRegex(ValueError, "CURRENT_FORMAL_STATUS_REQUIRED"):
            prepare_matched_ten(CONTEXT,p,c,NOW,None)

    def test_no_permission_no_pre_result_no_model_parity(self):
        p,c=documents()
        d=copy.deepcopy(CONTEXT);d["source_permission_evidence_sha256"]=""
        with self.assertRaisesRegex(ValueError,"SOURCE_AND_PERMISSION"):
            paired_checked(d,p,c,NOW)
        d=copy.deepcopy(CONTEXT);d["no_target_outcome"]=False
        with self.assertRaisesRegex(ValueError,"PRE_RESULT_SCOPE"):
            paired_checked(d,p,c,NOW)
        d=copy.deepcopy(CONTEXT);d["candidate_model_id"]="FIXTURE_PARENT"
        with self.assertRaisesRegex(ValueError,"TWO_DISTINCT_MODEL"):
            paired_checked(d,p,c,NOW)
    def test_unchanged_parent_candidate_hashes_and_picks(self):
        p,c=documents()
        p_orig=copy.deepcopy(p);c_orig=copy.deepcopy(c)
        out=paired_checked(CONTEXT,p,c,NOW)
        self.assertEqual((p,c),(p_orig,c_orig))
        self.assertEqual(len(out["parent_ranked_120_sha256"]),64)
        self.assertNotEqual(out["parent_ranked_120_sha256"],out["candidate_ranked_120_sha256"])


if __name__ == "__main__":
    unittest.main()
