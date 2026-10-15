#!/usr/bin/env python3
"""Gate 1C: test V216 producer-completion wake without extra writers.

Workflow fixture assertions only: no racing, external requests or formal actions.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
V216=ROOT/'.github/workflows/BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml'
COLLECTOR=ROOT/'.github/workflows/auto-update.yml'
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
        observer=V220.read_text(encoding='utf8')
        self.assertIn("V220_RECOVERY_COOLDOWN_OR_SCHEDULE_ACTIVE",observer)
        self.assertIn("cooldown=900",observer)

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
