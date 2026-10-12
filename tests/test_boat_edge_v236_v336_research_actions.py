"""V336 Actions-only research capture contract; no write access or formal scoring."""
import pathlib
import re
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / ".github/workflows/BOAT_EDGE_V336_SITE_RESEARCH_CAPTURE.yml"


class V336ProspectiveArtifactWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = PATH.read_text(encoding="utf-8")

    def test_current_main_and_bounded_live_schedule_only(self):
        body = self.body
        self.assertIn("workflow_run:", body)
        self.assertIn("workflow_dispatch:", body)
        self.assertIn("schedule:", body)
        self.assertIn("23,0-14 * * *", body)
        self.assertIn("github.ref == 'refs/heads/main'", body)
        self.assertIn("head_repository.full_name == github.repository", body)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", body)
        self.assertIn("cancel-in-progress: false", body)
        self.assertIn("ref: main", body)
        self.assertIn("--max-races 4", body)
        self.assertIn("--capture", body)
        self.assertIn("default: false", body)

    def test_no_repo_write_or_result_scoring(self):
        body = self.body
        self.assertRegex(body, r"(?m)^permissions:\\n  contents: read$")
        self.assertIn("persist-credentials: false", body)
        self.assertNotRegex(body, r"(?m)^  contents: write$")
        self.assertNotIn("git push", body.lower())
        self.assertNotIn("workflow_dispatch:  # force run result", body)
        self.assertIn("production_eligible", body)
        self.assertIn("formal_fresh_read", body)
        self.assertIn("model_promotion_authorized", body)
        self.assertIn("v336-site-research-", body)
        self.assertIn("actions/upload-artifact@v4", body)

    def test_artifact_packaging_code_is_valid_python_and_checks_source_sha(self):
        body = self.body
        match = re.search(r"(?ms)^          python3 - <<'PY'\\n(.*?)^          PY$", body)
        self.assertIsNotNone(match)
        code = textwrap.dedent(match.group(1))
        compile(code, "v336-artifact-bundle", "exec")
        self.assertIn("hashlib.sha256(raw).hexdigest()", code)
        self.assertIn("hashlib.sha256(body).hexdigest()", code)
        self.assertIn("V336_FROZEN_FILE_SHA_MISMATCH", code)
        self.assertIn("V336_SOURCE_BYTES_SHA_MISMATCH", code)
        self.assertIn("SITE_ONLY_LOCAL_SHA_RESEARCH_NOT_FORMAL", code)
        self.assertIn("independent_source_authentication_proven", code)


if __name__ == "__main__":
    unittest.main()
