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
    def test_v360_latest_race_ui_scripts_must_have_pages_sha_lineage(self):
        # Both compact comparison (V202) and racer cards (V203) change without
        # necessarily changing index.html; old Page success cannot cover them.
        targets={"assets/boat_edge_v202_display.js", "assets/boat_edge_v203_readable.js"}
        self.assertTrue(targets.issubset(set(UI_PATHS)))
        workflow=(ROOT/".github/workflows/v277-pages-monitor.yml").read_text(encoding="utf8")
        for asset in targets:
            self.assertTrue((ROOT/asset).is_file(),asset)
            self.assertGreaterEqual(workflow.count("'"+asset+"'"),2,asset)
        current,deployed=fixtures(UI_PATHS,"assets/boat_edge_v203_readable.js")
        run={"name":"pages build and deployment","head_sha":"a"*40,
             "created_at":(NOW-timedelta(minutes=5)).isoformat(),
             "updated_at":(NOW-timedelta(minutes=4)).isoformat(),
             "status":"completed","conclusion":"success"}
        bad=report([run],current,NOW,deployed_ui_commits=deployed)
        self.assertFalse(bad["ui_lineage_verified"])
        self.assertEqual(bad["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(bad["ui_checked_in_safari"])
        for asset in targets:
            one,two=fixtures(UI_PATHS,asset)
            self.assertFalse(same_ui_lineage(one,two),asset)

    def test_v377_race_first_mobile_css_cannot_be_unpublished(self):
        # PR #212 adds a standalone source-ranked mobile layout stylesheet.
        # A successful prior Pages run cannot validate a subsequent CSS-only edit.
        css="assets/boat_edge_v371_simple_ui.css"
        self.assertIn(css,UI_PATHS)
        self.assertTrue((ROOT/css).is_file())
        workflow=(ROOT/".github/workflows/v277-pages-monitor.yml").read_text(encoding="utf8")
        self.assertGreaterEqual(workflow.count("'"+css+"'"),2)
        index=(ROOT/"index.html").read_text(encoding="utf8")
        self.assertIn("boat_edge_v371_simple_ui.css?v=371",index)
        main,older=fixtures(UI_PATHS,css)
        self.assertFalse(same_ui_lineage(main,older),css)
        run={"name":"pages build and deployment","head_sha":"a"*40,
             "created_at":(NOW-timedelta(minutes=5)).isoformat(),
             "updated_at":(NOW-timedelta(minutes=4)).isoformat(),
             "status":"completed","conclusion":"success"}
        out=report([run],main,NOW,deployed_ui_commits=older)
        self.assertFalse(out["ui_lineage_verified"])
        self.assertEqual(out["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(out["ui_checked_in_safari"])

    def test_v374_topk_quickview_scripts_and_styles_are_sha_proven(self):
        # Rendering JS/CSS can change with no index.html update; latest Pages
        # evidence must cover the actual production assets in V373 browser CI.
        targets={
            "assets/boat_edge_v206_quickview.js",
            "assets/boat_edge_v206_quickview.css",
            "assets/boat_edge_v207_first_prediction.js",
            "assets/boat_edge_v207_first_prediction.css",
            "assets/boat_edge_v304_topk_mobile.css",
        }
        self.assertTrue(targets.issubset(set(UI_PATHS)))
        workflow=(ROOT/".github/workflows/v277-pages-monitor.yml").read_text(encoding="utf8")
        for path in targets:
            self.assertTrue((ROOT/path).is_file(),path)
            self.assertGreaterEqual(workflow.count("'"+path+"'"),2,path)
            main,old=fixtures(UI_PATHS,path)
            self.assertFalse(same_ui_lineage(main,old),path)
        changed="assets/boat_edge_v207_first_prediction.js"
        main,old=fixtures(UI_PATHS,changed)
        run={"name":"pages build and deployment","head_sha":"a"*40,
             "created_at":(NOW-timedelta(minutes=5)).isoformat(),
             "updated_at":(NOW-timedelta(minutes=4)).isoformat(),
             "status":"completed","conclusion":"success"}
        result=report([run],main,NOW,deployed_ui_commits=old)
        self.assertFalse(result["ui_lineage_verified"])
        self.assertEqual(result["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(result["ui_checked_in_safari"])

    def test_t01_all_sha_monitored_site_ui_paths_also_trigger_audit(self):
        # V277 already resolves last-touch SHA for each UI_PATHS member, but
        # path-filter omissions meant those updates did not launch monitoring.
        workflow=(ROOT/".github/workflows/v277-pages-monitor.yml").read_text(encoding="utf8")
        self.assertIn("  pull_request:",workflow)
        self.assertIn("  push:",workflow)
        self.assertEqual(len(UI_PATHS),len(set(UI_PATHS)))
        for path in UI_PATHS:
            self.assertTrue((ROOT/path).is_file(),path)
            self.assertGreaterEqual(workflow.count("'"+path+"'"),2,"MISSING_PR_OR_PUSH_TRIGGER: "+path)
        # A green Pages job for an older SHA is not proof the homepage hit
        # banner JavaScript from today's deployment has been published.
        homepage="assets/boat_edge_v241_home.js"
        self.assertIn(homepage,UI_PATHS)
        current,deployed=fixtures(UI_PATHS,homepage)
        run={"name":"pages build and deployment","head_sha":"a"*40,
             "created_at":(NOW-timedelta(minutes=5)).isoformat(),
             "updated_at":(NOW-timedelta(minutes=4)).isoformat(),
             "status":"completed","conclusion":"success"}
        result=report([run],current,NOW,deployed_ui_commits=deployed)
        self.assertFalse(result["ui_lineage_verified"])
        self.assertEqual(result["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(result["ui_checked_in_safari"])

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
