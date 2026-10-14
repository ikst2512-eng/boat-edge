"""No-network, no-result fixtures for same-run official scratch synchronization."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.boat_edge_v01_collector_scratch import JST, prove, run

KEY = "20261014-12-06"
NOW = datetime(2026, 10, 14, 17, 17, tzinfo=JST)
CARDS = "<html>official racelist six racers</html>".encode("utf8")
BEFORE = "<html>official beforeinfo six start exhibition</html>".encode("utf8")


class SameRunScratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.race_path = self.root / "data/races" / (KEY + ".json")
        self.raw = self.root / "data/raw/20261014"
        self.scratch = self.root / "data/site_scratches_v182" / (KEY + ".json")
        self.race_path.parent.mkdir(parents=True)
        self.raw.mkdir(parents=True)
        formal = self.root / "data/formal_status.json"
        formal.write_text(json.dumps({
            "guards": {"results_seen": False, "unlock": False,
                       "scoring": False, "RESULT_UNLOCK_TOKEN": None},
            "formalFirst100": {"races": 0}
        }), encoding="utf8")
        for name, b in (("racelist", CARDS), ("beforeinfo", BEFORE)):
            (self.raw / ("12_06_" + name + ".html")).write_bytes(b)
        self.race = {
            "race_key": KEY,
            "meta": {"phase": "PRE_RESULT", "deadline": "17:25",
                     "venue_code": "12", "race_no": 6,
                     "results_seen": False, "unlock": False, "scoring": False},
            "racers": [{"lane": i, "registration_no": str(3000 + i),
                        "raw_text": "出走番号 " + str(i)} for i in range(1, 7)],
            "source_audit": {
                "race_card": {"status": "ok",
                              "source": "https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261014&jcd=12&rno=6",
                              "fetched_at": (NOW - timedelta(seconds=30)).isoformat(),
                              "sha256": hashlib.sha256(CARDS).hexdigest()},
                "beforeinfo": {"status": "ok",
                               "source": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261014&jcd=12&rno=6",
                               "fetched_at": (NOW - timedelta(seconds=20)).isoformat(),
                               "sha256": hashlib.sha256(BEFORE).hexdigest()},
            },
            "beforeinfo": {
                "racers": [{"lane": i, "exhibition_time": 6.75} for i in range(1, 7)],
                "start_exhibition": [{"lane": i, "st": "0.12"} for i in range(1, 7)],
            },
        }
        self.save()

    def save(self):
        self.race_path.write_text(json.dumps(self.race), encoding="utf8")

    def test_verified_same_run_source_updates_stale_blocking_proof(self):
        self.scratch.parent.mkdir(parents=True)
        self.scratch.write_text(json.dumps({
            "race_key": KEY, "blocked": True,
            "checked_at": (NOW - timedelta(minutes=20)).isoformat(),
            "reason": "公式直前情報の展示データを検証できない",
        }), encoding="utf8")
        count = run(self.root, NOW)
        proof = json.loads(self.scratch.read_text())
        self.assertEqual(count["in_window_proven"], 1)
        self.assertIs(proof["blocked"], False)
        self.assertEqual(proof["official_beforeinfo_six_boat_complete"], True)
        self.assertEqual(proof["race_card_sha256"], hashlib.sha256(CARDS).hexdigest())
        self.assertEqual(proof["beforeinfo_sha256"], hashlib.sha256(BEFORE).hexdigest())
        self.assertEqual(proof["checked_at"], NOW.isoformat())
        self.assertEqual(self.race_path.read_text(), json.dumps(self.race))

    def test_mismatched_original_html_refuses_green_replacement(self):
        (self.raw / "12_06_beforeinfo.html").write_bytes(b"changed unofficial bytes")
        proof, reason = prove(self.root, KEY, NOW)
        self.assertIsNone(proof)
        self.assertEqual(reason, "beforeinfo_raw_sha_mismatch")
        self.assertEqual(run(self.root, NOW)["in_window_proven"], 0)
        self.assertFalse(self.scratch.exists())

    def test_incomplete_six_exhibition_refuses_green(self):
        self.race["beforeinfo"]["start_exhibition"].pop()
        self.save()
        proof, reason = prove(self.root, KEY, NOW)
        self.assertIsNone(proof)
        self.assertEqual(reason, "six_boat_exhibition_unverified")

    def test_explicit_withdrawal_never_unblocks(self):
        (self.raw / "12_06_racelist.html").write_bytes(CARDS + " 欠場 2号艇".encode())
        self.race["source_audit"]["race_card"]["sha256"] = hashlib.sha256(
            (self.raw / "12_06_racelist.html").read_bytes()).hexdigest()
        self.save()
        proof, reason = prove(self.root, KEY, NOW)
        self.assertEqual(reason, "blocked")
        self.assertTrue(proof["blocked"])
        self.assertEqual(proof["official_raw_flags"], ["racelist"])
        self.assertEqual(run(self.root, NOW)["blocked"], 1)

    def test_stale_source_and_late_clock_refuse_backfill(self):
        proof, reason = prove(self.root, KEY, NOW + timedelta(minutes=10))
        self.assertIsNone(proof)
        self.assertEqual(reason, "outside_2_19_window")
        self.race["source_audit"]["beforeinfo"]["fetched_at"] = (
            NOW - timedelta(minutes=18)).isoformat()
        self.save()
        self.assertEqual(prove(self.root, KEY, NOW)[1], "beforeinfo_source_stale")

    def test_formal_gate_lock_refuses_before_reading_any_result(self):
        p = self.root / "data/formal_status.json"
        formal = json.loads(p.read_text())
        formal["guards"]["results_seen"] = True
        p.write_text(json.dumps(formal))
        with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_LOCK"):
            run(self.root, NOW)
        self.assertFalse(self.scratch.exists())


if __name__ == "__main__":
    unittest.main()
