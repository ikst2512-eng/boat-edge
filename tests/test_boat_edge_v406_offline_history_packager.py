"""V406 offline package tests, using only invented six-boat race rows."""
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import COLUMNS, JST, validate_manifest
from boat_edge_v403_five_year_coverage_audit import UNPROVEN
from boat_edge_v404_asof_history_features import snapshot
from boat_edge_v405_batch_asof_history_features import build_batch
from boat_edge_v406_offline_history_packager import (
    CUTOFF, INDEX_SCHEMA, package_days, stage_from_index, iter_staged_days,
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def synth_day(day, venue=1, race=1, published="20:00:00"):
    key = day.strftime("%Y%m%d") + f"{venue:02d}{race:02d}"
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for boat in range(1, 7):
        writer.writerow({
            "race_key": key, "boat": str(boat),
            "racer_id": str(4600 + boat),
            "actual_course": str(7 - boat), "finish": str(boat),
            "published_at": day.isoformat() + "T" + published + "+09:00",
        })
    raw = output.getvalue().encode("utf-8")
    man = {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": digest(raw),
        "source_name": "INVENTED_SYNTHETIC_FIXTURE_ONLY",
        "source_locator": "fixture:no-external-source",
        "rights_evidence": "author-created synthetic fixture only",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": "invented-test-row",
    }
    report = {
        "schema": "BOAT_EDGE_V402_OFFLINE_B_K_RECONCILIATION_RESEARCH_V1",
        "source_day": day.isoformat(),
        "k_normalized_sha256": digest(raw),
        "b_original_sha256": "a"*64,
        "b_staged_sha256": "b"*64,
        "b_program_races_supplied": 1,
        "by_venue": {f"{venue:02d}": {
            "b_program_races": 1, "k_complete_races": 1,
            "excluded_races": 0,
        }},
        "reconciled_six_boat_races": 1,
        "excluded_with_explicit_reason": 0,
        "b_k_staged_race_universe_reconciled": True,
        "research_only": True,
        **{flag: False for flag in UNPROVEN},
    }
    return {"source_day": day.isoformat(), "k_csv": raw,
            "k_manifest": man, "v402_report": report}


def b_target(day, venue=2, race=1):
    return {
        "schema": "BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1",
        "race_key": day.strftime("%Y%m%d") + f"{venue:02d}{race:02d}",
        "deadline_jst": day.isoformat() + "T08:35:00+09:00",
        "entries": [{"boat": i, "racer_id": str(4600 + i)}
                    for i in range(1, 7)],
    }


class V406OfflinePackagingTests(unittest.TestCase):
    def setUp(self):
        self.first = synth_day(date(2021, 10, 1))
        self.yesterday = synth_day(date(2026, 9, 29))
        self.today = synth_day(date(2026, 9, 30))

    def test_pack_noncontiguous_days_truthful_coverage_and_hashes(self):
        raw, manifest, audit = package_days([self.today, self.first, self.yesterday])
        self.assertEqual(manifest["csv_sha256"], digest(raw))
        self.assertEqual(audit["history_csv_sha256"], digest(raw))
        self.assertEqual(audit["normalized_complete_races"], 3)
        self.assertEqual(audit["normalized_six_boat_rows"], 18)
        self.assertEqual(audit["input_days"], 3)
        self.assertEqual(audit["coverage"]["days_without_verified_v402_reports"], 1823)
        self.assertFalse(audit["calendar_coverage_complete"])
        self.assertFalse(audit["historic_source_rights_independently_verified"])
        self.assertFalse(audit["accuracy_improvement_proven"])
        self.assertFalse(audit["formal_fresh_read"])
        self.assertEqual([x["source_day"] for x in audit["source_lineage"]],
                         ["2021-10-01", "2026-09-29", "2026-09-30"])
        validate_manifest(manifest, raw, CUTOFF)
        keys = [line.split(",")[0] for line in raw.decode().splitlines()[1::6]]
        self.assertEqual(keys, ["202110010101", "202609290101", "202609300101"])

    def test_package_can_feed_v404_and_v405_without_promoting_accuracy(self):
        raw, manifest, _ = package_days([self.yesterday, self.today])
        target = b_target(date(2026, 9, 30))
        single = snapshot(raw, manifest, target)
        batch = build_batch(raw, manifest, [target])["snapshots"][0]
        self.assertEqual(batch, single)
        self.assertEqual(single["historical_races_eligible_before_target"], 1)
        self.assertEqual(single["historical_races_not_yet_available"], 1)
        self.assertFalse(single["accuracy_improvement_proven"])

    def test_duplicate_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_STAGED_DAY"):
            package_days([self.first, self.first])

    def test_wrong_index_date_rejected(self):
        entry = deepcopy(self.yesterday)
        entry["source_day"] = "2026-09-30"
        with self.assertRaisesRegex(ValueError, "INDEX_V402_DAY_MISMATCH"):
            package_days([entry])

    def test_tampered_k_source_sha_rejected(self):
        entry = deepcopy(self.first)
        entry["k_manifest"]["csv_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "RAW_HISTORY_SHA256_MISMATCH"):
            package_days([entry])

    def test_k_and_v402_sha_mismatch_rejected(self):
        entry = deepcopy(self.first)
        entry["v402_report"]["k_normalized_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "V402_K_CSV_SHA_MISMATCH"):
            package_days([entry])

    def test_v402_unexplained_count_rejected(self):
        entry = deepcopy(self.first)
        entry["v402_report"]["reconciled_six_boat_races"] = 2
        entry["v402_report"]["b_program_races_supplied"] = 2
        entry["v402_report"]["by_venue"]["01"]["k_complete_races"] = 2
        entry["v402_report"]["by_venue"]["01"]["b_program_races"] = 2
        with self.assertRaisesRegex(ValueError, "V402_K_RACE_TOTAL_MISMATCH"):
            package_days([entry])

    def test_false_venue_k_totals_rejected(self):
        entry = deepcopy(self.first)
        entry["v402_report"]["by_venue"] = {"02": {
            "b_program_races": 1, "k_complete_races": 1, "excluded_races": 0}}
        with self.assertRaisesRegex(ValueError, "V402_K_VENUE_COUNTS_MISMATCH"):
            package_days([entry])

    def test_wrong_k_day_rejected(self):
        entry = deepcopy(self.first)
        entry["source_day"] = "2026-09-29"
        entry["v402_report"]["source_day"] = "2026-09-29"
        with self.assertRaisesRegex(ValueError, "STAGED_CSV_SOURCE_DAY_MISMATCH"):
            package_days([entry])

    def test_formal_protected_date_rejected(self):
        invalid = synth_day(date(2026, 10, 1))
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_OUTSIDE_FIVE_YEAR_DATE"):
            package_days([invalid])

    def test_unreviewed_rights_fail_closed(self):
        entry = deepcopy(self.first)
        entry["k_manifest"]["rights_review_status"] = "PENDING"
        with self.assertRaisesRegex(ValueError, "SOURCE_RIGHTS_REVIEW_NOT_ATTESTED"):
            package_days([entry])

    def test_unproven_v402_flags_must_be_false(self):
        entry = deepcopy(self.first)
        entry["v402_report"]["accuracy_improvement_proven"] = True
        with self.assertRaisesRegex(ValueError, "V402_RESEARCH_ISOLATION_REQUIRED"):
            package_days([entry])

    def test_missing_and_invalid_list_rejected(self):
        with self.assertRaisesRegex(ValueError, "STAGED_DAY_LIST_REQUIRED"):
            package_days([])
        with self.assertRaisesRegex(ValueError, "EXACT_STAGED_DAY_FIELDS_REQUIRED"):
            package_days([{"other": 1}])

    def test_stage_index_is_local_only_and_checks_relative_paths(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root).resolve()
            (root / "day.csv").write_bytes(self.first["k_csv"])
            (root / "manifest.json").write_text(
                json.dumps(self.first["k_manifest"]), encoding="utf-8")
            (root / "report.json").write_text(
                json.dumps(self.first["v402_report"]), encoding="utf-8")
            record = {
                "source_day": "2021-10-01",
                "normalized_csv": "day.csv", "v400_manifest": "manifest.json",
                "v402_report": "report.json",
            }
            index = {"schema": INDEX_SCHEMA, "days": [record]}
            self.assertEqual(package_days(stage_from_index(root, index))[2]["input_days"], 1)
            changed = deepcopy(index)
            changed["days"][0]["normalized_csv"] = "../private.csv"
            with self.assertRaisesRegex(ValueError, "UNSAFE_STAGE_RELATIVE_PATH"):
                stage_from_index(root, changed)
            changed["days"][0]["normalized_csv"] = "https://example.org/x"
            with self.assertRaisesRegex(ValueError, "STAGE_FILE_MISSING_OR_OUTSIDE_ROOT"):
                stage_from_index(root, changed)
            changed["days"][0]["normalized_csv"] = "/tmp/private.csv"
            with self.assertRaisesRegex(ValueError, "UNSAFE_STAGE_RELATIVE_PATH"):
                stage_from_index(root, changed)

    def test_lazy_day_generator_exact_output_and_guards(self):
        inputs = [self.first, self.yesterday, self.today]
        ordered = package_days(inputs)
        lazy = package_days(item for item in inputs)
        self.assertEqual(ordered, lazy)
        with self.assertRaisesRegex(ValueError, "STAGED_DAY_LIST_REQUIRED"):
            package_days(item for item in ())
        # Duplicate-day protection rejects a repeated 1,827-day stream
        # before the overall day-count limit can be reached.
        with self.assertRaisesRegex(ValueError, "DUPLICATE_STAGED_DAY"):
            package_days(item for item in [self.first]*1827)
        with self.assertRaisesRegex(ValueError, "EXACT_STAGED_DAY_FIELDS_REQUIRED"):
            package_days(iter("not a history day"))

    def test_streaming_index_reads_one_day_at_a_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            entries = []
            for label, data in [("first", self.first), ("last", self.today)]:
                (root / (label+".csv")).write_bytes(data["k_csv"])
                (root / (label+".manifest.json")).write_text(
                    json.dumps(data["k_manifest"]), encoding="utf-8")
                (root / (label+".report.json")).write_text(
                    json.dumps(data["v402_report"]), encoding="utf-8")
                entries.append({
                    "source_day": data["source_day"],
                    "normalized_csv": label+".csv",
                    "v400_manifest": label+".manifest.json",
                    "v402_report": label+".report.json",
                })
            index = {"schema": INDEX_SCHEMA, "days": entries}
            iterator = iter_staged_days(root, index)
            self.assertFalse(isinstance(iterator, list))
            first = next(iterator)
            self.assertEqual(first["source_day"], "2021-10-01")
            # Source is read on demand: remove the second day's original CSV
            # before advancing and require a missing-file failure.
            (root / "last.csv").unlink()
            with self.assertRaisesRegex(ValueError, "STAGE_FILE_MISSING_OR_OUTSIDE_ROOT"):
                next(iterator)

    def test_stream_index_rejects_invalid_paths_before_first_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            index = {"schema": INDEX_SCHEMA, "days": [{
                "source_day": "2021-10-01",
                "normalized_csv": "first.csv",
                "v400_manifest": "../secret.json",
                "v402_report": "first.report.json",
            }]}
            with self.assertRaisesRegex(ValueError, "UNSAFE_STAGE_RELATIVE_PATH"):
                next(iter_staged_days(root, index))
            too_many = {"schema": INDEX_SCHEMA, "days": [
                {"source_day": "2021-10-01", "normalized_csv": "first.csv",
                 "v400_manifest": "first.json", "v402_report": "first.report.json"}
            ] * 1827}
            with self.assertRaisesRegex(ValueError, "STAGED_DAY_LIST_REQUIRED"):
                next(iter_staged_days(root, too_many))

    def test_byte_determinism_order_independence(self):
        a = package_days([self.first, self.today])
        b = package_days([self.today, self.first])
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[1], b[1])
        self.assertEqual(a[2], b[2])


if __name__ == "__main__":
    unittest.main()
