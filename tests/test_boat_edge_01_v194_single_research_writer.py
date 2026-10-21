"""Guard retired research Git writers without requiring deleted workflow files.

Read only workflow and source text. Does not access outcomes or formal records.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"


class ResearchFreezeSingleOwner(unittest.TestCase):
    def test_obsolete_independent_research_writers_remain_deleted(self):
        for name in (
            "BOAT_EDGE_V194.yml",
            "BOAT_EDGE_V180_CONDITIONAL_TAIL_SHADOW.yml",
            "BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml",
            "V195.yml",
        ):
            with self.subTest(workflow=name):
                self.assertFalse((WF / name).exists(),
                                 "Retired research workflow must not regain cron/main writer")

    def test_only_fallback_owns_optional_research_freeze(self):
        primary = (WF / "V235.yml").read_text(encoding="utf-8")
        fallback = (WF / "V234.yml").read_text(encoding="utf-8")
        for text in (primary, fallback):
            self.assertIn("  schedule:", text)
            self.assertIn("cancel-in-progress: false", text)
            self.assertIn("git reset --hard origin/main", text)
            self.assertNotIn("git push --force", text)
        self.assertNotIn("V274 immediately freeze qualifying V254", primary)
        self.assertNotIn("scripts/boat_edge_v254_third_tail.py freeze", primary)
        self.assertIn("V275 immediately freeze qualifying V254", fallback)
        self.assertIn("scripts/boat_edge_v254_third_tail.py freeze", fallback)

    def test_research_source_provenance_guard_retained(self):
        source = (ROOT / "scripts/boat_edge_v254_third_tail.py").read_text(encoding="utf-8")
        for marker in ("SOURCE_GIT_PROVENANCE_UNVERIFIED",
                       "NOT_IN_FUTURE_FREEZE_WINDOW",
                       "V254_FORMAL_GATE_MUST_STAY_CLOSED"):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
