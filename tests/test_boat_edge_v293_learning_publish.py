"""V293: offline source-only V70 write safety. No result, payout, or network access."""
import ast
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/site-learning.yml'

class V293LearningPublish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=WORKFLOW.read_text(encoding='utf-8')
        block=cls.source.split("          python - <<'PY'\n",1)[1].split("\n          PY\n",1)[0]
        cls.worker='\n'.join(line[10:] if line.startswith('          ') else line
                             for line in block.splitlines())

    def test_embedded_learning_python_parses(self):
        ast.parse(self.worker)
        self.assertIn("results=Path(\"data/site_results\")",self.worker)
        self.assertIn('def safe_pre_result(d):',self.worker)
        self.assertNotIn('race/result?',self.worker)
        self.assertNotIn('api/v1',self.worker)

    def test_stable_evaluation_and_summary_without_clock_only_changes(self):
        worker=self.worker
        self.assertIn("prior=load(target)",worker)
        self.assertIn('all(k=="evaluated_at" or prior[k]==row[k] for k in row)',worker)
        self.assertIn('row=prior',worker)
        self.assertIn('all(k=="updated_at" or prior[k]==summary[k] for k in summary)',worker)
        self.assertIn('summary=prior',worker)
        self.assertIn('summary_path.write_text',worker)
        self.assertLess(worker.index('summary=prior'),worker.index('summary_path.write_text'))
        self.assertIn('"results_seen_in_prediction":False',worker)

    def test_retry_is_bounded_and_raises_on_true_conflict(self):
        source=self.source
        self.assertIn('fetch-depth: 0',source)
        self.assertIn('for n in 1 2 3 4 5 6; do',source)
        self.assertIn('git fetch --no-tags origin main',source)
        self.assertIn('git rebase origin/main',source)
        self.assertIn('git rebase --abort || true',source)
        self.assertIn('git push origin HEAD:main',source)
        self.assertIn('V293_LEARNING_SOURCE_CONFLICT_SKIP_UNSAFE_REBASE',source)
        self.assertIn('V293_LEARNING_EVIDENCE_UNCHANGED_NO_PAGES_COMMIT',source)
        self.assertNotIn('git push --force',source)

    def test_allowed_files_only_and_formal_gate(self):
        source=self.source
        self.assertIn('V293_FORBIDDEN_LEARNING_STAGE_',source)
        self.assertIn('V293_SITE_ONLY_MEASURED_LEARNING_STAGED',source)
        self.assertIn('data/site_learning/evaluations/',source)
        self.assertIn('git diff --cached --check',source)
        self.assertIn("guards.get('RESULT_UNLOCK_TOKEN') is None",source)
        formal=json.loads((ROOT/'data/formal_status.json').read_text(encoding='utf-8'))
        guard=formal.get('guards',{})
        self.assertTrue(all(guard.get(k) is False for k in ('results_seen','unlock','scoring')))
        self.assertIsNone(guard.get('RESULT_UNLOCK_TOKEN'))
        self.assertEqual(formal.get('formalFirst100',{}).get('races'),0)

if __name__=='__main__':
    unittest.main()
