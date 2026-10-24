"""Tests for fail-closed pre-result enrichment ingestion validation."""
import datetime as dt
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("validator", Path(__file__).with_name("validate_pre_result_enrichment.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

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


if __name__ == "__main__":
    unittest.main()
