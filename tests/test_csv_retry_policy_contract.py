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
  self.assertIn("for role in csv_priority:",block)
  self.assertIn("url=SOURCES[role]",block)
  self.assertIn('csv_priority=("original_exhibition","stt","tkz","sui","race_cards")',block)
  self.assertIn("assert set(csv_priority)==set(SOURCES)",block)
  self.assertIn("if (pending_codes and (err or source_is_sparse(role,rows) or missing_pending_codes(rows) or preview_source_is_incomplete(role,rows))):",block)
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
 def test_retry_cannot_replace_with_incomplete_values(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("no_regression=all(",text)
  self.assertIn("not complete_row(role,prior_by[code]) or complete_row(role,next_by[code])",text)
  self.assertIn("preview_source_is_incomplete(role,rows)",text)
  self.assertIn("prior_codes <= next_codes",text)
 def test_partial_race_can_improve_independently(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("newly_complete=sum(",text)
  self.assertIn("len(new_rows)>len(rows) or newly_complete>0",text)
  self.assertIn("no_regression=all(",text)
 def test_partial_csv_rows_trigger_retry(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("pending_codes=set()",text)
  self.assertIn("0 <= (cutoff-check_time).total_seconds()/60 <= 45",text)
  self.assertIn('"near_deadline_targets":len(pending_codes)',text)
  self.assertIn("if not source_write_allowed(DATA,race_key,deadline,check_time):",text)
  self.assertIn("def missing_pending_codes(rows):",text)
  self.assertIn("or missing_pending_codes(rows) or preview_source_is_incomplete(role,rows))):",text)
  self.assertIn('"predeadline_race_rows_missing":len(missing_pending_codes(rows))',text)
 def test_incomplete_six_boat_previews_trigger_retry(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("def preview_source_is_incomplete(role,rows):",text)
  self.assertIn('role=="stt"',text)
  self.assertIn('role=="tkz"',text)
  self.assertIn('role=="original_exhibition"',text)
  self.assertIn('"pending_value_incomplete":preview_source_is_incomplete(role,rows)',text)
 def test_publication_wait_separated_from_core7_failure(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn('"source_availability"',text)
  self.assertIn('"NOT_PUBLISHED" if info["error"]=="not_published"',text)
  self.assertIn('"WAIT_PREVIEW_CSV_PUBLICATION" if previews_unpublished',text)
  self.assertIn('"WAIT_CORE7_100"',text)
  self.assertIn('preview_roles=("stt","tkz","sui","original_exhibition")',text)
 def test_official_csv_split_is_diagnostic_only(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn('"official_ready_csv_missing"',text)
  self.assertIn('"does_not_grant_core7_or_formal_readiness":True',text)
  self.assertIn('official.get("status")=="ok"',text)
 def test_deadline_and_formal_guards_remain(self):
  text=WORKFLOW.read_text(encoding="utf-8")
  self.assertIn("source_write_allowed(DATA,race_key,clock,datetime.now(JST))",text)
  self.assertIn('"formal_prediction_ready":False',text)
  self.assertIn('"results_seen":False',text)
if __name__=="__main__":unittest.main()
