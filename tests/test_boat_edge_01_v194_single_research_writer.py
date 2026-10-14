"""01: keep independent prospective research freeze owners single-writer.

Read workflow source only. This suite does not load races, results, payouts,
pre-deadline evidence or Formal Fresh sources.
"""
from pathlib import Path
import re
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"

class ResearchFreezeSingleOwner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.health = (WF / "BOAT_EDGE_V194.yml").read_text(encoding="utf-8")
        cls.v180 = (WF / "BOAT_EDGE_V180_CONDITIONAL_TAIL_SHADOW.yml").read_text(encoding="utf-8")
        cls.v185 = (WF / "BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml").read_text(encoding="utf-8")
        cls.v195 = (WF / "V195.yml").read_text(encoding="utf-8")

    def test_live_prospective_freezers_retain_ten_minute_windows(self):
        for name, text, target in (
            ("V180", self.v180, "data/site_tail_shadow_v180/predictions/"),
            ("V185", self.v185, "data/site_tail_shadow_v185/"),
        ):
            with self.subTest(owner=name):
                self.assertIn("workflow_dispatch:", text)
                self.assertIn("*/10 0-14,23 * * *", text)
                self.assertIn("if: github.ref == 'refs/heads/main'", text)
                self.assertIn("git push origin HEAD:main", text)
                self.assertIn(target, text)
                self.assertNotIn("data/formal_results", text)

    def test_v194_diagnostic_is_hourly_and_not_a_third_freezer(self):
        x = self.health
        events = x.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("    - cron: '33 0-14,23 * * *'", events)
        self.assertEqual(len(re.findall(r"(?m)^    - cron:", events)), 1)
        self.assertIn("'.github/workflows/BOAT_EDGE_V194.yml'", events)
        self.assertIn("  workflow_dispatch:", events)
        self.assertIn("if: github.ref == 'refs/heads/main'", x)
        self.assertIn("V194_PRE_RESULT_FREEZE_DIAG", x)
        self.assertIn("V194_OUTCOME_AND_FORMAL_GATES_UNTOUCHED", x)
        self.assertIn("data/site_tail_shadow_v185/diagnostics/", x)
        self.assertIn("V194_DIAGNOSTICS_UNCHANGED_NO_MAIN_CHURN", x)
        self.assertNotIn("python3 scripts/site_v180_shadow.py --repo .", x)
        self.assertNotIn("python3 scripts/site_v185_role_shadow.py --repo .", x)
        self.assertNotIn("git add -A -- data/site_tail_shadow_v180/predictions", x)
        self.assertNotIn("git add -A -- data/site_tail_shadow_v185/predictions", x)
        self.assertNotIn("git reset --hard", x)
        self.assertNotIn("data/site_results", x)
        self.assertNotIn("data/formal_results", x)
        staged = re.findall(r"(?m)^\s+git add(?: -A)? -- ([^\n]+)$", x)
        self.assertEqual(staged, ["data/site_tail_shadow_v185/diagnostics/"])
        # The existing code generates diagnostic status without touching outcomes.
        snippet = x.split("python3 - <<'PYDIAG'\n", 1)[1].split("\n          PYDIAG", 1)[0]
        compile(textwrap.dedent(snippet), "V194_DIAG_FIXTURE", "exec")

    def test_v195_one_time_bootstrap_cannot_redispatch(self):
        x = self.v195
        events = x.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("  workflow_dispatch:", events)
        for trigger in ("  schedule:", "  push:", "  workflow_run:"):
            self.assertNotIn(trigger, events)
        self.assertIn("  contents: read", x)
        self.assertNotIn("actions: write", x)
        self.assertNotIn("gh api -X POST", x)
        self.assertNotIn("git push", x)
        self.assertIn("V195_RETIRED_NO_V194_REDISPATCH", x)


if __name__ == "__main__":
    unittest.main()
