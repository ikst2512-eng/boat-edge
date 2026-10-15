"""Synthetic-only regressions. Never access actual races or result files."""
import csv
import hashlib
import importlib.util
import io
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "boat_edge_02_s_offline_input.py"
spec = importlib.util.spec_from_file_location("s_offline", SCRIPT)
s_offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s_offline)
KEY = "20260929" + "01" + "03"


def fixtures(overrides=None, changes=None):
    row = {"レースコード": KEY, "レース日": "2026-09-29", "レース場コード": "01", "レース回": "3R"}
    for i in range(1, 7):
        row[f"艇{i}_登録番号"] = str(4000 + i)
        row[f"艇{i}_全国勝率"] = str(i)
        row[f"艇{i}_全国2連対率"] = "40"
        row[f"艇{i}_全国3連対率"] = "60"
        row[f"艇{i}_当地勝率"] = "5.1"
        row[f"艇{i}_当地2連対率"] = "30"
        row[f"艇{i}_当地3連対率"] = "50"
        row[f"艇{i}_全国平均ST"] = f"{0.10 + i/100:.2f}"
        row[f"艇{i}_モーター2連対率"] = str(i*10)
        row[f"艇{i}_モーター3連対率"] = str(i*10 + 20)
        row[f"艇{i}_ボート2連対率"] = "40"
        row[f"艇{i}_ボート3連対率"] = "50"
        row[f"艇{i}_F本数"] = "0"
        row[f"艇{i}_L本数"] = "0"
    if changes:
        row.update(changes)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    raw = stream.getvalue().encode()
    manifest = {
        "schema": s_offline.MANIFEST_SCHEMA,
        "source_kind": s_offline.SOURCE_KIND,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "race_key": KEY,
        "deadline_jst": "2026-09-29T12:00:00+09:00",
        "first_seen_at_jst": "2026-09-29T09:02:00+09:00",
        "data_available_at_jst": "2026-09-29T09:00:00+09:00",
        "rights_status": s_offline.RIGHTS_STATUS,
        "rights_evidence": "Operator-staged synthetic source for unit tests only",
    }
    if overrides:
        manifest.update(overrides)
    return raw, manifest


class SOfflineTests(unittest.TestCase):
    def test_all_fields_and_six_boats(self):
        raw, manifest = fixtures()
        data = s_offline.ingest_offline_csv(raw, manifest)
        self.assertEqual(data["coverage"]["raw_fields_present"], 78)
        self.assertEqual(len(data["boats"]), 6)
        self.assertEqual(data["boats"]["1"]["values"]["national_win_rate_relative"], -2.5)
        self.assertFalse(data["model_training_performed"])
        self.assertFalse(data["formal_fresh_read"])

    def test_missing_never_imputed(self):
        raw, manifest = fixtures(changes={"艇2_全国平均ST": ""})
        data = s_offline.ingest_offline_csv(raw, manifest)
        self.assertIsNone(data["boats"]["2"]["values"]["avg_st"])
        self.assertTrue(all(data["boats"][str(b)]["values"]["avg_st_relative"] is None for b in range(1,7)))
        self.assertEqual(data["coverage"]["raw_fields_present"], 77)

    def test_sha_tampering_blocked(self):
        raw, manifest = fixtures()
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_SHA_MISMATCH"):
            s_offline.ingest_offline_csv(raw + b"garbage", manifest)

    def test_third_party_provider_cannot_be_attested(self):
        raw, manifest = fixtures(overrides={"source_kind": "BOATERS_EXPORT"})
        with self.assertRaisesRegex(ValueError, "THIRD_PARTY_OR_UNREVIEWED"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_no_self_attested_license(self):
        raw, manifest = fixtures(overrides={"rights_status": "UNKNOWN"})
        with self.assertRaisesRegex(ValueError, "OFFLINE_RIGHTS_REVIEW_REQUIRED"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_no_empty_rights_evidence(self):
        raw, manifest = fixtures(overrides={"rights_evidence": ""})
        with self.assertRaisesRegex(ValueError, "SPECIFIC_RIGHTS_EVIDENCE_REQUIRED"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_denies_formal_race_after_oct_1(self):
        raw, manifest = fixtures(overrides={"race_key": "202610010103"})
        with self.assertRaisesRegex(ValueError, "TARGET_OUTSIDE_PROTECTED"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_after_deadline_blocks(self):
        raw, manifest = fixtures(overrides={"first_seen_at_jst": "2026-09-29T12:00:00+09:00"})
        with self.assertRaisesRegex(ValueError, "TIME_WINDOW"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_available_after_first_seen_blocks(self):
        raw, manifest = fixtures(overrides={"data_available_at_jst": "2026-09-29T09:04:00+09:00"})
        with self.assertRaisesRegex(ValueError, "TIME_WINDOW"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_wrong_timezone_blocks(self):
        raw, manifest = fixtures(overrides={"first_seen_at_jst": "2026-09-29T00:02:00+00:00"})
        with self.assertRaisesRegex(ValueError, "FIRST_SEEN_MUST_BE_JST"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_duplicate_registration_blocks(self):
        raw, manifest = fixtures(changes={"艇2_登録番号": "4001"})
        with self.assertRaisesRegex(ValueError, "SIX_DISTINCT"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_reject_non_numeric_st(self):
        raw, manifest = fixtures(changes={"艇1_全国平均ST": "F.01"})
        with self.assertRaisesRegex(ValueError, "BAD_FEATURE"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_reject_out_of_range_motor(self):
        raw, manifest = fixtures(changes={"艇1_モーター2連対率": "102.3"})
        with self.assertRaisesRegex(ValueError, "OUT_OF_RANGE"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_reject_proprietary_elo_column(self):
        raw, manifest = fixtures(changes={"サイト独自Elo": "1510"})
        with self.assertRaisesRegex(ValueError, "TARGET_OUTCOME_OR_ODDS_COLUMNS_FORBIDDEN"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_reject_outcome_column(self):
        raw, manifest = fixtures(changes={"3連単オッズ": "20"})
        with self.assertRaisesRegex(ValueError, "TARGET_OUTCOME_OR_ODDS_COLUMNS_FORBIDDEN"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_no_duplicate_race_rows(self):
        raw, manifest = fixtures()
        raw = raw + raw.splitlines(keepends=True)[-1]
        manifest["source_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "TARGET_MUST_HAVE_EXACTLY_ONE"):
            s_offline.ingest_offline_csv(raw, manifest)

    def test_extra_manifest_key_blocks(self):
        raw, manifest = fixtures(overrides={"unverified": True})
        with self.assertRaisesRegex(ValueError, "EXACT_OPERATOR_MANIFEST_REQUIRED"):
            s_offline.ingest_offline_csv(raw, manifest)


if __name__ == "__main__":
    unittest.main()
