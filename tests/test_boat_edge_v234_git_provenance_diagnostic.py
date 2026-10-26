import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_v234_git_provenance_diagnostic import classify


class GitProvenanceDiagnosticTests(unittest.TestCase):
    def test_missing_git_and_time_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data/site_autopilot/v232_cohort/20261025-01-01.json"
            p.parent.mkdir(parents=True)
            record = {"deadline_jst": "2026-10-25T12:00:00+09:00",
                      "snapshot_saved_at": "2026-10-25T11:50:00+09:00",
                      "evidence_committed_at": "2026-10-25T11:51:00+09:00"}
            p.write_text(json.dumps(record))
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            self.assertEqual(classify(root, p)[0], "no_git_creation_commit")
            record["evidence_committed_at"] = "2026-10-25T12:01:00+09:00"
            p.write_text(json.dumps(record))
            self.assertEqual(classify(root, p)[0], "invalid_claimed_prededline_times")


if __name__ == "__main__":
    unittest.main()
