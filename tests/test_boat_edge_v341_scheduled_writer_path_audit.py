"""V341 static writer ownership diagnostics: no file data, results or network."""
import tempfile
import unittest
from pathlib import Path

from scripts.boat_edge_v341_scheduled_writer_path_audit import audit, staged_paths


class V341WriterOverlap(unittest.TestCase):
    def test_real_high_level_collector_overlap_is_candidate_only(self):
        root = Path(__file__).resolve().parents[1] / ".github/workflows"
        report = audit(root)
        self.assertTrue(report["read_only"])
        self.assertEqual(report["verified_duplicate_writers"], 0)
        self.assertFalse(report["results_or_formal_data_read"])
        records = {x["workflow"]: x for x in report["scheduled_candidate_records"]}
        self.assertIn("auto-update.yml", records)
        self.assertIn("site-odds.yml", records)
        self.assertIn("data", records["auto-update.yml"]["staged_literals"])
        self.assertIn("data/site_odds", records["site-odds.yml"]["staged_literals"])
        self.assertNotIn("v336-site-research-live-freeze.yml", records)
        self.assertTrue(any(
            {pair["left"], pair["right"]} ==
            {"auto-update.yml", "site-odds.yml"}
            for pair in report["overlap_pairs_first_100"]
        ) or report["pairs_output_truncated"])

    def test_explicit_literal_writes_detected_without_executing_anything(self):
        paths, dynamic = staged_paths(
            "git add -A data/ || true\n"
            "git add -- data/site_odds/current.json\n"
            "git add -- \"$file\"\n"
            "git add -- ../outside\n"
            "git add -- '/absolute/file'\n"
        )
        self.assertEqual(paths, ["data", "data/site_odds/current.json"])
        self.assertTrue(dynamic)

    def test_quoted_event_key_and_disjoint_writers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def sample(name, event, permission, stage):
                (root / name).write_text(
                    f"name: {name}\n{event}:\n"
                    "  schedule:\n    - cron: '*/5 * * * *'\n"
                    f"permissions:\n  contents: {permission}\n"
                    "jobs:\n  check:\n    runs-on: ubuntu-latest\n"
                    "    steps:\n      - run: |\n"
                    f"          git add -- {stage}\n", encoding="utf-8"
                )
            sample("a.yml", "on", "write", "data/")
            sample("b.yml", "'on'", "write", "data/site_odds/")
            sample("c.yml", '"on"', "write", "docs/")
            sample("read.yml", "on", "read", "data/site_odds/")
            result = audit(root)
            self.assertEqual(result["scheduled_contents_write_candidates"], 3)
            self.assertEqual(result["candidate_overlapping_workflow_pairs"], 1)
            pair = result["overlap_pairs_first_100"][0]
            self.assertEqual({pair["left"], pair["right"]}, {"a.yml", "b.yml"})
            self.assertEqual(pair["staging_path_witnesses"],
                             [{"left": "data", "right": "data/site_odds"}])
            self.assertEqual(result, audit(root))


if __name__ == "__main__":
    unittest.main()
