import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.boat_edge_02_source_coverage_audit import audit, load_expected


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
            self.assertEqual(report["summary"]["beforeinfo"]["by_status"], {"incomplete_exhibition": 1})
            self.assertIsNone(report["all_scheduled_race_success_percent"])

    def test_unavailable_schedule_is_unknown_not_zero(self):
        with TemporaryDirectory() as tmp:
            report = audit(Path(tmp), "20261021")
            self.assertIsNone(report["missing_scheduled_race_keys"])
            self.assertIsNone(report["scheduled_card_presence_percent"])

    def test_schedule_duplicates_rejected(self):
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "schedule.json"
            key = "20261021-16-07"
            f.write_text(json.dumps({"date_jst": "20261021", "race_keys": [key, key]}))
            with self.assertRaises(ValueError):
                load_expected(f, "20261021")


if __name__ == "__main__":
    unittest.main()
