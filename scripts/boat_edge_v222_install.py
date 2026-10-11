#!/usr/bin/env python3
"""V222 reproducible site-only install. No formal/result/payout access and no model changes."""
from __future__ import annotations
import hashlib, pathlib, sys

EXPECTED_V108_GIT_BLOB='996e0f9692c7094bf19981a6f5ed2d7d42b63350'
OLD='  const capture=!isFinalSnapshot(previous)||previous?.stake_plan_version==="V141-10000-PROSPECTIVE";'
NEW='''  // V222_LOCAL_FINAL_IMMUTABLE: keep the first FINAL_15M local prediction exactly as seen.
  // Never revise a recorded prospective ticket/odds/stake snapshot on later UI redraws.
  // A malformed existing record is not silently replaced with a fresh-looking record.
  if(previous!==null && previous!==undefined)return previous;
  const capture=true;'''
SCRIPT_ANCHOR='<script src="./assets/boat_edge_v207_first_prediction.js?v=208"></script>'
SCRIPT_TAG='<script defer src="./assets/boat_edge_v222_live_odds.js?v=222"></script>'

def blobsha(raw:bytes):
    return hashlib.sha1((f'blob {len(raw)}\0').encode()+raw).hexdigest()

def put_if_changed(path:pathlib.Path, content:bytes):
    if path.is_file() and path.read_bytes()==content:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(content)
    return True

def patch(root:pathlib.Path, *, synthetic=False):
    src=root/'assets/boat_edge_v108.js'
    raw=src.read_bytes()
    text=raw.decode('utf8')
    if 'V222_LOCAL_FINAL_IMMUTABLE' in text:
        if text.count('V222_LOCAL_FINAL_IMMUTABLE')!=1 or OLD in text or NEW not in text:
            raise ValueError('V222_EXISTING_FREEZE_PATCH_MISMATCH')
    else:
        if not synthetic and blobsha(raw)!=EXPECTED_V108_GIT_BLOB:
            raise ValueError(f'V222_V108_CHANGED_FAIL_CLOSED expected {EXPECTED_V108_GIT_BLOB} got {blobsha(raw)}')
        if text.count(OLD)!=1 or text.count('  const previous=readLocal(snapKey(key),null);')!=1:
            raise ValueError('V222_V108_FREEZE_ANCHOR_AMBIGUOUS')
        if 'window.BoatEdgeV166Invalidate=key=>' not in text or 'function saveFinalSnapshot(' not in text:
            raise ValueError('V222_V108_INTERFACE_MISSING')
        text=text.replace(OLD,NEW)
        put_if_changed(src,text.encode('utf8'))
    index=root/'index.html'
    html=index.read_text(encoding='utf8')
    if html.count(SCRIPT_TAG)>1:raise ValueError('V222_DUPLICATE_SITE_TAG')
    if SCRIPT_TAG not in html:
        if html.count(SCRIPT_ANCHOR)!=1:raise ValueError('V222_SITE_SCRIPT_ANCHOR_AMBIGUOUS')
        html=html.replace(SCRIPT_ANCHOR,SCRIPT_ANCHOR+'\n'+SCRIPT_TAG)
        put_if_changed(index,html.encode('utf8'))
    if html.count(SCRIPT_TAG)!=1:raise ValueError('V222_SCRIPT_NOT_INCLUDED')
    if not (root/'assets/boat_edge_v222_live_odds.js').is_file():raise ValueError('V222_ADDON_MISSING')
    print('V222_PINNED_FREEZE_GUARD_AND_LIVE_ODDS_DISPLAY_READY')

if __name__=='__main__':
    patch(pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.'))
