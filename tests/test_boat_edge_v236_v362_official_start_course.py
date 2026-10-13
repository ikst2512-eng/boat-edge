"""V362: six labelled official course rows, immutable live research and replay.

Synthetic pre-result source HTML only. No outside network, results or formal use.
"""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v332_live_local_freeze import candidate_from_raw, live_local_freeze
from boat_edge_v343_race_input_replay import verify
from boat_edge_v362_official_start_course_proof import parse_proven_course_rows
from test_boat_edge_v236_v332_live_local_e2e import (
    KEY, PRE, LATE, mock_page, prepare,
)
from test_boat_edge_v236_v339_cross_run_audit import report

ORDER = [2, 1, 3, 4, 5, 6]
ST = {1: ".13", 2: "F.04", 3: ".16", 4: ".17", 5: ".09", 6: ".11"}


def labelled_html(order=ORDER, st=ST):
    lines = [
        "<html><body><table><thead><tr><th colspan='3'>スタート展示</th></tr>",
        "<tr><th>コース</th><th>並び</th><th>ST</th></tr>",
        "</thead><tbody>",
    ]
    for boat in order:
        lines.append(
            "<tr><td colspan='3'><div class='table1_boatImage1'>"
            f"<span class='table1_boatImage1Number is-type{boat}'>{boat}</span>"
            f"<span class='table1_boatImage1Line'><img src='/static_extra/pc/images/img_boat2_{boat}.png'/></span>"
            f"<span class='table1_boatImage1Time'>{st[boat]}</span>"
            "</div></td></tr>"
        )
    lines.append("</tbody></table></body></html>")
    return "".join(lines).encode("utf-8")


def fixture(root):
    prepare(root)
    raw = labelled_html()
    path = root / "data/races" / (KEY + ".json")
    record = json.loads(path.read_bytes())
    for row in record["beforeinfo"]["start_exhibition"]:
        del row["course"]
        row["st"] = ST[row["lane"]]
    record["source_audit"]["beforeinfo"]["sha256"] = hashlib.sha256(raw).hexdigest()
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    html_file = root / "data/raw" / KEY[:8] / "22_12_beforeinfo.html"
    html_file.parent.mkdir(parents=True)
    html_file.write_bytes(raw)
    return raw, path, html_file


class V362LabelledOfficialStartCourse(unittest.TestCase):
    def test_source_table_order_not_boat_number_and_st_exact(self):
        with tempfile.TemporaryDirectory() as d:
            raw, path, _ = fixture(Path(d))
            race = json.loads(path.read_bytes())
            proof = parse_proven_course_rows(raw, race)
            self.assertEqual(proof["course_by_boat"]["1"], 2)
            self.assertEqual(proof["course_by_boat"]["2"], 1)
            self.assertTrue(proof["matched_six_race_card_st_values"])
            self.assertFalse(proof["actual_entry_independently_verified"])
            self.assertFalse(proof["source_authenticity_independently_verified"])

    def test_full_predeadline_freeze_replay_preserves_original_and_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, html_file = fixture(root)
            before = path.read_bytes()
            freeze = live_local_freeze(root, KEY, capture=True,
                                       fetcher=mock_page, clock=lambda: PRE)
            frozen = freeze["record"]
            self.assertEqual(frozen["official_start_course_source_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual(frozen["candidate"]["course_by_boat_exhibition"]["1"], 2)
            self.assertEqual(frozen["candidate"]["course_by_boat_exhibition"]["2"], 1)
            self.assertEqual(frozen["candidate"]["start_course_official_table_proof_model"],
                             "BOAT_EDGE_V362_OFFICIAL_LABELLED_START_COURSE_PROOF")
            self.assertEqual(frozen["research_ranked_120_schema"],
                             "BOAT_EDGE_V360_PREDEADLINE_RESEARCH_RANKED120")
            self.assertEqual(path.read_bytes(), before)
            archive = root / "data/source_captures" / KEY[:8] / KEY
            self.assertEqual((archive / "race_input.json").read_bytes(), before)
            self.assertEqual((archive / "official_start_beforeinfo.html").read_bytes(), raw)
            # Exact archived source reproduces the complete 3x120 even when
            # current mutable input and main's raw html are no longer present.
            path.unlink()
            html_file.unlink()
            result = verify(root, report(digest=freeze["sha256"]))
            self.assertTrue(result["all_supplied_full_120_verified"])
            self.assertTrue(result["rows"][0]["archived_official_start_course_source_replayed"])
            self.assertFalse(result["results_read"])
            self.assertFalse(result["eligible_for_formal_fresh_scoring"])

    def test_missing_table_bytes_or_wrong_declared_sha_never_freezes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, html_file = fixture(root)
            html_file.unlink()
            with self.assertRaisesRegex(ValueError, "START_SOURCE_SAME_RACE_RAW_HTML_MISSING"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertFalse((root / "data/research_local_v332").exists())
            html_file.parent.mkdir(parents=True, exist_ok=True)
            html_file.write_bytes(raw)
            race = json.loads(path.read_bytes())
            race["source_audit"]["beforeinfo"]["sha256"] = "a" * 64
            path.write_text(json.dumps(race))
            with self.assertRaisesRegex(ValueError, "SHA_MISMATCH"):
                live_local_freeze(root, KEY, clock=lambda: PRE)

    def test_changed_start_st_icon_and_table_headers_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, _ = fixture(root)
            race = json.loads(path.read_bytes())
            with self.assertRaisesRegex(ValueError, "ICON_MISMATCH"):
                parse_proven_course_rows(
                    raw.replace(b"img_boat2_2.png", b"img_boat2_1.png"), race)
            with self.assertRaisesRegex(ValueError, "COURSE_HEADERS_INVALID"):
                parse_proven_course_rows(
                    raw.replace("コース".encode(), "艇番".encode()), race)
            with self.assertRaisesRegex(ValueError, "DUPLICATE_BOAT"):
                parse_proven_course_rows(labelled_html([1, 1, 3, 4, 5, 6]), race)
            race["beforeinfo"]["start_exhibition"][0]["st"] = ".30"
            with self.assertRaisesRegex(ValueError, "ST_VS_RACE_MISMATCH"):
                parse_proven_course_rows(raw, race)

    def test_existing_explicit_course_conflict_and_closed_deadline_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, _ = fixture(root)
            race = json.loads(path.read_bytes())
            race["beforeinfo"]["start_exhibition"][0]["course"] = 1
            with self.assertRaisesRegex(ValueError, "DECLARED_COURSE_CONFLICT"):
                parse_proven_course_rows(raw, race)
            with self.assertRaisesRegex(ValueError, "LIVE_WINDOW_CLOSED"):
                candidate_from_raw(path.read_bytes(), KEY, LATE, raw)

    def test_wrong_official_page_type_cannot_supply_start_course_proof(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _, path, _ = fixture(root)
            race = json.loads(path.read_bytes())
            race["source_audit"]["beforeinfo"]["source"] = (
                f"https://www.boatrace.jp/owpc/pc/race/racelist"
                f"?hd={KEY[:8]}&jcd=22&rno=12"
            )
            path.write_text(json.dumps(race))
            with self.assertRaisesRegex(ValueError, "START_SOURCE_NOT_OFFICIAL_BEFOREINFO"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_archived_table_tamper_blocks_replay_even_if_freeze_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, _, _ = fixture(root)
            frozen = live_local_freeze(root, KEY, capture=True,
                                       fetcher=mock_page, clock=lambda: PRE)
            archive = root / "data/source_captures" / KEY[:8] / KEY / "official_start_beforeinfo.html"
            archive.write_bytes(raw + b"tamper")
            with self.assertRaisesRegex(ValueError, "ARCHIVED_OFFICIAL_START_SOURCE_SHA_MISMATCH"):
                verify(root, report(digest=frozen["sha256"]))

    def test_auxiliary_source_symlink_denied_without_network_or_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, html_file = fixture(root)
            html_file.unlink()
            other = root / "local.html"
            other.write_bytes(raw)
            html_file.symlink_to(other)
            with self.assertRaisesRegex(ValueError, "START_SOURCE_RAW_SYMLINK_FORBIDDEN"):
                live_local_freeze(root, KEY, capture=True,
                                  fetcher=lambda _: self.fail("NO_NETWORK_FOR_SYMLINK"),
                                  clock=lambda: PRE)
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_invalid_non_pre_result_and_formal_dates_never_use_archived_parser(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw, path, _ = fixture(root)
            race = json.loads(path.read_bytes())
            race["meta"]["results_seen"] = True
            path.write_text(json.dumps(race))
            with self.assertRaisesRegex(ValueError, "START_SOURCE_PRE_RESULT_ONLY"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_TARGET_EXCLUDED"):
                live_local_freeze(root, "20261001-22-12", clock=lambda: PRE)


if __name__ == "__main__":
    unittest.main()
