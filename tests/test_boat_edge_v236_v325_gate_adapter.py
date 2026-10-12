"""V325 never equates mere shadow file presence with verified evidence."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v325_readiness_gate_adapter import classify_site_row


class V325GateAdapter(unittest.TestCase):
    def test_shadow_presence_is_not_predeadline_or_sha_proof(self):
        row = {
            "race_key": "20261013-22-12",
            "site_baseline_predeadline_metadata": True,
            "v318_shadow_present": True,
        }
        report = classify_site_row(row)
        checks = report["gate"]["checks"]
        self.assertTrue(checks["baseline_predeadline"])
        self.assertFalse(checks["candidate_predeadline"])
        self.assertFalse(checks["both_sha256_consistent"])
        self.assertFalse(checks["server_first_seen_before_deadline_verified"])
        self.assertFalse(report["gate"]["ready_for_independent_review"])
        self.assertIn("SHADOW_CONTENT_NOT_AUDITED", report["reasons"])
        self.assertFalse(report["formal_fresh_read"])

    def test_missing_shadow_and_baseline(self):
        row = {
            "race_key": "20261013-22-11",
            "site_baseline_predeadline_metadata": False,
            "v318_shadow_present": False,
        }
        report = classify_site_row(row)
        self.assertIn("SHADOW_NOT_PRESENT", report["reasons"])
        self.assertIn("BASELINE_PREDEADLINE_NOT_VERIFIED", report["reasons"])
        self.assertFalse(report["gate"]["ready_for_independent_review"])


if __name__ == "__main__":
    unittest.main()
