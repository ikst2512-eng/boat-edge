#!/usr/bin/env python3
"""V228: site-reference FINAL15 pre-result rescue, no result/payout/formal input reads.

Loads the EXACT pinned V133/V226 server implementation, then strips all
post-result logic and formal-merge access before executing its pre-result loop.
Does not reconstruct old forecasts. Existing snapshots remain immutable.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path

MODEL_SHA = '7b2916df307fcb2783cfc6ddc38ff73903d56da5'
SOURCE = Path('scripts/site_final_history_v133.py')
CUT = 'for sp in sorted(SNAPS.glob("????????-??-??.json")):\n'
RESULT_ANCHOR = ('    result=read_json(RESULTS/f"{key}.json")\n'
                 '    if result and result.get("status")=="confirmed":\n'
                 '        continue\n')
FORMAL_ANCHOR = ('    race=merge_formal(race,key)\n'
                 '    pred=formal_pred(race) if has_formal(race) else build_fallback(race)\n')
FORMAL_REPLACEMENT = (
    '    # V228_SITE_REFERENCE_ONLY: do not open formal prediction files.\n'
    '    if has_formal(race) or any((base/f"{key}.json").is_file() for base in FORMAL_DIRS):\n'
    '        continue\n'
    '    pred=build_fallback(race)\n')


def git_blob(source: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()


def build_frozen_source(raw: str, pin: str = MODEL_SHA) -> str:
    if git_blob(raw.encode('utf-8')) != pin:
        raise AssertionError('V228_ORIGINAL_V133_SOURCE_BLOB_SHA_DRIFT_FAIL_CLOSED')
    for anchor in (CUT, RESULT_ANCHOR, FORMAL_ANCHOR):
        if raw.count(anchor) != 1:
            raise AssertionError('V228_REQUIRED_SOURCE_ANCHOR_MISMATCH')
    if not all(raw.count(x)==1 for x in ('V226_IMMUTABLE_ORIGINAL_SNAPSHOT',
                                        'V226_SOURCE_GUARD','V226_DECISION_WINDOW','V226_ODDS_GUARD')):
        raise AssertionError('V228_V226_PROSPECTIVE_GUARDS_NOT_PINNED')
    pre,tail=raw.split(CUT)
    if 'for hp in sorted(HIST.glob(' not in tail or 'read_json(RESULTS' not in tail:
        raise AssertionError('V228_POST_RESULT_BOUNDARY_MISMATCH')
    if pre.count(RESULT_ANCHOR)!=1 or pre.count(FORMAL_ANCHOR)!=1:
        raise AssertionError('V228_PRE_RESULT_PATCH_MISMATCH')
    pre=pre.replace(RESULT_ANCHOR,'    # V228_NO_RESULT_READ: remain pre-result by deadline and source guards.\n')
    pre=pre.replace(FORMAL_ANCHOR,FORMAL_REPLACEMENT)
    # First-forecast freeze only; no post-result history or past-data mutation.
    pre+='\nprint("V228_SITE_ONLY_FIRST_FREEZE_NO_RESULT_INPUT", json.dumps({"new_snapshots":snapshots,"day":TODAY},sort_keys=True))\n'
    ast.parse(pre)
    return pre


def check_formal_closed(root: Path):
    status=root/'data/formal_status.json'
    if not status.is_file():
        raise AssertionError('V228_FORMAL_GUARD_FILE_MISSING')
    d=json.loads(status.read_text(encoding='utf8'))
    g=d.get('guards') or {}
    if not all(g.get(k) is False for k in ('results_seen','unlock','scoring')) or g.get('RESULT_UNLOCK_TOKEN') is not None:
        raise AssertionError('V228_FORMAL_LANE_NOT_CLOSED_NO_SITE_FREEZE')
    if d.get('connected') is True and (d.get('formalFirst100') or {}).get('races',0)>0:
        # Guarding this lane matters more than additional site-reference examples.
        raise AssertionError('V228_FORMAL_FRESH_ACTIVE_NO_SITE_RESCUE')


def run(root: Path) -> None:
    root=root.resolve()
    check_formal_closed(root)
    raw=(root/SOURCE).read_text(encoding='utf8')
    code=build_frozen_source(raw)
    # There is no network or results API in the source-only V133 freeze loop.
    # Prevent local result/payout/formal file reads even on unforeseen code paths.
    orig_text, orig_bytes=Path.read_text,Path.read_bytes
    forbidden={'site_results','results','payout','payouts','formal_predictions','formal'}
    def safe_parts(path:Path):
        if any(x in forbidden for x in path.parts):
            raise RuntimeError('V228_FORBIDDEN_INPUT_READ_'+str(path))
    def guarded_text(path:Path,*a,**kw):
        safe_parts(path)
        return orig_text(path,*a,**kw)
    def guarded_bytes(path:Path,*a,**kw):
        safe_parts(path)
        return orig_bytes(path,*a,**kw)
    import os
    cwd=os.getcwd()
    os.chdir(root)
    try:
        Path.read_text=guarded_text
        Path.read_bytes=guarded_bytes
        exec(compile(code,'V228_PINNED_SITE_PRE_RESULT_ONLY','exec'), {'__name__':'__main__'})
    finally:
        Path.read_text=orig_text
        Path.read_bytes=orig_bytes
        os.chdir(cwd)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',default='.')
    args=a.parse_args()
    run(Path(args.root))
