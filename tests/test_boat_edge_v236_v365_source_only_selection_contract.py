"""V365 isolated source-refresh selection contract, fixture-only.

No provider calls, result reads, prediction mutation, or formal access.
"""
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v365_source_only_selection_contract import select_source_refresh
from boat_edge_v230_fast_lane import targets as old_v230_targets
from test_boat_edge_v236_v364_v230_v336_selection_contract import (
    NOW, KEY, setup_selection,
)


def write_race(root, modifier):
    p = root / "data/races" / (KEY + ".json")
    data = json.loads(p.read_bytes())
    modifier(data)
    p.write_text(json.dumps(data), encoding="utf-8")


class V365SourceOnlySelection(unittest.TestCase):
    def test_existing_first_prediction_does_not_block_source_only_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            snap = root / "data/site_prediction_snapshots" / (KEY + ".json")
            snap.parent.mkdir(parents=True)
            opaque = b"SITE_FROZEN_FIRST_PREDICTION_DO_NOT_READ_OR_OVERWRITE"
            snap.write_bytes(opaque)
            original_race = (root / "data/races" / (KEY + ".json")).read_bytes()
            self.assertEqual(old_v230_targets(root, NOW), [])
            report = select_source_refresh(root, NOW)
            self.assertEqual([r["race_key"] for r in report["candidates"]], [KEY])
            candidate = report["candidates"][0]
            self.assertTrue(candidate["independent_site_first_prediction_exists"])
            self.assertTrue(candidate["refresh_only_no_first_prediction_overwrite"])
            self.assertFalse(candidate["source_fetch_permitted_by_this_scan"])
            self.assertEqual(snap.read_bytes(), opaque)
            self.assertEqual((root / "data/races" / (KEY + ".json")).read_bytes(), original_race)
            for key in ("source_refresh_performed", "first_prediction_opened",
                        "results_read", "formal_fresh_read", "writes_performed",
                        "production_prediction_changed", "formal_unlock_authorized",
                        "can_authorize_prediction_or_capture"):
                self.assertIs(report[key], False)
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_without_snapshot_still_selects_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            report = select_source_refresh(root, NOW)
            self.assertEqual([x["race_key"] for x in report["candidates"]], [KEY])
            self.assertFalse(report["candidates"][0]["independent_site_first_prediction_exists"])
            self.assertEqual(old_v230_targets(root, NOW), [KEY])

    def test_closed_and_too_early_race_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            self.assertEqual(select_source_refresh(root, NOW + timedelta(minutes=11))["candidates"], [])
            self.assertEqual(select_source_refresh(root, NOW - timedelta(minutes=15))["candidates"], [])
            self.assertTrue(select_source_refresh(root, NOW)["candidates"])

    def test_formal_guards_and_result_bearing_cards_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            for lock in ("results_seen", "unlock", "scoring"):
                setup_selection(root)
                write_race(root, lambda r: r["meta"].__setitem__(lock, True))
                report = select_source_refresh(root, NOW)
                self.assertEqual(report["candidates"], [])
                self.assertIn("RACE_IDENTITY_OR_PRE_RESULT_GUARD_INVALID", report["rejected"])
            for forbidden in ("results", "result", "payout", "finish", "outcomes"):
                setup_selection(root)
                write_race(root, lambda r: r.__setitem__(forbidden, {"DO_NOT_READ": True}))
                self.assertEqual(select_source_refresh(root, NOW)["candidates"], [])
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_wrong_deadline_identity_race_number_and_date_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for change in (
                lambda r: r["meta"].__setitem__("deadline", "16:41"),
                lambda r: r["meta"].__setitem__("venue_code", "21"),
                lambda r: r["meta"].__setitem__("race_no", 11),
                lambda r: r["meta"].__setitem__("date", "2026-10-12"),
                lambda r: r.__setitem__("race_key", "20261013-22-11"),
                lambda r: r["racers"].pop(),
            ):
                setup_selection(root)
                write_race(root, change)
                self.assertEqual(select_source_refresh(root, NOW)["candidates"], [])
            setup_selection(root)
            idx = root / "data/today.json"
            data = json.loads(idx.read_bytes())
            data["venues"][0]["jcd"] = "21"
            idx.write_text(json.dumps(data))
            self.assertEqual(select_source_refresh(root, NOW)["candidates"], [])
            self.assertIn("VENUE_MISMATCH", select_source_refresh(root, NOW)["rejected"])

    def test_duplicate_index_refuses_race_and_symlink_never_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            idx = root / "data/today.json"
            data = json.loads(idx.read_bytes())
            data["venues"][0]["races"].append(dict(data["venues"][0]["races"][0]))
            idx.write_text(json.dumps(data))
            report = select_source_refresh(root, NOW)
            self.assertEqual(report["candidates"], [])
            self.assertEqual(report["rejected"]["DUPLICATE_INDEX_RACE"], 1)
            setup_selection(root)
            snap_dir = root / "data/site_prediction_snapshots"
            snap_dir.mkdir()
            (snap_dir / (KEY + ".json")).symlink_to(root / "no_such_target")
            report = select_source_refresh(root, NOW)
            self.assertEqual(report["candidates"], [])
            self.assertIn("FIRST_PREDICTION_SYMLINK", report["rejected"])

    def test_malformed_clock_and_limit_fail_before_any_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_selection(root)
            for now in (NOW.replace(tzinfo=None), "2026-10-13T16:30:00+09:00"):
                with self.assertRaises(ValueError):
                    select_source_refresh(root, now)
            for cap in (0, 13, True):
                with self.assertRaisesRegex(ValueError, "INVALID_CAP"):
                    select_source_refresh(root, NOW, cap)


if __name__ == "__main__":
    unittest.main()
