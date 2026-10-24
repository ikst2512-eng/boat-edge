"""Tests for fail-closed pre-result enrichment ingestion validation."""
import datetime as dt
import importlib.util
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location("validator", Path(__file__).with_name("validate_pre_result_enrichment.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
apply_spec = importlib.util.spec_from_file_location('applicator', Path(__file__).with_name('apply_pre_result_enrichment.py'))
applicator = importlib.util.module_from_spec(apply_spec)
apply_spec.loader.exec_module(applicator)

RACE = {
    "race_key": "20261024-04-01",
    "meta": {
        "date": "2026-10-24", "deadline": "10:52", "phase": "PRE_RESULT",
        "results_seen": False, "unlock": False, "scoring": False,
    },
    "racers": [{"registration_no": str(4000+i)} for i in range(6)],
}
NOW = dt.datetime(2026, 10, 24, 11, 0, tzinfo=validator.JST)
AUDIT = {
    "status": "ok",
    "source": "https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261024&jcd=04&rno=1",
    "fetched_at": "2026-10-24T10:40:00+09:00",
    "sha256": "a" * 64,
}


class EnrichmentValidatorTests(unittest.TestCase):
    def check(self, payload, ok=True):
        result = validator.validate(RACE, payload, now=NOW)
        self.assertEqual(result["ok"], ok, result)
        return result

    def test_valid_actual_entry(self):
        self.check({"actual_entry": [1, 3, 2, 4, 5, 6], "source_audit": {"actual_entry": AUDIT}})

    def test_duplicate_entry(self):
        self.check({"actual_entry": [1, 1, 2, 4, 5, 6], "source_audit": {"actual_entry": AUDIT}}, False)

    def test_unverified_source(self):
        self.check({"actual_entry": [1, 2, 3, 4, 5, 6]}, False)

    def test_after_deadline(self):
        evidence = dict(AUDIT, fetched_at="2026-10-24T10:53:00+09:00")
        self.check({"actual_entry": [1, 2, 3, 4, 5, 6], "source_audit": {"actual_entry": evidence}}, False)

    def test_wrong_race(self):
        evidence = dict(AUDIT, source=AUDIT["source"].replace("jcd=04", "jcd=05"))
        self.check({"actual_entry": [1, 2, 3, 4, 5, 6], "source_audit": {"actual_entry": evidence}}, False)

    def test_result_leak(self):
        evidence = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261024&jcd=04&rno=1")
        self.check({"actual_entry": [1, 2, 3, 4, 5, 6], "source_audit": {"actual_entry": evidence}}, False)

    def test_unknown_field(self):
        self.check({"actual_entry": [1, 2, 3, 4, 5, 6], "finish_order": [1, 2, 3], "source_audit": {"actual_entry": AUDIT}}, False)

    def test_course_stats_with_provenance(self):
        rows = [{"registration_no": str(4000+i), "course": i+1, "first_rate": 20, "second_rate": 15, "third_rate": 10} for i in range(6)]
        source = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261024&jcd=04&rno=1")
        self.check({"course_stats": rows, "source_audit": {"course_stats": source}})

    def test_bad_course_percentages(self):
        rows = [{"registration_no": str(4000+i), "course": i+1, "first_rate": 80, "second_rate": 30, "third_rate": 10} for i in range(6)]
        source = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261024&jcd=04&rno=1")
        self.check({"course_stats": rows, "source_audit": {"course_stats": source}}, False)


    def test_apply_entry_preserves_locked_fields(self):
        payload = {"actual_entry": [1,3,2,4,5,6], "source_audit": {"actual_entry": AUDIT}}
        updated = applicator.apply(RACE, payload, now=NOW)
        self.assertEqual(updated["actual_entry"], [1,3,2,4,5,6])
        self.assertEqual(updated["meta"], RACE["meta"])
        self.assertEqual(updated["source_audit"]["actual_entry"], AUDIT)
        self.assertNotIn("actual_entry", RACE)

    def test_apply_course_stats_joins_registration_numbers(self):
        rows = [{"registration_no": str(4005-i), "course": 6-i,
                 "first_rate": 20.0, "second_rate": 15.0,
                 "third_rate": 10.0} for i in range(6)]
        source = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261024&jcd=04&rno=1")
        updated = applicator.apply(RACE, {"course_stats": rows, "source_audit": {"course_stats": source}}, now=NOW)
        self.assertEqual(len(updated["racers"]), 6)
        self.assertEqual(updated["racers"][0]["course_stats"]["course"], 1)
        self.assertEqual(updated["racers"][-1]["course_stats"]["course"], 6)
        self.assertEqual(updated["source_audit"]["course_stats"], source)
        self.assertNotIn("course_stats", RACE["racers"][0])

    def test_apply_rejects_unaudited_entry(self):
        with self.assertRaises(ValueError):
            applicator.apply(RACE, {"actual_entry": [1,2,3,4,5,6]}, now=NOW)


    def test_malformed_course_values_fail_closed(self):
        source = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261024&jcd=04&rno=1")
        for broken in ([], {}, True, float("nan"), float("inf")):
            rows = [{"registration_no": str(4000+i), "course": i+1,
                     "first_rate": 20, "second_rate": 15, "third_rate": 10} for i in range(6)]
            rows[0]["course"] = broken
            self.check({"course_stats": rows, "source_audit": {"course_stats": source}}, False)

    def test_malformed_percentage_values_fail_closed(self):
        source = dict(AUDIT, source="https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261024&jcd=04&rno=1")
        for broken in (True, float("nan"), float("inf"), -1, 101, "20"):
            rows = [{"registration_no": str(4000+i), "course": i+1,
                     "first_rate": 20, "second_rate": 15, "third_rate": 10} for i in range(6)]
            rows[2]["first_rate"] = broken
            self.check({"course_stats": rows, "source_audit": {"course_stats": source}}, False)


if __name__ == "__main__":
    unittest.main()
