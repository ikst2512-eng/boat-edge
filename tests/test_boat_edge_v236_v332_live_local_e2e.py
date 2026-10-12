"""V332 genuine end-to-end candidate+raw-capture+immutable freeze tests (mock HTTP)."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from boat_edge_v315_source_capture import capture_one
from boat_edge_v332_live_local_freeze import live_local_freeze

KEY = "20261013-22-12"
DEADLINE = "2026-10-13T16:40:00+09:00"
JST = timezone(timedelta(hours=9))
PRE = datetime(2026, 10, 13, 16, 20, tzinfo=JST)
LATE = datetime(2026, 10, 13, 16, 41, tzinfo=JST)
URLS = {
    "official": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261013&jcd=22&rno=12",
    "boaters": "https://boaters-boatrace.com/race/20261013-22-12",
    "kyoteibiyori": "https://kyoteibiyori.com/race/20261013-22-12",
}


def mock_page(url):
    return (("<html>PROVISIONAL-TEST-PAGE-" + url + "</html>") * 3).encode(), "text/html", url


def prepare(root, meta_overrides=None, source_overrides=None, result_marker=False):
    meta = {
        "date": "2026-10-13", "deadline": "16:40",
        "updated_at": "2026-10-13T16:19:00+09:00",
        "phase": "PRE_RESULT", "results_seen": False,
        "unlock": False, "scoring": False,
    }
    meta.update(meta_overrides or {})
    sources = {
        "race_card": {
            "status": "ok", "source": URLS["official"],
            "sha256": "a" * 64,
            "fetched_at": "2026-10-13T16:18:00+09:00",
        },
        "beforeinfo": {
            "status": "ok", "source": URLS["official"],
            "sha256": "b" * 64,
            "fetched_at": "2026-10-13T16:19:00+09:00",
        },
    }
    if source_overrides:
        sources["beforeinfo"].update(source_overrides)
    racers = []
    for lane in range(1, 7):
        racers.append({
            "lane": lane, "raw_text": "research synthetic row",
            "national": {"win_rate": 7.5 - 0.3 * lane},
            "motor": {"quinella_rate": 30 + lane},
            "avg_st": .1 + lane * .01,
        })
    entries = [{"lane": lane, "course": (2 if lane == 1 else 1 if lane == 2 else lane)}
               for lane in range(1, 7)]
    race = {
        "race_key": KEY, "meta": meta, "source_audit": sources,
        "racers": racers, "beforeinfo": {"start_exhibition": entries},
    }
    if result_marker:
        race["results"] = {"forbidden": "do not read"}
    folder = root / "data/races"
    folder.mkdir(parents=True)
    (folder / (KEY + ".json")).write_text(json.dumps(race), encoding="utf-8")


class V332LiveE2E(unittest.TestCase):
    def test_mock_public_sources_freeze_without_any_git_commit(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root)
            (root / "data/formal_status.json").write_text("MUST_NOT_BE_READ")
            result = live_local_freeze(root, KEY, URLS, capture=True,
                                       fetcher=mock_page, clock=lambda: PRE)
            rec = result["record"]
            self.assertEqual(rec["evidence_level"], "LOCAL_RECEIPT_RAW_SHA_ONLY")
            self.assertEqual(set(rec["source_receipts"]), set(URLS))
            self.assertEqual(set(rec["candidate"]["modes"]), {
                "national_only", "national_motor", "national_motor_st"})
            self.assertEqual(len(rec["candidate"]["modes"]["national_motor_st"]["top10_boat_research_only"]), 10)
            self.assertEqual(rec["candidate"]["course_by_boat_exhibition"]["1"], 2)
            self.assertFalse(rec["actual_course_independently_verified"])
            self.assertFalse(rec["original_exhibition_fields_parsed"])
            self.assertFalse(rec["git_first_seen_before_deadline_verified"])
            self.assertFalse(rec["accuracy_improvement_proven"])
            self.assertFalse(rec["results_read"])
            self.assertFalse(rec["formal_fresh_read"])
            data = (root / result["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), result["sha256"])
            self.assertEqual(json.loads(data)["candidate_sha256"], rec["candidate_sha256"])
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                live_local_freeze(root, KEY, clock=lambda: PRE)

    def test_tampered_raw_capture_blocks_immutable_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root)
            for provider, url in URLS.items():
                capture_one(root, KEY, DEADLINE, provider, url,
                            fetcher=mock_page, clock=lambda: PRE)
            raw = root / "data/source_captures/20261013" / KEY / "boaters.html"
            raw.write_bytes(b"modified after capture" * 8)
            with self.assertRaisesRegex(ValueError, "SOURCE_RAW_SHA256_MISMATCH"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_missing_url_rejected_before_any_network_or_capture(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root)
            with self.assertRaisesRegex(ValueError, "SOURCE_URL_REQUIRED:kyoteibiyori"):
                live_local_freeze(root, KEY, {"boaters": URLS["boaters"]},
                                  capture=True, fetcher=mock_page, clock=lambda: PRE)
            self.assertFalse((root / "data/source_captures").exists())

    def test_closed_race_and_result_flag_do_not_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root)
            def must_not_fetch(_):
                raise AssertionError("NETWORK_MUST_NOT_RUN")
            with self.assertRaisesRegex(ValueError, "LIVE_WINDOW_CLOSED"):
                live_local_freeze(root, KEY, URLS, capture=True,
                                  fetcher=must_not_fetch, clock=lambda: LATE)
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root, meta_overrides={"results_seen": True})
            with self.assertRaisesRegex(ValueError, "RESULT_OR_UNLOCK_FLAG_FORBIDDEN"):
                live_local_freeze(root, KEY, URLS, capture=True,
                                  fetcher=must_not_fetch, clock=lambda: PRE)

    def test_postdeadline_source_blocks_even_with_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root, source_overrides={"fetched_at": "2026-10-13T17:00:00+09:00"})
            with self.assertRaisesRegex(ValueError, "SOURCE_NOT_ASOF_PREDEADLINE"):
                live_local_freeze(root, KEY, URLS, capture=True,
                                  fetcher=mock_page, clock=lambda: PRE)

    def test_formal_october_first_excluded_before_filesystem_access(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_TARGET_EXCLUDED"):
                live_local_freeze(pathlib.Path(d), "20261001-22-12", clock=lambda: PRE)

    def test_result_bearing_race_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            prepare(root, result_marker=True)
            with self.assertRaisesRegex(ValueError, "RESULT_BEARING_RACE_DOCUMENT_FORBIDDEN"):
                live_local_freeze(root, KEY, clock=lambda: PRE)


if __name__ == "__main__":
    unittest.main()
