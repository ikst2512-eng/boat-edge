#!/usr/bin/env python3
"""Read-only static Git binding for the V235/V229/V228 freeze chain."""
import hashlib
import json
import subprocess
from pathlib import Path

CHAIN=(".github/workflows/V235.yml","scripts/boat_edge_v229_atomic_freeze.py",
       "scripts/boat_edge_v228_freeze_only.py","scripts/boat_edge_v232_pre_result_cohort.py")

def audit(root):
    root=Path(root).resolve()
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    evidence={}
    problems=[]
    for rel in CHAIN:
        p=root/rel
        if p.is_symlink() or not p.is_file():
            problems.append(rel+":missing_or_symlink")
            continue
        try:
            committed=subprocess.check_output(["git","show",sha+":"+rel],cwd=root,stderr=subprocess.DEVNULL)
            local=p.read_bytes()
            if local!=committed:
                problems.append(rel+":worktree_differs_from_head")
            evidence[rel]=hashlib.sha256(committed).hexdigest()
        except (OSError,subprocess.CalledProcessError):
            problems.append(rel+":git_blob_unavailable")
    return {"schema":"BOAT_EDGE_V235_STATIC_FREEZE_CHAIN_GIT_BINDING_V1",
            "scope":"READ_ONLY_SITE_RESEARCH_NOT_FORMAL_FRESH",
            "git_sha":sha,"declared_freeze_chain_source_sha256":evidence,
            "chain_source_errors":problems,
            "static_chain_hashes_verified":not problems and len(evidence)==len(CHAIN),
            "runtime_generated_code_bytes_independently_verified":False,
            "per_race_source_receipt_committed_before_deadline":False,
            "prediction_eligibility_granted":False,"accuracy_improvement_proven":False}
if __name__=="__main__":
    print(json.dumps(audit(Path(".")),ensure_ascii=False,indent=2,sort_keys=True))
