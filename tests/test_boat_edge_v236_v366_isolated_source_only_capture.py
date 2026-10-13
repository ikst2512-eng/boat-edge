"""V366 offline mocked official SOURCE ONLY proof tests, never web/results/site write."""
import hashlib
import json
from datetime import timedelta
from unittest.mock import patch
import tempfile as real_tempfile
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v366_isolated_source_only_capture import (
    capture_source_only, _source_url,
)
from test_boat_edge_v236_v365_source_only_selection_contract import setup_selection
from test_boat_edge_v236_v364_v230_v336_selection_contract import NOW, KEY
from test_boat_edge_v236_v362_official_start_course import labelled_html


def source_pages():
    start = labelled_html()
    # Match the REAL official racelist's own 12-tab navigation, not merely
    # registrations in a table. Reuse the matching synthetic predeadline tab
    # with only its exact official page endpoint changed.
    official_nav = start.split(b"<table><thead><tr><th colspan='3'>", 1)[0]
    official_nav = official_nav.replace(b"/beforeinfo?", b"/racelist?")
    racelist = (
        official_nav + b"<table>"
        + "".join(f"<tr><td>{4000+lane} / A1</td></tr>" for lane in range(1, 7)).encode("utf8")
        + b"</table></body></html>"
    )
    before_table = (
        "<table><thead><tr><th>展示タイム</th></tr></thead><tbody>"
        + "".join(
            f"<tr><td>{lane}</td><td>R</td><td>M</td><td>T</td>"
            f"<td>6.{80+lane}</td><td>0.0</td></tr>" for lane in range(1, 7)
        )
        + "</tbody></table>"
    ).encode("utf8")
    beforeinfo = start.replace(b"</body></html>", before_table + b"</body></html>")
    return racelist, beforeinfo


def setup_case(root, snapshot=True):
    setup_selection(root)
    race_path = root / "data/races" / (KEY + ".json")
    obj = json.loads(race_path.read_bytes())
    for lane, racer in enumerate(obj["racers"], 1):
        racer["registration_no"] = str(4000 + lane)
    race_path.write_text(json.dumps(obj, ensure_ascii=False))
    index = (root / "data/today.json").read_bytes()
    original = race_path.read_bytes()
    old_snap = None
    if snapshot:
        p = root / "data/site_prediction_snapshots" / (KEY + ".json")
        p.parent.mkdir(parents=True, exist_ok=True)
        old_snap = b"INVALID_UTF8_PREDICTION_NEVER_OPENED_OR_OVERWRITTEN" + bytes([255])
        p.write_bytes(old_snap)
    return original, index, old_snap


def fetcher_for(pages, requests=None):
    def fetch(url):
        if requests is not None:
            requests.append(url)
        if "/racelist?" in url:
            raw = pages[0]
        elif "/beforeinfo?" in url:
            raw = pages[1]
        else:
            raise AssertionError("ONLY_OFFICIAL_RACELIST_OR_BEFOREINFO")
        return raw, "text/html", url
    return fetch


class V366SourceOnlyProof(unittest.TestCase):
    def test_source_only_capture_is_immutable_and_keeps_site_data_byte_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            race_bytes, index_bytes, first = setup_case(root)
            pages = source_pages()
            requests = []
            proof = capture_source_only(
                root, KEY, clock=lambda: NOW, fetcher=fetcher_for(pages, requests))
            self.assertTrue(proof["source_only_capture_completed"])
            self.assertFalse(proof["research_freeze_performed"])
            self.assertEqual(requests, [
                _source_url(KEY, "racelist"), _source_url(KEY, "beforeinfo")])
            folder = root / proof["path"]
            record = json.loads((folder / "manifest.json").read_bytes())
            self.assertEqual(
                hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest(),
                proof["manifest_sha256"])
            self.assertEqual(record["input_race_sha256"], hashlib.sha256(race_bytes).hexdigest())
            self.assertEqual(record["registered_racers_matched"],
                             [str(4000 + lane) for lane in range(1, 7)])
            self.assertTrue(record["official_exhibition_coverage"]["six_boat_complete"])
            self.assertEqual(record["official_start_course_proof"]["course_by_boat"]["1"], 2)
            self.assertEqual(record["official_start_course_proof"]["course_by_boat"]["2"], 1)
            for name, raw in zip(("racelist", "beforeinfo"), pages):
                self.assertEqual((folder / (name + ".html")).read_bytes(), raw)
                self.assertEqual(record["sources"][name]["sha256"],
                                 hashlib.sha256(raw).hexdigest())
            self.assertEqual((root / "data/races" / (KEY + ".json")).read_bytes(), race_bytes)
            self.assertEqual((root / "data/today.json").read_bytes(), index_bytes)
            self.assertEqual(
                (root / "data/site_prediction_snapshots" / (KEY + ".json")).read_bytes(),
                first)
            self.assertFalse((root / "data/research_local_v332").exists())
            self.assertFalse((root / "data/source_captures").exists())
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=lambda _: self.fail("NO_RETRY_FETCH"))

    def test_official_six_racer_mismatch_stops_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            pages = source_pages()
            wrong_list = pages[0].replace(b"4006 / A1", b"4444 / A1")
            with self.assertRaisesRegex(ValueError, "SIX_REGISTERED_RACERS"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=fetcher_for((wrong_list, pages[1])))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_official_beforeinfo_st_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            first, before = source_pages()
            before = before.replace(b"F.04", b"F.05")
            # A row still parses but if the identity/ST is changed in the
            # source itself, parse proof must match that source.
            before = before.replace(b"img_boat2_2.png", b"img_boat2_1.png")
            with self.assertRaisesRegex(ValueError, "ICON_MISMATCH"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=fetcher_for((first, before)))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_racelist_also_must_identify_selected_race_and_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            original, before = source_pages()
            for altered in (
                original.replace(b"/racelist?rno=12", b"/racelist?rno=11", 1),
                original.replace(b"hd=20261013", b"hd=20261012", 1),
                original.replace(b"jcd=22", b"jcd=21", 1),
                original.replace(b"<td class='is-activeColor1'>16:40",
                                 b"<td class='is-activeColor1'>16:41"),
                original.replace(b"/racelist?", b"/beforeinfo?", 1),
            ):
                with self.subTest(altered=altered[:50]):
                    with self.assertRaisesRegex(ValueError,
                                                 "ACTIVE_RACE_TAB_|ACTIVE_RACE_DEADLINE_"):
                        capture_source_only(root, KEY, clock=lambda: NOW,
                                            fetcher=fetcher_for((altered, before)))
                    self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_official_wrong_active_race_and_deadline_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            first, before = source_pages()
            for altered in (
                before.replace(b"jcd=22", b"jcd=21", 1),
                before.replace(b"<td class='is-activeColor1'>16:40",
                               b"<td class='is-activeColor1'>16:39"),
            ):
                with self.assertRaisesRegex(ValueError, "MISMATCH"):
                    capture_source_only(root, KEY, clock=lambda: NOW,
                                        fetcher=fetcher_for((first, altered)))
                self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_network_redirect_and_result_endpoint_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            pages = source_pages()
            def redirect(url):
                return pages[0], "text/html", url.replace("/racelist?", "/result?")
            with self.assertRaisesRegex(ValueError, "UNVERIFIED_HTML_RESPONSE"):
                capture_source_only(root, KEY, clock=lambda: NOW, fetcher=redirect)
            with self.assertRaisesRegex(ValueError, "NON_PRE_RESULT_ENDPOINT"):
                _source_url(KEY, "result")
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_explicit_withdrawal_even_with_six_rows_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            reg, bef = source_pages()
            reg = reg.replace(b"</body>", "欠場".encode() + b"</body>")
            with self.assertRaisesRegex(ValueError, "WITHDRAWAL_OR_ABSENCE_SIGNAL"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=fetcher_for((reg, bef)))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_formal_target_rejected_before_local_inputs_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_TARGET_EXCLUDED"):
                capture_source_only(root, "20261001-22-12",
                                    clock=lambda: self.fail("NO_FORMAL_CLOCK_READ"),
                                    fetcher=lambda _: self.fail("NO_FORMAL_FETCH"))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_close_during_network_does_not_persist_late_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            pages = source_pages()
            current = [NOW]
            def too_slow(url):
                current[0] = NOW + timedelta(minutes=12)
                return fetcher_for(pages)(url)
            with self.assertRaisesRegex(ValueError, "FETCH_ENDED_OUTSIDE_LIVE_WINDOW"):
                capture_source_only(root, KEY, clock=lambda: current[0],
                                    fetcher=too_slow)
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_deadline_during_bundle_staging_never_publishes_source_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, _, original_prediction = setup_case(root)
            instant = [NOW]
            actual_stage = real_tempfile.TemporaryDirectory
            def after_stage_starts(*args, **kwargs):
                instant[0] = NOW + timedelta(minutes=12)
                return actual_stage(*args, **kwargs)
            with patch("boat_edge_v366_isolated_source_only_capture.tempfile.TemporaryDirectory",
                       side_effect=after_stage_starts):
                with self.assertRaisesRegex(ValueError, "WINDOW_CLOSED_DURING_SOURCE_STAGING"):
                    capture_source_only(root, KEY, clock=lambda: instant[0],
                                        fetcher=fetcher_for(source_pages()))
            self.assertFalse((root / "data/research_source_only_v366" /
                              KEY[:8] / KEY).exists())
            self.assertEqual(
                (root / "data/site_prediction_snapshots" / (KEY + ".json")).read_bytes(),
                original_prediction)
            self.assertEqual(
                (root / "data/races" / (KEY + ".json")).read_bytes(),
                first)

    def test_change_race_during_fetch_refuses_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            pages = source_pages()
            def concurrent_change(url):
                if "/beforeinfo?" in url:
                    path = root / "data/races" / (KEY + ".json")
                    race = json.loads(path.read_bytes())
                    race["changed_during_fetch"] = "new_unverified"
                    path.write_text(json.dumps(race))
                return fetcher_for(pages)(url)
            with self.assertRaisesRegex(ValueError, "RACE_CHANGED_DURING_SOURCE_FETCH"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=concurrent_change)
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_closed_and_locked_index_never_call_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            for clock in (NOW + timedelta(minutes=10),
                          NOW - timedelta(minutes=30)):
                with self.assertRaisesRegex(ValueError, "NOT_CURRENTLY_ELIGIBLE"):
                    capture_source_only(root, KEY, clock=lambda: clock,
                                        fetcher=lambda _: self.fail("NO_NETWORK"))
            path = root / "data/today.json"
            index = json.loads(path.read_bytes())
            index["results_seen"] = True
            path.write_text(json.dumps(index))
            with self.assertRaisesRegex(ValueError, "NOT_CURRENTLY_ELIGIBLE"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=lambda _: self.fail("NO_NETWORK"))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_formal_fresh_date_never_considered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_TARGET_EXCLUDED"):
                capture_source_only(root, "20261001-22-12", clock=lambda: NOW,
                                    fetcher=lambda _: self.fail("NO_NETWORK"))


if __name__ == "__main__":
    unittest.main()
