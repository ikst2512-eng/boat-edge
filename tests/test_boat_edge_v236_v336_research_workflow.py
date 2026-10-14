"""V336 manual-only permission-blocked research guardrails (static, offline)."""
from pathlib import Path
import json
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v336-site-research-live-freeze.yml"


class V336WorkflowSafety(unittest.TestCase):
    def test_manual_only_and_artifact_retention(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", s)
        # Periodic diagnostics cannot create authorized source captures or
        # immutable predictions. Keep the manual research route without
        # launching up to 288 redundant runners/day.
        events = s.split("on:", 1)[1].split("permissions:", 1)[0]
        self.assertNotIn("  schedule:", events)
        self.assertNotIn("  workflow_run:", events)
        self.assertNotIn("  push:", events)
        self.assertIn("python3 scripts/boat_edge_v334_live_batch_runner.py", s)
        self.assertIn("--root . --window-minutes 15 --max-races 12", s)
        self.assertNotIn("--capture --window-minutes", s)
        self.assertIn("V336_UNAUTHORIZED_AUTOCAPTURE_OR_FREEZE", s)
        self.assertIn("'third_party_capture_permitted':False", s)
        self.assertIn("actions/upload-artifact@v4", s)
        self.assertIn("retention-days: 30", s)
        self.assertIn("data/research_local_v332/", s)
        self.assertIn("data/source_captures/", s)
        # V340 exposes concrete lack-of-coverage rather than 0/0 success.
        self.assertIn("report['run_diagnostic']", s)
        self.assertIn("window['coverage']", s)
        self.assertIn("RESEARCH_REPORT_SAFETY_FLAGS_INVALID", s)
        self.assertIn("'global_uniqueness_verified':False", s)
        self.assertIn("'research_only':True", s)

    def test_issue_204_provider_permission_register_denies_all_unknown(self):
        # Development CI uses sparse checkout (scripts/tests/assets/.github),
        # so read the exact committed docs blob without creating a duplicate.
        permission_path="docs/BOAT_EDGE_01_V374_SOURCE_PERMISSION_REGISTER.json"
        installed=ROOT/permission_path
        if installed.is_file():
            source=installed.read_text(encoding="utf8")
        else:
            source=subprocess.check_output(
                ["git","show","HEAD:"+permission_path],cwd=ROOT,text=True)
        document=json.loads(source)
        self.assertEqual(document["issue"],204)
        self.assertEqual(set(document["providers"]),{"boaters","kyoteibiyori"})
        fields={"approved_for_automated_access","approved_for_ai_training",
                "approved_for_redistribution","scope","date","written_grant"}
        for record in document["providers"].values():
            self.assertEqual(set(record), fields)
            self.assertIs(record["approved_for_automated_access"],False)
            self.assertIs(record["approved_for_ai_training"],False)
            self.assertIs(record["approved_for_redistribution"],False)
            self.assertIsNone(record["written_grant"])

    def test_v357_parser_dependencies_installed_before_capture(self):
        # PR #161 introduced BeautifulSoup/lxml parsers; V336 failed on absent bs4.
        # Keep dependency installation BEFORE the isolated research runner in CI.
        s = WORKFLOW.read_text(encoding="utf-8")
        install = s.find("python3 -m pip install --disable-pip-version-check requests beautifulsoup4 lxml")
        smoke = s.find("python3 -c 'from bs4 import BeautifulSoup; import lxml, requests'")
        run = s.find("python3 scripts/boat_edge_v334_live_batch_runner.py")
        self.assertGreaterEqual(install, 0, "V336_HTML_PARSER_INSTALL_MISSING")
        self.assertGreater(smoke, install, "V336_DEPENDENCY_IMPORT_SMOKE_MISSING")
        self.assertGreater(run, smoke, "V336_DEPENDENCIES_MUST_PRECEDE_LIVE_CAPTURE")
        self.assertIn("contents: read", s)
        self.assertIn("persist-credentials: false", s)

    def test_no_repo_write_or_formal_unlock(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", s)
        self.assertIn("persist-credentials: false", s)
        self.assertIn("github.ref == 'refs/heads/main'", s)
        self.assertIn("RESULT_UNLOCK_TOKEN", s)
        self.assertIn("git status --porcelain --untracked-files=no", s)
        for forbidden in ("contents: write", "git push", "git commit",
                          "resultlist", "payout", "race_result", "gh pr merge"):
            self.assertNotIn(forbidden, s)


if __name__ == "__main__":
    unittest.main()
