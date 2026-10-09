#!/usr/bin/env python3
"""V178: strict formal source attestation and visible consumer parity; preserve producer/weights/history."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args()
base=Path(a.root)
path=base/'index.html'
s=path.read_text(encoding='utf-8')
old="if(!window.BoatEdgeV177?.acceptRaw?.(raw,raceKey,state.formal))continue;\n      const norm=normalizeFormalOverlay(raw);"
new="if(!window.BoatEdgeV177?.acceptRaw?.(raw,raceKey,state.formal))continue;\n      if(!await window.BoatEdgeV178?.verifyRaw?.(raw,raceKey,state.formal))continue;\n      const norm=normalizeFormalOverlay(raw);"
if old in s:
    assert s.count(old)==1,'AMBIGUOUS_V177_READER'
    s=s.replace(old,new)
elif new not in s:raise SystemExit('V178_FORMAL_READER_MISMATCH')
old="return window.BoatEdgeV177?.acceptNormalized?.(d,state.formal)===true;"
new="return window.BoatEdgeV177?.acceptNormalized?.(d,state.formal)===true &&\n    window.BoatEdgeV178?.isVerified?.(d,state.formal)===true;"
if old in s:
    assert s.count(old)==1,'AMBIGUOUS_V177_GUARD'
    s=s.replace(old,new)
elif new not in s:raise SystemExit('V178_GUARD_MISMATCH')
tag='<script src="./assets/boat_edge_v178_verified_parity.js?v=178"></script>'
if tag not in s:
    assert s.count('</body>')==1,'AMBIGUOUS_HTML'
    s=s.replace('</body>',tag+'\n</body>')
assert s.count(tag)==1
assert s.count('window.BoatEdgeV178?.verifyRaw?.(')==1
assert s.count('window.BoatEdgeV178?.isVerified?.(')==1
assert '<script src="./assets/boat_edge_v177_latest_bridge.js?v=177"></script>' in s
path.write_text(s,encoding='utf-8')
print('V178_HTML_BRIDGE_SAFE_PATCH_PASS')
