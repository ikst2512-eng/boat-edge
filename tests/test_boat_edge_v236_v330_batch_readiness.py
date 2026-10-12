"""V330 batch scan is dry-run, excludes closed races, never reads results."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v330_batch_readiness import scan

JST = timezone(timedelta(hours=9))


class V330BatchReadiness(unittest.TestCase):
    def test_closed_race_reports_blocker_without_freezing(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            folder = root / "data/races"
            folder.mkdir(parents=True)
            (folder / "20261013-02-09.json").write_text(json.dumps({
                "race_key": "20261013-02-09",
                "meta": {"phase": "PRE_RESULT", "results_seen": False,
                         "unlock": False, "scoring": False, "date": "2026-10-13",
                         "deadline": "14:48"}
            }))
            (root / "data/formal_status.json").write_text("DO_NOT_READ")
            report = scan(root, "20261013", datetime(2026, 10, 13, 15, tzinfo=JST))
            self.assertEqual(report["races_inspected"], 1)
            self.assertEqual(report["ready_for_live_freeze"], 0)
            self.assertIn("CLOSED_RACE_NO_BACKFILL", report["blocker_counts"])
            self.assertFalse(report["results_read"])
            self.assertFalse(report["writes_performed"])
            self.assertFalse((root / "data/research_shadow_v318").exists())

    def test_empty_date_reports_zero(self):
        with tempfile.TemporaryDirectory() as d:
            report = scan(pathlib.Path(d), "20261013")
            self.assertEqual(report["races_inspected"], 0)
            self.assertEqual(report["rows"], [])


if __name__ == "__main__":
    unittest.main()
