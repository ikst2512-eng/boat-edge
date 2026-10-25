"""Regression tests for the read-only CORE7 evidence reporter."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fresh_core7_blockers.py"
JST = timezone(timedelta(hours=9))


class Core7DiagnosticTests(unittest.TestCase):
    def test_no_unlock_and_distinct_blockers(self):
        day = datetime.now(JST).strftime("%Y%m%d")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            races = base / "data" / "races"
            races.mkdir(parents=True)
            (base / "data" / "model_status.json").write_text(
                json.dumps({"updated_at": "test", "source_rows": {},
                            "core7": {"eligible_count": 0}}), encoding="utf-8")
            missing = {
                "meta": {"deadline": "00:00"},
                "source_audit": {"race_card": {"status": "ok"},
                                 "stt": {"status": "missing", "availability_reason": "race_row_absent"},
                                 "tkz": {"status": "ok"}, "sui": {"status": "ok"},
                                 "original_exhibition": {"status": "ok"}},
                "current_model_input": {"core7_ready": False}}
            complete = {
                "meta": {"deadline": "23:59"},
                "source_audit": {k: {"status": "ok"} for k in
                    ("race_card", "stt", "tkz", "sui", "original_exhibition")},
                "current_model_input": {"core7_ready": True}}
            for key, doc in [("01-01", missing), ("01-02", complete)]:
                (races / f"{day}-{key}.json").write_text(json.dumps(doc), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT)], cwd=base,
                               text=True, capture_output=True, check=True)
            report = json.loads((base / "fresh_core7_blockers.json").read_text(encoding="utf-8"))
            counts = report["saved_race_counts"]
            self.assertEqual(counts["stt:race_row_absent"], 1)
            self.assertEqual(counts["core7_ready_on_saved_race"], 1)
            self.assertEqual(counts["races_not_core7_ready"], 1)
            self.assertEqual(counts["not_ready_deadline_passed"], 1)
            self.assertEqual(counts["deadline_future"], 1)
            self.assertTrue(report["urgent_and_post_enrichment_denominators_must_not_be_added"])
            self.assertFalse(report["formal_unlock_authorized"])
            self.assertFalse(report["results_accessed"])
            self.assertNotIn("formal_predictions", p.stdout)


if __name__ == "__main__":
    unittest.main()
