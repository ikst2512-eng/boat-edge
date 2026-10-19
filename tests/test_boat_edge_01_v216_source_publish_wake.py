#!/usr/bin/env python3
"""Gate 1C: test V216 producer-completion wake without extra writers.

Workflow fixture assertions only: no racing, external requests or formal actions.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
V216=ROOT/'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml'
COLLECTOR=ROOT/'.github/workflows/auto-update.yml'
ODDS=ROOT/'.github/workflows/site-odds.yml'
V220=ROOT/'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml'

class V216CollectorWake(unittest.TestCase):
    def test_primary_schedule_and_same_owner_preserved(self):
        wf=V216.read_text(encoding='utf8')
        for expression in (
            "cron: '4,19,34,49 * * * *'",
            "cron: '9,24,39,54 * * * *'",
            "cron: '14,29,44,59 * * * *'",
            "group: boat-edge-v216-pre-result-source-diag",
            "cancel-in-progress: false",
            "PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_01_gate1c_source_ready.py",
            "git add -- data/site_ops_v220/gate1c_source_ready/*.json",
            "V216_PRE_RESULT_ATOMIC_FREEZE_GIT_PUBLISHED",
        ):
            self.assertIn(expression,wf)
        # Workflow-run adds no new scheduled workflow and cannot touch the
        # existing first-Git prediction writer.
        self.assertEqual(wf.count('  schedule:'),1)
        self.assertEqual(wf.count('  workflow_run:'),1)
        self.assertEqual(wf.count("      - 'BOAT EDGE 自動更新'"),1)
        self.assertEqual(wf.count("      - 'BOAT EDGE 3連単オッズ更新 V71'"),1)
        self.assertNotIn("      - 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'",wf)
        self.assertNotIn("git push --force",wf)

    def test_independent_cron_nudges_existing_v229_without_workflow_run_echo(self):
        # A skipped workflow still has a completion event. The V216 observer
        # must never become an upstream subscription of V229/V220/V235.
        wf=V216.read_text(encoding='utf8')
        job=wf.split('jobs:',1)[1]
        label='      - name: Recover source-ready first Git freeze during independent V216 cron'
        self.assertEqual(wf.count(label),1)
        start=wf.index(label)
        end=wf.index('      - name:',start+len(label))
        step=wf[start:end]
        self.assertIn("if: github.event_name == 'schedule'",step)
        self.assertIn('GH_TOKEN: ${{ github.token }}',step)
        self.assertIn('bash -n scripts/boat_edge_v01_first_freeze_nudge.sh',step)
        self.assertEqual(step.count('bash scripts/boat_edge_v01_first_freeze_nudge.sh'),1)
        self.assertNotIn('gh workflow run',step)
        # The observation is first-Git published before the nudge reads main;
        # its own paper selection and past-result settlement stay downstream.
        self.assertLess(wf.index("V216_PRE_RESULT_ATOMIC_FREEZE_GIT_PUBLISHED"),
                        start)
        self.assertLess(end,wf.index(
            '      - name: Continue approved-only daily 50000 yen paper selection BEFORE results'))
        for path in ('BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml','V235.yml',
                     'BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml'):
            downstream=(ROOT/'.github/workflows'/path).read_text(encoding='utf8')
            self.assertNotIn(
                "      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",
                downstream.split('jobs:',1)[0])
        nudge=(ROOT/'scripts/boat_edge_v01_first_freeze_nudge.sh').read_text(encoding='utf8')
        for safety in ('--recovery-plan','V229_ALREADY_ACTIVE','120 - $now',
                       'NOT_SOURCE_READY_OR_OUTSIDE_WINDOW',
                       'runs?per_page=100'):
            self.assertIn(safety,nudge)
        # The V216 schedule preserves two prospective 2-10m opportunities
        # for a 19:56 deadline (19:49 and 19:54); delivery remains best effort.
        self.assertIn("cron: '4,19,34,49 * * * *'",wf)
        self.assertIn("cron: '9,24,39,54 * * * *'",wf)

    def test_observer_is_only_downstream_of_source_producers(self):
        v216=V216.read_text(encoding='utf8')
        v235=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf8')
        event=v216.split('jobs:',1)[0]
        job=v216.split('  deadline-audit:',1)[1].split('    runs-on:',1)[0]
        self.assertNotIn("      - 'BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring'", event)
        self.assertNotIn("      - 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'", event)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository",job)
        self.assertNotIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",v235.split('jobs:',1)[0])
        self.assertNotIn("github.event.workflow_run.name == 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",v235.split('  freeze-then-score-site-only:',1)[1].split('    runs-on:',1)[0])

    def test_privileged_event_accepts_verified_main_source_only(self):
        wf=V216.read_text(encoding='utf8')
        for part in (
            "workflows:",
            "types: [completed]",
            "branches: [main]",
            "github.ref == 'refs/heads/main'",
            "github.event_name != 'workflow_run'",
            "github.event.workflow_run.conclusion == 'success'",
            "github.event.workflow_run.head_branch == 'main'",
            "github.event.workflow_run.head_repository.full_name == github.repository",
        ):
            self.assertIn(part,wf)
        # A V216 completed run is not itself a collector event. Any V220
        # recovery stays separately source-ready and 15m collector-cooled.
        collector=COLLECTOR.read_text(encoding='utf8')
        self.assertIn("      - 'BOAT EDGE 3連単オッズ更新 V71'",collector)
        self.assertNotIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",collector)
        odds=ODDS.read_text(encoding='utf8')
        # V71 must not listen to V216: a skipped upstream is still a
        # completed workflow_run and causes recursive event fanout.
        self.assertNotIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",odds)
        # Both collector and odds keep their strict source-publishing guards.
        self.assertIn("V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED",odds)
        self.assertIn("V270_PRE_RESULT_SAFE_PUSH_PASS",collector)
        observer=V220.read_text(encoding='utf8')
        self.assertIn("V220_RECOVERY_COOLDOWN_OR_SCHEDULE_ACTIVE",observer)
        self.assertIn("cooldown=900",observer)

    def test_collector_is_not_woken_by_its_own_downstream_first_git_freeze(self):
        collector=COLLECTOR.read_text(encoding='utf8')
        v229=(ROOT/'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text(encoding='utf8')
        event=collector.split('on:',1)[1].split('permissions:',1)[0]
        self.assertIn('cron: "*/5 * * * *"',event)
        self.assertIn("      - 'BOAT EDGE 3連単オッズ更新 V71'",event)
        self.assertNotIn("      - 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'",event)
        self.assertIn("      - 'BOAT EDGE 自動更新'",v229.split('jobs:',1)[0])
        self.assertIn('group: boat-edge-current-v17',collector)
        self.assertNotIn('git push --force',collector)

    def test_formal_guards_and_first_git_evidence_owner_unmodified(self):
        wf=V216.read_text(encoding='utf8')
        for marker in (
            "V286_V265_SOURCE_PIN_AND_FORMAL_LOCK_PASS_NO_REINSTALL",
            "V216_FORMAL_RESULT_UNSEEN_GUARD_BLOCKED",
            "V216_FORMAL_FIRST100_GUARD_BLOCKED",
            "V216_UNEXPECTED_FROZEN_EVIDENCE_FILE_",
            "git fetch --no-tags origin main",
            "git reset --hard origin/main",
            "git clean -fd -- data/site_ops_v220/gate1c_source_ready/",
        ):
            self.assertIn(marker,wf)
        self.assertIn("data/site_paper_sim/readiness_history_v215/",wf)

    def test_v71_off_peak_cron_preserves_twelve_five_minute_wakes_without_feedback(self):
        odds=ODDS.read_text(encoding='utf8')
        event=odds.split('on:',1)[1].split('permissions:',1)[0]
        self.assertEqual(event.count('  schedule:'),1)
        self.assertNotIn('  workflow_run:',event)
        self.assertIn('  workflow_dispatch:',event)
        lines=[line.strip() for line in event.splitlines() if line.strip().startswith('- cron:')]
        self.assertEqual(len(lines),1)
        fields=lines[0].split('"')[1].split()
        self.assertEqual(fields[1:],['*','*','*','*'])
        slots=[int(n) for n in fields[0].split(',')]
        self.assertEqual(sorted(slots),list(range(2,60,5)))
        self.assertEqual(len(set(slots)),12)
        self.assertIn('group: boat-edge-site-odds-v71',odds)
        self.assertIn('V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED',odds)

    def test_pages_publishes_after_v229_without_first_git_feedback(self):
        pages=(ROOT/'.github/workflows/pages-controlled-publish.yml').read_text(encoding='utf8')
        v229=(ROOT/'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text(encoding='utf8')
        event=v229.split('jobs:',1)[0]
        pages_event=pages.split('jobs:',1)[0]
        self.assertNotIn("      - 'BOAT EDGE 01 - Controlled GitHub Pages Publish'",event)
        self.assertIn("      - 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'",pages_event)
        self.assertIn('cron: \'*/5 23,0-14 * * *\'',pages_event)
        self.assertIn('V229_TRACKED_SOURCE_PINS_PASS',v229)

    def test_v216_completion_must_not_fan_out_into_freeze_or_recovery(self):
        # Workflow-level exclusion is essential: skipped jobs still complete.
        v229=(ROOT/'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text(encoding='utf8')
        v235=(ROOT/'.github/workflows/V235.yml').read_text(encoding='utf8')
        v220=V220.read_text(encoding='utf8')
        v216=V216.read_text(encoding='utf8')
        for text in (v229,v235,v220):
            header=text.split('jobs:',1)[0]
            job=text.split('jobs:',1)[1].split('    runs-on:',1)[0]
            self.assertNotIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",header)
            self.assertNotIn("github.event.workflow_run.name == 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",job)
            self.assertIn('  schedule:',header)
            self.assertIn('  workflow_dispatch:',header)
        for text in (v229,v235):
            self.assertIn("      - 'BOAT EDGE 自動更新'",text.split('jobs:',1)[0])
            self.assertIn("      - 'BOAT EDGE 3連単オッズ更新 V71'",text.split('jobs:',1)[0])
            self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository",text)
        self.assertIn("      - 'BOAT EDGE V235 - Stable Autonomous Prediction Freeze and Verified Scoring'",v229)
        self.assertIn('V220_V216_SELF_WAKE_NO_FEEDBACK_DISPATCH',v220)
        self.assertIn('BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml) cooldown=900',v220)
        self.assertIn('V229_TRACKED_SOURCE_PINS_PASS',v229)
        self.assertIn('python3 scripts/boat_edge_v229_atomic_freeze.py',v229)
        self.assertIn("cron: '4,19,34,49 * * * *'",v216)
        self.assertNotIn('git push --force',v229)


if __name__=='__main__':
    unittest.main()
