import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from boat_edge_v232_missing_static_diagnosis import classify
class TestDiagnosis(unittest.TestCase):
    def test_missing_snapshot_not_promoted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data/site_autopilot/v229_evidence/20261011-01-04.json'
            p.parent.mkdir(parents=True)
            p.write_text('{}')
            r=classify(d)
            self.assertEqual(r['reasons']['SNAPSHOT_UNREADABLE'],1)
            self.assertFalse(r['historical_v232_eligibility_proven'])
            self.assertFalse(r['result_data_read'])
