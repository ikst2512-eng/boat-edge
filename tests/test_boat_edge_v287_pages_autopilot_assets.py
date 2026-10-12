"""V287: Autopilot HTML and all dependent local scripts must share deployed Pages lineage.

Read-only offline tests; never browse races, inspect outcomes, or mutate formal Fresh.
"""
from __future__ import annotations

import re
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.boat_edge_v277_pages_monitor import UI_PATHS, report, same_ui_lineage

ROOT=Path(__file__).resolve().parents[1]
NOW=datetime(2026,10,13,0,0,tzinfo=timezone.utc)


def fixtures(paths, bad_asset=None):
    current=[]
    deployed=[]
    for n,path in enumerate(paths):
        sha=(f"{n+1:040x}")[-40:]
        remote=("f"*40) if path==bad_asset else sha
        instant=(NOW-timedelta(minutes=40+n)).isoformat()
        current.append({"sha":sha,"commit":{"committer":{"date":instant}}})
        deployed.append({"sha":remote,"commit":{"committer":{"date":instant}}})
    return current,deployed


class V287AutopilotPagesAssets(unittest.TestCase):
    def test_every_active_autopilot_script_is_in_pages_lineage(self):
        html=(ROOT/"autopilot.html").read_text(encoding="utf8")
        paths=set(re.findall(r'<script\b[^>]*\bsrc=["\']\./(assets/[^"\'?]+\.js)(?:\?[^"\']*)?["\']',html))
        self.assertEqual(len(paths),6)
        self.assertIn("assets/boat_edge_v286_freeze_evidence.js",paths)
        self.assertTrue(paths.issubset(set(UI_PATHS)), sorted(paths-set(UI_PATHS)))
        self.assertEqual(len(set(UI_PATHS)),len(UI_PATHS))
        for path in paths:
            self.assertTrue((ROOT/path).is_file(),path)

    def test_missing_or_stale_freeze_script_blocks_latest_ui_claim(self):
        current,deployed=fixtures(UI_PATHS,"assets/boat_edge_v286_freeze_evidence.js")
        run={"name":"pages build and deployment","head_sha":"a"*40,
             "created_at":(NOW-timedelta(minutes=5)).isoformat(),
             "updated_at":(NOW-timedelta(minutes=4)).isoformat(),
             "status":"completed","conclusion":"success"}
        self.assertFalse(same_ui_lineage(current,deployed))
        result=report([run],current,NOW,deployed_ui_commits=deployed)
        self.assertEqual(result["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(result["ui_lineage_verified"])
        self.assertEqual(result["ui_lineage_paths_checked"],len(UI_PATHS))
        self.assertFalse(result["ui_checked_in_safari"])
        good=report([run],current,NOW,deployed_ui_commits=current)
        self.assertTrue(good["ui_lineage_verified"])
        self.assertEqual(good["status"],"LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS")

    def test_observer_executes_on_main_ui_push_not_pr(self):
        workflow=(ROOT/".github/workflows/v277-pages-monitor.yml").read_text(encoding="utf8")
        verify="Verify GitHub Pages publication against latest UI commit on main"
        self.assertEqual(workflow.count(verify),1)
        self.assertIn("github.event_name == 'push'",workflow)
        self.assertIn("github.ref == 'refs/heads/main'",workflow)
        self.assertIn("cancel-in-progress: false",workflow)
        for path in ["autopilot.html","assets/boat_edge_v286_freeze_evidence.js",
                     "assets/boat_edge_v278_next_watch.js",
                     "tests/test_boat_edge_v287_pages_autopilot_assets.py"]:
            self.assertGreaterEqual(workflow.count("'"+path+"'"),2,path)
        self.assertIn("test_boat_edge_v287_pages_autopilot_assets.py' -v",workflow)
        self.assertNotIn("actions/deploy-pages",workflow)
        self.assertNotIn("contents: write",workflow)


if __name__=="__main__":
    unittest.main()
