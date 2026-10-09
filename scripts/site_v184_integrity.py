"""V184 immutable source/first-commit verification for V183 future site-reference shadow.
This module does not read results, payouts, formal-Fresh targets or odds.
"""
from __future__ import annotations
import hashlib,json,math,re,subprocess
from datetime import datetime,timezone,timedelta
from pathlib import Path
from site_v180_shadow import candidate_rows, POLICY

HEX=re.compile(r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')

def dateutc(v):
    try:
        d=datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None

def tree_blob(root,commit,path):
    if not HEX.fullmatch(str(commit or '').lower()) or ':' in path or path.startswith('/') or '\\' in path or '..' in path.split('/'):
        return None
    try:
        p=subprocess.run(['git','show',f'{commit}:{path}'],cwd=root,capture_output=True,timeout=12,check=False)
        return p.stdout if p.returncode==0 else None
    except (OSError,subprocess.SubprocessError):return None

def verify_shadow_commit_binding(root,relative,current,shadow,added):
    """Return (pass, reason, originally-committed pre-result source).
    Even if the on-disk snapshot or shadow later changes, it cannot pass by
    inheriting an earlier git ADD timestamp. Must match first commit's bytes.
    """
    if not isinstance(shadow,dict) or not isinstance(added,dict):return False,'V184_MISSING_BINDING',None
    key=shadow.get('race_key')
    if not isinstance(key,str) or not re.fullmatch(r'20\d{6}-\d{2}-\d{2}',key) or key[:8]<'20261010':
        return False,'V184_INVALID_FUTURE_KEY',None
    sha=added.get('commit'); stamp=dateutc(added.get('time'))
    if not stamp or not HEX.fullmatch(str(sha or '').lower()):return False,'V184_BAD_COMMIT_ID',None
    frozen=tree_blob(root,sha,relative)
    if frozen is None:return False,'V184_ORIGINAL_SHADOW_NOT_COMMITTED',None
    if frozen!=current:return False,'V184_SHADOW_EDITED_AFTER_FIRST_COMMIT',None
    source_path=f'data/site_prediction_snapshots/{key}.json'
    source_bytes=tree_blob(root,sha,source_path)
    if source_bytes is None:return False,'V184_ORIGINAL_SOURCE_NOT_IN_COMMIT',None
    if hashlib.sha256(source_bytes).hexdigest()!=shadow.get('source_sha256'):
        return False,'V184_PRECOMMIT_SNAPSHOT_SHA_MISMATCH',None
    try:source=json.loads(source_bytes)
    except (ValueError,UnicodeError):return False,'V184_SOURCE_JSON_INVALID',None
    if not isinstance(source,dict) or source.get('race_key')!=key or source.get('snapshot_window')!='FINAL_15M':
        return False,'V184_SOURCE_BINDING_MISMATCH',None
    if source.get('prediction_kind')!='SITE_REFERENCE_V122' or source.get('mode_policy')!=POLICY:
        return False,'V184_SOURCE_POLICY_MISMATCH',None
    if source.get('saved_at')!=shadow.get('source_saved_at') or source.get('first_saved_at')!=shadow.get('source_first_saved_at'):
        return False,'V184_SOURCE_TIME_MISMATCH',None
    try:deadline=datetime.strptime(key[:8]+str(source['deadline']),'%Y%m%d%H:%M').replace(tzinfo=timezone(timedelta(hours=9))).astimezone(timezone.utc)
    except (TypeError,ValueError,KeyError):return False,'V184_DEADLINE_MISSING',None
    saved=dateutc(source.get('saved_at'))
    if not saved or not saved<stamp<deadline or not 0<(deadline-saved).total_seconds()/60<=16:
        return False,'V184_NOT_IN_ORIGINAL_PREDEADLINE_WINDOW',None
    if (stamp-saved).total_seconds()>20*60:return False,'V184_SLOW_COMMIT',None
    if not re.fullmatch(r'[a-f0-9]{64}',str(shadow.get('source_race_sha256',''))):
        return False,'V184_RACE_SHA_UNBOUND',None
    # The full candidate must be reproducible from the original source's pre-result tickets.
    try:
        expected=candidate_rows(source)
        found=shadow['candidate_ranked_120']
        if len(found)!=120 or len(expected)!=120:return False,'V184_RECOMPUTE_BAD_LENGTH',None
        for a,b in zip(expected,found):
            if a['combo']!=b.get('combo') or abs(a['score']-float(b.get('score')))>1e-12:
                return False,'V184_CANDIDATE_NOT_REPRODUCIBLE',None
        base=[r['combo'] for r in source['modes']['hit']['tickets']]
        if shadow.get('baseline_top10')!=base:return False,'V184_BASELINE_NOT_REPRODUCIBLE',None
    except (KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError):
        return False,'V184_RECOMPUTE_ERROR',None
    return True,'PASS',source
