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
            subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "initial"], cwd=root, check=True)
            self.assertEqual(classify(root, p)[0], "no_git_creation_commit")
            record["evidence_committed_at"] = "2026-10-25T12:01:00+09:00"
            p.write_text(json.dumps(record))
            self.assertEqual(classify(root, p)[0], "invalid_claimed_prededline_times")

    def test_subsecond_ambiguity_is_not_eligible(self):
        from unittest.mock import patch
        from scripts.boat_edge_v234_git_provenance_diagnostic import timing_detail
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data/site_autopilot/v232_cohort/20261025-01-01.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({
                "deadline_jst": "2026-10-25T12:00:00+09:00",
                "snapshot_saved_at": "2026-10-25T11:50:00.500000+09:00",
                "evidence_committed_at": "2026-10-25T11:50:00.600000+09:00"
            }))
            def fake_git(_root, *args):
                if args[0] == "log":
                    return b"0123456789abcdef0123456789abcdef01234567|2026-10-25T11:50:00+09:00"
                if args[0] == "show":
                    return p.read_bytes()
                return None
            with patch("scripts.boat_edge_v234_git_provenance_diagnostic.git", fake_git):
                self.assertEqual(classify(root, p)[0],
                                 "git_second_precision_subsecond_ambiguity_not_eligible")
            detail = timing_detail(root, p)
            self.assertFalse(detail["timing_available"])

    def test_greater_than_one_second_remains_invalid(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data/site_autopilot/v232_cohort/20261025-01-01.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({
                "deadline_jst": "2026-10-25T12:00:00+09:00",
                "snapshot_saved_at": "2026-10-25T11:50:02.500000+09:00",
                "evidence_committed_at": "2026-10-25T11:50:03+09:00"
            }))
            def fake_git(_root, *args):
                if args[0] == "log":
                    return b"0123456789abcdef0123456789abcdef01234567|2026-10-25T11:50:00+09:00"
                if args[0] == "show":
                    return p.read_bytes()
                return None
            with patch("scripts.boat_edge_v234_git_provenance_diagnostic.git", fake_git):
                self.assertEqual(classify(root, p)[0], "git_creation_precedes_claimed_snapshot")


if __name__ == "__main__":
    unittest.main()
