"""V334 dry-run and live batch complete mocked 3-source freeze integration."""
from datetime import datetime, timedelta, timezone
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v334_live_batch_runner import live_window, run

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 13, 16, 30, tzinfo=JST)


def fake_fetch(url):
    return ("<html>mocked external page for " + url + "</html>" * 4).encode(), "text/html", url


def prepare(root, key="20261013-22-12", deadline="16:40", lock=False,
            meta_result=False, original=True):
    date, venue, no = key.split("-")
    url = (f"https://www.boatrace.jp/owpc/pc/race/beforeinfo"
           f"?hd={date}&jcd={venue}&rno={int(no)}")
    meta = {
        "date": date[:4] + "-" + date[4:6] + "-" + date[6:],
        "deadline": deadline,
        "updated_at": date[:4] + "-" + date[4:6] + "-" + date[6:] + "T16:19:00+09:00",
        "phase": "PRE_RESULT", "results_seen": meta_result,
        "unlock": lock, "scoring": False,
    }
    source = {
        "race_card": {
            "status": "ok", "source": url, "sha256": "a" * 64,
            "fetched_at": meta["date"] + "T16:18:00+09:00",
        },
        "beforeinfo": {
            "status": "ok", "source": url, "sha256": "b" * 64,
            "fetched_at": meta["date"] + "T16:19:00+09:00",
        },
    }
    racers = [{
        "lane": i, "raw_text": "synthetic racer",
        "national": {"win_rate": 8.0 - 0.5 * i},
        "motor": {"quinella_rate": 30.0 + i},
        "avg_st": 0.10 + 0.01 * i,
    } for i in range(1, 7)]
    doc = {
        "race_key": key, "meta": meta,
        "source_audit": source, "racers": racers,
        "beforeinfo": {"start_exhibition": [
            {"lane": i, "course": i} for i in range(1, 7)
        ]} if original else {},
    }
    target = root / "data/races"
    target.mkdir(parents=True, exist_ok=True)
    (target / (key + ".json")).write_text(json.dumps(doc), encoding="utf-8")


class V334LiveBatch(unittest.TestCase):
    def test_full_batch_five_step_flow_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            prepare(root)
            (root / "data/formal_status.json").write_text("DO NOT OPEN")
            dry = run(root, clock=lambda: NOW)
            self.assertEqual([x["race_key"] for x in dry["window"]["candidates"]],
                             ["20261013-22-12"])
            self.assertFalse(dry["capture_requested"])
            self.assertFalse((root / "data/source_captures").exists())
            actual = run(root, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            self.assertEqual(actual["completed_count"], 1)
            self.assertEqual(actual["failures"], [])
            self.assertEqual(actual["completed"][0]["modes"], [
                "national_motor", "national_motor_st", "national_only"])
            target = root / actual["completed"][0]["path"]
            frozen = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(frozen["model_id"],
                             "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY")
            self.assertEqual(len(frozen["source_receipts"]), 3)
            self.assertFalse(frozen["actual_course_independently_verified"])
            self.assertFalse(frozen["accuracy_improvement_proven"])
            self.assertFalse(frozen["formal_fresh_read"])
            # A second invocation never mutates or overwrites a frozen prediction.
            repeat = run(root, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            self.assertEqual(repeat["completed_count"], 0)
            self.assertIn("RESEARCH_FREEZE_EXISTS",
                          [x["reason"] for x in repeat["window"]["skipped"]])

    def test_current_date_only_and_near_deadline_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            prepare(root, "20261013-22-12", "16:40")
            prepare(root, "20261012-02-09", "16:40")
            prepare(root, "20261013-22-11", "17:20")
            prepare(root, "20261013-22-10", "15:30")
            prepare(root, "20261013-22-09", "16:31")
            selected = live_window(root, NOW)
            self.assertEqual([x["race_key"] for x in selected["candidates"]],
                             ["20261013-22-12"])
            self.assertIn("LESS_THAN_TWO_MINUTES",
                          [x["reason"] for x in selected["skipped"]])

    def test_reject_locked_race_and_no_synthetic_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            prepare(root, lock=True)
            report = run(root, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            self.assertEqual(report["completed_count"], 0)
            self.assertIn("RACE_WINDOW_INVALID:PRE_RESULT_GUARD_NOT_READY",
                          [x["reason"] for x in report["window"]["skipped"]])
            self.assertFalse((root / "data/source_captures").exists())
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            prepare(root, original=False)
            report = run(root, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            self.assertEqual(report["completed_count"], 0)
            self.assertEqual(len(report["failures"]), 1)
            self.assertFalse((root / "data/source_captures").exists())

    def test_stale_beforeinfo_rejected_without_source_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            prepare(root)
            race_path = root / "data/races/20261013-22-12.json"
            race = json.loads(race_path.read_text())
            race["source_audit"]["beforeinfo"]["fetched_at"] = (
                "2026-10-13T16:00:00+09:00"
            )
            race_path.write_text(json.dumps(race))
            calls = []
            def no_fetch(url):
                calls.append(url)
                raise AssertionError("MUST_NOT_FETCH")
            report = run(root, capture=True, clock=lambda: NOW, fetcher=no_fetch)
            self.assertEqual(report["completed_count"], 0)
            self.assertEqual(len(report["failures"]), 1)
            self.assertIn("SOURCE_TOO_STALE_FOR_FINAL_WINDOW:beforeinfo",
                          report["failures"][0]["reason"])
            self.assertEqual(calls, [])

    def test_invalid_limits_and_naive_clock_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with self.assertRaises(ValueError):
                live_window(root, NOW, max_races=100)
            with self.assertRaises(ValueError):
                live_window(root, NOW, window_minutes=0)
            with self.assertRaises(ValueError):
                run(root, clock=lambda: NOW.replace(tzinfo=None))


if __name__ == "__main__":
    unittest.main()
