import unittest
from scripts.boat_edge_v344_exact_writer_triage import triage
from scripts.boat_edge_v345_writer_trigger_evidence import audit


class V345Evidence(unittest.TestCase):
    def test_candidate_preservation_and_conservative_status(self):
        result = audit()
        self.assertEqual(result, audit())
        self.assertEqual(result["candidate_count"], triage()["exact_witness_count"])
        self.assertEqual(result["verified_duplicate_writers"], 0)
        self.assertTrue(result["no_disable_authorized"])
        self.assertTrue(all(not x["verified_runtime_write_collision"] for x in result["candidates"]))
        self.assertTrue(all("git_add_line_evidence" in x and "shared_literal_crons" in x
                            for x in result["candidates"]))


if __name__ == "__main__":
    unittest.main()
