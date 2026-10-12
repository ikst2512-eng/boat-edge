"""V229 read-only actionable-window diagnostics: synthetic PRE_RESULT inputs only."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v229_eligibility_diagnostic import inspect, load

NOW = datetime(2026, 10, 13, 0, 30, tzinfo=timezone.utc)
ISO = NOW.isoformat()


def write(root, rel, obj):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def setup_race(root, key, deadline, inputs=False):
    audit = {"race_card": {"status": "ok", "fetched_at": ISO},
             "beforeinfo": {"status": "ok", "fetched_at": ISO}} if inputs else {}
    write(root, f"data/races/{key}.json",
          {"meta": {"deadline": deadline}, "source_audit": audit})
    if inputs:
        write(root, f"data/site_scratches_v182/{key}.json",
              {"race_key": key, "blocked": False,
               "race_card_source_status": "ok",
               "official_beforeinfo_source_status": "ok",
               "checked_at": ISO})
        write(root, f"data/site_odds/{key}.json",
              {"race_key": key, "phase": "PRE_RESULT_PURCHASE_ONLY",
               "trifecta_odds": {str(i): 1.0 for i in range(120)},
               "fetched_at": ISO})


class SiteWindowDiagnostics(unittest.TestCase):
    def test_window_scoping_and_upcoming_do_not_mark_all_day_as_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_race(root, "20261013-14-01", "09:35", inputs=False)
            setup_race(root, "20261013-14-02", "10:10", inputs=False)
            setup_race(root, "20261013-14-03", "09:25", inputs=False)
            report = inspect(root, NOW)
            self.assertEqual(report["races_scanned"], 3)
            self.assertEqual(report["decision_window_races"], 1)
            self.assertEqual(report["outside_window_races"], 2)
            self.assertEqual(report["preliminary_ready_races"], 0)
            self.assertEqual(report["next_race"]["race_key"], "20261013-14-02")
            self.assertEqual(report["reason_counts_in_window"],
                {"beforeinfo_missing_or_stale": 1,
                 "odds_120_missing_or_invalid": 1,
                 "race_card_missing_or_stale": 1,
                 "scratch_unverified_or_stale": 1})

    def test_good_preliminary_race_and_immutable_snapshot_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "20261013-22-12"
            setup_race(root, key, "09:35", inputs=True)
            first = inspect(root, NOW)
            self.assertEqual(first["preliminary_ready_races"], 1)
            self.assertEqual(first["window_races"][0]["reasons"], [])
            self.assertIn("Preliminary", first["caveat"])
            write(root, f"data/site_prediction_snapshots/{key}.json",
                  {"schema": "synthetic"})
            second = inspect(root, NOW)
            self.assertEqual(second["preliminary_ready_races"], 0)
            self.assertEqual(second["reason_counts_in_window"],
                             {"snapshot_already_exists": 1})

    def test_outside_window_does_not_attempt_to_read_other_site_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_race(root, "20261013-22-12", "16:40")
            report = inspect(root, NOW)
            self.assertEqual(report["decision_window_races"], 0)
            self.assertEqual(report["reason_counts_in_window"], {})
            self.assertEqual(report["outside_window_races"], 1)

    def test_symlink_never_reads_target_even_if_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = write(root, "data/site_results/hidden.json",
                           {"secret": "RESULT_MUST_NOT_BE_READ"})
            alias = root / "data/races/20261013-14-01.json"
            alias.parent.mkdir(parents=True, exist_ok=True)
            alias.symlink_to(target)
            self.assertEqual(load(alias), {})
            report = inspect(root, NOW)
            self.assertEqual(report["races_scanned"], 1)
            self.assertEqual(report["decision_window_races"], 1)
            self.assertEqual(report["window_races"][0]["reasons"], ["deadline_unknown"])

    def test_missing_deadline_is_reported_and_unaware_time_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_race(root, "20261013-14-01", "not-a-time")
            report = inspect(root, NOW)
            self.assertFalse(report["window_races"][0]["preliminary_eligible"])
            with self.assertRaisesRegex(ValueError, "AWARE_CLOCK_REQUIRED"):
                inspect(root, datetime(2026, 10, 13, 0, 30))


if __name__ == "__main__":
    unittest.main()
