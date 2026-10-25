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
  self.assertIn("if (pending_codes and (err or source_is_sparse(role,rows) or missing_pending_codes(rows))):",block)
  self.assertIn("for delay in (2,5):",block)
  self.assertIn("retry_count",block)
  self.assertNotIn('if role=="original_exhibition" and (err',block)
 def test_nonempty_source_not_replaced_with_failed_response(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  start=text.index("          def source_is_sparse(role,rows):")
  end=text.index("          def idx(role):",start)
  block=text[start:end]
  self.assertIn("if new_rows and not new_err:",block)
  self.assertIn("prior_codes <= next_codes",block)
 def test_partial_csv_rows_trigger_retry(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("pending_codes=set()",text)
  self.assertIn("0 <= (cutoff-check_time).total_seconds()/60 <= 45",text)
  self.assertIn('"near_deadline_targets":len(pending_codes)',text)
  self.assertIn("if not source_write_allowed(DATA,race_key,deadline,check_time):",text)
  self.assertIn("def missing_pending_codes(rows):",text)
  self.assertIn("or missing_pending_codes(rows):",text)
  self.assertIn('"predeadline_race_rows_missing":len(missing_pending_codes(rows))',text)
 def test_publication_wait_separated_from_core7_failure(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn('"source_availability"',text)
  self.assertIn('"NOT_PUBLISHED" if info["error"]=="not_published"',text)
  self.assertIn('"WAIT_FIVE_SOURCE_PUBLICATION" if all_unpublished',text)
  self.assertIn('"WAIT_CORE7_100"',text)
 def test_deadline_and_formal_guards_remain(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("source_write_allowed(DATA,race_key,clock,datetime.now(JST))",text)
  self.assertIn('"formal_prediction_ready":False',text)
  self.assertIn('"results_seen":False',text)
if __name__=="__main__":unittest.main()
