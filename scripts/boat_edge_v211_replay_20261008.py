#!/usr/bin/env python3
"""BOAT EDGE site-reference 2026-10-08 historical observation only.
No bet ever reconstructed without independently frozen pre-result selection and scratch+calibration audit.
Does not touch formal Fresh lanes or existing data files.
"""
from pathlib import Path
import json,hashlib,datetime as dt,html
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'data'
OUT=BASE/'site_paper_sim'
OUT.mkdir(parents=True,exist_ok=True)
KEYDATE='20261008'
START=50000

def get(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None

def clock(t):
    try:
        x=dt.datetime.fromisoformat(str(t).replace('Z','+00:00'))
        return x if x.tzinfo else None
    except (ValueError,TypeError):return None

snapshots=sorted((BASE/'site_prediction_snapshots').glob(KEYDATE+'-??-??.json'))
results=sorted((BASE/'site_results').glob(KEYDATE+'-??-??.json'))
odds=sorted((BASE/'site_odds').glob(KEYDATE+'-??-??.json'))
scratch=sorted((BASE/'site_scratches_v182').glob(KEYDATE+'-??-??.json'))
cal=get(OUT/'calibration.json') or {}
cal_ok=(cal.get('status')=='VALIDATED_OOS' and cal.get('scope')=='SITE_REFERENCE_PAPER_ONLY' and cal.get('out_of_sample') is True)
mode_names={'hit':'的中重視','balance':'バランス','hole':'波乱展開','narrow':'激絞り'}
rows=[];reason_counts={};hits={k:0 for k in mode_names};evaluated={k:0 for k in mode_names}
for path in snapshots:
    s=get(path);key=path.stem
    if not s or s.get('race_key')!=key:
        reason_counts['スナップ不一致']=reason_counts.get('スナップ不一致',0)+1;continue
    audit=get(BASE/'site_prediction_audit'/path.name) or {}
    verified=(s.get('snapshot_window')=='FINAL_15M' and all(s.get('guards',{}).get(k) is False for k in ('results_seen','unlock','scoring'))
        and isinstance(s.get('minutes_to_deadline'),(int,float)) and 0<=s['minutes_to_deadline']<=16
        and audit.get('pass') is True and audit.get('latest_snapshot_sha256')==hashlib.sha256(path.read_bytes()).hexdigest())
    if not verified:
        reason_counts['保存監査不一致']=reason_counts.get('保存監査不一致',0)+1;continue
    result=get(BASE/'site_results'/path.name) or {}
    confirmed=result.get('race_key')==key and result.get('status')=='confirmed' and isinstance(result.get('trifecta'),str)
    win=result.get('trifecta') if confirmed else None
    modes={};picks={}
    for m in mode_names:
        ts=(s.get('modes',{}).get(m) or {}).get('tickets') or []
        picks[m]=[x.get('combo') for x in ts if isinstance(x,dict) and isinstance(x.get('combo'),str)]
        if confirmed and picks[m]:
            evaluated[m]+=1
            modes[m]=(win in picks[m])
            if modes[m]:hits[m]+=1
        else:modes[m]=None
    rows.append({'race_key':key,'venue':s.get('venue','未取得'),'race_no':s.get('race_no'),'deadline':s.get('deadline'),'saved_at':s.get('saved_at'),'mins_before_deadline':s.get('minutes_to_deadline'),
                 'odds_saved_with_snapshot':bool(s.get('odds_sha256')),'official_result_confirmed':confirmed,'winner':win,
                 'top3':picks['hit'][:3],'mode_hits':modes})
# V209 prospective gate: no 10/8 source-bound scratch evidence and no verified OOS calibration => every race is NO BET.
# A hypothetical later correction must never rewrite this replay into an observed executed paper wager.
bets=[]
reason='欠場・取消の10/8当時の確認証跡なし' if len(scratch)==0 else ('独立未見校正の合格証跡なし' if not cal_ok else '事前確定購入台帳なし')
report={
 'schema':'boat-edge-v210-20261008-replay-v1','scope':'SITE_REFERENCE_HISTORICAL_DIAGNOSTIC_NOT_FORMAL_FRESH',
 'date':'2026-10-08','timestamp_policy':'immutable predictions only, results opened solely for retrospective descriptive scoring',
 'source_counts':{'frozen_snapshots':len(snapshots),'verified_snapshots':len(rows),'snapshot_audit_rejects':len(snapshots)-len(rows),'odds_files':len(odds),'result_files':len(results),'scratch_evidence_files':len(scratch)},
 'paper_simulation':{'opening_balance_yen':START,'paper_bets':len(bets),'invested_yen':0,'returned_yen':0,'closing_balance_yen':START,'roi_percent':None,
                     'skip_reason':reason,'calibration_verified':cal_ok,'no_ex_post_purchases':True,'not_real_money':True},
 'retrospective_fixed_ticket_hit':{k:{'mode':mode_names[k],'evaluated':evaluated[k],'hits':hits[k],
    'hit_rate_percent':round(hits[k]*100/evaluated[k],2) if evaluated[k] else None} for k in mode_names},
 'audit_rejection_counts':reason_counts,'races':rows
}
(OUT/'replay_20261008.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def esc(x):return html.escape(str(x))
cs=report['source_counts'];p=report['paper_simulation']
mode_cards=''.join(f'<div class="metric"><small>{esc(v["mode"])}／保存買い目</small><strong>{v["hits"]}/{v["evaluated"]}</strong><span>的中率 {"－" if v["hit_rate_percent"] is None else str(v["hit_rate_percent"])+"%"}</span></div>' for v in report['retrospective_fixed_ticket_hit'].values())
trs=[]
for r in rows:
    td=''.join('<td class="'+('hit' if r['mode_hits'][m] is True else 'miss' if r['mode_hits'][m] is False else '')+'">'+('的中' if r['mode_hits'][m] is True else '不的中' if r['mode_hits'][m] is False else '未確定')+'</td>' for m in mode_names)
    trs.append('<tr><td>'+esc(r['venue'])+' '+esc(r['race_no'])+'R</td><td>'+esc('/'.join(r['top3']))+'</td><td>'+esc(r['winner'] or '結果未確認')+'</td>'+td+'</tr>')
page='''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>10/8 AI自走リプレイ｜BOAT EDGE</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;color:#18314e;background:#f2f6fc}body{max-width:1050px;margin:0 auto;padding:14px 14px 50px}a{color:#1264aa}header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;border-bottom:2px solid #bdd2e8;padding:11px 0}h1{font-size:24px;margin:23px 0 4px}p{line-height:1.65}small,.minor{color:#607990}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:15px 0}.metric{background:white;border:1px solid #d8e4ef;border-radius:10px;padding:11px;display:grid;gap:5px}.metric strong{font-size:22px;font-variant-numeric:tabular-nums}.metric span{font-size:12px}.warn{padding:12px;border:1px solid #e9d397;background:#fff9e9;border-radius:10px;font-size:13px}.panel{background:#fff;padding:15px;border-radius:12px;border:1px solid #dae5ed;margin-top:15px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px 8px;border-bottom:1px solid #e6eef5;text-align:center}th{background:#eaf2fa;position:sticky;top:0}.scroll{overflow:auto;max-height:500px}.hit{color:#16784a;font-weight:900}.miss{color:#8392a3}h2{font-size:17px}.note{font-size:12px;color:#607990}.stats{display:flex;gap:9px;flex-wrap:wrap;font-size:12px} .stats b{color:#194d82}@media(max-width:500px){body{padding:10px}.grid{grid-template-columns:repeat(2,1fr)}.metric strong{font-size:19px}table{min-width:700px}h1{font-size:20px}}</style></head><body>
<header><strong>BOAT EDGE / AI自走シミュレーション</strong><nav><a href="./ai-simulation.html">現在の自走状況</a> · <a href="./">サイトへ戻る</a></nav></header>
<h1>2026年10月8日 リプレイ</h1><p class="minor">過去日の保存買い目と公式結果を照合。1日5万円のV211ルールで仮想購入を再判定したもの。</p>
<section class="grid"><div class="metric"><small>当日運用予算</small><strong>50,000円</strong></div><div class="metric"><small>当日未使用予算</small><strong>50,000円</strong></div><div class="metric"><small>仮想購入</small><strong>0件</strong><span>回収率は算定不可</span></div></section>
<div class="warn"><b>なぜ0件？</b> __SKIP_REASON__。保存済み予想を的中結果で後付け購入することはしない。利益ゼロは予想実力の評価ではない。</div>
<section class="panel"><h2>確認できた保存ファイル</h2><div class="stats"><span>最終予想 <b>'''+str(cs['frozen_snapshots'])+'''R</b></span><span>監査一致 <b>'''+str(cs['verified_snapshots'])+'''R</b></span><span>オッズ <b>'''+str(cs['odds_files'])+'''R</b></span><span>結果 <b>'''+str(cs['result_files'])+'''R</b></span><span>欠場確認 <b>'''+str(cs['scratch_evidence_files'])+'''R</b></span></div></section>
<section class="panel"><h2>保存済みの予想の的中状況（購入成績ではない）</h2><p class="note">締切前に固定された各予想モードの買い目を、公式の確定結果で照合した参考統計。オッズ・配分・実購入額から算出した回収率ではない。</p><div class="grid">'''+mode_cards+'''</div></section>
<section class="panel"><h2>レース別の照合</h2><div class="scroll"><table><thead><tr><th>レース</th><th>的中重視の上位3点</th><th>確定結果</th><th>的中重視</th><th>バランス</th><th>波乱</th><th>激絞り</th></tr></thead><tbody>'''+''.join(trs)+'''</tbody></table></div><p class="note">欠場確認・独立校正が不足するため、この表の的中は仮想購入した実績ではない。</p></section>
<p class="note">formal Freshとは独立したサイト参考予想の過去日観測。過去の予想・購入額・オッズを補完しない。実際の舟券購入処理なし。</p></body></html>'''
(ROOT/'ai-simulation-20261008.html').write_text(page.replace('__SKIP_REASON__',esc(reason)),encoding='utf-8')
print('V210_REPLAY_VALID '+json.dumps({k:report[k] for k in ('source_counts','paper_simulation','retrospective_fixed_ticket_hit')},ensure_ascii=False))
