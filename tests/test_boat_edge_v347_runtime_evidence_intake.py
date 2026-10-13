import unittest
from scripts.boat_edge_v346_runtime_proof_gate import audit as v346_audit
from scripts.boat_edge_v347_runtime_evidence_intake import audit, validate_records


class V347EvidenceIntake(unittest.TestCase):
    def test_empty_evidence_is_not_proof_of_no_collisions(self):
        report = audit()
        self.assertEqual(report["static_candidate_count"], v346_audit()["static_candidate_count"])
        self.assertEqual(report["valid_run_records"], 0)
        self.assertTrue(report["missing_run_records_are_not_zero_collisions"])
        self.assertFalse(report["workflow_disable_authorized"])

    def test_reject_incomplete_or_invalid_run_records(self):
        result = validate_records([{}, {"workflow": "a.yml", "run_id": -1,
            "started_at": "s", "completed_at": "e", "commit_sha": "abc", "changed_paths": ["x"]}])
        self.assertEqual(len(result["accepted"]), 0)
        self.assertEqual(len(result["rejected"]), 2)

    def test_complete_record_is_still_not_a_duplicate_verdict(self):
        row = {"workflow": "a.yml", "run_id": 123, "started_at": "s",
               "completed_at": "e", "commit_sha": "abc", "changed_paths": ["data/a"]}
        self.assertEqual(len(validate_records([row])["accepted"]), 1)
        report = audit([row])
        self.assertEqual(report["verified_duplicate_writers"], 0)
        self.assertFalse(report["workflow_disable_authorized"])


if __name__ == "__main__":
    unittest.main()
