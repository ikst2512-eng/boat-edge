"""Real local Git object tests, synthetic content; no race results."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_research_git_receipt import audit_first_add


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class GitReceipt(unittest.TestCase):
    def test_first_add_and_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            git(root, "init")
            git(root, "config", "user.email", "research@example.invalid")
            git(root, "config", "user.name", "Research Fixture")
            (root / "README").write_text("parent")
            git(root, "add", "README")
            git(root, "commit", "-m", "parent")
            data = b"frozen synthetic prediction bytes"
            (root / "frozen.json").write_bytes(data)
            git(root, "add", "frozen.json")
            git(root, "commit", "-m", "first add")
            sha = git(root, "rev-parse", "HEAD")
            digest = hashlib.sha256(data).hexdigest()
            result = audit_first_add(root, sha, "frozen.json", digest)
            self.assertTrue(result["git_object_first_add_verified"])
            self.assertFalse(result["eligible_for_paired_real_race_score"])
            with self.assertRaisesRegex(ValueError, "SHA256_MISMATCH"):
                audit_first_add(root, sha, "frozen.json", "a"*64)
            (root / "frozen.json").write_text("later")
            git(root, "add", "frozen.json")
            git(root, "commit", "-m", "change")
            with self.assertRaisesRegex(ValueError, "FIRST_ADD_NOT_PROVEN"):
                audit_first_add(root, git(root, "rev-parse", "HEAD"), "frozen.json", hashlib.sha256(b"later").hexdigest())

    def test_reject_path_traversal(self):
        with self.assertRaisesRegex(ValueError, "SAFE_REPO_PATH"):
            audit_first_add(".", "a"*40, "../bad", "b"*64)
