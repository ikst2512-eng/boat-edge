"""Synthetic local Git fixtures only: no real race outcomes or Formal Fresh."""
import hashlib
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import audit_pair_git_provenance as audit


class LocalGitIntegration(unittest.TestCase):
    def run_git(self, root, *args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()

    def test_git_objects_pass_but_external_proof_remains_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.run_git(root, "init", "-q")
            self.run_git(root, "config", "user.email", "audit@example.invalid")
            self.run_git(root, "config", "user.name", "Audit Test")
            contents = {}
            for side in ("baseline", "candidate"):
                contents[f"freeze/{side}/input.json"] = b"same-input-bytes"
                contents[f"freeze/{side}/model.py"] = side.encode()
                contents[f"freeze/{side}/prediction.json"] = (side + " prediction").encode()
            for path, raw in contents.items():
                dst = root / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(raw)
            self.run_git(root, "add", "freeze")
            with patch.dict("os.environ", {
                "GIT_AUTHOR_DATE": "2026-10-25T13:50:00+09:00",
                "GIT_COMMITTER_DATE": "2026-10-25T13:50:00+09:00",
            }):
                self.run_git(root, "commit", "-qm", "synthetic fixture")
            commit = self.run_git(root, "rev-parse", "HEAD")
            pair = {}
            for side in ("baseline", "candidate"):
                item = {}
                for field, filename in (("input", "input.json"), ("model", "model.py"), ("prediction", "prediction.json")):
                    path = f"freeze/{side}/{filename}"
                    item[field] = {
                        "path": path,
                        "sha256": hashlib.sha256(contents[path]).hexdigest(),
                        "first_commit": commit,
                    }
                item["prediction_saved_at_jst"] = "2026-10-25T13:49:00+09:00"
                pair[side] = item
            manifest = {
                "scope": "RESEARCH_ONLY_PRE_OUTCOME_PAIR",
                "race_key": "20261025-06-08",
                "deadline_jst": "2026-10-25T14:06:00+09:00",
                **pair,
            }
            accepted = audit.verify(root, manifest)
            self.assertEqual(accepted["local_git_object_consistency"], "PASS")
            self.assertFalse(accepted["comparable_for_real_race_scoring"])
            self.assertFalse(accepted["independent_publication_time_proven"])
            self.assertFalse(accepted["model_outcome_blindness_proven"])
            real_git = audit.git
            def disconnected_history(check_root, *args):
                if args[:2] == ("merge-base", "--is-ancestor"):
                    raise ValueError("GIT_PROOF_UNAVAILABLE")
                return real_git(check_root, *args)
            with patch.object(audit, "git", side_effect=disconnected_history):
                with self.assertRaisesRegex(ValueError, "MODEL_OR_INPUT_NOT_ANCESTOR_OF_PREDICTION"):
                    audit.verify(root, manifest)
            late_model = root / "freeze/candidate/model_after_prediction.py"
            late_model.write_bytes(b"post-prediction-model")
            self.run_git(root, "add", "freeze/candidate/model_after_prediction.py")
            with patch.dict("os.environ", {
                "GIT_AUTHOR_DATE": "2026-10-25T13:55:00+09:00",
                "GIT_COMMITTER_DATE": "2026-10-25T13:55:00+09:00",
            }):
                self.run_git(root, "commit", "-qm", "later model")
            late_commit = self.run_git(root, "rev-parse", "HEAD")
            old_model = manifest["candidate"]["model"]
            manifest["candidate"]["model"] = {
                "path": "freeze/candidate/model_after_prediction.py",
                "sha256": hashlib.sha256(b"post-prediction-model").hexdigest(),
                "first_commit": late_commit,
            }
            with self.assertRaisesRegex(ValueError, "MODEL_OR_INPUT_GIT_AFTER_PREDICTION"):
                audit.verify(root, manifest)
            manifest["candidate"]["model"] = old_model
            # The original first-add commit remains valid, but an intervening
            # modification must invalidate a later frozen prediction.
            modified = root / "freeze/candidate/model.py"
            modified.write_bytes(b"changed-before-future-prediction")
            self.run_git(root, "add", "freeze/candidate/model.py")
            with patch.dict("os.environ", {
                "GIT_AUTHOR_DATE": "2026-10-25T13:56:00+09:00",
                "GIT_COMMITTER_DATE": "2026-10-25T13:56:00+09:00",
            }):
                self.run_git(root, "commit", "-qm", "modified model")
            future_prediction = root / "freeze/candidate/prediction_later.json"
            future_prediction.write_bytes(b"later prediction")
            self.run_git(root, "add", "freeze/candidate/prediction_later.json")
            with patch.dict("os.environ", {
                "GIT_AUTHOR_DATE": "2026-10-25T13:57:00+09:00",
                "GIT_COMMITTER_DATE": "2026-10-25T13:57:00+09:00",
            }):
                self.run_git(root, "commit", "-qm", "later prediction")
            future_commit = self.run_git(root, "rev-parse", "HEAD")
            old_prediction = manifest["candidate"]["prediction"]
            manifest["candidate"]["prediction"] = {
                "path": "freeze/candidate/prediction_later.json",
                "sha256": hashlib.sha256(b"later prediction").hexdigest(),
                "first_commit": future_commit,
            }
            with self.assertRaisesRegex(ValueError, "MODEL_OR_INPUT_CHANGED_BEFORE_PREDICTION"):
                audit.verify(root, manifest)
            manifest["candidate"]["prediction"] = old_prediction
            manifest["candidate"]["model"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "GIT_TREE_BYTES_SHA_MISMATCH"):
                audit.verify(root, manifest)
            manifest["candidate"]["model"]["sha256"] = hashlib.sha256(contents["freeze/candidate/model.py"]).hexdigest()
            manifest["candidate"]["input"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "GIT_TREE_BYTES_SHA_MISMATCH"):
                audit.verify(root, manifest)
            manifest["candidate"]["input"]["sha256"] = hashlib.sha256(contents["freeze/candidate/input.json"]).hexdigest()
            manifest["candidate"]["prediction_saved_at_jst"] = "2026-10-25T14:07:00+09:00"
            with self.assertRaisesRegex(ValueError, "INVALID_PREDICTION_FREEZE_TIME"):
                audit.verify(root, manifest)


if __name__ == "__main__":
    unittest.main()
