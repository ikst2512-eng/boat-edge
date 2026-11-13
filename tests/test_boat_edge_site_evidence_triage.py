import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_site_evidence_triage import inspect_site_evidence, audit_directory

class SiteEvidenceTriage(unittest.TestCase):
    def test_never_promotes_site_source_evidence(self):
        x = inspect_site_evidence({"race_key":"20261011-01-04",
            "race_sha256":"a"*64, "snapshot_saved_at":"2026-10-11T07:38:23+00:00"},
            {"race_key":"20261011-01-04","first_git_commit":"c"*40,
             "deadline_jst":"2026-10-11T16:47:00+09:00",
             "winning_combo":"3-5-1"})
        self.assertTrue(x["site_evidence_fields"]["first_git_commit"])
        self.assertTrue(x["scored_record_present"])
        self.assertFalse(x["comparison_eligible"])
        self.assertFalse(x["actual_result_read_for_scoring"])
        self.assertFalse(x["formal_fresh_eligible"])
    def test_missing_score_is_not_missing_git_proof(self):
        x = inspect_site_evidence({"race_key": "20261011-01-07", "race_sha256": "a"*64})
        self.assertFalse(x["scored_record_present"])
        self.assertIn("first_git_commit", x["missing_source_fields"])
        self.assertFalse(x["comparison_eligible"])

    def test_key_mismatch_refused(self):
        with self.assertRaisesRegex(ValueError,"RACE_KEY_MISMATCH"):
            inspect_site_evidence({"race_key":"one"},{"race_key":"two"})
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(audit_directory(Path(d))["checked"], 0)
