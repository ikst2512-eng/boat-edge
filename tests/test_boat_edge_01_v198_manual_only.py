"""V198 retrospective diagnostic was retired; it must never become a live writer.

This is a read-only source/workflow contract with no outcome file access.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/BOAT_EDGE_V198_ROLE_DIAGNOSTIC.yml"


class V198QuarantinedManualResearch(unittest.TestCase):
    def test_obsolete_v198_research_writer_remains_deleted(self):
        self.assertFalse(WORKFLOW.exists(), "Retired diagnostic must not regain Git write triggers")

    def test_current_first_git_freeze_owners_remain_live(self):
        for name in ("V234.yml", "V235.yml"):
            with self.subTest(workflow=name):
                source=(ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
                self.assertIn("  schedule:",source)
                self.assertIn("scripts/boat_edge_v230_fast_lane.py",source)
                self.assertIn("git reset --hard origin/main",source)
                self.assertIn("cancel-in-progress: false",source)
                self.assertNotIn("git push --force",source)

    def test_prospective_research_rejects_missing_original_git_proof(self):
        source=(ROOT/"scripts/boat_edge_v254_third_tail.py").read_text(encoding="utf-8")
        self.assertIn("SOURCE_GIT_PROVENANCE_UNVERIFIED",source)
        self.assertIn("NOT_IN_FUTURE_FREEZE_WINDOW",source)
        self.assertIn("V254_FORMAL_GATE_MUST_STAY_CLOSED",source)


if __name__ == "__main__":
    unittest.main()
