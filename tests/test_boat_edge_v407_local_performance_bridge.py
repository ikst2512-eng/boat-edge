"""Synthetic-only regression for V407 locally parsed K to V401 bridge."""
import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace as Entry
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import JST
from boat_edge_v401_staged_k_bridge import normalize
from boat_edge_v402_offline_b_k_reconciliation import reconcile, B_MANIFEST
from boat_edge_v404_asof_history_features import TARGET_SCHEMA, snapshot
from boat_edge_v405_batch_asof_history_features import build_batch
from boat_edge_v406_offline_history_packager import package_days
from boat_edge_v407_local_performance_bridge import (
    B_SCHEMA, PUB_SCHEMA, STAGING_SCHEMA, parse_local_txt, stage_local_entries,
    parse_local_k_files, load_local_txt_sources,
)

DAY = date(2026, 9, 30)
KEY = "202609300101"
KEY2 = "202609300102"
KEY3 = "202609300103"


def b_race(key):
    return {
        "race_key": key, "deadline_jst": DAY.isoformat() + "T08:35:00+09:00",
        "entries": [{"boat": i, "racer_id": str(4500 + i)}
                    for i in range(1, 7)],
    }


def b_stage(*keys):
    return {"schema": B_SCHEMA, "source_day": DAY.isoformat(),
            "races": [b_race(k) for k in keys]}


def pub(*keys):
    return {"schema": PUB_SCHEMA, "source_day": DAY.isoformat(),
            "races": {key: "2026-09-30T21:00:00+09:00" for key in keys}}


def k_entries(race_no=1):
    return [Entry(
        race_date=DAY, venue_code="01", race_number=race_no,
        boat_number=i, racer_number=4500 + i,
        entrance_position=7-i, result_position=i,
    ) for i in range(1, 7)]


def k_manifest(source_raw, staged_raw):
    return {
        "schema": "BOAT_EDGE_V401_K_SOURCE_PROVENANCE_V1",
        "raw_source_sha256": hashlib.sha256(source_raw).hexdigest(),
        "staged_sha256": hashlib.sha256(staged_raw).hexdigest(),
        "source_name": "SYNTHETIC_SELF_CREATED",
        "source_locator": "fixture:local-only",
        "rights_evidence": "synthetic author-created rows, no real data",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": "synthetic fixture V407",
        "parser_name": "synthetic-entry-object",
        "parser_version": "test1",
        "retrieved_at_jst": "2026-09-30T22:00:00+09:00",
    }


class V407OfflineNativeBridgeTests(unittest.TestCase):
    def test_valid_six_boat_maps_to_v401(self):
        stage = stage_local_entries(k_entries(), b_stage(KEY), pub(KEY))
        self.assertEqual(stage["schema"], STAGING_SCHEMA)
        self.assertEqual(stage["races"][0]["race_key"], KEY)
        self.assertEqual(stage["races"][0]["entries"][0],
                         {"boat": 1, "racer_id": "4501",
                          "actual_course": 6, "finish": 1})
        self.assertEqual(stage["excluded"], [])

    def test_out_of_order_parsed_boats_sort_deterministically(self):
        a = stage_local_entries(k_entries(), b_stage(KEY), pub(KEY))
        b = stage_local_entries(list(reversed(k_entries())), b_stage(KEY), pub(KEY))
        self.assertEqual(a, b)

    def test_native_v401_normalization_integration(self):
        stage = stage_local_entries(k_entries(), b_stage(KEY), pub(KEY))
        staged_raw = json.dumps(stage, ensure_ascii=False).encode()
        raw = b"SYNTHETIC_NOT_A_REAL_K_ARCHIVE"
        csv_bytes, manifest, audit = normalize(
            raw, staged_raw, k_manifest(raw, staged_raw),
            datetime(2026, 10, 1, tzinfo=JST),
        )
        self.assertEqual(audit["included_races"], 1)
        self.assertEqual(audit["excluded_races"], 0)
        self.assertEqual(len(csv_bytes.decode().splitlines()), 7)
        self.assertEqual(manifest["csv_sha256"], hashlib.sha256(csv_bytes).hexdigest())
        self.assertFalse(audit["model_promotion_authorized"])

    def test_full_v407_to_v401_v402_v406_v404_v405_synthetic_handoff(self):
        # Entire authorized-local path is tested with invented results only.
        b = b_stage(KEY)
        k = stage_local_entries(k_entries(), b, pub(KEY))
        kraw = json.dumps(k, sort_keys=True, separators=(",", ":")).encode()
        source_raw = b"SYNTHETIC_K_SOURCE_BYTES_NOT_A_REAL_ARCHIVE"
        csv_raw, manifest, audit401 = normalize(
            source_raw, kraw, k_manifest(source_raw, kraw),
            datetime(2026, 10, 1, tzinfo=JST),
        )
        braw = json.dumps(b, sort_keys=True, separators=(",", ":")).encode()
        b_source = b"SYNTHETIC_B_SOURCE_BYTES_NOT_A_REAL_ARCHIVE"
        bman = {
            "schema": B_MANIFEST,
            "source_sha256": hashlib.sha256(b_source).hexdigest(),
            "staged_sha256": hashlib.sha256(braw).hexdigest(),
            "source_locator": "fixture:invented-only",
            "rights_evidence": "author-created synthetic B, not real permission",
            "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
            "parser_name": "fake-B-roster",
            "parser_version": "test-only",
            "retrieved_at_jst": "2026-09-29T20:00:00+09:00",
        }
        report402 = reconcile(
            csv_raw, manifest, audit401, b_source, braw, bman,
            datetime(2026, 10, 1, tzinfo=JST),
        )
        self.assertEqual(report402["reconciled_six_boat_races"], 1)
        joined, joint_man, audit406 = package_days([{
            "source_day": DAY.isoformat(), "k_csv": csv_raw,
            "k_manifest": manifest, "v402_report": report402,
        }])
        self.assertEqual(joined, csv_raw)
        self.assertEqual(audit406["normalized_complete_races"], 1)
        target = {
            "schema": TARGET_SCHEMA,
            "race_key": KEY3,
            "deadline_jst": "2026-09-30T23:35:00+09:00",
            "entries": b_race(KEY3)["entries"],
        }
        single = snapshot(joined, joint_man, target)
        batch = build_batch(joined, joint_man, [target])["snapshots"][0]
        self.assertEqual(single, batch)
        self.assertEqual(batch["historical_races_eligible_before_target"], 1)
        self.assertFalse(batch["accuracy_improvement_proven"])
        self.assertFalse(report402["license_independently_verified"])
        self.assertFalse(audit406["historic_source_rights_independently_verified"])

    def test_missing_k_race_explicit_source_ambiguous_exclusion(self):
        stage = stage_local_entries(k_entries(), b_stage(KEY, KEY2), pub(KEY))
        self.assertEqual(stage["excluded"],
                         [{"race_key": KEY2, "reason": "SOURCE_AMBIGUOUS"}])

    def test_five_entry_race_excluded_without_imputation(self):
        stage = stage_local_entries(k_entries()[:5] + k_entries(2),
                                    b_stage(KEY, KEY2), pub(KEY2))
        self.assertEqual(stage["excluded"],
                         [{"race_key": KEY, "reason": "INCOMPLETE_RESULTS"}])

    def test_nonstandard_finish_marked_exclusion(self):
        first = k_entries()
        first[0].result_position = None
        stage = stage_local_entries(first + k_entries(2),
                                    b_stage(KEY, KEY2), pub(KEY2))
        self.assertEqual(stage["excluded"],
                         [{"race_key": KEY, "reason": "NON_STANDARD_FINISH"}])

    def test_missing_actual_course_marked_exclusion(self):
        first = k_entries()
        first[0].entrance_position = None
        stage = stage_local_entries(first + k_entries(2),
                                    b_stage(KEY, KEY2), pub(KEY2))
        self.assertEqual(stage["excluded"],
                         [{"race_key": KEY, "reason": "UNVERIFIED_ACTUAL_COURSE"}])

    def test_wrong_racer_id_not_hidden_by_exclusion(self):
        first = k_entries()
        first[0].racer_number = 4999
        with self.assertRaisesRegex(ValueError, "B_K_RACER_NUMBER_MISMATCH"):
            stage_local_entries(first, b_stage(KEY), pub(KEY))

    def test_duplicate_boat_hard_fails(self):
        first = k_entries()
        first[1].boat_number = 1
        with self.assertRaisesRegex(ValueError, "K_DUPLICATE_OR_MISSING_BOAT_ID"):
            stage_local_entries(first, b_stage(KEY), pub(KEY))

    def test_wrong_actual_course_permutation_hard_fails(self):
        first = k_entries()
        first[1].entrance_position = 6
        with self.assertRaisesRegex(ValueError, "K_ACTUAL_COURSE_DUPLICATE"):
            stage_local_entries(first, b_stage(KEY), pub(KEY))

    def test_wrong_finish_permutation_hard_fails(self):
        first = k_entries()
        first[1].result_position = 1
        with self.assertRaisesRegex(ValueError, "K_FINISH_DUPLICATE"):
            stage_local_entries(first, b_stage(KEY), pub(KEY))

    def test_publication_missing_never_invented(self):
        with self.assertRaisesRegex(ValueError, "K_PUBLICATION_PROVENANCE_MISSING"):
            stage_local_entries(k_entries(), b_stage(KEY), pub())

    def test_publication_must_be_after_b_deadline(self):
        published = pub(KEY)
        published["races"][KEY] = "2026-09-30T08:35:00+09:00"
        with self.assertRaisesRegex(ValueError, "K_PUBLICATION_NOT_AFTER_B_DEADLINE"):
            stage_local_entries(k_entries(), b_stage(KEY), published)

    def test_k_publication_requires_explicit_jst(self):
        published = pub(KEY)
        published["races"][KEY] = "2026-09-30T21:00:00Z"
        with self.assertRaisesRegex(ValueError, "EXPLICIT_JST_OFFSET_REQUIRED"):
            stage_local_entries(k_entries(), b_stage(KEY), published)

    def test_extra_publication_must_not_go_unobserved(self):
        with self.assertRaisesRegex(ValueError, "K_PUBLICATION_MAP_MUST_COVER_EXACT_INCLUDED"):
            stage_local_entries(k_entries(), b_stage(KEY), pub(KEY, KEY2))

    def test_unlisted_race_hard_fails(self):
        with self.assertRaisesRegex(ValueError, "K_RACE_NOT_IN_OPERATOR_B_STAGE"):
            stage_local_entries(k_entries(2), b_stage(KEY), pub(KEY))

    def test_20261001_fresh_protection(self):
        changed = deepcopy(b_stage(KEY))
        changed["source_day"] = "2026-10-01"
        changed["races"][0]["race_key"] = "202610010101"
        changed["races"][0]["deadline_jst"] = "2026-10-01T08:35:00+09:00"
        changed_pub = pub(KEY)
        changed_pub["source_day"] = "2026-10-01"
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_UNSUPPORTED_TARGET_DATE"):
            stage_local_entries(k_entries(), changed, changed_pub)

    def test_parsed_k_missing_date_never_assumed(self):
        first = k_entries()
        first[0].race_date = None
        with self.assertRaisesRegex(ValueError, "K_PARSER_INVALID_RACE_DATE_VENUE_OR_BOAT"):
            stage_local_entries(first, b_stage(KEY), pub(KEY))

    def test_parser_input_never_downloads_or_ignores_decode_errors(self):
        with self.assertRaisesRegex(ValueError, "LOCAL_K_TEXT_BYTES_REQUIRED"):
            parse_local_txt(b"")
        with self.assertRaisesRegex(ValueError, "LOCAL_K_CP932_DECODE_FAILED"):
            parse_local_txt(b"\x81")
        # Import of PerformanceParser, never import or instantiate Downloader.
        with patch.dict(sys.modules, {"boatrace_lzh": None,
                                      "boatrace_lzh.performance": None}):
            with self.assertRaisesRegex(RuntimeError, "OPTIONAL_LOCAL_BOATRACE_LZH_PARSER_NOT_INSTALLED"):
                parse_local_txt(b"synthetic local text")

    def test_multi_venue_K_directory_parser_with_exact_B_rosters(self):
        try:
            import importlib.metadata
            importlib.metadata.version("boatrace-lzh")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("optional parser not installed")
        def synthetic_K(code,name):
            lines=[
                "STARTK", f"{code}KBGN",
                f"{name}［成績］     9/30     架空開催　第 1日",
                "第 1日       2026/ 9/30      ボートレース",
                "1R      一般      H1800m   晴れ  風 南 2m 波 2cm",
                "着 艇 登番 選手名 ﾓｰﾀｰ ﾎﾞｰﾄ 展示 進入 ST ﾚｰｽﾀｲﾑ",
            ]
            lines.extend(
                f"   {i:02d}  {i} {4500+i} 架　空　選　手 53   59 6.71 {i} 0.07 2.03.6"
                for i in range(1,7)
            )
            return ("\n".join(lines)+"\n"+" "*200).encode("cp932")
        sources={
            "kiryu.txt":synthetic_K("01","桐　生"),
            "toda.TXT":synthetic_K("02","戸　田"),
        }
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            for name,raw in sources.items():
                (root/name).write_bytes(raw)
            loaded=load_local_txt_sources(local_dir=root)
            self.assertEqual(sorted(loaded),["kiryu.txt","toda.TXT"])
            entries=parse_local_k_files(loaded)
            self.assertEqual(len(entries),12)
            with self.assertRaisesRegex(ValueError, "LOCAL_K_UNPARSEABLE_SOURCE_FILE"):
                parse_local_k_files({**loaded,
                                     "unparsable.txt": b"SYNTHETIC GARBAGE"*12})
            b=b_stage(KEY,"202609300201")
            k=stage_local_entries(entries,b,pub(KEY,"202609300201"))
            self.assertEqual([r["race_key"] for r in k["races"]],
                             ["202609300101","202609300201"])
            self.assertEqual(len(k["races"]),2)

    def test_actual_optional_performance_parser_on_invented_cp932_k_text(self):
        # This is invented local K-style text, NOT an official race or a
        # downloaded result. It verifies the real optional parser interface.
        try:
            import importlib.metadata
            importlib.metadata.version("boatrace-lzh")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("optional parser not installed")
        heading = [
            "STARTK", "01KBGN",
            "桐　生［成績］       9/30      架空検証の開催　第 1日",
            "    第 1日      2026/ 9/30       ボートレース桐生",
            "    1R       一般         H1800m  晴れ  風  南 2m  波 2cm",
            "   着 艇 登番 選手名 ﾓｰﾀｰ ﾎﾞｰﾄ 展示 進入 ST ﾚｰｽﾀｲﾑ",
        ]
        for i in range(1, 7):
            heading.append(
                f"   {i:02d}  {i} {4500+i} 架　空　選　手 "
                f"53 59 6.71 {i} 0.07 2.03.6"
            )
        raw = ("\n".join(heading) + "\n" + " "*200).encode("cp932")
        parsed = parse_local_txt(raw)
        self.assertEqual(len(parsed), 6)
        stage = stage_local_entries(parsed, b_stage(KEY), pub(KEY))
        self.assertEqual(len(stage["races"]), 1)
        self.assertEqual(len(stage["races"][0]["entries"]), 6)

    def test_forged_b_target_actual_course_field_rejected(self):
        b = b_stage(KEY)
        b["races"][0]["entries"][0]["actual_course"] = 1
        with self.assertRaisesRegex(ValueError, "TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE"):
            stage_local_entries(k_entries(), b, pub(KEY))

    def test_no_complete_records_rejected(self):
        with self.assertRaisesRegex(ValueError, "NO_COMPLETE_OPERATOR_STAGED_K_RACES"):
            stage_local_entries([], b_stage(KEY), pub())


if __name__ == "__main__":
    unittest.main()
