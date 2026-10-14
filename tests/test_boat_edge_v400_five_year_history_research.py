"""Fixture-only regression for V400; no actual outcome file is accessed."""
import csv
import hashlib
import io
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import (  # noqa: E402
    COLUMNS, JST, build_counts,
)


def rows(race_key, stamp, courses=None, finish=None):
    courses = courses or (1, 2, 3, 4, 5, 6)
    finish = finish or (1, 2, 3, 4, 5, 6)
    return [{"race_key": race_key, "boat": str(i), "racer_id": str(4500+i),
             "actual_course": str(courses[i-1]), "finish": str(finish[i-1]),
             "published_at": stamp} for i in range(1, 7)]


def encode(data):
    buf = io.StringIO(newline="")
    out = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    out.writeheader()
    out.writerows(data)
    return buf.getvalue().encode()


def manifest(raw):
    return {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "source_name": "SYNTHETIC_FIXTURE_ONLY",
        "source_locator": "local:synthetic_fixture",
        "rights_evidence": "TEST_FIXTURE_NO_REAL_RIGHTS_ASSERTION",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": "TEST_NORMALIZED_CSV_V1",
    }


class FiveYearResearchTest(unittest.TestCase):
    cutoff = datetime(2026, 10, 1, tzinfo=JST)
    earlier = rows("202110010101", "2021-10-01T17:10:00+09:00")
    recent = rows("202609300101", "2026-09-30T21:10:00+09:00",
                  courses=(2, 1, 3, 4, 5, 6), finish=(2, 1, 3, 4, 5, 6))

    def build(self, data, *, as_of=None, mutate_manifest=None):
        raw = encode(data)
        m = manifest(raw)
        if mutate_manifest:
            mutate_manifest(m)
        return build_counts(raw, m, as_of or self.cutoff)

    def test_boundary_and_recency_and_actual_course_counts(self):
        result = self.build(self.earlier + self.recent)
        self.assertEqual(result["race_count"], 2)
        self.assertEqual(result["six_boat_rows"], 12)
        self.assertFalse(result["calibrated"])
        self.assertFalse(result["model_promotion_authorized"])
        self.assertFalse(result["rights_independently_verified_by_script"])
        v = result["count_tables"]["racer:4501/course:2"]["windows_days"]
        self.assertEqual(v["90"], {"sample_count": 1, "first": 0,
                                    "second": 1, "third": 0})
        self.assertEqual(v["1826"]["second"], 1)
        a = result["count_tables"]["racer:4502/course:2"]["half_life_180d_weighted"]
        b = result["count_tables"]["racer:4502/course:1"]["half_life_180d_weighted"]
        self.assertGreater(b["effective_entries"], a["effective_entries"])
        self.assertEqual(result["count_tables"]["all/course:1"]["windows_days"]["1826"]["sample_count"], 2)
        self.assertEqual(result["count_tables"]["all/course:1"]["windows_days"]["90"]["sample_count"], 1)
        self.assertEqual(result["history_start"], "2021-10-01")

    def test_reproducible_byte_exact(self):
        raw = encode(self.earlier + self.recent)
        m = manifest(raw)
        a = json.dumps(build_counts(raw, m, self.cutoff), sort_keys=True,
                       ensure_ascii=False, separators=(",", ":")).encode()
        b = json.dumps(build_counts(raw, m, self.cutoff), sort_keys=True,
                       ensure_ascii=False, separators=(",", ":")).encode()
        self.assertEqual(a, b)
        self.assertEqual(hashlib.sha256(a).digest(), hashlib.sha256(b).digest())

    def test_wrong_digest_disallowed(self):
        with self.assertRaisesRegex(ValueError, "RAW_HISTORY_SHA256_MISMATCH"):
            self.build(self.recent, mutate_manifest=lambda m: m.update(csv_sha256="0" * 64))

    def test_rights_not_attested_disallowed(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_RIGHTS_REVIEW_NOT_ATTESTED"):
            self.build(self.recent, mutate_manifest=lambda m: m.update(rights_review_status="UNKNOWN"))

    def test_protected_20261001_race_disallowed(self):
        x = rows("202610010101", "2026-10-01T20:00:00+09:00")
        with self.assertRaisesRegex(ValueError, "RACE_OUTSIDE_ALLOWED_RANGE"):
            self.build(x)

    def test_future_published_at_leak_disallowed(self):
        x = rows("202609300101", "2026-10-01T09:00:00+09:00")
        with self.assertRaisesRegex(ValueError, "HISTORICAL_PUBLISHED_AT_LEAK"):
            self.build(x)

    def test_actual_course_permutation_required(self):
        x = rows("202609300101", "2026-09-30T20:00:00+09:00",
                 courses=(1, 1, 3, 4, 5, 6))
        with self.assertRaisesRegex(ValueError, "ACTUAL_COURSE_NOT_SIX_WAY"):
            self.build(x)

    def test_finish_permutation_required(self):
        x = rows("202609300101", "2026-09-30T20:00:00+09:00",
                 finish=(1, 1, 3, 4, 5, 6))
        with self.assertRaisesRegex(ValueError, "FINISH_NOT_SIX_UNIQUE"):
            self.build(x)

    def test_duplicate_race_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "HISTORY_NOT_SORTED_OR_DUPLICATE"):
            self.build(self.recent + self.recent)

    def test_partial_race_rejected(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_SIX_BOAT_RACE"):
            self.build(self.recent[:5])

    def test_future_cutoff_or_unlock_forbidden(self):
        with self.assertRaisesRegex(ValueError, "AS_OF_OUTSIDE_PROTECTED_HISTORICAL_WINDOW"):
            self.build(self.recent, as_of=datetime(2026, 10, 14, tzinfo=JST))

    def test_older_than_5years_forbidden(self):
        x = rows("202109300101", "2021-09-30T20:00:00+09:00")
        with self.assertRaisesRegex(ValueError, "RACE_OUTSIDE_ALLOWED_RANGE"):
            self.build(x)

    def test_unsorted_boats_rejected(self):
        x = list(self.recent)
        x[1], x[2] = x[2], x[1]
        with self.assertRaisesRegex(ValueError, "HISTORY_NOT_SORTED"):
            self.build(x)

    def test_source_must_include_explicit_jst(self):
        x = rows("202609300101", "2026-09-30T20:00:00Z")
        with self.assertRaisesRegex(ValueError, "EXPLICIT_JST_OFFSET_REQUIRED"):
            self.build(x)

    def test_empty_dataset_rejected(self):
        with self.assertRaisesRegex(ValueError, "HISTORICAL_DATASET_EMPTY"):
            self.build([])


if __name__ == "__main__":
    unittest.main()
