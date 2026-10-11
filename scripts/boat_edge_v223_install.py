#!/usr/bin/env python3
"""Install V223 source freshness disclosure after validated V222; site only."""
from pathlib import Path
import sys

JS='<script defer src="./assets/boat_edge_v223_source_visibility.js?v=223"></script>'
CSS='<link rel="stylesheet" href="./assets/boat_edge_v223_source_visibility.css?v=223">'
ANCHOR='<script defer src="./assets/boat_edge_v222_live_odds.js?v=222"></script>'

def install(root):
    root=Path(root)
    page=root/'index.html'
    s=page.read_text(encoding='utf8')
    if s.count(ANCHOR)!=1:raise ValueError('V223_REQUIRES_V222_ODDS_PLUGIN')
    if s.count(JS)>1 or s.count(CSS)>1:raise ValueError('V223_DUPLICATED_ASSET_TAGS')
    if JS in s and CSS not in s or CSS in s and JS not in s:raise ValueError('V223_PARTIAL_PAGE_FAIL_CLOSED')
    if JS not in s:
        s=s.replace(ANCHOR,ANCHOR+'\n'+CSS+'\n'+JS)
        page.write_text(s,encoding='utf8')
    if s.count(JS)!=1 or s.count(CSS)!=1:raise ValueError('V223_PLUGIN_TAGS_MISSING')
    for file in ('assets/boat_edge_v223_source_visibility.js','assets/boat_edge_v223_source_visibility.css'):
        if not (root/file).is_file():raise ValueError('V223_ASSET_MISSING '+file)
    print('V223_SOURCE_VISIBILITY_SITE_ONLY_READY')

if __name__=='__main__':install(sys.argv[1] if len(sys.argv)>1 else '.')
