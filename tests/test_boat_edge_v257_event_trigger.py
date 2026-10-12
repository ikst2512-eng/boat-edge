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
        # V235 freezes new third-tail candidates synchronously BEFORE its
        # result-only stage. Enqueuing V254 again after V235 completes is
        # redundant and can miss the future window. Keep V232 event fallback.
        self.assertIn("'BOAT EDGE V232 - Independent Pre-Result Accuracy Cohort'",workflow)
        self.assertNotIn("'BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring'",workflow)
        self.assertIn("cron: '3,8,13,18,23,28,33,38,43,48,53,58 0-14,23 * * *'",workflow)
        self.assertIn("V274 immediately freeze qualifying V254",(ROOT/'.github/workflows/V235.yml').read_text())
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
        self.assertIn("      - name: V274 immediately freeze qualifying V254",primary)
        # Collectors may read official PRE_RESULT only; the downstream future
        # research freeze remains strictly source/Git/deadline guarded.
        self.assertIn("git reset --hard origin/main",primary)
        self.assertIn("scripts/boat_edge_v254_third_tail.py freeze",primary)
        collector=(ROOT/'.github/workflows/auto-update.yml').read_text(encoding='utf-8')
        self.assertIn("name: BOAT EDGE 自動更新",collector)
        self.assertIn("  schedule:",collector)
        self.assertIn("V270_PRE_RESULT_SAFE_PUSH_PASS",collector)
        self.assertNotIn("git push --force",primary)
        self.assertNotIn("git push --force",collector)

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
        for forbidden in ('site_results/', 'scripts/boat_edge_v234_settle.py', 'git pull --rebase',
                          'git push --force', 'gh workflow run'):
            self.assertNotIn(forbidden,stage)
        self.assertIn("V254_FORMAL_GATE_MUST_STAY_CLOSED",
            (ROOT/'scripts/boat_edge_v254_third_tail.py').read_text())

    def test_v287_only_primary_and_staggered_safe_fallback_have_live_cron(self):
        import re
        folder=ROOT/'.github/workflows'
        old=(folder/'V233.yml').read_text(encoding='utf-8')
        fallback=(folder/'V234.yml').read_text(encoding='utf-8')
        primary=(folder/'V235.yml').read_text(encoding='utf-8')
        shadow=WORKFLOW.read_text(encoding='utf-8')
        # V233 still supports explicit manual recovery, but its
        # unguarded legacy Git rebase is never launched on a schedule.
        self.assertIn('workflow_dispatch:',old)
        self.assertNotIn('  schedule:',old)
        self.assertIn('  schedule:',fallback)
        self.assertIn('  schedule:',primary)
        self.assertIn('  schedule:',shadow)
        def minute_slot(src):
            slots=[line.split("cron: '",1)[1].split("'",1)[0]
                   for line in src.splitlines() if "cron: '" in line]
            self.assertEqual(len(slots),1,
                'Each active owner must have one verified 5-minute schedule')
            minute,hour,dom,month,weekday=slots[0].split()
            self.assertEqual((hour,dom,month,weekday),
                ('0-14,23','*','*','*'),
                '23 UTC must cover Japanese 08:00-08:59')
            return set(map(int,minute.split(',')))
        primary_slots=minute_slot(primary)
        tail_slots=minute_slot(shadow)
        backup_slots=minute_slot(fallback)
        self.assertEqual(primary_slots,set(range(2,60,5)))
        self.assertEqual(tail_slots,set(range(3,60,5)))
        self.assertEqual(backup_slots,set(range(4,60,5)))
        self.assertFalse(primary_slots & backup_slots)
        self.assertFalse(tail_slots & backup_slots)
        # Both active source owners still prohibit retrospective
        # enrichment and freeze independently before any result score.
        self.assertIn('V274 immediately freeze qualifying V254',primary)
        self.assertIn('V275 immediately freeze qualifying V254',fallback)
        self.assertIn('V234_CONCURRENT_GIT_UPDATE_ABANDON_LOCAL_PREDICTIONS',fallback)
        self.assertIn('V234_CONCURRENT_GIT_UPDATE_ABANDON_LOCAL_PREDICTIONS',primary)
        self.assertNotIn('git pull --rebase origin main',fallback)
        self.assertNotIn('git pull --rebase origin main',primary)

    def test_v286_first_race_835_jst_has_prospective_owner_and_shadow_slots(self):
        """Guard the UTC-23h schedules covering Japan's first saved 08:35 race.

        Scheduled slots are opportunities, not proof of successfully published
        exhibition/odds, and never authorize using results or backfilled picks.
        """
        import re
        primary=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf-8')
        research=WORKFLOW.read_text(encoding='utf-8')
        def cron_slots(workflow):
            match=re.search(r"cron: '(\d+(?:,\d+)*) ([^ ]+) \* \* \*'",workflow)
            self.assertIsNotNone(match,'Expected real scheduled UTC slots')
            self.assertEqual(match.group(2),'0-14,23',
                '23 UTC must cover Japanese 08:00-08:59')
            return set(map(int,match.group(1).split(',')))
        parent=cron_slots(primary)
        tail=cron_slots(research)
        self.assertEqual(parent,set(range(2,60,5)))
        self.assertEqual(tail,set(range(3,60,5)))
        # 08:35 JST == 23:35 UTC on the previous calendar day.
        # Source capture must remain >120s before deadline; independent shadow
        # may freeze only while original Git attestation is still pre-result.
        for minute in (22,27,32):
            self.assertIn(minute,parent)
            self.assertIn(minute+1,tail)
            self.assertGreaterEqual(35-(minute+1),2)
        self.assertIn("V274 immediately freeze qualifying V254",primary)
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
