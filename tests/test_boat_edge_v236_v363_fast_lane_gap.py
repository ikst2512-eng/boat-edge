"""V363 synthetic non-invasive upstream refresh gap diagnostics."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v334_live_batch_runner import run
from boat_edge_v363_fast_lane_gap_diagnostic import classify
from test_boat_edge_v236_v334_live_batch import NOW, prepare

KEY = "20261015-22-12"


def stale_card(root):
    path = root / "data/races" / (KEY + ".json")
    record = json.loads(path.read_bytes())
    record["source_audit"]["race_card"]["fetched_at"] = "2026-10-15T16:00:00+09:00"
    path.write_text(json.dumps(record), encoding="utf-8")


class V363UpstreamGap(unittest.TestCase):
    def test_existing_site_prediction_snapshot_and_stale_source_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            stale_card(root)
            directory = root / "data/site_prediction_snapshots"
            directory.mkdir(parents=True)
            # Deliberately not JSON: we MUST NOT open or inspect this file.
            (directory / (KEY + ".json")).write_bytes(b"DO_NOT_OPEN_SITE_PREDICTION")
            report = run(root, capture=True, clock=lambda: NOW,
                         fetcher=lambda _: self.fail("NO_NETWORK_ON_STALE_CARD"))
            self.assertEqual(report["completed_count"], 0)
            self.assertEqual(report["run_diagnostic"], "ELIGIBLE_BUT_NO_FREEZE_COMPLETED")
            self.assertEqual(report["failures"][0]["reason"],
                             "SOURCE_TOO_STALE_FOR_FINAL_WINDOW:race_card")
            scan = report["failures"][0]["selection_scan"]
            gap = scan["upstream_fast_lane_gap_diagnostic"]
            self.assertTrue(gap["site_prediction_snapshot_exists_as_regular_file"])
            self.assertTrue(gap["v230_existing_snapshot_filter_applies_if_same_checkout"])
            self.assertTrue(gap["race_card_refresh_needed_from_selection_metadata"])
            self.assertTrue(gap["potential_v230_fast_lane_snapshot_refresh_gap"])
            self.assertFalse(gap["refresh_gap_cause_independently_proven"])
            self.assertFalse(gap["source_refresh_performed"])
            self.assertFalse(gap["site_prediction_snapshot_opened"])
            self.assertFalse(gap["results_read"])
            self.assertFalse(gap["formal_fresh_read"])
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_stale_card_without_snapshot_does_not_attribute_snapshot_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            stale_card(root)
            report = run(root, capture=False, clock=lambda: NOW)
            gap = report["window"]["candidates"][0]["selection_scan"][
                "upstream_fast_lane_gap_diagnostic"]
            self.assertFalse(gap["site_prediction_snapshot_exists_as_regular_file"])
            self.assertTrue(gap["race_card_refresh_needed_from_selection_metadata"])
            self.assertFalse(gap["potential_v230_fast_lane_snapshot_refresh_gap"])
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_existing_snapshot_with_fresh_sources_is_not_a_claimed_gap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            directory = root / "data/site_prediction_snapshots"
            directory.mkdir(parents=True)
            (directory / (KEY + ".json")).write_text("DO_NOT_OPEN")
            report = run(root, capture=False, clock=lambda: NOW)
            gap = report["window"]["candidates"][0]["selection_scan"][
                "upstream_fast_lane_gap_diagnostic"]
            self.assertTrue(gap["site_prediction_snapshot_exists_as_regular_file"])
            self.assertFalse(gap["race_card_refresh_needed_from_selection_metadata"])
            self.assertFalse(gap["beforeinfo_refresh_needed_from_selection_metadata"])
            self.assertFalse(gap["potential_v230_fast_lane_snapshot_refresh_gap"])

    def test_symlink_not_followed_and_bad_scan_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            directory = root / "data/site_prediction_snapshots"
            directory.mkdir(parents=True)
            (directory / (KEY + ".json")).symlink_to(root / "does-not-exist")
            report = run(root, clock=lambda: NOW)
            gap = report["window"]["candidates"][0]["selection_scan"][
                "upstream_fast_lane_gap_diagnostic"]
            self.assertTrue(gap["site_prediction_snapshot_is_symlink_not_read"])
            self.assertFalse(gap["v230_existing_snapshot_filter_applies_if_same_checkout"])
            with self.assertRaisesRegex(ValueError, "V363_UNTRUSTED_READ_ONLY_SCAN"):
                classify(root, {"preflight_can_authorize_freeze": True})
            self.assertFalse((root / "data/research_local_v332").exists())


if __name__ == "__main__":
    unittest.main()
