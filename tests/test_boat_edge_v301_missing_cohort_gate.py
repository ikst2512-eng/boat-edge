"""V301 must not misreport missing scored data as zero audited races."""
import tempfile
import unittest
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from boat_edge_v301_paired_evidence import audit, EvidenceError


class MissingCohortGate(unittest.TestCase):
    def test_missing_scored_directory_is_evidence_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"data").mkdir()
            (root/"data/formal_status.json").write_text(json.dumps({
                "formalFirst100":{"races":0},
                "guards":{"results_seen":False,"unlock":False,
                          "scoring":False,"RESULT_UNLOCK_TOKEN":None}
            }),encoding="utf-8")
            with self.assertRaisesRegex(
                EvidenceError,"SCORED_COHORT_DIRECTORY_MISSING_v236"
            ):
                audit(root)
    def test_existing_empty_directory_is_not_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"data/site_autopilot/v236_scored").mkdir(parents=True)
            (root/"data/formal_status.json").write_text(json.dumps({
                "formalFirst100":{"races":0},
                "guards":{"results_seen":False,"unlock":False,
                          "scoring":False,"RESULT_UNLOCK_TOKEN":None}
            }),encoding="utf-8")
            with self.assertRaisesRegex(
                EvidenceError,"SCORED_COHORT_DIRECTORY_MISSING_v240"
            ):
                audit(root)


if __name__=="__main__":
    unittest.main()
