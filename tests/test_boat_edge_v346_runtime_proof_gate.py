import unittest
from scripts.boat_edge_v345_writer_trigger_evidence import audit as v345_audit
from scripts.boat_edge_v346_runtime_proof_gate import audit


class V346RuntimeGate(unittest.TestCase):
    def test_static_candidates_cannot_become_verified_runtime_duplicates(self):
        result = audit()
        self.assertEqual(result, audit())
        self.assertEqual(result["static_candidate_count"], v345_audit()["candidate_count"])
        self.assertEqual(result["verified_duplicate_writers"], 0)
        self.assertEqual(result["runtime_evidence_coverage"], 0)
        self.assertTrue(result["runtime_proof_missing"])
        self.assertFalse(result["workflow_disable_authorized"])
        self.assertTrue(all(not x["disable_authorized"] and not x["runtime_runs_inspected"]
                            for x in result["candidates"]))


if __name__ == "__main__":
    unittest.main()
