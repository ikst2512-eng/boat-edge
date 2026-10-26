import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from boat_edge_v232_v234_readonly_triage import classify
class TestTriage(unittest.TestCase):
    def test_empty_is_safe(self):
        with tempfile.TemporaryDirectory() as d:
            x=classify(d)
            self.assertEqual(x['checked'],0)
            self.assertFalse(x['results_read'])
    def test_absence_not_misclassified_as_settlement_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data/site_autopilot/v229_evidence/20261011-01-04.json'
            p.parent.mkdir(parents=True)
            p.write_text('{}')
            x=classify(d)
            self.assertEqual(x['reason_counts']['NO_V232_COHORT_NOT_A_SETTLEMENT_FAILURE'],1)
            self.assertFalse(x['historical_noncreation_cause_proven'])
