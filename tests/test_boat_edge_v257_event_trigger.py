"""V257: V232-success event is a hint, never authorization to read results.

The V254 prefreeze script independently checks Git-committed PRE_RESULT source
and <=15min future deadline. These tests exercise event gates and missing
source provenance without any result endpoint or model/prediction change.
"""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from scripts.boat_edge_v254_third_tail import freeze, stamp

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v254-third-tail-shadow.yml"

class V257SourceTrigger(unittest.TestCase):
    def test_exact_v232_source_completion_trigger_with_conclusion_branch_guard(self):
        workflow=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_run:",workflow)
        # The current immutable site-only freeze pipeline is V235. V232
        # stays available as a legacy fallback, but cannot be the sole trigger.
        self.assertIn("'BOAT EDGE V232 - Independent Pre-Result Accuracy Cohort'",workflow)
        self.assertIn("'BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring'",workflow)
        self.assertIn("types: [completed]",workflow)
        self.assertIn("types: [completed]",workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'",workflow)
        self.assertIn("concurrency:",workflow)
        self.assertIn("cancel-in-progress: false",workflow)
        self.assertIn("git reset --hard origin/main",workflow)
        self.assertIn("data/site_autopilot/v254_frozen/",workflow)
        self.assertIn("V254_ONLY_PRE_RESULT_RESEARCH_STAGED",workflow)
        self.assertIn("V254_ONLY_SITE_RESEARCH_SCORE_STAGED",workflow)

    def test_v274_same_runner_future_freeze_before_any_result_scoring(self):
        v235=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        source=v235.index('      - name: Immutable pre-result source prediction cohort')
        inline=v235.index('      - name: V274 immediately freeze qualifying V254')
        post=v235.index('      - name: Only after pre-result commit - score already confirmed SITE results')
        self.assertTrue(source < inline < post)
        step=v235[inline:post]
        self.assertIn('scripts/boat_edge_v254_third_tail.py freeze',step)
        self.assertIn("test_boat_edge_v254_third_tail.py",step)
        self.assertIn('git reset --hard origin/main',step)
        self.assertIn('data/site_autopilot/v254_frozen',step)
        self.assertIn('V274_FORBIDDEN_PRE_RESULT_STAGE_',step)
        self.assertIn('V274_FUTURE_SHADOW_PRE_RESULT_PUBLISHED',step)
        self.assertIn('V274_NO_ELIGIBLE_NEW_PRE_RESULT_COHORT_NO_BACKFILL',step)
        self.assertIn('V274_NO_PUBLISHED_SHADOW_CONFLICT_SAFE_RETRY_NEXT_RUN',step)
        self.assertIn('git diff --cached --check',step)
        self.assertNotIn('site_results/',step)
        self.assertNotIn('settle',step)
        self.assertNotIn('git pull --rebase',step)
        self.assertNotIn('gh workflow run',step)
        # Standalone V254 still independently verifies the original first Git
        # commit and race deadline, and remains the periodic/event fallback.
        script=(ROOT/'scripts/boat_edge_v254_third_tail.py').read_text(encoding='utf-8')
        self.assertIn("SOURCE_GIT_PROVENANCE_UNVERIFIED",script)
        self.assertIn("NOT_IN_FUTURE_FREEZE_WINDOW",script)
        self.assertIn("V254_FORMAL_GATE_MUST_STAY_CLOSED",script)
        research=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('workflow_dispatch:',research)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",research)
        self.assertIn("scripts/boat_edge_v254_third_tail.py freeze",research)

    def test_v275_v234_source_producer_also_freezes_pre_result_tail(self):
        v234=(ROOT/'.github/workflows/V234.yml').read_text(encoding='utf-8')
        source=v234.index('      - name: Immutable pre-result source prediction cohort')
        freeze=v234.index('      - name: V275 immediately freeze qualifying V254')
        results=v234.index('      - name: Only after pre-result commit - score already confirmed SITE results')
        self.assertLess(source,freeze)
        self.assertLess(freeze,results)
        stage=v234[freeze:results]
        for marker in (
            'scripts/boat_edge_v254_third_tail.py freeze',
            "test_boat_edge_v254_third_tail.py",
            'git reset --hard origin/main',
            'data/site_autopilot/v254_frozen',
            'V275_FORBIDDEN_PRE_RESULT_STAGE_',
            'V275_FUTURE_SHADOW_PRE_RESULT_PUBLISHED',
            'V275_NO_ELIGIBLE_NEW_PRE_RESULT_COHORT_NO_BACKFILL',
            'V275_NO_PUBLISHED_SHADOW_CONFLICT_SAFE_RETRY_NEXT_RUN',
            'git diff --cached --check'):
            self.assertIn(marker,stage)
        for forbidden in ('site_results/', 'settle', 'git pull --rebase',
                          'git push --force', 'gh workflow run'):
            self.assertNotIn(forbidden,stage)
        self.assertIn("V254_FORMAL_GATE_MUST_STAY_CLOSED",
            (ROOT/'scripts/boat_edge_v254_third_tail.py').read_text())

    def test_v271_single_owner_scheduled_result_and_readiness(self):
        # Retired writers may be manually launched for recovery, but not
        # on the same 5-minute cron as their verified successors.
        legacy=[
          ROOT/'.github/workflows/site-results.yml',
          ROOT/'.github/workflows/BOAT_EDGE_V215_DEADLINE_READINESS.yml',
        ]
        for path in legacy:
            text=path.read_text(encoding='utf-8')
            self.assertIn('workflow_dispatch:',text,path.name)
            self.assertNotIn('  schedule:',text,path.name)
        self.assertIn('  schedule:',
            (ROOT/'.github/workflows/site-v109.yml').read_text(encoding='utf-8'))
        self.assertIn('  schedule:',
            (ROOT/'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml').read_text(encoding='utf-8'))
        self.assertIn('  schedule:',
            (ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8'))

    def temp_root(self):
        holder=tempfile.TemporaryDirectory()
        root=Path(holder.name)
        p=root/"data/formal_status.json"
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({"guards":{
          "results_seen":False,"unlock":False,"scoring":False,"RESULT_UNLOCK_TOKEN":None
        }}),encoding="utf-8")
        return holder,root

    def test_empty_v232_source_does_not_invent_candidate(self):
        tmp,root=self.temp_root()
        try:
            out=freeze(root,stamp("2026-10-12T04:28:00+00:00"))
            self.assertEqual(out["frozen_today"],0)
            self.assertEqual(out["source_cohorts_today"],0)
            self.assertEqual(out["future_window_cohorts_seen"],0)
            self.assertEqual(out["unfrozen_future_window_at_start"],0)
            self.assertEqual(out["new_frozen_this_run"],0)
            self.assertEqual(out["rejected_current_run"],{})
            self.assertFalse(out["result_access"])
            self.assertFalse(out["model_promotion_authorized"])
            self.assertFalse(out["production_model_changed"])
            self.assertFalse((root/"data/site_autopilot/v254_frozen").exists())
        finally:tmp.cleanup()

    def test_missing_original_git_proof_is_counted_not_frozen(self):
        tmp,root=self.temp_root()
        try:
            folder=root/"data/site_autopilot/v232_cohort"
            folder.mkdir(parents=True)
            original={
                "race_key":"20261012-14-11",
                "deadline_jst":"2026-10-12T13:34:00+09:00",
                "snapshot_saved_at":"2026-10-12T04:24:00+00:00",
                "evidence_committed_at":"2026-10-12T04:24:01+00:00",
            }
            (folder/"20261012-14-11.json").write_text(json.dumps(original),encoding="utf-8")
            out=freeze(root,stamp("2026-10-12T04:28:00+00:00"))
            self.assertEqual(out["source_cohorts_today"],1)
            self.assertEqual(out["future_window_cohorts_seen"],1)
            self.assertEqual(out["unfrozen_future_window_at_start"],1)
            self.assertEqual(out["new_frozen_this_run"],0)
            self.assertEqual(out["frozen_today"],0)
            self.assertEqual(out["rejected_current_run"].get("SOURCE_GIT_PROVENANCE_UNVERIFIED"),1)
            self.assertFalse((root/"data/site_autopilot/v254_frozen").exists())
            # Deadline has passed: source is not eligible for after-the-fact freeze.
            late=freeze(root,stamp("2026-10-12T04:36:00+00:00"))
            self.assertEqual(late["future_window_cohorts_seen"],0)
            self.assertEqual(late["frozen_today"],0)
        finally:tmp.cleanup()

    def test_formal_unlock_always_prevents_freeze(self):
        tmp,root=self.temp_root()
        try:
            path=root/"data/formal_status.json"
            d=json.loads(path.read_text(encoding="utf-8"))
            d["guards"]["results_seen"]=True
            path.write_text(json.dumps(d),encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"V254_FORMAL_GATE_MUST_STAY_CLOSED"):
                freeze(root,stamp("2026-10-12T04:28:00+00:00"))
        finally:tmp.cleanup()

if __name__=="__main__":
    unittest.main()
