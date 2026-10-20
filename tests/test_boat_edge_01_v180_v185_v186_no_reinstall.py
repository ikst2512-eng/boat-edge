"""Protect tracked V180/V185/V186 research from scheduled historical reinstalls.

Source/fixture-only; does not read outcome, payout, external providers, or Formal Fresh.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
CASES = {
    "BOAT_EDGE_V180_CONDITIONAL_TAIL_SHADOW.yml": (
        "V180",
        ("scripts/site_v180_shadow.py", "tests/test_v180_shadow.py"),
        ("python3 tests/test_v180_shadow.py", "python3 scripts/site_v180_shadow.py --repo .",
         "data/site_tail_shadow_v180/predictions/"),
    ),
    "BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml": (
        "V185",
        ("scripts/site_v185_role_shadow.py", "scripts/site_v185_score.py",
         "tests/test_v185_role_shadow.py", "tests/test_v185_git_provenance.py"),
        ("python3 tests/test_v185_role_shadow.py", "python3 tests/test_v185_git_provenance.py",
         "python3 scripts/site_v185_role_shadow.py --repo .",
         "data/site_tail_shadow_v185/"),
    ),
    "BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml": (
        "V186",
        ("scripts/site_v186_refresh_scratch.py", "scripts/site_v186_patch_ui.py",
         "tests/test_v186_refresh.py"),
        ("python3 tests/test_v186_refresh.py", "python3 scripts/site_v186_refresh_scratch.py",
         "data/site_scratches_v182/"),
    ),
}


class GuardTrackedResearchers(unittest.TestCase):
    def test_retired_research_writers_stay_deleted_without_losing_sources(self):
        for name, (label, paths, _required) in CASES.items():
            if label == "V186":
                continue
            with self.subTest(workflow=name):
                self.assertFalse((WF / name).exists(), "Retired research cron must stay absent")
                for p in paths:
                    self.assertTrue((ROOT / p).is_file(), p)

    def test_active_v186_scratch_freshness_is_preserved(self):
        name = "BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml"
        label, paths, required = CASES[name]
        content = (WF / name).read_text(encoding="utf-8")
        self.assertIn("Verify tracked V186 sources without restoring historical code", content)
        self.assertIn("V186_TRACKED_MAIN_SOURCE_NO_LEGACY_RESTORE_PASS", content)
        for forbidden in ("PYRESTORE", "base64.b64decode", "gzip.decompress",
                          "write_bytes(data)", "write_bytes(raw)",
                          "data/formal_results", "RESULT_UNLOCK_TOKEN="):
            self.assertNotIn(forbidden, content)
        for p in paths:
            self.assertTrue((ROOT / p).is_file(), p)
            self.assertIn(p, content)
        for statement in required:
            self.assertIn(statement, content)
        triggers = content.split("permissions:", 1)[0]
        self.assertIn("  workflow_dispatch:", triggers)
        self.assertIn("  schedule:", triggers)
        self.assertIn("2-59/5 0-14,23 * * *", triggers)
        self.assertIn("if: github.ref == 'refs/heads/main'", content)
        self.assertIn("cancel-in-progress: false", content)
        self.assertIn("git push origin HEAD:main", content)


if __name__ == "__main__":
    unittest.main()
