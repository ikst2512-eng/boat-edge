"""V339 regression: explicit SITE research artifacts, no result access."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v339_cross_run_research_audit import audit

KEY = "20261013-22-12"
MODES = ["national_motor", "national_motor_st", "national_only"]


def report(key=KEY, digest="a" * 64, completed=True):
    date = key[:8]
    return {
        "model_id": "BOAT_EDGE_V334_SITE_RESEARCH_BATCH_ONLY",
        "window": {
            "date": date, "candidates": [{"race_key": key, "minutes_left": 10.0}],
            "coverage": {"selected": 1},
        },
        "capture_requested": True,
        "completed": ([{
            "race_key": key,
            "path": f"data/research_local_v332/{date}/{key}.json",
            "sha256": digest, "modes": MODES,
        }] if completed else []),
        "completed_count": int(completed),
        "failures": ([] if completed else [{"race_key": key, "reason": "OFFICIAL_UNAVAILABLE"}]),
        "results_read": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False, "wagers_authorized": False,
    }


class V339CrossRunAudit(unittest.TestCase):
    def test_distinct_races_count_once_without_claiming_global_history(self):
        first = report()
        second = report("20261013-22-11", "b" * 64)
        result = audit([first, second])
        self.assertEqual(result["explicit_report_count"], 2)
        self.assertEqual(result["total_local_freezes_across_reports"], 2)
        self.assertEqual(result["distinct_frozen_race_keys_within_supplied_reports"], 2)
        self.assertTrue(result["unique_within_supplied_reports_only"])
        self.assertFalse(result["complete_actions_history_or_global_uniqueness_attested"])
        self.assertFalse(result["timestamps_independently_authenticated"])
        self.assertFalse(result["eligible_for_formal_fresh_scoring"])

    def test_same_race_identical_sha_still_counts_as_cross_run_repeat(self):
        result = audit([report(), report()])
        self.assertEqual(result["total_local_freezes_across_reports"], 2)
        self.assertEqual(result["distinct_frozen_race_keys_within_supplied_reports"], 1)
        self.assertEqual(result["cross_run_repeat_race_count"], 1)
        self.assertEqual(result["cross_run_divergent_sha_race_count"], 0)
        self.assertFalse(result["unique_within_supplied_reports_only"])

    def test_same_race_changed_sha_is_divergent_freeze(self):
        result = audit([report(), report(digest="b" * 64)])
        self.assertEqual(result["cross_run_repeat_race_count"], 1)
        self.assertEqual(result["cross_run_divergent_sha_race_count"], 1)
        self.assertEqual(len(result["divergent_races"][KEY]), 2)

    def test_failed_capture_does_not_invent_a_frozen_race(self):
        result = audit([report(completed=False)])
        self.assertEqual(result["total_failed_attempts_across_reports"], 1)
        self.assertEqual(result["total_local_freezes_across_reports"], 0)
        self.assertEqual(result["distinct_frozen_race_keys_within_supplied_reports"], 0)
        self.assertFalse(result["accuracy_improvement_proven"])

    def test_invalid_sources_modes_flags_and_formal_target_fail_closed(self):
        cases = [
            ("wrong hash", lambda r: r["completed"][0].update(sha256="BAD")),
            ("wrong path", lambda r: r["completed"][0].update(path="../result.json")),
            ("mode cherry pick", lambda r: r["completed"][0].update(modes=["national_only"])),
            ("unselected", lambda r: r["completed"][0].update(race_key="20261013-22-11")),
            ("date mismatch", lambda r: r["window"].update(date="20261012")),
            ("inflated count", lambda r: r.update(completed_count=2)),
            ("unlocked", lambda r: r.update(formal_fresh_read=True)),
            ("elevated model", lambda r: r.update(accuracy_improvement_proven=True)),
            ("partial coverage", lambda r: r["window"]["coverage"].update(selected=0)),
        ]
        for name, edit in cases:
            with self.subTest(name=name):
                record = report()
                edit(record)
                with self.assertRaises(ValueError):
                    audit([record])
        with self.assertRaisesRegex(ValueError, "NONFORMAL_DATE_REQUIRED"):
            audit([report("20261001-22-12")])
        with self.assertRaisesRegex(ValueError, "EXPLICIT_REPORT_LIST_REQUIRED"):
            audit([])


if __name__ == "__main__":
    unittest.main()
