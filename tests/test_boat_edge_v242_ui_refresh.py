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

    def test_existing_workers_still_pin_python_sources(self):
        for worker, html, token in (
            (".github/workflows/v238.yml", "tail-diagnostics.html", "V238_EXISTING_SOURCE_DRIFT_FAIL_CLOSED_"),
        ):
            code = self.source(worker)
            self.assertIn(token, code)
            self.assertIn(f"if { 'file' if html == 'health.html' else 'name' } == '{html}'", code)
            self.assertIn("hashlib.sha256(data).hexdigest()", code)
            self.assertIn("if git push origin HEAD:main", code)
        code = self.source('.github/workflows/v237.yml')
        self.assertIn('V237_TRACKED_SOURCE_PIN_MISMATCH_', code)
        self.assertIn('scripts/boat_edge_v237_health.py', code)
        self.assertIn('tests/test_boat_edge_v237_health.py', code)
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
