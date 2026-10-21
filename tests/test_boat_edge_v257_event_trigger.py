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
    def test_retired_v254_is_manual_only_and_live_owner_preserves_guard(self):
        workflow=WORKFLOW.read_text(encoding="utf-8")
        header=workflow.split("\njobs:",1)[0]
        self.assertIn("workflow_dispatch:",header)
        self.assertNotIn("\n  schedule:",header)
        self.assertNotIn("\n  workflow_run:",header)
        self.assertNotIn("V274 immediately freeze qualifying V254",
                         (ROOT/'.github/workflows/V235.yml').read_text())
        self.assertIn("V275 immediately freeze qualifying V254",
                      (ROOT/'.github/workflows/V234.yml').read_text())
        self.assertIn("concurrency:",workflow)
        self.assertIn("cancel-in-progress: false",workflow)
        self.assertIn("git reset --hard origin/main",workflow)
        self.assertIn("V254_ONLY_PRE_RESULT_RESEARCH_STAGED",workflow)
        self.assertIn("V254_ONLY_SITE_RESEARCH_SCORE_STAGED",workflow)

    def test_v288_safe_collector_completion_triggers_v235_even_if_cron_is_delayed(self):
        primary=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        self.assertIn("workflow_run:",primary)
        self.assertIn("'BOAT EDGE 自動更新'",primary)
        self.assertIn("types: [completed]",primary)
        job=primary.split("  freeze-then-score-site-only:",1)[1]
        gate=job.split("    runs-on:",1)[0]
        self.assertIn("github.ref == 'refs/heads/main'",gate)
        self.assertIn("github.event_name != 'workflow_run'",gate)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",gate)
        self.assertIn("github.event.workflow_run.head_branch == 'main'",gate)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository",gate)
        self.assertIn("cancel-in-progress: false",primary)
        self.assertIn("  schedule:",primary)
        self.assertNotIn("      - name: V274 immediately freeze qualifying V254",primary)
        # Collectors may read official PRE_RESULT only; the downstream future
        # research freeze remains strictly source/Git/deadline guarded.
        self.assertIn("git reset --hard origin/main",primary)
        self.assertNotIn("scripts/boat_edge_v254_third_tail.py freeze",primary)
        collector=(ROOT/'.github/workflows/auto-update.yml').read_text(encoding='utf-8')
        self.assertIn("name: BOAT EDGE 自動更新",collector)
        self.assertIn("  schedule:",collector)
        self.assertIn("V270_PRE_RESULT_SAFE_PUSH_PASS",collector)
        self.assertNotIn("git push --force",primary)
        self.assertNotIn("git push --force",collector)

    def test_v235_skips_optional_shadow_while_v234_keeps_backup(self):
        primary=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        self.assertNotIn("V274 immediately freeze qualifying V254",primary)
        self.assertNotIn("scripts/boat_edge_v254_third_tail.py freeze",primary)
        self.assertIn("scripts/boat_edge_v229_atomic_freeze",primary)
        self.assertIn("Only after pre-result commit - score already confirmed SITE results",primary)
        backup=(ROOT/'.github/workflows/V234.yml').read_text(encoding='utf-8')
        self.assertIn("V275 immediately freeze qualifying V254",backup)
        research=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("workflow_dispatch:",research)
        self.assertNotIn("  schedule:",research.split("\\njobs:",1)[0])

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
        for forbidden in ('site_results/', 'scripts/boat_edge_v234_settle.py', 'git pull --rebase',
                          'git push --force', 'gh workflow run'):
            self.assertNotIn(forbidden,stage)
        self.assertIn("V254_FORMAL_GATE_MUST_STAY_CLOSED",
            (ROOT/'scripts/boat_edge_v254_third_tail.py').read_text())

    def test_only_primary_and_staggered_fallback_have_live_prediction_cron(self):
        import re
        folder=ROOT/'.github/workflows'
        self.assertFalse((folder/'V233.yml').exists())
        fallback=(folder/'V234.yml').read_text(encoding='utf-8')
        primary=(folder/'V235.yml').read_text(encoding='utf-8')
        shadow=WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('  schedule:',fallback)
        self.assertIn('  schedule:',primary)
        self.assertNotIn('  schedule:',shadow)
        self.assertNotIn('  workflow_run:',shadow)
        self.assertIn('workflow_dispatch:',shadow)
        def slots(source, prewarm=False):
            parts=re.findall(r"^\s+- cron: '([^']+)'$",source,re.MULTILINE)
            self.assertEqual(len(parts),2 if prewarm else 3)
            if prewarm:
                self.assertEqual(parts.count('20 23 * * *'),1)
                parts.remove('20 23 * * *')
            minutes=set()
            for spec in parts:
                minute,hour,day,month,weekday=spec.split()
                self.assertEqual((hour,day,month,weekday),('0-14,23','*','*','*'))
                parsed=set(map(int,minute.split(',')))
                self.assertFalse(minutes & parsed)
                minutes |= parsed
            return minutes
        main_slots=slots(primary,prewarm=True)
        backup_slots=slots(fallback)
        self.assertEqual(main_slots,set(range(2,60,5)))
        self.assertEqual(backup_slots,set(range(4,60,5)))
        self.assertFalse(main_slots & backup_slots)
        self.assertNotIn('scripts/boat_edge_v254_third_tail.py freeze',primary)
        self.assertIn('scripts/boat_edge_v254_third_tail.py freeze',fallback)
        for source in (primary,fallback):
            self.assertIn('git reset --hard origin/main',source)
            self.assertNotIn('git push --force',source)

    def test_first_race_835_jst_has_live_owner_without_research_cron(self):
        import re
        primary=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        research=WORKFLOW.read_text(encoding='utf-8')
        self.assertNotIn('  schedule:',research)
        slots=re.findall(r"^\s+- cron: '([^']+)'$",primary,re.MULTILINE)
        self.assertEqual(slots.count('20 23 * * *'),1)
        slots.remove('20 23 * * *')
        self.assertEqual(len(slots),1)
        minute,hour,*rest=slots[0].split()
        self.assertEqual((hour,rest),('0-14,23',['*','*','*']))
        minutes=set(map(int,minute.split(',')))
        self.assertEqual(minutes,set(range(2,60,5)))
        for minute in (22,27,32):
            self.assertIn(minute,minutes)
            self.assertGreaterEqual(35-minute,2)
        self.assertNotIn("V274 immediately freeze qualifying V254",primary)
        self.assertIn("scripts/boat_edge_v254_third_tail.py freeze",primary)
        source=(ROOT/'scripts/boat_edge_v232_pre_result_cohort.py').read_text(encoding='utf-8')
        guard=(ROOT/'scripts/boat_edge_v254_third_tail.py').read_text(encoding='utf-8')
        self.assertIn('120 <= (due-now).total_seconds() <= 900',source)
        self.assertIn('90<=(deadline-now).total_seconds()<=900',guard)
        self.assertIn('SOURCE_GIT_PROVENANCE_UNVERIFIED',guard)
        self.assertIn('V254_FORMAL_GATE_MUST_STAY_CLOSED',guard)

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
        },"formalFirst100":{"races":0}}),encoding="utf-8")
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
