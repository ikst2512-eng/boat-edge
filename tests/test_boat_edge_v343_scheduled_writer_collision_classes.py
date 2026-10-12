"""V343 candidate-only collision classification; real workflow declaration pins."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.boat_edge_v341_scheduled_writer_path_audit import audit as v341_audit
from scripts.boat_edge_v343_scheduled_writer_collision_classes import audit, classify_pair, path_relation

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/BOAT_EDGE_01_V343_REAL_WORKFLOW_CLASSIFICATION.json"


class V343StagingClassification(unittest.TestCase):
    def test_actual_workflow_pairs_are_pinned_to_expected_class(self):
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(doc["verified_duplicate_writers"], 0)
        self.assertTrue(doc["classification_is_only_candidate_not_verified_duplicate"])
        records = {r["workflow"]: r for r in v341_audit()["scheduled_candidate_records"]}
        self.assertNotIn("v336-site-research-live-freeze.yml", records)
        for item in doc["pinned_actual_workflow_cases"]:
            with self.subTest(pair=(item["left"], item["right"])):
                self.assertIn(item["left"], records)
                self.assertIn(item["right"], records)
                pair = classify_pair(records[item["left"]]["staged_literals"],
                                     records[item["right"]]["staged_literals"])
                self.assertIsNotNone(pair)
                self.assertEqual(pair["classification"], item["expected_classification"])
                witness_key = ("exact_path_witnesses_first_12" if
                               item["expected_witness"]["relation"] == "EXACT_PATH"
                               else "parent_directory_witnesses_first_12")
                self.assertIn(item["expected_witness"], pair[witness_key])
        report = audit()
        self.assertTrue(report["read_only"])
        self.assertEqual(report["verified_duplicate_writers"], 0)
        self.assertFalse(report["results_or_formal_data_read"])
        self.assertEqual(report["candidate_overlapping_workflow_pairs"],
                         sum(report["pair_class_counts"].values()))
        self.assertEqual(report, audit())

    def test_boundary_and_direction_not_naive_string_prefix(self):
        self.assertIsNone(path_relation("data/site", "data/site_odds"))
        self.assertIsNone(path_relation("data/one", "data/ones"))
        self.assertEqual(path_relation("data", "data/site_odds"), "LEFT_PARENT_OF_RIGHT")
        self.assertEqual(path_relation("data/site_odds", "data"), "RIGHT_PARENT_OF_LEFT")
        self.assertEqual(path_relation("data", "data"), "EXACT_PATH")
        self.assertIsNone(classify_pair(["data/a"], ["data/b"]))

    def test_mixed_and_synthetic_full_witness_counts_do_not_depend_on_display_cap(self):
        pair = classify_pair(["data", "docs", "racing"], ["data", "data/a", "docs/b"])
        self.assertEqual(pair["classification"], "MIXED_EXACT_AND_PARENT")
        self.assertEqual(pair["exact_path_witness_count"], 1)
        self.assertEqual(pair["parent_directory_witness_count"], 2)
        many = classify_pair(["data"], [f"data/file{n}" for n in range(15)])
        self.assertEqual(many["parent_directory_witness_count"], 15)
        self.assertEqual(len(many["parent_directory_witnesses_first_12"]), 12)
        self.assertTrue(many["parent_witnesses_truncated"])

    def test_readonly_temp_workflows_do_not_change_legacy_v341_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def put(name, git_add):
                (root / name).write_text(
                    f"name: {name}\non:\n  schedule:\n    - cron: '*/5 * * * *'\n"
                    "permissions:\n  contents: write\njobs:\n  test:\n"
                    "    runs-on: ubuntu-latest\n    steps:\n      - run: |\n"
                    f"          git add -- {git_add}\n", encoding="utf-8")
            put("a.yml", "data docs")
            put("b.yml", "data docs/a")
            put("c.yml", "data/site_odds")
            before = v341_audit(root)
            classified = audit(root)
            after = v341_audit(root)
            self.assertEqual(before, after)
            self.assertEqual(classified["candidate_overlapping_workflow_pairs"], 3)
            self.assertEqual(classified["pair_class_counts"]["MIXED_EXACT_AND_PARENT"], 1)
            self.assertEqual(classified["pair_class_counts"]["PARENT_CHILD_ONLY"], 2)
            self.assertEqual(classified["verified_duplicate_writers"], 0)
            self.assertTrue(classified["classification_does_not_authorize_workflow_disable"])


if __name__ == "__main__":
    unittest.main()
