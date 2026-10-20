"""Regression: retire the obsolete V226 hourly installer without stopping LIVE owners."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
V226 = ROOT / ".github/workflows/BOAT_EDGE_V226_SAFE_RECOVERY.yml"


class V226RecoveryOwner(unittest.TestCase):
    def test_retired_v226_installer_is_absent(self):
        # V226 was deleted during workflow retirement. Reintroducing even a
        # manual installer risks restoring stale, pre-approved source bytes.
        self.assertFalse(V226.exists(), "V226 legacy installer must stay retired")

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

    def test_retired_v226_cannot_reinstall_or_rewrite_source(self):
        # The absence of the workflow is stronger than the old manual-only
        # content check. Active C-1 owners are checked independently above.
        self.assertFalse(V226.is_file())


if __name__ == "__main__":
    unittest.main()
