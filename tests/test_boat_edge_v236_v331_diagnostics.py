"""V331 diagnose all blockers without making retrospective research freezes."""
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v331_input_diagnostics import diagnose

JST = timezone(timedelta(hours=9))


class V331Diagnostics(unittest.TestCase):
    def test_closed_race_still_reports_candidate_and_source_gaps(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            folder = root / "data/races"
            folder.mkdir(parents=True)
            key = "20261013-02-09"
            (folder / (key + ".json")).write_text(json.dumps({
                "race_key": key, "meta": {
                    "phase": "PRE_RESULT", "results_seen": False, "unlock": False,
                    "scoring": False, "date": "2026-10-13", "deadline": "14:48",
                    "updated_at": "2026-10-13T15:30:00+09:00",
                }, "source_audit": {},
            }))
            (root / "data/formal_status.json").write_text("DO_NOT_READ")
            report = diagnose(root, key, datetime(2026, 10, 13, 16, tzinfo=JST))
            self.assertFalse(report["ready_for_live_freeze"])
            self.assertIn("DEADLINE_CLOSED_NO_RETROACTIVE_FREEZE", report["issues"])
            self.assertIn("POSTDEADLINE_race_updated", report["issues"])
            self.assertIn("CANDIDATE_NOT_READY", report["issues"])
            self.assertIn("THREE_SOURCE_RECEIPTS_NOT_READY", report["issues"])
            self.assertFalse(report["formal_fresh_read"])
            self.assertFalse((root / "data/research_shadow_v318").exists())


if __name__ == "__main__":
    unittest.main()
