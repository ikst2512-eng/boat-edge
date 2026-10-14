"""V342: disabled legacy writers stay manual-only and cannot race V216."""
from pathlib import Path
import re
import unittest

from scripts.boat_edge_v299_workflow_inventory import audit, event_block


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

LEGACY = (
    "BOAT_EDGE_V209_AI_AUTORUN_SIM.yml",
    "BOAT_EDGE_V211_DAILY_50K_SIM.yml",
    "BOAT_EDGE_V212_PAPER_SIM_INSTALL.yml",
    "BOAT_EDGE_V213_SHADOW_ROI.yml",
    "BOAT_EDGE_V214_ODDS_ARCHIVE_SHADOW.yml",
    "site-health.yml",
    "site-recovery.yml",
    "site-v103.yml",
)


class RetiredSchedulerTests(unittest.TestCase):
    def test_legacy_writers_are_manual_only(self):
        report = audit(WORKFLOWS)
        entries = {item["workflow"]: item for item in report["workflows"]}
        for name in LEGACY:
            with self.subTest(name=name):
                self.assertEqual(entries[name]["triggers"], ["workflow_dispatch"])
                self.assertEqual(entries[name]["crons"], [])
                text = (WORKFLOWS / name).read_text(encoding="utf-8")
                self.assertIn("manual recovery ONLY", text)
                self.assertNotRegex(event_block(text), r"^  (?:push|schedule|workflow_run):")

    def test_v216_remains_single_live_paper_chain_owner(self):
        text = (WORKFLOWS / "BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml").read_text(
            encoding="utf-8"
        )
        events = event_block(text)
        self.assertIsNotNone(re.search(r"^  schedule:", events, re.M))
        self.assertIn("contents: write", text)
        ordered = (
            "python3 scripts/boat_edge_v215_readiness.py",
            "python3 scripts/boat_edge_v214_shadow.py freeze",
            "python3 scripts/boat_edge_v211_paper_sim.py select",
            "python3 scripts/boat_edge_v214_shadow.py settle",
            "python3 scripts/boat_edge_v211_paper_sim.py settle",
        )
        positions = [text.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("gzip.decompress", text)
        self.assertNotIn("base64.b64decode", text)

    def test_secondary_reports_do_not_fan_out_on_every_v235_run(self):
        # V235 is the live source; secondary diagnostics retain a bounded
        # hourly schedule and manual recovery, without a workflow_run fanout.
        for name in ("v238.yml", "v241.yml"):
            with self.subTest(name=name):
                text = (WORKFLOWS / name).read_text(encoding="utf-8")
                events = event_block(text)
                self.assertIn("  schedule:", events)
                self.assertIn("  workflow_dispatch:", events)
                self.assertNotRegex(events, r"^  workflow_run:",)
                self.assertIn("if: github.ref == 'refs/heads/main'", text)

    def test_result_collector_does_not_write_audit_todo(self):
        results = (WORKFLOWS / "site-v109.yml").read_text(encoding="utf-8")
        audit = (WORKFLOWS / "site-v125.yml").read_text(encoding="utf-8")
        self.assertIn("git restore -- BOAT_EDGE_CURRENT_TODO.md", results)
        self.assertIn("git add data/site_results data/site_archive", results)
        self.assertNotIn(
            "git add data/site_results data/site_archive BOAT_EDGE_CURRENT_TODO.md",
            results,
        )
        self.assertIn(
            "git add -A -- data/site_prediction_audit/ BOAT_EDGE_CURRENT_TODO.md",
            audit,
        )

    def test_retirement_reduces_scheduled_writer_inventory(self):
        report = audit(WORKFLOWS)
        scheduled = set(report["scheduled_contents_writers"])
        self.assertTrue(scheduled.isdisjoint(LEGACY))
        self.assertLessEqual(len(scheduled), 47)


if __name__ == "__main__":
    unittest.main()
