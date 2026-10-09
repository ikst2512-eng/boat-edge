from pathlib import Path
import json
src=Path('data/site_prediction_history/index.json')
if not src.exists():
    print('V182_BAND_AUDIT_INDEX_MISSING_SKIP');raise SystemExit(0)
races=list((json.loads(src.read_text(encoding='utf8')).get('races') or {}).values())
scopes=[r for r in races if r.get('prediction_kind','SITE_REFERENCE_V122').startswith('SITE_REFERENCE') and isinstance(r.get('payout'),(int,float)) and r.get('payout')>0]
terms={'under10':lambda p:p<1000,'10to20':lambda p:1000<=p<=2000,'20to50':lambda p:2000<p<=5000,'over50':lambda p:p>5000}
summary={}
for name,test in terms.items():
    rows=[r for r in scopes if test(r['payout'])]
    summary[name]={'races':len(rows),'hit10_hits':sum(bool((r.get('mode_hits') or {}).get('hit')) for r in rows),
        'balance_hits':sum(bool((r.get('mode_hits') or {}).get('balance')) for r in rows),
        'hole_hits':sum(bool((r.get('mode_hits') or {}).get('hole')) for r in rows)}
missed=[r for r in scopes if 1000<=r['payout']<=2000 and not (r.get('mode_hits') or {}).get('hit')]
# Conditional head / second / third miss. Always compare the *frozen* pre-result hit10 list.
def miss_cause(r):
    sp=Path('data/site_prediction_snapshots')/f"{r['race_key']}.json"
    try: snap=json.loads(sp.read_text(encoding='utf8'))
    except Exception:return 'NO_PRE_RESULT_SNAPSHOT_READABLE'
    if snap.get('snapshot_window')!='FINAL_15M':return 'NO_VALID_FINAL_SNAPSHOT'
    cs=[t.get('combo') for t in ((snap.get('modes') or {}).get('hit') or {}).get('tickets',[]) if t.get('combo')]
    try: head,second,third=r['winning_combo'].split('-')
    except Exception:return 'INVALID_SETTLEMENT_COMBO'
    with_head=[c.split('-') for c in cs if isinstance(c,str) and c.startswith(head+'-')]
    if not with_head:return 'HEAD_MISSING'
    s=any(x[1]==second for x in with_head)
    t=any(x[2]==third for x in with_head)
    if s and t:return 'SECOND_THIRD_PAIRING_MISS'
    if s:return 'THIRD_MISSING'
    if t:return 'SECOND_MISSING'
    return 'BOTH_TAILS_MISSING'
for r in missed:r['__v182_cause']=miss_cause(r)
causes={k:sum(r['__v182_cause']==k for r in missed) for k in sorted({r['__v182_cause'] for r in missed})}
# This list is diagnostic only: no outcome data may enter prediction training at current formal gate.
report={'schema_version':'boat-edge-v182-mid-odds-settled-site-reference-audit-v1',
 'scope':'EXISTING_POST_SETTLEMENT_SITE_HISTORY_ONLY_NOT_FORMAL_FRESH',
 'ranking_weights_changed':False,'no_odds_promotion':True,'formal_current_scoring':False,
 'denominator':len(scopes),'bands':summary,'midrange_hit10_missed_count':len(missed),'midrange_miss_causes':causes,
 'missed_keys':[{'race_key':r['race_key'],'winning_combo':r.get('winning_combo'),
 'payout_yen_per_100':r.get('payout'),'cause':r.get('__v182_cause')} for r in missed]}
out=Path('data/site_learning/v182_mid_odds_audit.json');out.parent.mkdir(parents=True,exist_ok=True)
s=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
if not out.exists() or out.read_text(encoding='utf8')!=s:out.write_text(s,encoding='utf8')
print('V182_10_20_BAND_AUDIT '+json.dumps({'races':len(scopes),'bands':summary},ensure_ascii=False))
