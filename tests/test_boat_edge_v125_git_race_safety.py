"""V125 revision audit must recompute from latest main instead of rebasing stale data."""
import ast
import re
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "site-v125.yml"


class V125GitRaceSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = WORKFLOW.read_text(encoding="utf-8")

    def test_audit_and_todo_are_replayable_exact_source(self):
        src = self.src
        capture = 'cat > "$RUNNER_TEMP/v125_audit_once.py" <<\'PY\''
        self.assertIn(capture, src)
        audit = src.split(capture, 1)[1].split("\n          PY", 1)[0]
        ast.parse(textwrap.dedent(audit))
        self.assertIn('SNAPS.glob(f"{TODAY}-??-??.json")', audit)
        self.assertIn("snapshot_sha256", audit)
        self.assertIn("first_audited_at", audit)
        self.assertIn("settlement", audit)
        self.assertIn('cat > "$RUNNER_TEMP/v125_todo_once.py"', src)
        self.assertIn('python "$RUNNER_TEMP/v125_audit_once.py"', src)

    def test_no_git_rebase_and_source_reset_before_every_replay(self):
        src = self.src
        save = src.split("      - name: Recompute and publish V125 audit from the latest main", 1)[1]
        self.assertNotIn("git pull --rebase", save)
        self.assertNotIn("git push --force", save)
        self.assertIn("for attempt in 1 2 3 4 5; do", save)
        self.assertIn("git fetch --no-tags origin main", save)
        self.assertIn("git reset --hard origin/main", save)
        self.assertIn("git clean -fd -- data/site_prediction_audit/", save)
        self.assertLess(save.index("git reset --hard origin/main"),
                        save.index('python "$RUNNER_TEMP/v125_audit_once.py"'))
        self.assertLess(save.index('python "$RUNNER_TEMP/v125_audit_once.py"'),
                        save.index("git add -A -- data/site_prediction_audit/"))
        self.assertLess(save.index("git add -A -- data/site_prediction_audit/"),
                        save.index("git commit -m"))
        self.assertLess(save.index("git commit -m"), save.index("git push origin HEAD:main"))

    def test_only_main_and_successful_same_repo_upstream_may_write(self):
        """V125 uses checkout main and contents:write, never branch event side effects."""
        src = self.src
        pre, job = src.split("jobs:", 1)
        self.assertIn("  push:", pre)
        self.assertIn("branches: [main]", pre)
        self.assertIn("github.ref == 'refs/heads/main'", job)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", job)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", job)
        self.assertIn("ref: main", job)
        self.assertIn("  contents: write", pre)
        self.assertIn("git push origin HEAD:main", job)

    def test_gate1c_v229_completion_wakes_existing_v125_without_new_writer(self):
        """Only successful same-repo V229 can nudge the existing V125 index owner."""
        src = self.src
        event, job = src.split("jobs:", 1)
        upstream = "BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit"
        historical = "BOAT EDGE V123 UI Matched Final History"
        self.assertEqual(event.count("  workflow_run:"), 1)
        self.assertEqual(event.count("  schedule:"), 1)
        self.assertEqual(event.count('      - "' + upstream + '"'), 1)
        self.assertEqual(event.count('      - "' + historical + '"'), 1)
        self.assertIn("github.event.workflow_run.name == '" + upstream + "'", job)
        self.assertIn("github.event.workflow_run.name == '" + historical + "'", job)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", job)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", job)
        self.assertNotIn("BOAT EDGE V220 - Autonomous Site Operations", event)
        self.assertNotIn("BOAT EDGE V235 - Stable Autonomous Prediction Freeze", event)
        self.assertEqual(src.count("      - name: Recompute and publish V125 audit from the latest main"), 1)
        self.assertIn('git reset --hard origin/main', job)
        self.assertIn('git clean -fd -- data/site_prediction_audit/', job)
        self.assertIn('if git push origin HEAD:main; then', job)
        v229 = (ROOT / ".github" / "workflows" /
                "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml").read_text(encoding="utf-8")
        self.assertNotIn("BOAT EDGE V125 Revision Safe FINAL15M Audit",
                         v229.split("permissions:", 1)[0])

    def test_late_replay_fail_closed_without_formal_results(self):
        src = self.src
        save = src.split("      - name: Recompute and publish V125 audit from the latest main", 1)[1]
        self.assertIn('assert not audit.get("errors")', save)
        self.assertIn('V125_PUBLISH_CONFLICT_FAILED_CLOSED', save)
        self.assertIn('exit 1', save)
        self.assertNotIn("data/formal_results/", save)
        self.assertNotIn("RESULT_UNLOCK_TOKEN", save)
        self.assertIn('github.event_name != \'schedule\'', src)
        self.assertIn('github.event_name != \'workflow_run\'', src)


if __name__ == "__main__":
    unittest.main()
