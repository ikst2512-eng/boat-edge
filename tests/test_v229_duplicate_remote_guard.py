import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "guard", Path(__file__).resolve().parents[1] / "scripts" / "v229_duplicate_remote_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class DuplicateRemoteGuardTests(unittest.TestCase):
    def call(self, files, remote_blobs):
        def run(argv, **kwargs):
            if argv[1] == "diff-tree":
                return subprocess.CompletedProcess(argv, 0, ("\n".join(files) + "\n").encode(), b"")
            ref = argv[-1]
            if ref.startswith("HEAD:"):
                return subprocess.CompletedProcess(argv, 0, b"same-sha\n", b"")
            value = remote_blobs.get(ref)
            return subprocess.CompletedProcess(argv, 0 if value else 128,
                                               (value or "").encode(), b"")
        with patch.object(guard.subprocess, "run", side_effect=run):
            return guard.duplicate_on_remote()

    def test_identical_first_writer_is_noop(self):
        name = "data/site_prediction_snapshots/20261031-04-01.json"
        self.assertTrue(self.call([name], {"origin/main:" + name: "same-sha\n"}))

    def test_modified_remote_never_acknowledged(self):
        name = "data/site_prediction_snapshots/20261031-04-01.json"
        self.assertFalse(self.call([name], {"origin/main:" + name: "different\n"}))
        self.assertFalse(self.call([name], {}))

    def test_all_committed_paths_must_match(self):
        a = "data/site_prediction_snapshots/20261031-04-01.json"
        b = "data/site_autopilot/v229_evidence/20261031-04-01.json"
        self.assertFalse(self.call([a, b], {"origin/main:" + a: "same-sha\n"}))

    def test_unapproved_commit_and_empty_commit_rejected(self):
        self.assertFalse(self.call(["scripts/site_final_history_v133.py"], {}))
        self.assertFalse(self.call([], {}))

if __name__ == "__main__":
    unittest.main()
