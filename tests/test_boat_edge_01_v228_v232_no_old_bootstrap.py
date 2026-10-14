"""V228/V232 must use tracked modern UI and source, not historical gzip bundles.

The runnable core's pre-result and formal locks stay unchanged. No remote fetch.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/'.github/workflows'
CASES={
    "BOAT_EDGE_V228_SITE_AI_AUTOPILOT.yml": (
        "V228", (
            "scripts/boat_edge_v227_autopilot.py",
            "tests/test_boat_edge_v227_autopilot.py",
            "scripts/boat_edge_v228_freeze_only.py",
            "tests/test_boat_edge_v228_freeze_only.py",
            "autopilot.html", "ai-simulation.html",
        ),(
            "python3 scripts/boat_edge_v228_freeze_only.py",
            "python3 scripts/boat_edge_v227_autopilot.py",
            "data/site_prediction_snapshots/",
            "V228_SITE_AUTOPILOT_MONITORING_AND_PRE_RESULT_SAFE_FREEZE_PASS",
        ),
    ),
    "BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml": (
        "V232", (
            "scripts/boat_edge_v232_pre_result_cohort.py",
            "tests/test_boat_edge_v232_pre_result_cohort.py",
            "cohort.html", "autopilot.html",
        ),(
            "python3 scripts/boat_edge_v232_pre_result_cohort.py",
            "python3 scripts/boat_edge_v215_readiness.py",
            "python3 scripts/boat_edge_v214_shadow.py freeze",
            "data/site_autopilot/v232_cohort/",
            "V232_GUARDS_AND_ACCURACY_SCOPE_CONFIRMED",
        ),
    ),
}

class NoOldCoreBootstrap(unittest.TestCase):
    def test_jobs_no_longer_reinstall_or_mutate_tracked_user_ui(self):
        for name,(label,files,required) in CASES.items():
            with self.subTest(name=name):
                text=(WORKFLOWS/name).read_text(encoding='utf-8')
                self.assertIn(f"Validate {label} tracked main sources and existing UI without legacy bootstrap",text)
                self.assertIn(f"{label}_TRACKED_SOURCES_AND_CURRENT_UI_NAV_PASS",text)
                self.assertIn("git ls-files --error-unmatch",text)
                self.assertNotIn('gzip.decompress',text)
                self.assertNotIn('base64.b64decode',text)
                self.assertNotIn('write_bytes(',text)
                self.assertNotIn('page.write_text(',text)
                for name2 in files:
                    self.assertTrue((ROOT/name2).is_file(),name2)
                    self.assertIn(name2,text)
                for marker in required:
                    self.assertIn(marker,text)

    def test_keep_pre_result_staging_clocks_and_no_formal_results(self):
        crons={"V228":"4,9,14,19,24,29,34,39,44,49,54,59",
               "V232":"4,9,14,19,24,29,34,39,44,49,54,59"}
        for name,(label,files,_) in CASES.items():
            with self.subTest(name=name):
                text=(WORKFLOWS/name).read_text(encoding='utf-8')
                self.assertIn("  schedule:",text)
                self.assertIn("  workflow_dispatch:",text)
                self.assertIn(crons[label],text)
                self.assertIn("github.ref == 'refs/heads/main'",text)
                self.assertIn('cancel-in-progress: false',text)
                self.assertNotIn('data/formal_results',text)
                self.assertNotIn('RESULT_UNLOCK_TOKEN=',text)

    def test_real_tracked_navigation_is_preserved(self):
        sim=(ROOT/'ai-simulation.html').read_text(encoding='utf-8')
        ui=(ROOT/'autopilot.html').read_text(encoding='utf-8')
        self.assertEqual(sim.count('BOAT_EDGE_V227_STATUS_NAV'),1)
        self.assertEqual(sim.count('href="./autopilot.html"'),1)
        self.assertEqual(ui.count('<a href="./cohort.html">未見予想の検証</a>'),1)


if __name__=='__main__':
    unittest.main()
