#!/usr/bin/env python3
"""Idempotent minimal read-only navigation patch for BOAT EDGE existing home.

Never changes any race logic, odds, amounts, prediction snapshots or data requests.
"""
from pathlib import Path

FILE=Path('index.html')
START='<main id="homeView" class="view active">'
TITLE='<div class="brandtext">BOAT EDGE <small>v30</small></div>'
BUTTON='<button class="primary-btn" id="refreshTopBtn">今すぐ更新</button>'
BOTTOM='<button data-view="auditView"><span class="navicon">✓</span>監査</button>'
HEAD_LINK='<link rel="stylesheet" href="./assets/boat_edge_v241_home.css?v=241">'
SCRIPT='<script defer src="./assets/boat_edge_v241_home.js?v=241"></script>'

BLOCK='''<section class="be241-home-shortcuts" aria-label="よく使う画面">
  <nav class="be241-shortcuts" aria-label="主要メニュー">
    <a href="./index.html"><span>⌂</span>レース</a>
    <a href="./results.html" class="b241-result-shortcut"><span>✓</span>結果・払戻</a>
    <a href="./ai-simulation.html"><span>◎</span>AI自走</a>
    <a href="./second-coverage.html"><span>≋</span>精度検証</a>
  </nav>
  <div class="be241-home-results"><div class="be241-home-result-title">検証済みの的中結果 <a href="./results.html">一覧を見る ›</a></div>
  <div class="be241-home-result-list" id="be241HomeResults"><span class="be241-home-results-status">結果照合中…</span></div>
  <div class="be241-home-results-status" id="be241HomeResultsStatus">締切前固定の予想だけを表示します。</div></div>
</section>'''

def patch_text(text):
    if 'id="be241HomeResults"' in text:
        if all(x in text for x in [HEAD_LINK,SCRIPT,'href="./results.html" class="be241-nav-link"','class="be241-brand-home"']):return text
        raise ValueError('PARTIAL_V241_PATCH_DRIFT_FAIL_CLOSED')
    required=[START,TITLE,BUTTON,BOTTOM,'</head>','</body>']
    for k in required:
        if text.count(k)!=1:raise ValueError('V241_INDEX_ANCHOR_MISMATCH_'+k[:35])
    text=text.replace(START,BLOCK+'\n  '+START,1)
    text=text.replace(TITLE,'<a class="be241-brand-home" href="./index.html" aria-label="BOAT EDGE ホームへ">BOAT EDGE</a>',1)
    text=text.replace(BUTTON,'<a class="be241-header-results" href="./results.html">✓ 結果・払戻</a>\n       '+BUTTON,1)
    text=text.replace(BOTTOM,'<a href="./results.html" class="be241-nav-link"><span class="navicon">✓</span>結果</a>',1)
    text=text.replace('</head>',HEAD_LINK+'\n</head>',1)
    text=text.replace('</body>',SCRIPT+'\n</body>',1)
    return text

def main():
    before=FILE.read_text(encoding='utf-8');after=patch_text(before)
    if after!=before:FILE.write_text(after,encoding='utf-8')
    print('V241_HOME_NAV_SAFE_PATCH_'+('NOOP' if before==after else 'APPLIED'))

if __name__=='__main__':main()
