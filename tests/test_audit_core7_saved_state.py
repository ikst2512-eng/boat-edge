"""Synthetic SITE status consistency checks (no external data or results)."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.audit_core7_saved_state import audit


class Core7SavedStateAuditTest(unittest.TestCase):
    def test_detects_disagreement_without_changing_any_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "races").mkdir()
            source = root / "model_status.json"
            source.write_text(json.dumps({"target_date": "2099-01-01",
                "core7": {"eligible_count": 2, "first": "209901010101",
                          "last": "209901010102"}}), encoding="utf-8")
            race = root / "races" / "20990101-01-01.json"
            race.write_text(json.dumps({"race_key": race.stem,
                "current_model_input": {"core7_ready": True}}), encoding="utf-8")
            before = (source.read_bytes(), race.read_bytes())
            report = audit(root, "2099-01-01")
            self.assertEqual(report["status"], "MISMATCH")
            self.assertEqual(report["saved"]["eligible_count"], 1)
            self.assertEqual(before, (source.read_bytes(), race.read_bytes()))
            self.assertFalse(report["formal_first100_eligible"])

    def test_matching_saved_state(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "races").mkdir()
            (root / "model_status.json").write_text(json.dumps({
                "target_date": "2099-01-01",
                "core7": {"eligible_count": 1, "first": "209901010101",
                          "last": "209901010101"}}), encoding="utf-8")
            race = root / "races" / "20990101-01-01.json"
            race.write_text(json.dumps({"race_key": race.stem,
                "current_model_input": {"core7_ready": True}}), encoding="utf-8")
            self.assertEqual(audit(root, "2099-01-01")["status"], "MATCH")


if __name__ == "__main__":
    unittest.main()
