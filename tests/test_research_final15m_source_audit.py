"""Tests for the read-only final-15m research audit."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from scripts.research_final15m_source_audit import summarize

JST = timezone(timedelta(hours=9))

class SourceAuditTest(unittest.TestCase):
    def test_missing_day_files_distinct_from_no_urgent_races(self):
        with tempfile.TemporaryDirectory() as td:
            now = datetime(2026, 10, 25, 1, 0, tzinfo=JST)
            empty = summarize(Path(td), now)
            self.assertEqual(empty["input_state"], "NO_RACE_FILES_FOR_DATE")
            self.assertEqual(empty["input_race_count"], 0)
            race = {"meta": {"deadline": "08:00"}, "source_audit": {}}
            (Path(td) / "20261025-01-01.json").write_text(json.dumps(race), encoding="utf-8")
            future = summarize(Path(td), now)
            self.assertEqual(future["input_state"], "RACE_FILES_PRESENT")
            self.assertEqual(future["input_race_count"], 1)
            self.assertEqual(future["cohorts"]["final15m"]["count"], 0)

    def test_invalid_race_files_are_visible(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            now = datetime(2026, 10, 25, 1, 0, tzinfo=JST)
            (p / "20261025-01-01.json").write_text("{broken", encoding="utf-8")
            bad = summarize(p, now)
            self.assertEqual(bad["input_state"], "RACE_FILES_UNUSABLE")
            self.assertEqual((bad["matched_file_count"], bad["input_race_count"], bad["invalid_file_count"]), (1, 0, 1))
            self.assertEqual(bad["invalid_files"], ["20261025-01-01.json"])
            (p / "20261025-01-02.json").write_text(json.dumps({"meta": {"deadline": "08:00"}}), encoding="utf-8")
            mixed = summarize(p, now)
            self.assertEqual(mixed["input_state"], "RACE_FILES_PARTIAL")
            self.assertEqual((mixed["matched_file_count"], mixed["input_race_count"], mixed["invalid_file_count"]), (2, 1, 1))
            (p / "20261025-01-03.json").write_text(json.dumps({"meta": {"deadline": "08:10"}, "source_audit": ["invalid"]}), encoding="utf-8")
            (p / "20261025-01-04.json").write_text(json.dumps({"meta": ["invalid"]}), encoding="utf-8")
            mixed = summarize(p, now)
            self.assertEqual(mixed["input_state"], "RACE_FILES_PARTIAL")
            self.assertEqual((mixed["matched_file_count"], mixed["input_race_count"], mixed["invalid_file_count"]), (4, 1, 3))
            self.assertEqual(len(mixed["invalid_files"]), 3)


    def test_deadline_cohorts_and_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            for ident, deadline, reason in [
                ("01-01", "20:10", "race_row_absent"),
                ("01-02", "20:30", "available"),
                ("01-03", "19:50", "available"),
            ]:
                data = {"meta": {"deadline": deadline},
                        "source_audit": {"stt": {"availability_reason": reason,
                                                 "observed_at": "2026-10-24T19:59:00+09:00"}}}
                (p / f"20261024-{ident}.json").write_text(json.dumps(data), encoding="utf-8")
            out = summarize(p, datetime(2026, 10, 24, 20, 0, tzinfo=JST))
            self.assertEqual(out["cohorts"]["final15m"]["count"], 1)
            self.assertEqual(out["cohorts"]["future"]["count"], 1)
            self.assertEqual(out["cohorts"]["past_locked"]["count"], 1)
            self.assertEqual(out["cohorts"]["final15m"]["reason_counts"]["stt"]["race_row_absent"], 1)
            self.assertEqual(out["cohorts"]["final15m"]["reason_counts"]["tkz"]["not_observed"], 1)
            self.assertTrue(out["read_only"])
            # A newly generated report cannot certify a stale race observation.
            stale = {"meta": {"deadline": "20:11"},
                     "source_audit": {"stt": {
                         "availability_reason": "available",
                         "observed_at": "2026-10-24T19:30:00+09:00"}}}
            (p / "20261024-01-04.json").write_text(json.dumps(stale), encoding="utf-8")
            later = summarize(p, datetime(2026, 10, 24, 20, 0, tzinfo=JST))
            self.assertEqual(later["cohorts"]["final15m"]["reason_counts"]["stt"]["stale_observation"], 1)
            late = {"meta": {"deadline": "20:12"},
                    "source_audit": {"stt": {
                        "availability_reason": "available",
                        "observed_at": "2026-10-24T20:13:00+09:00"}}}
            (p / "20261024-01-05.json").write_text(json.dumps(late), encoding="utf-8")
            checked = summarize(p, datetime(2026, 10, 24, 20, 14, tzinfo=JST))
            self.assertEqual(checked["cohorts"]["past_locked"]["reason_counts"]["stt"]["post_deadline_observation"], 2)

if __name__ == "__main__":
    unittest.main()
