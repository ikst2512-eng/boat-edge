"""Read-only V232 -> V234 exclusion diagnosis using the *existing* scorer gates.

Only checks immutable pre-result cohort / Git validation. Never fetches results,
never invokes run()/score(), writes no output files and never touches Formal Fresh.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from boat_edge_v234_settle import verify_frozen

def classify(root, now=None):
    root=Path(root).resolve()
    now=now or datetime.now(timezone.utc)
    v229=root/'data/site_autopilot/v229_evidence'
    v232=root/'data/site_autopilot/v232_cohort'
    v234=root/'data/site_autopilot/v234_scored'
    counts=Counter()
    samples={}
    for p in sorted(v229.glob('20??????-??-??.json')):
        key=p.stem
        cohort=v232/p.name
        settled=v234/p.name
        if not cohort.is_file():
            category='NO_V232_COHORT_NOT_A_SETTLEMENT_FAILURE'
        elif settled.is_file():
            category='V234_PRESENT'
        else:
            try:
                proof,why=verify_frozen(root,cohort,now)
                category=('V232_VERIFIED_RESULT_STAGE_UNDETERMINED'
                          if why is None else 'V232_VERIFY_'+why)
            except Exception as exc:
                category='V232_VERIFICATION_ERROR_'+type(exc).__name__
        counts[category]+=1
        if len(samples.get(category,[]))<5:
            samples.setdefault(category,[]).append(key)
    return dict(checked=sum(counts.values()),reason_counts=dict(sorted(counts.items())),
                sample_keys=samples,research_only=True,results_read=False,
                formal_fresh_eligible=False,
                historical_noncreation_cause_proven=False,
                result_stage_cause_proven=False)
