import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.boat_edge_02_source_coverage_audit import audit, load_expected, retry_candidates


class SourceCoverageTests(unittest.TestCase):
    def test_missing_schedule_and_status_are_separate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "data" / "races"
            target.mkdir(parents=True)
            key = "20261021-16-07"
            (target / (key + ".json")).write_text(json.dumps({
                "race_key": key,
                "meta": {"venue": "児島", "deadline": "13:00"},
                "source_audit": {
                    "race_card": {"status": "ok"},
                    "beforeinfo": {"status": "ok", "six_boat_coverage": {"six_boat_complete": False}},
                    "original_exhibition": {"status": "missing"}
                }
            }), encoding="utf-8")
            expected = {key, "20261021-17-09"}
            report = audit(root, "20261021", expected)
            self.assertEqual(report["missing_scheduled_race_keys"], ["20261021-17-09"])
            self.assertEqual(report["scheduled_card_presence_percent"], 50.0)
            self.assertEqual(report["summary"]["race_card"]["scheduled_recorded_ok_percent"], 50.0)
            self.assertEqual(report["summary"]["beforeinfo"]["scheduled_recorded_ok_percent"], 0.0)
            self.assertEqual(report["summary"]["beforeinfo"]["by_status"], {"incomplete_exhibition": 1})
            self.assertIsNone(report["all_scheduled_race_success_percent"])

    def test_unavailable_schedule_is_unknown_not_zero(self):
        with TemporaryDirectory() as tmp:
            report = audit(Path(tmp), "20261021")
            self.assertIsNone(report["missing_scheduled_race_keys"])
            self.assertIsNone(report["scheduled_card_presence_percent"])

    def test_retry_only_before_deadline(self):
        jst = timezone(timedelta(hours=9))
        rows = [{"race_key": "20261021-16-07", "deadline": "13:00",
                 "statuses": {"race_card": "ok", "beforeinfo": "missing"}}]
        early = retry_candidates(rows, "20261021", datetime(2026, 10, 21, 12, 0, tzinfo=jst))
        late = retry_candidates(rows, "20261021", datetime(2026, 10, 21, 14, 0, tzinfo=jst))
        self.assertEqual(len(early), 1)
        self.assertFalse(early[0]["automatic_fetch_authorized"])
        self.assertEqual(late, [])

    def test_corrupt_saved_card_counts_as_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "data" / "races"
            folder.mkdir(parents=True)
            key = "20261021-16-07"
            (folder / (key + ".json")).write_text('{"race_key":"WRONG"}')
            result = audit(root, "20261021", {key})
            self.assertEqual(result["missing_scheduled_race_keys"], [key])
            self.assertEqual(result["scheduled_card_presence_percent"], 0.0)

    def test_empty_schedule_rejected(self):
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "schedule.json"
            f.write_text(json.dumps({"date_jst": "20261021", "race_keys": []}))
            with self.assertRaises(ValueError):
                load_expected(f, "20261021")

    def test_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            retry_candidates([], "20261021", datetime(2026, 10, 21, 12))

    def test_schedule_duplicates_rejected(self):
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "schedule.json"
            key = "20261021-16-07"
            f.write_text(json.dumps({"date_jst": "20261021", "race_keys": [key, key]}))
            with self.assertRaises(ValueError):
                load_expected(f, "20261021")


if __name__ == "__main__":
    unittest.main()
