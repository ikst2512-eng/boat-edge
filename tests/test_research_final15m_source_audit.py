"""Tests for the read-only final-15m research audit."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from scripts.research_final15m_source_audit import summarize

JST = timezone(timedelta(hours=9))

class SourceAuditTest(unittest.TestCase):
    def test_deadline_cohorts_and_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            for ident, deadline, reason in [
                ("01-01", "20:10", "race_row_absent"),
                ("01-02", "20:30", "available"),
                ("01-03", "19:50", "available"),
            ]:
                data = {"meta": {"deadline": deadline},
                        "source_audit": {"stt": {"availability_reason": reason}}}
                (p / f"20261024-{ident}.json").write_text(json.dumps(data), encoding="utf-8")
            out = summarize(p, datetime(2026, 10, 24, 20, 0, tzinfo=JST))
            self.assertEqual(out["cohorts"]["final15m"]["count"], 1)
            self.assertEqual(out["cohorts"]["future"]["count"], 1)
            self.assertEqual(out["cohorts"]["past_locked"]["count"], 1)
            self.assertEqual(out["cohorts"]["final15m"]["reason_counts"]["stt"]["race_row_absent"], 1)
            self.assertEqual(out["cohorts"]["final15m"]["reason_counts"]["tkz"]["not_observed"], 1)
            self.assertTrue(out["read_only"])

if __name__ == "__main__":
    unittest.main()
