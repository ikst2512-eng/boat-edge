import unittest
from probe_health import assess
class HealthTests(unittest.TestCase):
 def test_no_races_not_success(self):
  self.assertEqual(assess({"status":"ok","due":0,"captured":0},{"manifests":0,"eligible_10":0,"invalid":0,"title_sources":1})["state"],"NO_RACES_DUE")
 def test_invalid_title_when_no_due_fails(self):
  x=assess({"status":"ok","due":0,"captured":0},{"manifests":0,"invalid":0,"invalid_title_sources":1,"title_sources":0})
  self.assertEqual(x["state"],"INVALID_CAPTURE_EVIDENCE")
 def test_missing_title_when_no_due_fails(self):
  x=assess({"status":"ok","due":0,"captured":0},{"manifests":0,"invalid":0,"title_sources":0})
  self.assertEqual(x["state"],"MISSING_DEADLINE_SOURCE_EVIDENCE")
 def test_valid_evidence_distinguished(self):
  x=assess({"status":"ok","due":2,"captured":2,"failed":0},{"manifests":2,"eligible_10":2,"invalid":0,"title_sources":1,"invalid_title_sources":0})
  self.assertEqual(x["proven_captures"],2)
  self.assertIn("NOT_EXTERNALLY_ATTESTED",x["state"])
 def test_missing_evidence(self):
  self.assertEqual(assess({"status":"ok","due":2,"captured":2},{"manifests":0,"eligible_10":0,"invalid":0,"title_sources":1})["state"],"MISSING_CAPTURE_EVIDENCE")
 def test_incomplete_cutoff_coverage_not_success(self):
  x=assess({"status":"ok","due":2,"captured":2,"failed":0},{"manifests":2,"eligible_10":1,"invalid":0,"title_sources":1})
  self.assertEqual(x["state"],"INCOMPLETE_CUTOFF_COVERAGE")
  self.assertEqual(x["proven_captures"],1)
 def test_incomplete_capture_not_success(self):
  x=assess({"status":"ok","due":3,"captured":2,"failed":0},{"manifests":2,"eligible_10":2,"invalid":0,"title_sources":1})
  self.assertEqual(x["state"],"PARTIAL_FAILURE")
  self.assertEqual(x["proven_captures"],0)
 def test_failure(self):
  self.assertEqual(assess({"status":"collector_failed"},{"manifests":0})["state"],"RUN_FAILED")
if __name__=="__main__":unittest.main()
