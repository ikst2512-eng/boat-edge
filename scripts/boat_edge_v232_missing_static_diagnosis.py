"""Offline, non-promoting diagnostic of V229 races lacking V232 cohort.

Checks currently stored artifacts only; never rewinds the clock, opens results,
or enrolls an old race. Current file mismatches may reflect post-freeze updates.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from boat_edge_v232_pre_result_cohort import read,stamp,deadline,digest

def classify(root):
    root=Path(root).resolve()
    base=root/'data/site_autopilot'
    counts=Counter()
    samples={}
    for evidence in sorted((base/'v229_evidence').glob('20??????-??-??.json')):
        key=evidence.stem
        if (base/'v232_cohort'/evidence.name).is_file():
            continue
        snapfile=root/'data/site_prediction_snapshots'/evidence.name
        auditfile=root/'data/site_prediction_audit'/evidence.name
        snap=read(snapfile)
        audit=read(auditfile)
        if not snap:
            reason='SNAPSHOT_UNREADABLE'
        elif snap.get('prediction_kind')!='SITE_REFERENCE_V122' or snap.get('snapshot_window')!='FINAL_15M':
            reason='NOT_FINAL_SITE_REFERENCE'
        elif any((snap.get('guards') or {}).get(k) is not False for k in ('results_seen','unlock','scoring')):
            reason='SNAPSHOT_GUARDS_OPEN'
        else:
            saved=stamp(snap.get('saved_at'))
            due=deadline(key,snap.get('deadline'))
            first=stamp(snap.get('first_saved_at'))
            if not saved or not due or not first:
                reason='SNAPSHOT_CLOCK_INVALID'
            elif not 120 <= (due-saved).total_seconds() <= 900:
                reason='SNAPSHOT_NOT_IN_2_TO_15_MINUTES'
            elif not 0 <= (saved-first).total_seconds() <= 10:
                reason='FIRST_SAVED_TIME_MISMATCH'
            elif not audit:
                reason='AUDIT_UNREADABLE'
            elif audit.get('pass') is not True:
                reason='AUDIT_NOT_PASS'
            elif audit.get('latest_snapshot_sha256')!=digest(snapfile):
                reason='AUDIT_SNAPSHOT_SHA_NOW_MISMATCH'
            elif not (stamp(audit.get('first_audited_at')) and saved<=stamp(audit.get('first_audited_at'))<due):
                reason='AUDIT_TIMESTAMP_OUTSIDE_WINDOW'
            elif not (root/'data/races'/evidence.name).is_file():
                reason='RACE_CARD_FILE_MISSING_NOW'
            elif digest(root/'data/races'/evidence.name)!=snap.get('race_sha256'):
                reason='RACE_CARD_SHA_NOW_MISMATCH'
            elif not snap.get('odds_sha256'):
                reason='ODDS_SHA_NOT_SAVED'
            elif not (root/'data/site_prediction_snapshots/odds_v214'/f"{key}-{snap['odds_sha256']}.json").is_file():
                reason='ODDS_SIDECAR_MISSING_NOW'
            else:
                reason='STATIC_EVIDENCE_PRESENT_EXECUTION_WINDOW_UNPROVEN'
        counts[reason]+=1
        if len(samples.get(reason,[]))<4:samples.setdefault(reason,[]).append(key)
    return {'checked':sum(counts.values()),'reasons':dict(sorted(counts.items())),
            'examples':samples,'historical_v232_eligibility_proven':False,
            'historical_execution_time_verified':False,'research_only':True,
            'result_data_read':False,'formal_fresh_eligible':False}

if __name__=='__main__':
    import json
    print('V232_MISSING_STATIC_DIAGNOSIS='+json.dumps(classify('.'),sort_keys=True))
