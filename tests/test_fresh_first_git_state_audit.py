"""Regression checks for the read-only first Git state audit."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "scripts" / "fresh_first_git_state_audit.py"
spec = importlib.util.spec_from_file_location("fresh_first_git_state_audit", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FirstGitStateAuditTests(unittest.TestCase):
    def test_key_rejects_git_argument_injection(self):
        with self.assertRaises(ValueError):
            mod.audit("--all")
        with self.assertRaises(ValueError):
            mod.audit("../20261026-21-01")

    def test_first_commit_is_not_formal_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = "20261026-21-02"
            with patch.object(mod.Path, "is_file", return_value=True), \
                 patch.object(mod.Path, "read_text", return_value=json.dumps({
                     "race_key": key, "meta": {"deadline": "09:01"},
                     "current_model_input": {"core7_ready": False}
                 })), \
                 patch.object(mod, "git", side_effect=[
                     "newestcommit\nfirstcommit",
                     "2026-10-26T08:56:00+09:00"
                 ]), \
                 patch.object(mod.subprocess, "run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = json.dumps({
                    "race_key": key, "meta": {"deadline": "09:01"},
                    "current_model_input": {"source_presence": {"stt": False}}
                }).encode()
                result = mod.audit(key)
            self.assertEqual(result["first_state_commit"], "firstcommit")
            self.assertTrue(result["first_state_committed_before_deadline"])
            self.assertFalse(result["formal_eligible"])
            self.assertEqual(result["proof_scope"], "GIT_STATE_ADDITION_ONLY_NOT_CSV_OR_PREDICTION_FREEZE")

if __name__ == "__main__":
    unittest.main()
