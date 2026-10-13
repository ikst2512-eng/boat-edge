"""V408 synthetic fixture-only test; no actual B or K source files or API calls."""
import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace as E
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import JST
from boat_edge_v402_offline_b_k_reconciliation import B_SCHEMA
from boat_edge_v407_local_performance_bridge import stage_local_entries, load_local_txt_sources
from boat_edge_v408_local_b_program_bridge import (
    MODEL, parse_local_b_txt, parse_local_b_files, stage_b_schedule,
)

DAY = date(2026, 9, 30)
B_KEY = "202609300101"


def entries(day=DAY, race=1, venue="01"):
    return [E(race_date=day, venue_code=venue, race_number=race,
              boat_number=i, racer_number=4500+i) for i in range(1, 7)]


def races(day=DAY, race=1, venue="01"):
    return [E(race_date=day, venue_code=venue, race_number=race)]


def closes(day=DAY, race=1, venue="01", hour=8, minute=35):
    return [E(venue_code=venue, race_number=race,
              close_time=datetime(day.year, day.month, day.day,
                                  hour, minute, tzinfo=JST))]


def kentries(day=DAY):
    return [E(race_date=day, venue_code="01", race_number=1,
              boat_number=i, racer_number=4500+i,
              entrance_position=i, result_position=i)
            for i in range(1,7)]


class V408LocalProgramBridgeTests(unittest.TestCase):
    def test_exact_six_boat_target_stage(self):
        result = stage_b_schedule(entries(), closes(), races(), DAY)
        self.assertEqual(result["schema"], B_SCHEMA)
        self.assertEqual(result["source_day"], DAY.isoformat())
        self.assertEqual(result["races"][0]["race_key"], B_KEY)
        self.assertEqual(result["races"][0]["deadline_jst"],
                         "2026-09-30T08:35:00+09:00")
        self.assertEqual(result["races"][0]["entries"],
                         [{"boat":i,"racer_id":str(4500+i)} for i in range(1,7)])

    def test_operator_K_stage_can_use_parsed_B_directly(self):
        b = stage_b_schedule(entries(), closes(), races(), DAY)
        publication = {
            "schema": "BOAT_EDGE_V407_OPERATOR_K_PUBLICATION_TIMES_V1",
            "source_day": DAY.isoformat(),
            "races": {B_KEY: "2026-09-30T21:00:00+09:00"},
        }
        k = stage_local_entries(kentries(), b, publication)
        self.assertEqual(len(k["races"]), 1)
        self.assertEqual(k["races"][0]["entries"][0]["racer_id"], "4501")
        self.assertEqual(k["excluded"], [])

    def test_reverse_order_stable(self):
        a = stage_b_schedule(entries(), closes(), races(), DAY)
        b = stage_b_schedule(list(reversed(entries())), closes(), races(), DAY)
        self.assertEqual(a, b)

    def test_multiple_races_are_sorted(self):
        e = entries(race=2) + entries()
        r = races(race=2) + races()
        c = closes(race=2) + closes()
        actual = stage_b_schedule(e,c,r,DAY)
        self.assertEqual([x["race_key"] for x in actual["races"]],
                         [B_KEY, "202609300102"])

    def test_missing_boat_hard_fails(self):
        with self.assertRaisesRegex(ValueError, "B_REQUIRES_SIX_DISTINCT_BOATS"):
            stage_b_schedule(entries()[:-1],closes(),races(),DAY)

    def test_duplicate_racer_hard_fails(self):
        e = entries()
        e[0].racer_number = e[1].racer_number
        with self.assertRaisesRegex(ValueError, "B_REQUIRES_SIX_DISTINCT_BOATS_AND_RACERS"):
            stage_b_schedule(e,closes(),races(),DAY)

    def test_duplicate_boat_hard_fails(self):
        e = entries()
        e[0].boat_number = 2
        with self.assertRaisesRegex(ValueError, "B_DUPLICATE_BOAT"):
            stage_b_schedule(e,closes(),races(),DAY)

    def test_missing_close_never_invented(self):
        with self.assertRaisesRegex(ValueError, "B_RACE_LIST_EMPTY_OR_OVER_LIMIT"):
            stage_b_schedule(entries(),[],races(),DAY)
        with self.assertRaisesRegex(ValueError, "B_PARSER_RACE_OR_CLOSE_COVERAGE_INCOMPLETE"):
            stage_b_schedule(entries()+entries(race=2),closes(),
                             races()+races(race=2),DAY)

    def test_duplicate_close_fails(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_B_CLOSE"):
            stage_b_schedule(entries(),closes()+closes(),races(),DAY)

    def test_close_wrong_day_rejected(self):
        c=closes()
        c[0].close_time += timedelta(days=1)
        with self.assertRaisesRegex(ValueError,"B_CLOSE_WRONG_OR_MISSING_DAY"):
            stage_b_schedule(entries(),c,races(),DAY)

    def test_non_jst_close_rejected(self):
        c=closes()
        c[0].close_time=c[0].close_time.replace(tzinfo=None)
        with self.assertRaisesRegex(ValueError,"EXPLICIT_JST_OFFSET_REQUIRED"):
            stage_b_schedule(entries(),c,races(),DAY)

    def test_exhibition_or_finish_never_copied_from_B_entry(self):
        e=entries()
        e[0].result_position = 1
        e[0].entrance_position = 4
        stage=stage_b_schedule(e,closes(),races(),DAY)
        self.assertNotIn("result_position",str(stage))
        self.assertNotIn("entrance_position",str(stage))

    def test_incomplete_parser_race_inventory_fails(self):
        with self.assertRaisesRegex(ValueError,"B_ENTRY_WITHOUT_RACE"):
            stage_b_schedule(entries(),closes(race=2),races(race=2),DAY)
        with self.assertRaisesRegex(ValueError,"B_PARSER_RACE_OR_CLOSE_COVERAGE_INCOMPLETE"):
            stage_b_schedule(entries(),closes()+closes(race=2),
                             races()+races(race=2),DAY)

    def test_day_or_venue_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"B_PARSER_INVALID_DATE_VENUE_RACE"):
            stage_b_schedule(entries(day=date(2026,9,29)),closes(),races(),DAY)
        with self.assertRaisesRegex(ValueError,"B_ENTRY_WITHOUT_RACE"):
            stage_b_schedule(entries(venue="02"),closes(),races(),DAY)

    def test_bad_racer_rejected(self):
        e=entries()
        e[0].racer_number=None
        with self.assertRaisesRegex(ValueError,"B_PARSER_INVALID_RACER"):
            stage_b_schedule(e,closes(),races(),DAY)

    def test_protected_from_20261001(self):
        with self.assertRaisesRegex(ValueError,"PROTECTED_OR_OUTSIDE_HISTORICAL_B_DATE"):
            stage_b_schedule([],[],[],date(2026,10,1))

    def test_parser_requires_bytes_and_strict_cp932(self):
        with self.assertRaisesRegex(ValueError,"LOCAL_B_TEXT_BYTES_REQUIRED"):
            parse_local_b_txt(b"",DAY)
        with self.assertRaisesRegex(ValueError,"LOCAL_B_CP932_DECODE_FAILED"):
            parse_local_b_txt(b"\x81",DAY)

    def test_secure_multi_venue_local_directory_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"a.txt").write_bytes(b"first locally generated B")
            (root/"b.TXT").write_bytes(b"second locally generated B")
            (root/"ignore.json").write_text("{}")
            sources=load_local_txt_sources(local_dir=root)
            self.assertEqual(sorted(sources),["a.txt","b.TXT"])
            self.assertEqual(sources["a.txt"],b"first locally generated B")
            self.assertEqual(len(sources),2)

    def test_local_dir_does_not_follow_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"b.txt").write_bytes(b"locally invented B")
            (root/"alias.txt").symlink_to(root/"b.txt")
            with self.assertRaisesRegex(ValueError,"LOCAL_TXT_FILE_UNSAFE_OR_MISSING"):
                load_local_txt_sources(local_dir=root)

    def test_directory_with_no_txt_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"ignore.json").write_text("{}")
            with self.assertRaisesRegex(ValueError,"LOCAL_TXT_FILE_COUNT_OUT_OF_RANGE"):
                load_local_txt_sources(local_dir=root)

    def test_two_venue_parser_processes_all_local_files(self):
        try:
            import importlib.metadata
            importlib.metadata.version("boatrace-lzh")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("optional parser is not installed")
        def invented_b(code,name,register_start):
            lines=[
                "STARTB", f"{code}BBGN",
                f"ボートレース{name}   ９月３０日   架空開催",
                "＊＊＊ 番組表 ＊＊＊",
                f"第１日    2026/ 9/30      ボートレース{name}",
                "　１Ｒ  一般     Ｈ１８００ｍ  電話投票締切予定０８：３５",
                "艇 選手 登録 選手名",
            ]
            lines.extend(
                f"{i} {register_start+i}架空選手35東京53B1 5.46 35.44 6.17 50.00 53 34.70 59 29.53"
                for i in range(1,7)
            )
            return ("\n".join(lines)+"\n").encode("cp932")
        sources={
            "kiryu.TXT":invented_b("01","桐生",4500),
            "toda.txt":invented_b("02","戸田",4600),
        }
        stage=parse_local_b_files(sources,DAY)
        self.assertEqual(len(stage["races"]),2)
        with self.assertRaisesRegex(ValueError, "LOCAL_B_UNPARSEABLE_SOURCE_FILE"):
            parse_local_b_files({**sources,
                                 "unparsable.txt": b"SYNTHETIC GARBAGE"*12},DAY)
        self.assertEqual([r["race_key"] for r in stage["races"]],
                         ["202609300101","202609300201"])
        self.assertEqual(stage["races"][0]["entries"][0]["racer_id"],"4501")
        self.assertEqual(stage["races"][1]["entries"][0]["racer_id"],"4601")

    def test_optional_library_actual_scheduleparser_on_invented_local_B(self):
        try:
            import importlib.metadata
            importlib.metadata.version("boatrace-lzh")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("optional test parser is not installed")
        lines = [
            "STARTB", "01BBGN",
            "ボートレース桐生   ９月３０日   架空開催",
            "＊＊＊ 番組表 ＊＊＊",
            "第１日      2026/ 9/30          ボートレース桐生",
            "　１Ｒ  一般      Ｈ１８００ｍ  電話投票締切予定０８：３５",
            "艇 選手 登録 選手名 成績",
        ]
        for i in range(1,7):
            lines.append(f"{i} {4500+i}架空選手35東京53B1 5.46 35.44 6.17 50.00 53 34.70 59 29.53")
        raw=("\n".join(lines)+"\n").encode("cp932")
        staged=parse_local_b_txt(raw,DAY)
        self.assertEqual(staged["schema"],B_SCHEMA)
        self.assertEqual(len(staged["races"]),1)
        self.assertEqual(len(staged["races"][0]["entries"]),6)
        self.assertEqual(staged["races"][0]["deadline_jst"],
                         "2026-09-30T08:35:00+09:00")


if __name__ == "__main__":
    unittest.main()
