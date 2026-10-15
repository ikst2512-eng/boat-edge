"""V410 synthetic-only: six-boat Elo, other-course descriptives, leakage guards."""
import csv
import hashlib
import io
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v400_five_year_history_research import COLUMNS
from boat_edge_v410_s_prior_opponent_elo import snapshot


def race(key, stamp, finishes=(1, 2, 3, 4, 5, 6), courses=(1, 2, 3, 4, 5, 6)):
    return [
        {"race_key": key, "boat": str(i), "racer_id": str(4500 + i),
         "actual_course": str(courses[i - 1]), "finish": str(finishes[i - 1]),
         "published_at": stamp} for i in range(1, 7)
    ]


def history(records):
    f = io.StringIO(newline="")
    writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in sorted(records, key=lambda r: (r["race_key"], int(r["boat"]))):
        writer.writerow(row)
    raw = f.getvalue().encode()
    manifest = {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "source_name": "SYNTHETIC_TEST_ONLY",
        "source_locator": "offline:synthetic",
        "rights_evidence": "Synthetic fixtures only. Not a real license grant.",
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": "V400_FIXTURE_V410",
    }
    return raw, manifest


def target():
    return {
        "schema": "BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1",
        "race_key": "202609300103",
        "deadline_jst": "2026-09-30T08:35:00+09:00",
        "entries": [{"boat": i, "racer_id": str(4500 + i)} for i in range(1, 7)],
    }


class OpponentEloFixtures(unittest.TestCase):
    def setUp(self):
        past = race("202609290101", "2026-09-29T23:00:00+09:00")
        today = race("202609300101", "2026-09-30T08:00:00+09:00",
                     courses=(2, 1, 3, 4, 5, 6))
        own = race("202609300103", "2026-09-30T08:10:00+09:00",
                   finishes=(6, 5, 4, 3, 2, 1))
        late = race("202609300104", "2026-09-30T10:00:00+09:00",
                    finishes=(6, 5, 4, 3, 2, 1))
        self.raw, self.manifest = history(past + today + own + late)
        self.t = target()

    def build(self, raw=None, man=None, target_doc=None):
        return snapshot(self.raw if raw is None else raw,
                        self.manifest if man is None else man,
                        self.t if target_doc is None else target_doc)

    def test_guard_keeps_only_two_prior_races(self):
        got = self.build()
        self.assertEqual(got["eligible_historical_races"], 2)
        self.assertEqual(got["same_target_races_excluded"], 1)
        self.assertEqual(got["not_yet_published_races_excluded"], 1)
        self.assertFalse(got["target_race_result_used"])
        self.assertFalse(got["formal_fresh_read"])

    def test_elo_is_computed_from_simultaneous_head_to_head(self):
        # One race with six equally rated entrants: top finisher's score
        # against all five is 5-2.5, giving 12 Elo points.
        raw, m = history(race("202609290101", "2026-09-29T22:00:00+09:00"))
        got = self.build(raw=raw, man=m)
        self.assertEqual(got["six_boats"]["1"]["opponent_relative_elo"], 1512.0)
        self.assertEqual(got["six_boats"]["6"]["opponent_relative_elo"], 1488.0)
        self.assertAlmostEqual(sum(got["six_boats"][str(i)]["elo_vs_six_boat_mean"]
                                   for i in range(1, 7)), 0.0)

    def test_other_boat_course_outcomes_are_descriptive(self):
        got = self.build()
        # For racer 4501 in course 1 on Sep 29, course 2 finished second.
        cell = got["six_boats"]["1"]["other_boat_course_outcomes"]["1"]["2"]
        self.assertEqual(cell["observed_races"], 1)
        self.assertEqual(cell["other_second"], 1)
        self.assertIsNone(cell["other_second_rate"])

    def test_target_result_never_used_even_when_falsely_early(self):
        old = race("202609300103", "2026-09-30T07:00:00+09:00")
        raw, m = history(old)
        got = self.build(raw=raw, man=m)
        self.assertEqual(got["eligible_historical_races"], 0)
        self.assertEqual(got["same_target_races_excluded"], 1)
        self.assertTrue(all(got["six_boats"][str(i)]["opponent_relative_elo"] is None
                            for i in range(1, 7)))

    def test_unseen_racers_remain_missing_and_relative_missing(self):
        t = target()
        t["entries"][0]["racer_id"] = "5200"
        got = self.build(target_doc=t)
        self.assertTrue(got["six_boats"]["1"]["elo_unobserved_prior_only"])
        self.assertIsNone(got["six_boats"]["1"]["opponent_relative_elo"])
        self.assertIsNone(got["six_boats"]["2"]["elo_vs_six_boat_mean"])

    def test_source_tampering_fails(self):
        m = deepcopy(self.manifest)
        m["csv_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RAW_HISTORY_SHA256_MISMATCH"):
            self.build(man=m)

    def test_rejects_target_with_outcome(self):
        t = target()
        t["entries"][0]["finish"] = 1
        with self.assertRaisesRegex(ValueError, "TARGET_MUST_NOT_CONTAIN_OUTCOME_OR_ACTUAL_COURSE"):
            self.build(target_doc=t)

    def test_rejects_protected_formal_target(self):
        t = target()
        t["race_key"] = "202610010103"
        t["deadline_jst"] = "2026-10-01T08:35:00+09:00"
        with self.assertRaisesRegex(ValueError, "PROTECTED_OR_UNSUPPORTED_TARGET_DATE"):
            self.build(target_doc=t)

    def test_rejects_invalid_six_racer_target(self):
        t = target()
        t["entries"][1]["racer_id"] = t["entries"][0]["racer_id"]
        with self.assertRaisesRegex(ValueError, "TARGET_REQUIRES_SIX_DISTINCT_RACERS"):
            self.build(target_doc=t)

    def test_zero_history_has_no_fake_elo(self):
        raw, m = history([])
        got = self.build(raw=raw, man=m)
        self.assertEqual(got["eligible_historical_races"], 0)
        self.assertTrue(all(got["six_boats"][str(i)]["elo_unobserved_prior_only"] for i in range(1,7)))

    def test_deterministic_for_unsorted_published_times(self):
        got = json.dumps(self.build(), sort_keys=True)
        again = json.dumps(self.build(), sort_keys=True)
        self.assertEqual(got, again)

    def test_at_least_twenty_historical_races_enables_descriptive_rate(self):
        from datetime import date, timedelta
        rows = []
        for offset in range(20):
            d = date(2026, 9, 1) + timedelta(days=offset)
            rows += race(d.strftime("%Y%m%d") + "0101", d.isoformat() + "T21:00:00+09:00")
        raw, m = history(rows)
        got = self.build(raw=raw, man=m)
        cell = got["six_boats"]["1"]["other_boat_course_outcomes"]["1"]["2"]
        self.assertEqual(cell["observed_races"], 20)
        self.assertEqual(cell["other_second_rate"], 1.0)
        self.assertEqual(got["eligible_historical_races"], 20)


if __name__ == "__main__":
    unittest.main()
