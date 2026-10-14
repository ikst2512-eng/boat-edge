"""Regression: retire the obsolete V226 hourly installer without stopping LIVE owners."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
V226 = ROOT / ".github/workflows/BOAT_EDGE_V226_SAFE_RECOVERY.yml"


class V226RecoveryOwner(unittest.TestCase):
    def test_old_install_job_cannot_run_hourly_or_write_main(self):
        source = V226.read_text(encoding="utf-8")
        header = source.split("\njobs:", 1)[0]
        # Exclude comments; the former 18-min/hour cron was a duplicate producer.
        header = "\n".join(s for s in header.splitlines() if not s.lstrip().startswith("#"))
        self.assertNotIn("schedule:", header)
        self.assertNotIn("cron:", header)
        self.assertIn("workflow_dispatch:", header)
        self.assertRegex(header, r"permissions:\s*\n\s+contents: read")
        self.assertNotRegex(source, r"git\s+(?:push|commit|add|reset|pull)")
        self.assertNotIn("Restore V167 SHA-verified verifier", source)
        self.assertIn("V226_MANUAL_RECOVERY_READ_ONLY_PASS", source)
        self.assertIn("persist-credentials: false", source)

    def test_current_production_model_installed_not_replaced(self):
        content = (ROOT / "scripts/site_final_history_v133.py").read_text(encoding="utf-8")
        for marker in ("V226_IMMUTABLE_ORIGINAL_SNAPSHOT", "V226_SOURCE_GUARD",
                       "V226_DECISION_WINDOW", "V226_ODDS_GUARD"):
            self.assertEqual(content.count(marker), 1, marker)
        sha = subprocess.check_output(
            ["git", "hash-object", "--", "scripts/site_final_history_v133.py"],
            cwd=ROOT, text=True).strip()
        self.assertEqual(sha, "7b2916df307fcb2783cfc6ddc38ff73903d56da5")

    def test_live_freeze_and_odds_sources_remain_scheduled(self):
        paths = (
            ".github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml",
            ".github/workflows/V235.yml",
            ".github/workflows/BOAT_EDGE_V167_ONE_UPLOAD.yml",
            ".github/workflows/auto-update.yml",
        )
        for name in paths:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("schedule:", text, name)
            self.assertRegex(text, r"cron:\s*['\"]", name)

    def test_no_model_ownership_or_results_endpoint_in_v226(self):
        contents = V226.read_text(encoding="utf-8")
        self.assertNotIn("data/site_results/", contents)
        self.assertNotIn("/payout", contents)
        self.assertNotIn("combined_api", contents)
        self.assertNotIn("write_text(", contents)
        self.assertNotIn("write_bytes(", contents)


if __name__ == "__main__":
    unittest.main()
