"""Read-only breakdown of V232 frozen-cohort first Git proof failures.

Uses git log and exact blob SHA; avoids result data, writes and historical
reconstruction. Git commit timestamps alone are not independent clock proof.
"""
from __future__ import annotations
from collections import Counter
from datetime import timedelta
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from boat_edge_v234_settle import read, time, sha

def _git(root,*args):
    p=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True,check=False,timeout=30)
    return p.stdout if p.returncode==0 else ''

def classify(root):
    root=Path(root).resolve()
    folder=root/'data/site_autopilot/v232_cohort'
    scored=root/'data/site_autopilot/v234_scored'
    counts=Counter()
    examples={}
    for p in sorted(folder.glob('20??????-??-??.json')):
        if (scored/p.name).exists():continue
        obj=read(p) or {}
        due=time(obj.get('deadline_jst'))
        saved=time(obj.get('snapshot_saved_at'))
        relative=p.relative_to(root).as_posix()
        lines=_git(root,'log','--diff-filter=A','--reverse','--format=%H|%cI','--',relative).strip().splitlines()
        if not lines:reason='NO_FIRST_ADD_IN_REACHABLE_HISTORY'
        else:
            commit,_,when=lines[0].partition('|')
            created=time(when)
            blob=subprocess.run(['git','show',f'{commit}:{relative}'],cwd=root,capture_output=True,check=False,timeout=30)
            if blob.returncode:reason='FIRST_ADD_BLOB_UNAVAILABLE'
            elif __import__('hashlib').sha256(blob.stdout).hexdigest()!=sha(p):reason='CURRENT_BYTES_DIFFER_FROM_FIRST_ADD'
            elif not due or not saved or not created:reason='TIME_FIELDS_INVALID'
            elif created < saved and created.replace(microsecond=0)==saved.replace(microsecond=0):
                reason='SAME_SECOND_GIT_TIMESTAMP_PRECISION_AMBIGUITY'
            elif created < saved:reason='FIRST_ADD_BEFORE_DECLARED_SNAPSHOT_SAVE'
            elif created >= due:reason='FIRST_ADD_AT_OR_AFTER_DEADLINE'
            elif not saved<=created<due:reason='FIRST_ADD_COMMIT_TIME_OUTSIDE_FREEZE_WINDOW'
            else:reason='GIT_FIRST_ADD_GATE_PASSES'
        counts[reason]+=1
        if len(examples.get(reason,[]))<5:examples.setdefault(reason,[]).append(p.stem)
    return {'research_only':True,'no_result_read':True,'formal_fresh_eligible':False,
            'git_commit_time_independently_attested':False,
            'same_second_is_not_order_proof':True,
            'unscored_v232_checked':sum(counts.values()),
            'reasons':dict(sorted(counts.items())),'examples':examples}

if __name__=='__main__':
    import json
    print('V232_GIT_PROOF_BREAKDOWN='+json.dumps(classify('.'),sort_keys=True))
