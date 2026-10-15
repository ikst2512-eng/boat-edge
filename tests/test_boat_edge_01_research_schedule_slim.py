"""01-only safe research workflow cleanup: preserve LIVE source/freeze ownership.

Fixture/static checks; no racing results or network access.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def event_section(name):
    source = (WORKFLOWS / name).read_text(encoding="utf-8")
    return source.split("on:\n", 1)[1].split("\npermissions:", 1)[0], source


class SafeResearchWorkflowCadence(unittest.TestCase):
    def test_v255_retrospective_calibration_uses_hourly_fallback(self):
        events, source = event_section("v255-calibration-evidence.yml")
        self.assertIn("  workflow_dispatch:", events)
        self.assertIn("  push:", events)
        self.assertIn("  schedule:", events)
        self.assertIn("cron: '9 0-14,23 * * *'", events)
        self.assertNotIn("cron: '9,29,49", events)
        self.assertIn("scripts/boat_edge_v255_confidence_audit.py", source)
        self.assertIn("data/site_autopilot/v255_confidence_current.json", source)
        self.assertIn("V255_UNCALIBRATED_CONFIDENCE_SOURCE_AUDIT_PASS", source)
        self.assertNotIn("gh workflow run V229", source)
        self.assertNotIn("gh workflow run V235", source)
        self.assertIn("if: github.ref == 'refs/heads/main'", source)

    def test_v171_self_trigger_does_not_reference_nonexistent_workflow(self):
        events, source = event_section("BOAT_EDGE_V171.yml")
        self.assertIn("'.github/workflows/BOAT_EDGE_V171.yml'", events)
        self.assertNotIn("BOAT_EDGE_V171_ONE_UPLOAD.yml", events)
        self.assertIn("  workflow_dispatch:", events)
        self.assertIn("cron: '0,5,10 23 * * *'", events)
        self.assertIn("cron: '15 0 * * *'", events)
        self.assertIn("V171_FREEZE_COMMIT_TOO_LATE", source)
        self.assertIn("V171_FREEZE_PUSH_TOO_LATE", source)
        self.assertIn("data/site_learning/v171_prospective_venue/", source)

    def test_core_prospective_freeze_workflows_remain_independent(self):
        for path in (
            "auto-update.yml",
            "site-odds.yml",
            "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml",
            "V235.yml",
        ):
            with self.subTest(path=path):
                txt = (WORKFLOWS / path).read_text(encoding="utf-8")
                self.assertIn("  schedule:", txt)
                self.assertIn("  workflow_dispatch:", txt)


if __name__ == "__main__":
    unittest.main()
