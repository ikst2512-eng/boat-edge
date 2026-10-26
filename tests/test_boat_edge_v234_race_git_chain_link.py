import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_v234_race_git_chain_link import audit, classify


class RaceGitChainLinkTests(unittest.TestCase):
    def test_no_snapshot_does_not_establish_eligibility(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            row=classify(root,"20261027-21-01")
            self.assertEqual(row["status"],"SNAPSHOT_FILE_MISSING")
            report=audit(root)
            self.assertEqual(report["sample_size"],0)
            self.assertFalse(report["prospective_eligibility_established"])

    def test_invalid_key(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(classify(Path(t),"../no")["status"],"INVALID_KEY")
