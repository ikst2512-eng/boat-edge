#!/usr/bin/env python3
"""Exact Git tree identity for a predeclared research model dependency manifest.

Does not discover dependencies automatically; omitted files remain a blocker.
This is research-only and never grants retrospective or prospective eligibility.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")


def git(root,*args):
    p=subprocess.run(["git",*args],cwd=root,capture_output=True)
    if p.returncode:raise ValueError("GIT_COMMAND_FAILED")
    return p.stdout


def verify(root, manifest):
    root=Path(root).resolve()
    if manifest.get("schema")!="BOAT_EDGE_PREDECLARED_MODEL_TREE_V1":
        raise ValueError("UNEXPECTED_MANIFEST_SCHEMA")
    sha=manifest.get("commit_sha")
    if not isinstance(sha,str) or not SHA40.fullmatch(sha):
        raise ValueError("INVALID_COMMIT_SHA")
    paths=manifest.get("required_paths")
    if not isinstance(paths,list) or not paths or len(paths)!=len(set(paths)):
        raise ValueError("INVALID_REQUIRED_PATHS")
    contents={}
    for path in paths:
        if not isinstance(path,str) or not path or path.startswith("/") or "\\" in path:
            raise ValueError("UNSAFE_MODEL_PATH")
        parts=Path(path).parts
        if ".." in parts or "." in parts:
            raise ValueError("UNSAFE_MODEL_PATH")
        data=git(root,"show",f"{sha}:{path}")
        contents[path]=hashlib.sha256(data).hexdigest()
    if contents!=manifest.get("source_sha256_by_path"):
        raise ValueError("MODEL_DEPENDENCY_DIGEST_MISMATCH")
    # Verified only for explicitly declared files, not unknown transitive imports.
    return {"declared_files_verified":len(contents),"commit_sha":sha,
            "all_transitive_dependencies_proven":False,
            "prediction_eligibility_granted":False,
            "formal_fresh_unlocked":False}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--manifest",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(verify(a.root,json.loads(a.manifest.read_text(encoding="utf-8"))),indent=2))
