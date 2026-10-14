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
    def test_no_live_worker_restores_or_replaces_historical_sources(self):
        for name, (label, paths, required) in CASES.items():
            with self.subTest(workflow=name):
                content = (WF / name).read_text(encoding="utf-8")
                self.assertIn(
                    f"Verify tracked {label} sources without restoring historical code",
                    content,
                )
                self.assertIn(f"{label}_TRACKED_MAIN_SOURCE_NO_LEGACY_RESTORE_PASS",
                              content)
                self.assertNotIn("PYRESTORE", content)
                self.assertNotIn("base64.b64decode", content)
                self.assertNotIn("gzip.decompress", content)
                self.assertNotIn("write_bytes(data)", content)
                self.assertNotIn("write_bytes(raw)", content)
                for p in paths:
                    self.assertTrue((ROOT / p).is_file(), p)
                    self.assertIn(p, content)
                for statement in required:
                    self.assertIn(statement, content)

    def test_preserve_current_live_frequency_and_first_freeze_boundaries(self):
        expected_cron = {
            "V180": '*/10 0-14,23 * * *',
            "V185": '*/10 0-14,23 * * *',
            "V186": '2-59/5 0-14,23 * * *',
        }
        for name, (label, _paths, _required) in CASES.items():
            with self.subTest(workflow=name):
                content = (WF / name).read_text(encoding="utf-8")
                triggers = content.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
                self.assertIn("  workflow_dispatch:", triggers)
                self.assertIn("  schedule:", triggers)
                self.assertIn(expected_cron[label], triggers)
                self.assertIn("if: github.ref == 'refs/heads/main'", content)
                self.assertIn("cancel-in-progress: false", content)
                self.assertIn("git push origin HEAD:main", content)
                self.assertNotIn("data/formal_results", content)
                self.assertNotIn("RESULT_UNLOCK_TOKEN=", content)


if __name__ == "__main__":
    unittest.main()
