"""Evaluate whether a scheduled run provides actual capture evidence.

Fail closed: a green job with zero due races is NOT a capture success.
"""
import argparse,json
from pathlib import Path

def assess(run_status,summary):
    if run_status.get("status")!="ok":return {"state":"RUN_FAILED","proven_captures":0}
    due=run_status.get("due");captured=run_status.get("captured")
    if type(due) is not int or type(captured) is not int or due<0 or captured<0 or captured>due:
        return {"state":"INVALID_RUN_STATUS","proven_captures":0}
    if run_status.get("failed",0):
        return {"state":"PARTIAL_FAILURE","proven_captures":0}
    if due==0:return {"state":"NO_RACES_DUE","proven_captures":0}
    if type(summary.get("invalid")) is not int or summary["invalid"]>0:
        return {"state":"INVALID_CAPTURE_EVIDENCE","proven_captures":0}
    n=summary.get("manifests",0)
    if type(n) is not int or n<captured:
        return {"state":"MISSING_CAPTURE_EVIDENCE","proven_captures":0}
    valid=summary.get("eligible_10",0)
    if type(valid) is not int or valid<0 or valid>n:return {"state":"INVALID_CAPTURE_EVIDENCE","proven_captures":0}
    if valid==0:return {"state":"NO_CUTOFF_ELIGIBLE_CAPTURE","proven_captures":0}
    return {"state":"PROBE_EVIDENCE_PRESENT_NOT_EXTERNALLY_ATTESTED","proven_captures":valid,"note":"Only source snapshots, not verified official publication or saved predictions"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("status",type=Path);p.add_argument("summary",type=Path);a=p.parse_args()
    output=assess(json.loads(a.status.read_text()),json.loads(a.summary.read_text()))
    print(json.dumps(output,ensure_ascii=False,indent=2))
