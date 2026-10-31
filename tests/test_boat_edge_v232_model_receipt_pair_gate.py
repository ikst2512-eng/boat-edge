import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_v232_model_receipt_pair_gate import verify

class PairGateTests(unittest.TestCase):
    def test_missing_pair_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            result=verify(Path(t),"20261027-21-01")
            self.assertFalse(result["eligible"])
            self.assertEqual(result["reason"],"PAIR_FILE_MISSING")

if __name__=="__main__":
    unittest.main()
