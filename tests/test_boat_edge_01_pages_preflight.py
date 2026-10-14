"""Pages legacy mode must skip duplicate expensive pipeline; PR still tests stage.

No network, no Pages settings change and no race data access.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages-controlled-publish.yml"


class PagesSourcePreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.jobs = yaml.safe_load(cls.source)["jobs"]

    def test_preflight_starts_without_regression_dependency(self):
        source = self.jobs["verify-source"]
        self.assertNotIn("needs", source)
        self.assertIn("github.event_name != 'pull_request'", source["if"])
        script = " ".join(
            step.get("run", "") for step in source["steps"]
        )
        self.assertIn("PAGES_LEGACY_SOURCE_UNCHANGED_NO_CUSTOM_DEPLOY", script)
        self.assertIn("PAGES_ACTIONS_SOURCE_CONFIRMED", script)
        self.assertIn("echo enabled=false", script)
        self.assertIn("echo enabled=true", script)

    def test_legacy_fanout_skips_expensive_staging_but_pr_is_tested(self):
        stage = self.jobs["stage-regression"]
        self.assertEqual(stage["needs"], "verify-source")
        gate = stage["if"]
        self.assertIn("always()", gate)
        self.assertIn("github.event_name == 'pull_request'", gate)
        self.assertIn("needs.verify-source.outputs.enabled == 'true'", gate)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", gate)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", gate)
        tests = "\n".join(step.get("run", "") for step in stage["steps"])
        self.assertIn("test_site_pages_stage.py", tests)
        self.assertIn("Test actual site artifact composition", self.source)

    def test_deploy_requires_real_pages_mode_and_passing_stage(self):
        build = self.jobs["build"]
        self.assertEqual(build["needs"], ["verify-source", "stage-regression"])
        self.assertIn("needs.verify-source.outputs.enabled == 'true'", build["if"])
        self.assertIn("needs.stage-regression.result == 'success'", build["if"])
        deploy = self.jobs["deploy"]
        self.assertEqual(deploy["needs"], "build")
        self.assertIn("needs.build.result == 'success'", deploy["if"])
        self.assertIn("actions/deploy-pages@v4", self.source)


if __name__ == "__main__":
    unittest.main()
