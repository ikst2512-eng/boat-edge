import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from boat_edge_v232_git_gap_readonly import classify
class TestGap(unittest.TestCase):
    def test_empty_safe(self):
        with tempfile.TemporaryDirectory() as d:
            r=classify(d)
            self.assertEqual(r['unscored_v232_checked'],0)
            self.assertTrue(r['no_result_read'])
