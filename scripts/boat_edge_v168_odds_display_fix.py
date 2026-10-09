#!/usr/bin/env python3
"""V168 site-only fix for confirmed/fresh odds plus V167 auditor import path.
Targets exactly two files. No frozen predictions, stakes, results or payouts are altered.
"""
from __future__ import annotations
import argparse
from pathlib import Path

CORE=Path('assets/boat_edge_v108.js')
AUDIT=Path('.github/workflows/BOAT_EDGE_V167_ONE_UPLOAD.yml')
HTML=Path('index.html')
OLD_HTML='<script src="./assets/boat_edge_v108.js?v=163"></script>'
NEW_HTML='<script src="./assets/boat_edge_v108.js?v=168"></script>'

OLD_STATUS="if(postResult)return '<div class=\"be166-odds-status\">結果確定後：オッズは締切前保存時点の参考値（締切時オッズとの一致は未保証）。配分・的中判定は当時の保存記録だけで照合。</div>';"
NEW_STATUS="if(postResult)return '<div class=\"be166-odds-status\">結果確定：的中組み合わせは公式払戻から確定倍率を計算。他の買い目は確定倍率未取得として表示。保存時の予想・配分・オッズ履歴は改変しません。</div>';"
OLD_ROWS='const rows=baseRows.map(x=>({...x,odds:x.odds??(Number.isFinite(n(odds[x.combo]))?n(odds[x.combo]):null)}));'
NEW_ROWS='''const officialPay100=resultConfirmed?Number(result?.trifecta_payout_yen_per_100):NaN;
  const validFinal=resultConfirmed&&Boolean(officialResult)&&Number.isFinite(officialPay100)&&officialPay100>0;
  const rows=baseRows.map(x=>{
    // V168: independent display odds; never overwrite historical pre-race freeze.
    // On a completed race only the winning combination has a verified final price.
    const livePrice=be166OddsPrice(odds?.[x.combo]);
    const displayOdds=resultConfirmed?(validFinal&&x.combo===officialResult?officialPay100/100:null):livePrice;
    return {...x,odds:displayOdds,oddsBasis:resultConfirmed?(displayOdds!==null?'official_final':'final_unavailable'):(livePrice!==null?'fresh_official':'unavailable')};
  });'''
OLD_LABEL="<small>${hasOdds?odd.toFixed(1)+'倍':'オッズ－'}</small>"
NEW_LABEL="<small>${postResult?(hasOdds?'確定 '+odd.toFixed(1)+'倍':'確定倍率－'):(hasOdds?odd.toFixed(1)+'倍':'オッズ－')}</small>"
OLD_AUDIT='          python3 scripts/site_odds_v167_live_audit.py\n'
NEW_AUDIT='          PYTHONPATH=. python3 scripts/site_odds_v167_live_audit.py\n'

def replace_one(text, old, new, name):
    if text.count(new)==1 and text.count(old)==0:
        return text, False
    if text.count(old)!=1 or text.count(new):
        raise ValueError(f'{name}: unexpected original code or duplicate; stop before modifying')
    return text.replace(old,new,1), True

def build(core: str, audit: str):
    count=0
    for old,new,name in [(OLD_STATUS,NEW_STATUS,'settled disclosure'),
                         (OLD_ROWS,NEW_ROWS,'live/final odds mapping'),
                         (OLD_LABEL,NEW_LABEL,'ticket odds label')]:
        core,changed=replace_one(core,old,new,name);count+=changed
    audit,changed=replace_one(audit,OLD_AUDIT,NEW_AUDIT,'V167 import path');count+=changed
    required=['const frozenRows=effectiveSnap?.modes?.[mode]?.tickets||null;',
              'const serverSnap=serverRecord?.snapshot||null;',
              'const officialResult=resultConfirmed?normalizeCombo(result?.trifecta||result?.finish_order):null;',
              'async function oddsFor(key){']
    for s in required:
        if s not in core:raise ValueError('guard failed: '+s)
    assert "result?.trifecta_payout_yen_per_100" in core
    assert 'const displayOdds=resultConfirmed?' in core
    assert 'PYTHONPATH=. python3 scripts/site_odds_v167_live_audit.py' in audit
    return core,audit,count

def patch_html(html: str):
    return replace_one(html,OLD_HTML,NEW_HTML,'Safari cache-busting script version')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    p.add_argument('--apply', action='store_true')
    a=p.parse_args()
    if not (a.check or a.apply):p.error('--check or --apply required')
    before_core=CORE.read_text(encoding='utf-8')
    before_audit=AUDIT.read_text(encoding='utf-8')
    before_html=HTML.read_text(encoding='utf-8')
    new_core,new_audit,count=build(before_core,before_audit)
    new_html,changed=patch_html(before_html)
    count+=changed
    if a.apply:
        CORE.write_text(new_core,encoding='utf-8')
        AUDIT.write_text(new_audit,encoding='utf-8')
        HTML.write_text(new_html,encoding='utf-8')
    print('V168 '+('APPLIED' if a.apply else 'CHECK PASS')+f': modified anchors={count} / allowed files=3; immutable snapshots/results unchanged')

if __name__=='__main__':main()
