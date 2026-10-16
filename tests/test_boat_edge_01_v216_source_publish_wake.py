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
        self.assertNotIn("BOAT EDGE V229 - Atomic",wf)
        self.assertNotIn("git push --force",wf)

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
        self.assertNotIn("      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",odds)
        # All observation inputs remain pre-result, the collector and odds
        # producers never recursively listen to this V216 observer.
        self.assertIn("V71_SOURCE_TIMESTAMP_GUARDED_ODDS_PUBLISHED",odds)
        self.assertIn("V270_PRE_RESULT_SAFE_PUSH_PASS",collector)
        observer=V220.read_text(encoding='utf8')
        self.assertIn("V220_RECOVERY_COOLDOWN_OR_SCHEDULE_ACTIVE",observer)
        self.assertIn("cooldown=900",observer)

    def test_existing_v229_schedule_is_free_source_collector_fallback_only(self):
        # Existing V229 scheduled run is a heartbeat, not source eligibility.
        # A V229 triggered by the collector must NEVER wake it again.
        collector = COLLECTOR.read_text(encoding='utf8')
        v229 = (ROOT/'.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml').read_text(encoding='utf8')
        event = collector.split('on:\\n', 1)[1].split('\\npermissions:', 1)[0]
        job = collector.split('  update:\\n', 1)[1].split('    runs-on:', 1)[0]
        self.assertEqual(event.count('  schedule:'), 1)
        self.assertEqual(event.count('  workflow_run:'), 1)
        self.assertIn('cron: "*/5 * * * *"', event)
        self.assertIn("      - 'BOAT EDGE 3連単オッズ更新 V71'", event)
        self.assertIn("      - 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'", event)
        self.assertIn("github.event.workflow_run.name == 'BOAT EDGE 3連単オッズ更新 V71'", job)
        self.assertIn("github.event.workflow_run.name == 'BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit'", job)
        self.assertIn("github.event.workflow_run.event == 'schedule'", job)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", job)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", job)
        self.assertIn('group: boat-edge-current-v17', collector)
        self.assertIn('cancel-in-progress: false', collector)
        self.assertIn("      - 'BOAT EDGE 自動更新'", v229)
        self.assertIn("cron: '6,11,16,21,26,31,36,41,46,51,56 0-14,23 * * *'", v229)
        self.assertNotIn('BOAT EDGE V229 - Atomic Site Freeze and Pre-result Audit',
                         (ROOT/'.github/workflows/site-odds.yml').read_text(encoding='utf8'))
        self.assertNotIn('git push --force', collector)

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

if __name__=='__main__':
    unittest.main()
