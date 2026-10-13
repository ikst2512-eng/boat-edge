import unittest
from scripts.boat_edge_v343_scheduled_writer_collision_classes import audit as v343_audit
from scripts.boat_edge_v344_exact_writer_triage import triage


class V344ExactWriterTriage(unittest.TestCase):
    def test_real_workflows_all_exact_witnesses_are_accounted_for(self):
        source = v343_audit()
        report = triage()
        self.assertEqual(report, triage())
        self.assertEqual(report["exact_only_pairs"], source["pair_class_counts"]["EXACT_ONLY"])
        self.assertEqual(report["exact_witness_count"], source["exact_path_witness_count"])
        self.assertEqual(len(report["candidates"]), source["exact_path_witness_count"])
        self.assertEqual(report["verified_duplicate_writers"], 0)
        self.assertTrue(report["no_disable_or_owner_transfer_authorized"])
        self.assertTrue(all(not c["disable_authorized"] and c["owner"] == "UNRESOLVED"
                            for c in report["candidates"]))
        self.assertTrue(all(c["path"] for c in report["candidates"]))


if __name__ == "__main__":
    unittest.main()
