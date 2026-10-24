"""Offline tests of bounded scheduled PRE_RESULT capture selection."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_imminent_pre_result import batch, eligible
from archive_pre_result_source import JST

NOW = dt.datetime(2026, 10, 25, 10, 35, tzinfo=JST)


def race(key, deadline, locked=True):
    day, venue, no = key.split("-")
    return {"race_key": key, "meta": {
        "date": "2026-10-25", "venue_code": venue, "race_no": int(no),
        "deadline": deadline, "phase": "PRE_RESULT" if locked else "RESULT",
        "results_seen": False if locked else True, "scoring": False,
        "unlock": False}}


class BatchTests(unittest.TestCase):
    def test_only_imminent_locked_races_are_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "races"
            directory.mkdir()
            cases = [
                race("20261025-04-01", "10:52"),
                race("20261025-04-02", "10:34"),
                race("20261025-04-03", "12:20"),
                race("20261025-04-04", "10:50", locked=False),
                race("20261025-04-05", "10:36"),
            ]
            for item in cases:
                (directory / (item["race_key"] + ".json")).write_text(json.dumps(item))
            calls = []
            def fake_capture(item, output):
                calls.append(item["race_key"])
                return {"sha256": "a" * 64}
            result = batch(directory, Path(tmp) / "captures", now=NOW, capture=fake_capture)
            self.assertEqual(calls, ["20261025-04-01"])
            self.assertEqual(len(result["captured"]), 1)

    def test_mismatched_filename_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "20261025-04-02.json"
            p.write_text(json.dumps(race("20261025-04-01", "10:52")))
            self.assertIsNone(eligible(p, NOW))

    def test_no_data_no_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = batch(tmp, Path(tmp) / "captures", now=NOW)
            self.assertEqual(report["checked"], 0)
            self.assertEqual(report["captured"], [])


if __name__ == "__main__":
    unittest.main()
