import json
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_v234_confidence_audit import audit, wilson, SCHEMA


class ConfidenceAuditTests(unittest.TestCase):
    def test_wilson_edges(self):
        self.assertIsNone(wilson(0, 0))
        self.assertEqual(wilson(0, 10)[0], 0.0)
        self.assertEqual(wilson(10, 10)[1], 1.0)
        a, b = wilson(5, 10)
        self.assertLess(a, 0.5)
        self.assertGreater(b, 0.5)

    def test_summary_and_exclusion_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "data/site_autopilot/v234_scored"
            folder.mkdir(parents=True)
            row = dict(schema=SCHEMA, race_key="20261025-21-01",
                       scope="POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED",
                       head_hit=True, top3_hit=False, top5_hit=True, top10_hit=True,
                       accuracy_improvement_proven=False, model_promotion_authorized=False,
                       first_git_commit="a" * 40, cohort_sha256="b" * 64,
                       result_sha256="c" * 64)
            (folder / "20261025-21-01.json").write_text(json.dumps(row))
            summary = dict(settled_verified_races=1, head_hit=1, top3_hit=0,
                           top5_hit=1, top10_hit=1,
                           scoring_exclusions_this_run={"missing_git": 2})
            (root / "data/site_autopilot/v234_current.json").write_text(json.dumps(summary))
            out = audit(root)
            self.assertFalse(out["summary_mismatch"])
            self.assertEqual(out["metrics"]["top10_hit"]["hits"], 1)
            self.assertFalse(out["accuracy_improvement_proven"])
            self.assertEqual(out["scoring_exclusions_from_latest_run"]["missing_git"], 2)
            row["top3_hit"] = True
            row["top5_hit"] = False
            (folder / "20261025-21-01.json").write_text(json.dumps(row))
            self.assertEqual(audit(root)["invalid_record_count"], 1)


if __name__ == "__main__":
    unittest.main()
