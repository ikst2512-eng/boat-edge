"""V312 synthetic-only ablation and source safety tests."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v312_pre_result_ablation import build_shadow


def fixture():
    return {
        "race_key": "20261013-02-09",
        "meta": {"deadline": "14:48"},
        "source_audit": {
            name: {
                "status": "ok", "source": "https://www.boatrace.jp/source",
                "sha256": "a" * 64, "fetched_at": "2026-10-13T14:42:00+09:00"
            } for name in ("race_card", "beforeinfo")
        },
        "beforeinfo": {"start_exhibition": [
            {"lane": i, "course": 7-i, "st": "0.10"} for i in range(1, 7)
        ]},
        "racers": [
            {
                "lane": i, "national": {"win_rate": float(i)},
                "motor": {"quinella_rate": 25.0 + i},
                "avg_st": 0.10 + i / 100,
            } for i in range(1, 7)
        ],
        "validation": {"result": "NOT_CONSUMED"},
    }


class V312Shadow(unittest.TestCase):
    def test_ablations_rank_120_without_result_or_actual_claim(self):
        value = build_shadow(fixture())
        self.assertEqual(len(value["modes"]), 3)
        self.assertTrue(all(len(m["top10"]) == 10 for m in value["modes"].values()))
        # Boat 6 is strongest, but its exhibition course is 1.
        self.assertTrue(all(m["top10"][0].startswith("1-") for m in value["modes"].values()))
        self.assertFalse(value["source_bytes_independently_authenticated"])
        self.assertFalse(value["first_git_commit_before_deadline_attested"])
        self.assertFalse(value["scoring_authorized"])
        self.assertFalse(value["scratch_and_cancellation_independently_verified"])
        self.assertFalse(value["full_latest_prediction"])
        self.assertFalse(value["improvement_proven"])
        self.assertFalse(value["production_eligible"])
        self.assertEqual(value["entry_basis"], "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL")

    def test_unverified_source_and_late_rejected(self):
        race = fixture()
        race["source_audit"]["beforeinfo"]["fetched_at"] = "2026-10-13T15:00:00+09:00"
        with self.assertRaises(ValueError):
            build_shadow(race)
        race = fixture()
        race["source_audit"]["race_card"]["status"] = "not_in_window"
        with self.assertRaises(ValueError):
            build_shadow(race)

    def test_known_withdrawal_rejected(self):
        race = fixture()
        race["racers"][0]["raw_text"] = "出走取消"
        with self.assertRaises(ValueError):
            build_shadow(race)
        race = fixture()
        race["racers"][1]["withdrawn"] = True
        with self.assertRaises(ValueError):
            build_shadow(race)

    def test_six_features_fail_closed(self):
        race = fixture()
        race["racers"][1]["national"]["win_rate"] = None
        with self.assertRaises(ValueError):
            build_shadow(race)
        race = fixture()
        race["racers"][1]["lane"] = 1
        with self.assertRaises(ValueError):
            build_shadow(race)
        race = fixture()
        race["beforeinfo"]["start_exhibition"][1]["course"] = 1
        with self.assertRaises(ValueError):
            build_shadow(race)


if __name__ == "__main__":
    unittest.main()
