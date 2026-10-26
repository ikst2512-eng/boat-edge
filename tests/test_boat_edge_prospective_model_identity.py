import datetime as dt
import subprocess
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_prospective_model_identity import create, save_once


class ProspectiveIdentityTests(unittest.TestCase):
    def test_transitive_import_requires_declared_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "model.py").write_text("import dep\\n")
            (root / "dep.py").write_text("import nested\\n")
            (root / "nested.py").write_text("NESTED=1\\n")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "model.py", "dep.py", "nested.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=test", "-c",
                            "user.email=test@example.invalid", "commit", "-qm", "initial"],
                           cwd=root, check=True)
            now = dt.datetime(2026, 10, 26, tzinfo=dt.timezone.utc)
            due = "2026-10-27T10:00:00+09:00"
            with self.assertRaisesRegex(ValueError, "TRANSITIVE_LOCAL_DEPENDENCIES_NOT_DECLARED"):
                create(root, "20261027-21-04", "model.py", due, now=now,
                       dependency_paths=["dep.py"])
            row = create(root, "20261027-21-04", "model.py", due, now=now,
                         dependency_paths=["dep.py", "nested.py"])
            self.assertEqual(set(row["transitive_local_imports_checked"]), {"dep.py", "nested.py"})
            self.assertFalse(row["dependency_set_complete_independently_verified"])

    def test_future_only_clean_git_and_write_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "model.py").write_text("import dep\nMODEL=1\n")
            (root / "dep.py").write_text("DEP=1\n")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "model.py", "dep.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "initial"], cwd=root, check=True)
            now = dt.datetime(2026, 10, 26, tzinfo=dt.timezone.utc)
            due = "2026-10-27T10:00:00+09:00"
            with self.assertRaisesRegex(ValueError, "TRANSITIVE_LOCAL_DEPENDENCIES_NOT_DECLARED"):
                create(root, "20261027-21-02", "model.py", due, now=now)
            record = create(root, "20261027-21-02", "model.py", due, now=now, dependency_paths=["dep.py"])
            self.assertFalse(record["prediction_eligibility_granted"])
            self.assertEqual(record["model_source_scope"], "SINGLE_FILE_ONLY_DEPENDENCIES_NOT_ATTESTED")
            self.assertEqual(len(record["model_source_sha256"]), 64)
            self.assertEqual(len(record["declared_dependency_sha256"]["dep.py"]), 64)
            self.assertFalse(record["dependency_set_complete_independently_verified"])
            (root / "dep.py").write_text("DEP=2\n")
            with self.assertRaisesRegex(ValueError, "DEPENDENCY_DIFFERS_FROM_HEAD"):
                create(root, "20261027-21-03", "model.py", due, now=now, dependency_paths=["dep.py"])
            (root / "dep.py").write_text("DEP=1\n")
            save_once(root, record)
            with self.assertRaises(FileExistsError):
                save_once(root, record)
            (root / "model.py").write_text("import dep\nMODEL=2\n")
            with self.assertRaisesRegex(ValueError, "MODEL_DIFFERS_FROM_HEAD"):
                create(root, "20261027-21-03", "model.py", due, now=now)
            with self.assertRaisesRegex(ValueError, "LIVE_PREDEADLINE_ONLY"):
                create(root, "20261027-21-03", "model.py", due,
                       now=dt.datetime(2026, 10, 27, 1, 0, tzinfo=dt.timezone.utc))


if __name__ == "__main__":
    unittest.main()
