#!/usr/bin/env python3
"""V249 additive UI assets only. Does not rewrite existing JavaScript, odds, predictions or Fresh."""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import re

STYLE = '<link rel="stylesheet" href="./assets/boat_edge_v249_focus.css?v=248">'
SCRIPT = '<script defer src="./assets/boat_edge_v249_focus.js?v=248"></script>'
MARKERS = ('<main id="raceView"','id="raceTabs"','id="tab-pred"','id="tab-before"','id="tab-scenario"','id="tab-card"','id="be241HomeResults"','data-view="raceView"')

def modify(s: str) -> str:
    for marker in MARKERS:
        if marker not in s:
            raise ValueError('V249_UNEXPECTED_SITE_STRUCTURE_'+marker)
    if s.count('</head>') != 1 or s.count('</body>') != 1:
        raise ValueError('V249_UNEXPECTED_DOCUMENT_ENDINGS')
    # Collision detection rather than overwriting another version of the asset.
    for name, expected in [('boat_edge_v249_focus.css',STYLE),('boat_edge_v249_focus.js',SCRIPT)]:
        if name in s and s.count(expected)!=1:
            raise ValueError('V249_SITE_ASSET_REF_DRIFT_'+name)
    if STYLE not in s:
        s=s.replace('</head>',STYLE+'\n</head>',1)
    if SCRIPT not in s:
        s=s.replace('</body>',SCRIPT+'\n</body>',1)
    if s.count(STYLE)!=1 or s.count(SCRIPT)!=1:
        raise ValueError('V249_DUPLICATE_ASSET_REFERENCE')
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.')
    args=p.parse_args();root=Path(args.root)
    original=(root/'index.html').read_text(encoding='utf-8')
    new=modify(original)
    if new!=original:
        (root/'index.html').write_text(new,encoding='utf-8')
        print('V249_ADD_ONLY_RACE_NAV_PUBLISHED')
    else:print('V249_ALREADY_APPLIED_NO_CLONE')

if __name__=='__main__': main()
