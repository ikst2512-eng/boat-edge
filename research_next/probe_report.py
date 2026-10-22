"""Aggregate only validated, on-disk probe manifests with intact captured bytes."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
def report(root):
    output={"manifests":0,"eligible_12":0,"eligible_11":0,"eligible_10":0,"invalid":0}
    unique={12:set(),11:set(),10:set()}
    for p in Path(root).glob("*/*.json"):
        try:
            m=json.loads(p.read_text(encoding="utf-8"))
            name=m["body_name"]
            if not isinstance(name,str) or Path(name).name!=name or not name.endswith(".body"):raise ValueError("unsafe body name")
            body=p.parent/name
            if body.is_symlink() or body.parent!=p.parent or not body.is_file():raise ValueError("invalid body")
            data=body.read_bytes()
            if len(data)!=m["bytes"] or hashlib.sha256(data).hexdigest()!=m["sha256"]:raise ValueError("hash mismatch")
            if m["target_race_validated"] is not True:raise ValueError("race unverified")
            for minute in (12,11,10):
                if minute in m["eligible_margins"]:unique[minute].add((m["race_code"],m["source_url"]))
            output["manifests"]+=1
        except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError):
            output["invalid"]+=1
    for minute in (12,11,10):output[f"eligible_{minute}"]=len(unique[minute])
    return output
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root");a=p.parse_args()
    print(json.dumps(report(a.root),ensure_ascii=False,indent=2))
