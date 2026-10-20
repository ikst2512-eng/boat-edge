import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.boat_edge_02_source_coverage_audit import audit, load_expected, load_catalog, retry_candidates


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
                    "race_card": {"status": "ok", "sha256": "a" * 64, "fetched_at": "2026-10-21T12:00:00+09:00"},
                    "beforeinfo": {"status": "ok", "sha256": "b" * 64, "fetched_at": "2026-10-21T12:00:00+09:00", "six_boat_coverage": {"six_boat_complete": False}},
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

    def test_not_in_window_is_not_retry_error(self):
        jst = timezone(timedelta(hours=9))
        rows = [{"race_key": "20261021-16-07", "deadline": "13:49",
                 "statuses": {"race_card": "ok", "beforeinfo": "not_in_window"}}]
        result = retry_candidates(rows, "20261021", datetime(2026, 10, 21, 3, 0, tzinfo=jst))
        self.assertEqual(result, [])

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

    def test_unverified_ok_not_counted_as_success(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data" / "races"
            folder.mkdir(parents=True)
            key = "20261021-16-07"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key,
                "meta": {"date": "2026-10-21", "venue_code": "16"},
                "source_audit": {"race_card": {"status": "ok"}}
            }))
            result = audit(Path(tmp), "20261021", {key})
            self.assertEqual(result["summary"]["race_card"]["by_status"], {"unverified_ok": 1})
            self.assertEqual(result["summary"]["race_card"]["scheduled_recorded_ok_percent"], 0.0)

    def test_wrong_venue_metadata_rejected(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data" / "races"
            folder.mkdir(parents=True)
            key = "20261021-16-07"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key, "meta": {"venue_code": "17"}
            }))
            result = audit(Path(tmp), "20261021", {key})
            self.assertEqual(result["saved_venues"], 0)
            self.assertEqual(result["missing_scheduled_race_keys"], [key])

    def test_malformed_source_sha_not_verified(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data" / "races"
            folder.mkdir(parents=True)
            key = "20261021-16-07"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key,
                "source_audit": {
                    "race_card": {"status": "ok", "sha256": "not-a-sha",
                                  "fetched_at": "2026-10-21T12:00:00+09:00"}
                }
            }))
            result = audit(Path(tmp), "20261021", {key})
            self.assertEqual(result["summary"]["race_card"]["by_status"], {"unverified_ok": 1})

    def test_invalid_coverage_shape_is_not_success(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data" / "races"
            folder.mkdir(parents=True)
            key = "20261021-16-07"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key,
                "source_audit": {
                    "beforeinfo": {
                        "status": "ok", "sha256": "a" * 64,
                        "fetched_at": "2026-10-21T12:00:00+09:00",
                        "six_boat_coverage": ["not-a-dict"]
                    }
                }
            }))
            result = audit(Path(tmp), "20261021", {key})
            self.assertEqual(result["summary"]["beforeinfo"]["by_status"],
                             {"incomplete_exhibition": 1})

    def test_today_catalog_exposes_missing_races(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "today.json"
            catalog.write_text(json.dumps({
                "date": "2026-10-21",
                "venues": [{"jcd": "16", "races": [
                    {"race_key": "20261021-16-07", "deadline": "13:00"},
                    {"race_key": "20261021-16-08", "deadline": "13:30"}
                ]}]
            }))
            expected, deadlines = load_catalog(catalog, "20261021")
            self.assertEqual(len(expected), 2)
            report = audit(root, "20261021", expected, deadlines=deadlines)
            self.assertEqual(len(report["missing_scheduled_race_keys"]), 2)
            self.assertEqual(report["scheduled_card_presence_percent"], 0.0)
            self.assertEqual(report["missing_scheduled_deadlines"]["20261021-16-07"], "13:00")

    def test_catalog_cross_venue_identity_rejected(self):
        with TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "today.json"
            catalog.write_text(json.dumps({
                "date": "2026-10-21",
                "venues": [{"jcd": "16", "races": [
                    {"race_key": "20261021-17-07", "deadline": "13:00"}
                ]}]
            }))
            with self.assertRaises(ValueError):
                load_catalog(catalog, "20261021")

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
