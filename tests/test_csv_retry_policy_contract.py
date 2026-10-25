"""Ensure pre-result CSV recovery stays bounded and preserves evidence."""
from pathlib import Path
import unittest

WORKFLOW=Path(".github/workflows/auto-update.yml")
class CsvRetryPolicy(unittest.TestCase):
 def test_all_source_roles_use_common_retry(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  start=text.index("          def source_is_sparse(role,rows):")
  end=text.index("          def idx(role):",start)
  block=text[start:end]
  self.assertIn("for role,url in SOURCES.items():",block)
  self.assertIn("if err or source_is_sparse(role,rows):",block)
  self.assertIn("for delay in (2,5):",block)
  self.assertIn("retry_count",block)
  self.assertNotIn('if role=="original_exhibition" and (err',block)
 def test_nonempty_source_not_replaced_with_failed_response(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  start=text.index("          def source_is_sparse(role,rows):")
  end=text.index("          def idx(role):",start)
  block=text[start:end]
  self.assertIn("if new_rows and (not rows or",block)
  self.assertIn("len(new_rows)>len(rows)",block)
 def test_deadline_and_formal_guards_remain(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("source_write_allowed(DATA,race_key,clock,datetime.now(JST))",text)
  self.assertIn('"formal_prediction_ready":False',text)
  self.assertIn('"results_seen":False',text)
if __name__=="__main__":unittest.main()
