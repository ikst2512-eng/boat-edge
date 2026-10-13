"""V364: executable synthetic contract for V230 vs V336 race selection.

No HTTP, result/outcome records, formal files, source writes, or workflow edits.
The important distinction is that production SITE first-snapshot idempotence
does not imply research-only data freshness, even in one identical checkout.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v230_fast_lane import targets as existing_v230_targets
from boat_edge_v334_live_batch_runner import live_window
from test_boat_edge_v236_v334_live_batch import prepare

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 13, 16, 30, tzinfo=JST)
KEY = "20261013-22-12"


def setup_selection(root):
    prepare(root, key=KEY, deadline="16:40")
    race_path = root / "data/races" / (KEY + ".json")
    doc = json.loads(race_path.read_bytes())
    doc["meta"]["venue_code"] = "22"
    doc["meta"]["race_no"] = 12
    doc["source_audit"]["race_card"]["fetched_at"] = (
        "2026-10-13T16:00:00+09:00"
    )
    race_path.write_text(json.dumps(doc))
    today = {"date": "2026-10-13", "venues": [
        {"jcd": "22", "races": [
            {"race_key": KEY, "deadline": "16:40"}
        ]},
    ]}
    (root / "data/today.json").write_text(json.dumps(today))
    return race_path


class V364SelectionContract(unittest.TestCase):
    def test_snapshot_causes_v230_skip_while_v336_remains_interested(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            setup_selection(root)
            self.assertEqual(existing_v230_targets(root, NOW), [KEY])
            eligible = live_window(root, NOW)
            self.assertEqual(
                [v["race_key"] for v in eligible["candidates"]], [KEY]
            )
            self.assertIn(
                "SOURCE_SCAN_STALE:race_card",
                eligible["candidates"][0]["selection_scan"]["issues"],
            )
            snap = root / "data/site_prediction_snapshots" / (KEY + ".json")
            snap.parent.mkdir(parents=True)
            snap.write_bytes(b"EXISTING_UNREAD_SITE_PREDICTION")
            self.assertEqual(existing_v230_targets(root, NOW), [])
            still_selected = live_window(root, NOW)
            self.assertEqual(
                [v["race_key"] for v in still_selected["candidates"]], [KEY]
            )
            gap = still_selected["candidates"][0]["selection_scan"][
                "upstream_fast_lane_gap_diagnostic"
            ]
            self.assertTrue(
                gap["v230_existing_snapshot_filter_applies_if_same_checkout"]
            )
            self.assertTrue(
                gap["potential_v230_fast_lane_snapshot_refresh_gap"]
            )
            self.assertFalse(gap["refresh_gap_cause_independently_proven"])
            self.assertFalse(gap["source_refresh_performed"])
            self.assertFalse(gap["site_prediction_snapshot_opened"])
            self.assertFalse(gap["results_read"])
            self.assertFalse(gap["formal_fresh_read"])
            self.assertFalse(
                (root / "data/research_local_v332").exists()
            )

    def test_without_site_snapshot_both_paths_see_race(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            setup_selection(root)
            self.assertEqual(existing_v230_targets(root, NOW), [KEY])
            research = live_window(root, NOW)
            self.assertEqual(len(research["candidates"]), 1)
            gap = research["candidates"][0]["selection_scan"][
                "upstream_fast_lane_gap_diagnostic"
            ]
            self.assertFalse(gap["site_prediction_snapshot_exists_as_regular_file"])
            self.assertFalse(gap["potential_v230_fast_lane_snapshot_refresh_gap"])

    def test_closed_race_cannot_qualify_in_either_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            setup_selection(root)
            after = NOW + timedelta(minutes=15)
            self.assertEqual(existing_v230_targets(root, after), [])
            self.assertEqual(live_window(root, after)["candidates"], [])
            self.assertFalse(
                (root / "data/research_local_v332").exists()
            )


if __name__ == "__main__":
    unittest.main()
