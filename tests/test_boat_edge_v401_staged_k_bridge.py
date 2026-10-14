"""V401 fixture-only tests, synthetic rows; never fetch historical outcome endpoints."""
import hashlib
import json
import sys
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import JST  # noqa: E402
from boat_edge_v401_staged_k_bridge import normalize  # noqa: E402


class StagedKBridgeTests(unittest.TestCase):
    as_of = datetime(2026, 10, 1, tzinfo=JST)
    source = b"FAKE_LZH_FIXTURE_ONLY_NOT_REAL_K_ARCHIVE"

    @staticmethod
    def race(key="202609300101"):
        return {
            "race_key": key, "published_at": "2026-09-30T21:00:00+09:00",
            "entries": [{"boat": i, "racer_id": f"{4500+i}",
                         "actual_course": i, "finish": i} for i in range(1, 7)],
        }

    def stage(self, races=None, exclusions=None):
        return {
            "schema": "BOAT_EDGE_V401_STAGED_K_EXTRACT_V1",
            "source_day": "2026-09-30",
            "races": races if races is not None else [self.race()],
            "excluded": exclusions or [],
        }

    def manifest(self, staged):
        return {
            "schema": "BOAT_EDGE_V401_K_SOURCE_PROVENANCE_V1",
            "raw_source_sha256": hashlib.sha256(self.source).hexdigest(),
            "staged_sha256": hashlib.sha256(staged).hexdigest(),
            "source_name": "SYNTHETIC_FIXTURE_ONLY",
            "source_locator": "local:fixture-source",
            "rights_evidence": "synthetic-fixture-only",
            "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
            "normalization_protocol": "synthetic-input-test-v1",
            "parser_name": "V401_SYNTHETIC_TEST_ADAPTER",
            "parser_version": "v1",
            "retrieved_at_jst": "2026-09-30T21:30:00+09:00",
        }

    def check(self, payload=None, *, mutate_manifest=None):
        raw = json.dumps(payload if payload is not None else self.stage(),
                         ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        manifest = self.manifest(raw)
        if mutate_manifest:
            mutate_manifest(manifest)
        return normalize(self.source, raw, manifest, self.as_of)

    def test_valid_six_boat_bridge_to_v400(self):
        normalized, manifest, audit = self.check()
        self.assertEqual(audit["included_races"], 1)
        self.assertEqual(audit["excluded_races"], 0)
        self.assertFalse(audit["race_coverage_complete"])
        self.assertFalse(audit["source_authenticity_independently_verified"])
        self.assertFalse(audit["source_availability_at_train_cutoff_independently_verified"])
        self.assertFalse(audit["accuracy_improvement_proven"])
        self.assertEqual(hashlib.sha256(normalized).hexdigest(), manifest["csv_sha256"])
        self.assertEqual(len(normalized.splitlines()), 7)
        self.assertEqual(audit["included_by_venue"], {"01": 1})

    def test_racer_course_is_not_frame_proxy(self):
        p = self.stage()
        p["races"][0]["entries"][0]["actual_course"] = 2
        p["races"][0]["entries"][1]["actual_course"] = 1
        normalized, _, _ = self.check(p)
        self.assertIn(b"202609300101,1,4501,2,1,", normalized)

    def test_audited_exclusion(self):
        p = self.stage(exclusions=[{"race_key": "202609300102", "reason": "CANCELLED"}])
        _, _, audit = self.check(p)
        self.assertEqual(audit["included_races"], 1)
        self.assertEqual(audit["excluded_reasons"], {"CANCELLED": 1})
        self.assertFalse(audit["race_coverage_complete"])

    def test_deterministic_output(self):
        self.assertEqual(self.check(), self.check())

    def test_duplicate_boat_rejected(self):
        p = self.stage()
        p["races"][0]["entries"][1]["boat"] = 1
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_SIX_BOAT_RACE"):
            self.check(p)

    def test_duplicate_actual_course_rejected(self):
        p = self.stage()
        p["races"][0]["entries"][1]["actual_course"] = 1
        with self.assertRaisesRegex(ValueError, "ACTUAL_COURSE_NOT_SIX_WAY"):
            self.check(p)

    def test_duplicate_finish_rejected(self):
        p = self.stage()
        p["races"][0]["entries"][1]["finish"] = 1
        with self.assertRaisesRegex(ValueError, "FINISH_NOT_SIX_UNIQUE"):
            self.check(p)

    def test_non_six_race_rejected(self):
        p = self.stage()
        p["races"][0]["entries"].pop()
        with self.assertRaisesRegex(ValueError, "K_RACE_NOT_SIX_ENTRIES"):
            self.check(p)

    def test_source_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "ORIGINAL_K_BYTES_HASH_MISMATCH"):
            self.check(mutate_manifest=lambda m: m.update(raw_source_sha256="f"*64))

    def test_staged_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "STAGED_K_BYTES_HASH_MISMATCH"):
            self.check(mutate_manifest=lambda m: m.update(staged_sha256="f"*64))

    def test_rights_unreviewed_rejected(self):
        with self.assertRaisesRegex(ValueError, "HISTORICAL_SOURCE_RIGHTS_NOT_REVIEWED"):
            self.check(mutate_manifest=lambda m: m.update(rights_review_status="UNVERIFIED"))

    def test_invalid_future_timestamp_rejected(self):
        p = self.stage()
        p["races"][0]["published_at"] = "2026-10-02T10:00:00+09:00"
        with self.assertRaisesRegex(ValueError, "HISTORICAL_PUBLISHED_AT_LEAK"):
            self.check(p)

    def test_target_protected_race_rejected(self):
        p = self.stage(races=[self.race("202610010101")])
        p["source_day"] = "2026-10-01"
        with self.assertRaisesRegex(ValueError, "RACE_OUTSIDE_ALLOWED_RANGE"):
            self.check(p)

    def test_exclusion_overlap_rejected(self):
        p = self.stage(exclusions=[{"race_key": "202609300101", "reason": "CANCELLED"}])
        with self.assertRaisesRegex(ValueError, "EXCLUDED_RACE_DUPLICATE_OR_INCLUDED"):
            self.check(p)

    def test_unexplained_exclusion_rejected(self):
        p = self.stage(exclusions=[{"race_key": "202609300102", "reason": "UNKNOWN"}])
        with self.assertRaisesRegex(ValueError, "UNDECLARED_EXCLUSION_REASON"):
            self.check(p)

    def test_mixed_source_day_rejected(self):
        p = self.stage(races=[self.race("202609290101")])
        with self.assertRaisesRegex(ValueError, "SOURCE_DAY_RACE_KEY_MISMATCH"):
            self.check(p)

    def test_duplicate_race_rejected(self):
        p = self.stage(races=[self.race(), deepcopy(self.race())])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_STAGED_RACE_KEY"):
            self.check(p)

    def test_unreviewed_extracted_fields_rejected(self):
        p = self.stage()
        p["races"][0]["entries"][0].pop("actual_course")
        with self.assertRaisesRegex(ValueError, "EXACT_STAGED_ENTRY_KEYS_REQUIRED"):
            self.check(p)

    def test_no_complete_races_rejected(self):
        p = self.stage(races=[], exclusions=[{"race_key": "202609300101", "reason": "CANCELLED"}])
        with self.assertRaisesRegex(ValueError, "NO_COMPLETE_K_RACES_IN_SOURCE_DAY"):
            self.check(p)


if __name__ == "__main__":
    unittest.main()
