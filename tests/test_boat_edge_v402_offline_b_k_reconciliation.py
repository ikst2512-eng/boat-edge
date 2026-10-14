"""V402 synthetic-only B/K reconciliation regressions; never imports site results."""
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
from boat_edge_v402_offline_b_k_reconciliation import reconcile  # noqa: E402


def as_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


class BkReconciliationFixtureTests(unittest.TestCase):
    cutoff = datetime(2026, 10, 1, tzinfo=JST)
    source_k = b"SYNTHETIC_LZH_K_DO_NOT_TREAT_AS_REAL_RECORD"
    source_b = b"SYNTHETIC_LZH_B_DO_NOT_TREAT_AS_REAL_PROGRAM"
    race_key = "202609300101"
    def k_race(self):
        return {"race_key": self.race_key, "published_at": "2026-09-30T21:00:00+09:00",
                "entries": [{"boat": i, "racer_id": str(4500+i),
                             "actual_course": i, "finish": i} for i in range(1, 7)]}

    def k_stage(self):
        return {"schema": "BOAT_EDGE_V401_STAGED_K_EXTRACT_V1",
                "source_day": "2026-09-30", "races": [self.k_race()], "excluded": []}

    def k_manifest(self, raw):
        return {
            "schema": "BOAT_EDGE_V401_K_SOURCE_PROVENANCE_V1",
            "raw_source_sha256": hashlib.sha256(self.source_k).hexdigest(),
            "staged_sha256": hashlib.sha256(raw).hexdigest(),
            "source_name": "SYNTHETIC_TEST_SOURCE", "source_locator": "local:test",
            "rights_evidence": "synthetic-only-fixture",
            "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
            "normalization_protocol": "synthetic-staged-test-v1",
            "parser_name": "test", "parser_version": "v1",
            "retrieved_at_jst": "2026-09-30T21:30:00+09:00",
        }

    def b_stage(self):
        return {"schema": "BOAT_EDGE_V402_STAGED_B_PROGRAM_DAY_V1",
                "source_day": "2026-09-30", "races": [
                    {"race_key": self.race_key,
                     "deadline_jst": "2026-09-30T08:35:00+09:00",
                     "entries": [{"boat": i, "racer_id": str(4500+i)}
                                 for i in range(1, 7)]},
                ]}

    def b_manifest(self, raw):
        return {
            "schema": "BOAT_EDGE_V402_B_SOURCE_MANIFEST_V1",
            "source_sha256": hashlib.sha256(self.source_b).hexdigest(),
            "staged_sha256": hashlib.sha256(raw).hexdigest(),
            "source_locator": "local:synthetic_b_fixture",
            "rights_evidence": "synthetic-only-fixture",
            "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
            "parser_name": "synthetic-parser", "parser_version": "v1",
            "retrieved_at_jst": "2026-09-30T07:00:00+09:00",
        }

    def run_test(self, *, change_k=None, change_b=None, change_k_audit=None,
                 change_k_csv=None, change_k_manifest=None, change_b_manifest=None):
        k = self.k_stage()
        b = self.b_stage()
        if change_k: change_k(k)
        if change_b: change_b(b)
        stage_bytes = as_bytes(k)
        normalized, km, ka = normalize(
            self.source_k, stage_bytes, self.k_manifest(stage_bytes), self.cutoff)
        if change_k_csv: normalized = change_k_csv(normalized)
        if change_k_manifest: change_k_manifest(km)
        if change_k_audit: change_k_audit(ka)
        bbytes = as_bytes(b)
        bm = self.b_manifest(bbytes)
        if change_b_manifest: change_b_manifest(bm)
        return reconcile(normalized, km, ka, self.source_b, bbytes, bm, self.cutoff)

    def test_happy_path_and_non_claims(self):
        result = self.run_test()
        self.assertEqual(result["reconciled_six_boat_races"], 1)
        self.assertEqual(result["b_program_races_supplied"], 1)
        self.assertTrue(result["b_k_staged_race_universe_reconciled"])
        self.assertTrue(result["b_program_pre_first_deadline_capture_claim"])
        self.assertFalse(result["b_program_historic_capture_independently_authenticated"])
        self.assertFalse(result["national_daily_coverage_independently_verified"])
        self.assertFalse(result["license_independently_verified"])
        self.assertFalse(result["model_promotion_authorized"])

    def test_deterministic(self):
        self.assertEqual(self.run_test(), self.run_test())

    def test_frame_can_differ_from_actual_course(self):
        def change(k):
            k["races"][0]["entries"][0]["actual_course"] = 2
            k["races"][0]["entries"][1]["actual_course"] = 1
        self.assertEqual(self.run_test(change_k=change)["reconciled_six_boat_races"], 1)

    def test_explicit_k_exclusion_preserved(self):
        def change(k):
            k["excluded"] = [{"race_key": "202609300102",
                              "reason": "SCRATCH_OR_DISQUALIFICATION"}]
        def append_b(b):
            nxt = deepcopy(b["races"][0])
            nxt["race_key"] = "202609300102"
            b["races"].append(nxt)
        result = self.run_test(change_k=change, change_b=append_b)
        self.assertEqual(result["excluded_with_explicit_reason"], 1)
        self.assertEqual(result["b_program_races_supplied"], 2)

    def test_k_racer_conflict_rejected(self):
        def change(b):
            b["races"][0]["entries"][0]["racer_id"] = "4999"
        with self.assertRaisesRegex(ValueError, "B_K_BOAT_RACER_ID_MISMATCH"):
            self.run_test(change_b=change)

    def test_result_publication_before_deadline_rejected(self):
        def change(k):
            k["races"][0]["published_at"] = "2026-09-30T08:34:00+09:00"
        with self.assertRaisesRegex(ValueError, "K_RESULT_PUBLISHED_BEFORE_B_DEADLINE"):
            self.run_test(change_k=change)

    def test_result_publication_equal_deadline_rejected(self):
        def change(k):
            k["races"][0]["published_at"] = "2026-09-30T08:35:00+09:00"
        with self.assertRaisesRegex(ValueError, "K_RESULT_PUBLISHED_BEFORE_B_DEADLINE"):
            self.run_test(change_k=change)

    def test_unexplained_b_race_rejected(self):
        def change(b):
            nxt = deepcopy(b["races"][0])
            nxt["race_key"] = "202609300102"
            b["races"].append(nxt)
        with self.assertRaisesRegex(ValueError, "B_K_UNEXPLAINED_MISSING_RACES"):
            self.run_test(change_b=change)

    def test_k_race_missing_from_b_rejected(self):
        def change(b):
            b["races"][0]["race_key"] = "202609300102"
        with self.assertRaisesRegex(ValueError, "K_RACE_MISSING_FROM_B_PROGRAM"):
            self.run_test(change_b=change)

    def test_bad_b_original_sha_rejected(self):
        with self.assertRaisesRegex(ValueError, "B_SOURCE_BYTE_SHA_MISMATCH"):
            self.run_test(change_b_manifest=lambda bm: bm.update(source_sha256="0"*64))

    def test_bad_b_parsed_sha_rejected(self):
        with self.assertRaisesRegex(ValueError, "B_STAGED_BYTE_SHA_MISMATCH"):
            self.run_test(change_b_manifest=lambda bm: bm.update(staged_sha256="0"*64))

    def test_rights_unreviewed_rejected(self):
        with self.assertRaisesRegex(ValueError, "B_RIGHTS_REVIEW_NOT_ATTESTED"):
            self.run_test(change_b_manifest=lambda bm: bm.update(rights_review_status="UNKNOWN"))

    def test_b_duplicate_boat_rejected(self):
        def change(b):
            b["races"][0]["entries"][1]["boat"] = 1
        with self.assertRaisesRegex(ValueError, "B_INVALID_BOAT_OR_RACER"):
            self.run_test(change_b=change)

    def test_b_duplicate_racer_rejected(self):
        def change(b):
            b["races"][0]["entries"][1]["racer_id"] = "4501"
        with self.assertRaisesRegex(ValueError, "B_SIX_UNIQUE_BOATS_AND_RACERS_REQUIRED"):
            self.run_test(change_b=change)

    def test_b_duplicate_race_rejected(self):
        def change(b):
            b["races"].append(deepcopy(b["races"][0]))
        with self.assertRaisesRegex(ValueError, "B_INVALID_OR_DUPLICATE_RACE_KEY"):
            self.run_test(change_b=change)

    def test_k_exclusion_ledger_missing_rejected(self):
        with self.assertRaisesRegex(ValueError, "K_EXCLUSION_LEDGER_REQUIRED"):
            self.run_test(change_k_audit=lambda x: x.pop("excluded_race_rows"))

    def test_k_exclusion_reason_counts_tampered_rejected(self):
        def change(k):
            k["excluded"] = [{"race_key": "202609300102", "reason": "CANCELLED"}]
        def change_audit(x):
            x["excluded_reasons"] = {"SOURCE_AMBIGUOUS": 1}
        with self.assertRaisesRegex(ValueError, "K_EXCLUSION_REASON_COUNTS_MISMATCH"):
            self.run_test(change_k=change, change_k_audit=change_audit)

    def test_k_original_csv_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "RAW_HISTORY_SHA256_MISMATCH"):
            self.run_test(change_k_csv=lambda x: x+b"\n")

    def test_b_race_wrong_day_rejected(self):
        def change(b):
            b["races"][0]["race_key"] = "202610010101"
        with self.assertRaisesRegex(ValueError, "B_INVALID_OR_DUPLICATE_RACE_KEY"):
            self.run_test(change_b=change)

    def test_late_b_retrieval_is_not_proof(self):
        result = self.run_test(change_b_manifest=lambda bm:
                               bm.update(retrieved_at_jst="2026-10-13T11:00:00+09:00"))
        self.assertFalse(result["b_program_pre_first_deadline_capture_claim"])
        self.assertFalse(result["b_program_historic_capture_independently_authenticated"])

    def test_b_manifest_unknown_field_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXACT_B_SOURCE_MANIFEST_REQUIRED"):
            self.run_test(change_b_manifest=lambda bm: bm.update(license_independently_verified=True))


if __name__ == "__main__":
    unittest.main()
