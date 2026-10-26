import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_model_tree_manifest_audit import verify


class TreeManifestTests(unittest.TestCase):
    def test_explicit_git_blob_and_digest(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/"model.py").write_text("import helper\n")
            (root/"helper.py").write_text("value=1\n")
            subprocess.run(["git","init","-q"],cwd=root,check=True)
            subprocess.run(["git","add","model.py","helper.py"],cwd=root,check=True)
            subprocess.run(["git","-c","user.name=test","-c","user.email=test@example.invalid",
                            "commit","-qm","test"],cwd=root,check=True)
            sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
            manifest={"schema":"BOAT_EDGE_PREDECLARED_MODEL_TREE_V1","commit_sha":sha,
                      "required_paths":["model.py","helper.py"],
                      "source_sha256_by_path":{p:hashlib.sha256((root/p).read_bytes()).hexdigest()
                                               for p in ("model.py","helper.py")}}
            self.assertEqual(verify(root,manifest)["declared_files_verified"],2)
            manifest["source_sha256_by_path"]["helper.py"]="0"*64
            with self.assertRaisesRegex(ValueError,"DIGEST_MISMATCH"):
                verify(root,manifest)
            manifest["required_paths"]=["../secret"]
            with self.assertRaisesRegex(ValueError,"UNSAFE_MODEL_PATH"):
                verify(root,manifest)


if __name__=="__main__":
    unittest.main()
