"""V307 regression: PR gate must be read-only and retain distinct UI and formal checks."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
YAML=ROOT/'.github/workflows/v307-ui-integration-gate.yml'

class UIWorkflowContract(unittest.TestCase):
    def test_ui_gate_is_readonly_no_scheduled_data_writer(self):
        text=YAML.read_text(encoding='utf8')
        header=text.split('\npermissions:',1)[0]
        self.assertIn('  pull_request:',header)
        self.assertIn('  push:',header)
        for forbidden in ('  schedule:','  workflow_run:','  workflow_dispatch:'):
            self.assertNotIn(forbidden,header)
        self.assertIn('permissions:\n  contents: read',text)
        self.assertNotIn('contents: write',text)
        self.assertIn('persist-credentials: false',text)
        for forbidden in ('git push ', 'gh workflow run', 'RESULT_UNLOCK_TOKEN=', 'git commit ', '/race/result', '/race/pay', 'site_results/', 'data/formal_predictions/'):
            self.assertNotIn(forbidden,text)
        self.assertIn('cancel-in-progress: true',text)
    def test_all_site_candidates_and_formal_gate_are_explicit(self):
        text=YAML.read_text(encoding='utf8')
        for p in ('tests/test_boat_edge_v248_ui.cjs', 'tests/test_boat_edge_v244_site.cjs',
                  'tests/test_boat_edge_v247_ui.cjs','tests/test_boat_edge_v297_nav.cjs',
                  'tests/test_boat_edge_v298_matrix.cjs','tests/test_boat_edge_v299_head_selector.cjs',
                  'tests/test_boat_edge_v304_topk.cjs','tests/test_boat_edge_v305_evidence.cjs',
                  'tests/test_boat_edge_v306_race_switch.cjs'):
            self.assertIn(p,text)
        self.assertIn('CANDIDATE_TEST_NOT_YET_ON_BRANCH',text)
        self.assertIn('V307_FORMAL_FRESH_RESULT_UNSEEN_LOCK_PASS',text)
        self.assertIn('x["formalFirst100"]["races"]==0',text)
        self.assertIn('git diff --exit-code',text)

if __name__=='__main__':
    unittest.main()
