"""V240 completed owner-approved UI queue has no unattended daily runner.

Read-only source test. Preserve intentional paid manual action and PR safety.
"""
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/'.github/workflows/v240-autodev.yml'
QUEUE=ROOT/'BOAT_EDGE_AUTODEV_TASKS.md'

class CompleteUIQueue(unittest.TestCase):
    def test_owner_approved_queue_is_exhausted_and_unattended_cron_removed(self):
        q=QUEUE.read_text(encoding='utf-8')
        tasks=re.findall(r'^- \[([ x])\] (A\d+)\s*\|',q,re.M)
        self.assertEqual(len(tasks),37)
        self.assertEqual(tasks[0][1],'A01')
        self.assertEqual(tasks[-1][1],'A37')
        self.assertTrue(all(state=='x' for state,_ in tasks))
        w=WF.read_text(encoding='utf-8')
        events=w.split('\non:\n',1)[1].split('\npermissions:',1)[0]
        self.assertNotIn('  schedule:',events)
        self.assertNotIn('    - cron:',events)
        self.assertIn('  workflow_dispatch:',events)
        self.assertIn('  pull_request:',events)
        self.assertIn('  push:',events)

    def test_manual_paid_gate_kept_but_auto_main_writes_still_forbidden(self):
        w=WF.read_text(encoding='utf-8')
        for token in (
            "inputs.run_paid_codex == true",
            "secrets.OPENAI_API_KEY != ''",
            "if ! python3 scripts/boat_edge_v240_guard.py --pending",
            'steps.gate.outputs.can_run',
            "git push origin \"HEAD:refs/heads/$branch\"",
            "gh pr create --repo",
            "--draft",
            "tests/test_boat_edge_v240_pr_publish.py",
            "FORMAL_GATE_NOT_CLOSED",
        ):
            self.assertIn(token,w)
        self.assertNotIn('git push origin HEAD:main',w)


if __name__=='__main__':
    unittest.main()
