"""V308 fixture-only tests, no real race data or results."""
import importlib.util
import pathlib
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("v308", SCRIPTS / "boat_edge_v308_frozen_pl120_pipeline.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def record():
    return {
        "race_key": "SYNTHETIC-01",
        "deadline_jst": "2026-10-13T12:00:00+09:00",
        "frozen_at_jst": "2026-10-13T11:50:00+09:00",
        "source_sha256": "a" * 64,
        "source_verified": True,
        "actual_course_by_boat": {"1": 2, "2": 1, "3": 3, "4": 4, "5": 5, "6": 6},
        "strength_by_boat": {"1": 1, "2": 10, "3": 1, "4": 1, "5": 1, "6": 1},
    }


class V308Pipeline(unittest.TestCase):
    def test_actual_course_ranking_and_research_lock(self):
        x = m.build_report(record())
        self.assertEqual(len(x["ranked_120"]), 120)
        self.assertEqual(x["top10"][0][0], "1")
        self.assertAlmostEqual(x["head_mass"]["1"], 10 / 15)
        self.assertFalse(x["promotion_authorized"])
        self.assertFalse(x["production_eligible"])
        self.assertFalse(x["wagers_authorized"])
        self.assertFalse(x["calibrated"])
        self.assertEqual(len(x["pre_result_provenance_sha256"]), 64)

    def test_fail_closed_when_source_or_course_not_verified(self):
        x = record()
        x["source_verified"] = False
        with self.assertRaises(ValueError):
            m.build_report(x)
        x = record()
        x["actual_course_by_boat"]["2"] = 2
        with self.assertRaises(ValueError):
            m.build_report(x)
        x = record()
        x["result"] = "1-2-3"
        with self.assertRaises(ValueError):
            m.build_report(x)


if __name__ == "__main__":
    unittest.main()
