"""V404 offline fixture tests: past-only course stats, never Formal Fresh."""
import csv
import hashlib
import io
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import COLUMNS  # noqa: E402
from boat_edge_v404_asof_history_features import MODEL, snapshot  # noqa: E402


def one_race(key, published, courses=None, finishes=None, racer_start=4501):
    courses = courses or [1, 2, 3, 4, 5, 6]
    finishes = finishes or [1, 2, 3, 4, 5, 6]
    return [
        {
            "race_key": key, "boat": str(i), "racer_id": str(racer_start + i - 1),
            "actual_course": str(courses[i-1]), "finish": str(finishes[i-1]),
            "published_at": published
        }
        for i in range(1, 7)
    ]


def history(records):
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in records:
        w.writerow(r)
    raw = f.getvalue().encode("utf-8")
    manifest = {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "source_name": "SYNTHETIC_FIXTURE_ONLY",
        "source_locator": "local:fixture",
        "rights_evidence": "test-not-actual-permission",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": "test_only",
    }
    return raw, manifest


def target(key="202609300103", deadline="2026-09-30T08:35:00+09:00"):
    return {
        "schema": "BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1",
        "race_key": key,
        "deadline_jst": deadline,
        "entries": [{"boat": i, "racer_id": str(4500 + i)} for i in range(1, 7)]
    }


class AsOfResearchFixtureTests(unittest.TestCase):
    def setUp(self):
        old = one_race("202110010101", "2021-10-01T22:00:00+09:00")
        within_three = one_race("202509300101", "2025-09-30T21:00:00+09:00",
                                racer_start=5001)
        yesterday = one_race("202609290101", "2026-09-29T21:00:00+09:00",
                             courses=[2, 1, 3, 4, 5, 6])
        today_early = one_race("202609300101", "2026-09-30T08:00:00+09:00")
        today_late = one_race("202609300102", "2026-09-30T15:00:00+09:00")
        same_target = one_race("202609300103", "2026-09-30T09:00:00+09:00")
        self.raw, self.manifest = history(
            old + within_three + yesterday + today_early + today_late + same_target
        )
        self.target = target()

    def build(self, obj=None, raw=None, manifest=None):
        return snapshot(self.raw if raw is None else raw,
                        self.manifest if manifest is None else manifest,
                        self.target if obj is None else obj)

    def test_strictly_prior_history_only(self):
        r = self.build()
        self.assertEqual(r["historical_races_eligible_before_target"], 4)
        self.assertEqual(r["historical_races_not_yet_available"], 1)
        self.assertEqual(r["same_target_outcome_excluded"], 1)
        self.assertTrue(r["actual_course_of_target_not_observed_or_inferred"])
        self.assertFalse(r["accuracy_improvement_proven"])
        self.assertFalse(r["target_b_roster_historic_predeadline_capture_verified"])
        self.assertEqual(r["source_sha256"], self.manifest["csv_sha256"])

    def test_five_year_old_data_not_in_90_days(self):
        r = self.build()
        course = r["national_actual_course_counts"]["1"]
        self.assertEqual(course["90"]["entries"], 2)
        self.assertEqual(course["365"]["entries"], 2)
        self.assertEqual(course["1826"]["entries"], 4)


    def test_exact_90_365_1095_day_boundaries_including_earlier_today(self):
        from datetime import date, timedelta
        end = date(2026, 9, 30)
        # Oldest synthetic record is 2021-10-01, within the formal-safe window.
        ages = [0, 89, 90, 364, 365, 1094, 1095, 1825]
        rows = []
        for age in ages:
            d = end - timedelta(days=age)
            published = d.isoformat() + ("T07:00:00+09:00" if age == 0
                                         else "T21:00:00+09:00")
            rows += one_race(d.strftime("%Y%m%d") + "0101", published)
        rows.sort(key=lambda r: (r["race_key"], int(r["boat"])))
        raw, man = history(rows)
        result = self.build(raw=raw, manifest=man)
        counts = result["national_actual_course_counts"]["1"]
        self.assertEqual([counts[str(w)]["entries"] for w in (90,365,1095,1826)],
                         [2,4,6,8])
        self.assertEqual(result["historical_races_eligible_before_target"], 8)

    def test_recency_censored_on_target(self):
        r = self.build()
        self.assertEqual(r["history_max_date"], "2026-09-30")
        self.assertEqual(r["history_min_date"], "2021-10-01")
        self.assertEqual(r["rolling_windows_days"], [90,365,1095,1826])

    def test_actual_course_counts_not_assumed_frame(self):
        r = self.build()
        course2 = r["racer_actual_course_counts_by_boat"]["1"]["course_counts"]["2"]
        self.assertEqual(course2["90"]["entries"], 1)
        self.assertEqual(course2["90"]["second"], 0)
        self.assertEqual(course2["90"]["first"], 1)

    def test_non_target_racer_is_not_selected(self):
        r = self.build()
        a=r["racer_actual_course_counts_by_boat"]["1"]["course_counts"]["1"]
        self.assertEqual(a["365"]["entries"], 1)
        self.assertEqual(a["1826"]["entries"], 2)

    def test_empty_history_valid_and_missing_not_imputed(self):
        raw, m = history([])
        r=self.build(raw=raw,manifest=m)
        self.assertEqual(r["historical_races_eligible_before_target"], 0)
        self.assertEqual(r["racer_actual_course_counts_by_boat"]["1"]["course_counts"]["1"]["90"]["entries"],0)
        self.assertIsNone(r["history_min_date"])

    def test_deterministic_serialization(self):
        a = json.dumps(self.build(), sort_keys=True,ensure_ascii=False)
        b = json.dumps(self.build(), sort_keys=True,ensure_ascii=False)
        self.assertEqual(a,b)

    def test_manifest_tamper_rejected(self):
        m=deepcopy(self.manifest)
        m["csv_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError, "RAW_HISTORY_SHA256_MISMATCH"):
            self.build(manifest=m)

    def test_target_outcome_field_rejected(self):
        t=deepcopy(self.target)
        t["entries"][0]["finish"]=1
        with self.assertRaisesRegex(ValueError, "TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE"):
            self.build(obj=t)

    def test_target_actual_course_field_rejected(self):
        t=deepcopy(self.target)
        t["entries"][0]["actual_course"]=1
        with self.assertRaisesRegex(ValueError, "TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE"):
            self.build(obj=t)

    def test_b_schema_invalid_rejected(self):
        t=deepcopy(self.target)
        t["schema"]="some-other-schema"
        with self.assertRaisesRegex(ValueError, "EXACT_B_ONLY_TARGET_REQUIRED"):
            self.build(obj=t)

    def test_duplicate_target_racer_rejected(self):
        t=deepcopy(self.target)
        t["entries"][1]["racer_id"]="4501"
        with self.assertRaisesRegex(ValueError, "TARGET_REQUIRES_SIX_DISTINCT_RACERS"):
            self.build(obj=t)

    def test_duplicate_target_boat_rejected(self):
        t=deepcopy(self.target)
        t["entries"][1]["boat"]=1
        with self.assertRaisesRegex(ValueError, "INVALID_TARGET_BOAT_OR_RACER"):
            self.build(obj=t)

    def test_protected_20261001_target_rejected(self):
        t=target("202610010103","2026-10-01T08:35:00+09:00")
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_UNSUPPORTED_TARGET_DATE"):
            self.build(obj=t)

    def test_target_deadline_wrong_day_rejected(self):
        t=target(deadline="2026-10-01T08:35:00+09:00")
        with self.assertRaisesRegex(ValueError, "TARGET_DEADLINE_DATE_MISMATCH"):
            self.build(obj=t)

    def test_deadline_must_be_jst_rejected(self):
        t=target(deadline="2026-09-30T08:35:00Z")
        with self.assertRaisesRegex(ValueError, "EXPLICIT_JST_OFFSET_REQUIRED"):
            self.build(obj=t)

    def test_exhibition_permutation_not_imported(self):
        r=self.build()
        self.assertNotIn("target_actual_course_by_boat",r)
        self.assertNotIn("finish",r["target"])
        self.assertNotIn("actual_course",r["target"])

    def test_post_deadline_yesterday_result_is_not_used(self):
        records=one_race("202609290101", "2026-09-30T08:36:00+09:00")
        raw, m=history(records)
        r=self.build(raw=raw,manifest=m)
        self.assertEqual(r["historical_races_eligible_before_target"],0)
        self.assertEqual(r["historical_races_not_yet_available"],1)

    def test_same_target_result_even_if_fake_early_source_not_used(self):
        records=one_race("202609300103", "2026-09-30T08:30:00+09:00")
        raw,m=history(records)
        r=self.build(raw=raw,manifest=m)
        self.assertEqual(r["same_target_outcome_excluded"],1)
        self.assertEqual(r["historical_races_eligible_before_target"],0)

    def test_future_race_with_falsified_early_publication_rejected(self):
        rec=one_race("202609300104", "2026-09-29T22:00:00+09:00")
        raw,m=history(rec)
        with self.assertRaisesRegex(ValueError,"HISTORICAL_PUBLISHED_AT_LEAK"):
            self.build(raw=raw,manifest=m)

    def test_wrong_six_course_history_rejected(self):
        rec=one_race("202609290101","2026-09-29T21:00:00+09:00",
                     courses=[1,1,3,4,5,6])
        raw,m=history(rec)
        with self.assertRaisesRegex(ValueError,"ACTUAL_COURSE_NOT_SIX_WAY_PERMUTATION"):
            self.build(raw=raw,manifest=m)


if __name__ == "__main__":
    unittest.main()
