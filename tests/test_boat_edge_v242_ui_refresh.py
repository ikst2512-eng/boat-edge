"""V242: read-only tests for UI refresh without altering prediction or audit evidence."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestV242SiteRefresh(unittest.TestCase):
    @staticmethod
    def source(name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_health_refresh_does_not_accumulate_rows(self):
        h = self.source("health.html")
        self.assertIn('id="refreshHealth"', h)
        self.assertIn('href="./">BOAT EDGE</a>', h)
        self.assertIn('boat_edge_v271_health.js?v=271', h)
        js = self.source('assets/boat_edge_v271_health.js')
        self.assertIn('BOAT_EDGE_V242_UI_REFRESH', js)
        self.assertIn("getElementById('rates').replaceChildren()", js)
        self.assertIn("getElementById('observed').replaceChildren()", js)
        self.assertIn("button.disabled = false", js)
        self.assertIn("v237_current.json?t=' + Date.now()", js)
        self.assertNotIn('raceresult', h + js)

    def test_tail_refresh_is_user_initiated_and_no_synthetic_results(self):
        h = self.source("tail-diagnostics.html")
        self.assertIn('id="refreshTail"', h)
        self.assertIn('href="./index.html"', h)
        self.assertIn('BOAT_EDGE_V242_UI_REFRESH', h)
        self.assertIn("v238_current.json?t='+Date.now()", h)
        self.assertIn("button.disabled=false", h)
        self.assertIn("p.both_hit", h)
        self.assertNotIn("data/formal_", h)

    def test_existing_workers_keep_source_and_ui_provenance_guards(self):
        # V238 no longer pins an old gzip bundle to tracked production code.
        # The runtime must verify current main instead of reinstalling old UI.
        report=self.source('.github/workflows/v238.yml')
        self.assertIn('V238_TRACKED_CURRENT_SOURCE_NO_REINSTALL_PASS', report)
        self.assertIn('git ls-files --error-unmatch', report)
        self.assertIn('git diff --exit-code -- scripts/boat_edge_v238_tail_diagnostic.py', report)
        self.assertIn('git add -- data/site_autopilot/v238_current.json', report)
        self.assertIn("allowed={'data/site_autopilot/v238_current.json'}", report)
        self.assertIn("if git push origin HEAD:main", report)
        self.assertNotIn('V238_EXISTING_SOURCE_DRIFT_FAIL_CLOSED_', report)
        self.assertNotIn('base64.b64decode', report)
        self.assertNotIn('gzip.decompress', report)

        # V237 remains a separate guarded health owner; do not loosen its
        # source checks or the independent tracked pins in this V242 update.
        health=self.source('.github/workflows/v237.yml')
        self.assertIn('V237_TRACKED_SOURCE_PIN_MISMATCH_', health)
        self.assertIn('scripts/boat_edge_v237_health.py', health)
        self.assertIn('tests/test_boat_edge_v237_health.py', health)
        from scripts.verify_workflow_source_pins import verify
        verify(ROOT)

    def test_inline_javascript_syntax(self):
        for name in ("health.html", "tail-diagnostics.html"):
            html = self.source(name)
            matches = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
            self.assertEqual(len(matches), 1, name)
            checked = subprocess.run(["node", "--check", "-"], input=matches[0],
                                     text=True, capture_output=True, check=False)
            self.assertEqual(checked.returncode, 0, name + ": " + checked.stderr)
        checked = subprocess.run(['node','--check',str(ROOT/'assets/boat_edge_v271_health.js')],
                                 capture_output=True,text=True,check=False)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_formal_fresh_remains_locked(self):
        status = json.loads(self.source("data/formal_status.json"))
        flags = status.get("guards") or {}
        self.assertTrue(all(flags.get(k) is False for k in ("results_seen", "unlock", "scoring")))
        self.assertIsNone(flags.get("RESULT_UNLOCK_TOKEN"))


if __name__ == "__main__":
    unittest.main()
