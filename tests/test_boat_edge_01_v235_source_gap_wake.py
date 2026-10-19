"""Offline Gate 1C source-producer -> existing V235 wake regressions."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.boat_edge_01_v235_source_gap_wake import probe

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 20, 10, 0, tzinfo=JST)
KEY = "20261020-18-03"


def setup(root):
    data = root / "data"
    (data / "races").mkdir(parents=True)
    (data / "site_prediction_snapshots").mkdir(parents=True)
    (data / "formal_status.json").write_text(json.dumps({
        "guards": {"results_seen": False, "unlock": False, "scoring": False,
                   "RESULT_UNLOCK_TOKEN": None},
        "formalFirst100": {"races": 0},
    }), encoding="utf8")
    (data / "today.json").write_text(json.dumps({
        "date": "2026-10-20", "phase": "PRE_RESULT",
        "results_seen": False, "unlock": False, "scoring": False,
        "venues": [{"jcd": "18", "races": [{
            "race_key": KEY, "race_no": 3, "deadline": "10:07"}]}],
    }), encoding="utf8")
    race = {"race_key": KEY, "racers": [{"lane": lane} for lane in range(1, 7)],
            "meta": {"date": "2026-10-20", "venue_code": "18", "race_no": 3,
                     "deadline": "10:07", "phase": "PRE_RESULT",
                     "results_seen": False, "unlock": False, "scoring": False}}
    path = data / "races" / (KEY + ".json")
    path.write_text(json.dumps(race), encoding="utf8")
    return data, path


class SourceGapV235Wake(unittest.TestCase):
    def test_real_incomplete_source_in_strict_window_is_only_dispatch_hint(self):
        with tempfile.TemporaryDirectory() as td:
            data, path = setup(Path(td))
            result = probe(Path(td), NOW)
            self.assertTrue(result["wake_needed"])
            self.assertEqual(result["race_keys"], [KEY])
            self.assertFalse(result["eligible_denominator_proven"])
            self.assertIn("beforeinfo_unavailable", result["gap_counts"])
            self.assertIn("odds_evidence_missing", result["gap_counts"])
            self.assertNotIn("prediction_saved_proven", result)

    def test_fully_sourced_or_frozen_not_rewoken(self):
        with tempfile.TemporaryDirectory() as td:
            data, path = setup(Path(td))
            with patch("scripts.boat_edge_01_v235_source_gap_wake.source_status",
                       return_value=["frozen_prediction_missing_or_invalid"]):
                self.assertFalse(probe(Path(td), NOW)["wake_needed"])
            (data / "site_prediction_snapshots" / (KEY + ".json")).write_text(
                json.dumps({"race_key": KEY}), encoding="utf8")
            self.assertFalse(probe(Path(td), NOW)["wake_needed"])

    def test_outside_window_clock_disagreement_and_foreign_day_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            data, path = setup(Path(td))
            self.assertFalse(probe(Path(td), NOW - timedelta(minutes=4))["wake_needed"])
            self.assertFalse(probe(Path(td), NOW + timedelta(minutes=6))["wake_needed"])
            race = json.loads(path.read_text(encoding="utf8"))
            race["meta"]["deadline"] = "10:08"
            path.write_text(json.dumps(race), encoding="utf8")
            self.assertFalse(probe(Path(td), NOW)["wake_needed"])
            race["meta"]["deadline"] = "10:07"
            path.write_text(json.dumps(race), encoding="utf8")
            catalog = data / "today.json"
            plan = json.loads(catalog.read_text(encoding="utf8"))
            plan["date"] = "2026-10-19"
            catalog.write_text(json.dumps(plan), encoding="utf8")
            self.assertFalse(probe(Path(td), NOW)["wake_needed"])

    def test_formal_open_invalid_symlink_and_untrusted_clock_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            data, path = setup(Path(td))
            self.assertFalse(probe(Path(td), datetime(2026, 10, 20, 10, 0))["wake_needed"])
            f = data / "formal_status.json"
            formal = json.loads(f.read_text(encoding="utf8"))
            formal["guards"]["unlock"] = True
            f.write_text(json.dumps(formal), encoding="utf8")
            self.assertFalse(probe(Path(td), NOW)["wake_needed"])
            formal["guards"]["unlock"] = False
            f.write_text(json.dumps(formal), encoding="utf8")
            path.unlink()
            path.symlink_to(f)
            self.assertFalse(probe(Path(td), NOW)["wake_needed"])

    def test_one_way_producers_no_feedback_subscription_or_new_writer(self):
        root = Path(__file__).resolve().parents[1]
        shell = (root / "scripts/boat_edge_01_v235_source_gap_wake.sh").read_text(encoding="utf8")
        for producer in ("auto-update.yml", "site-odds.yml"):
            wf = (root / ".github/workflows" / producer).read_text(encoding="utf8")
            self.assertIn("bash scripts/boat_edge_01_v235_source_gap_wake.sh", wf)
            self.assertIn("if: success()", wf)
        self.assertIn("gh workflow run \"$wf\" --ref main", shell)
        self.assertIn("wf=V235.yml", shell)
        self.assertIn('GITHUB_REPOSITORY', shell)
        self.assertIn("GATE1C_V235_NUDGE_EXISTING_V235_ACTIVE", shell)
        self.assertIn("GATE1C_V235_NUDGE_REAL_V235_COOLDOWN", shell)
        self.assertIn("fromdateiso8601", shell)
        self.assertIn("180", shell)
        self.assertNotIn("workflow_run:", shell)
        self.assertNotIn("gh workflow run BOAT_EDGE_V229", shell)


if __name__ == "__main__":
    unittest.main()
