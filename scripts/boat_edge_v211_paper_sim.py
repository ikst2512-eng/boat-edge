#!/usr/bin/env python3
"""BOAT EDGE V211: autonomous PAPER ONLY simulation, completely separate from formal Fresh.
Selection phase never opens, imports, or lists result data.
Settlement phase only opens results for a previously frozen purchase.
"""
import argparse, datetime as dt, hashlib, json, math, pathlib, re

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBO=re.compile(r'^[1-6]-[1-6]-[1-6]$')
START=50000
MODEL='V211_DAILY_50K_PAPER_NOT_FORMAL'


def parse(ts):
    try:
        d=dt.datetime.fromisoformat(str(ts).replace('Z','+00:00'))
        return d.astimezone(UTC) if d.tzinfo else None
    except (TypeError,ValueError): return None


def read(path):
    try:return json.loads(path.read_text(encoding='utf8'))
    except (OSError,ValueError):return None


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')


def jst_day(timestamp):
    time=parse(timestamp)
    return time.astimezone(JST).strftime('%Y%m%d') if time else None


def treasury(bets,now):
    # Each JST calendar day gets its OWN virtual 50,000-yen spending allowance.
    # No previous-day cash rollover, and same-day wins do not enlarge this budget.
    day=now.astimezone(JST).strftime('%Y%m%d')
    day_bets=[x for x in bets if jst_day(x.get('decision_at'))==day]
    day_spent=sum(x['stake_yen'] for x in day_bets)
    if day_spent>START:raise SystemExit('FAIL: daily paper budget exceeded '+day)
    returned=sum(x.get('return_yen',0) for x in bets if x.get('state')=='settled')
    closed=sum(x['stake_yen'] for x in bets if x.get('state')=='settled')
    invested=sum(x['stake_yen'] for x in bets)
    outstanding=sum(x['stake_yen'] for x in bets if x.get('state')=='pending')
    return dict(start_yen=START,daily_budget_yen=START,day=day,
                today_spent_yen=day_spent,today_remaining_yen=START-day_spent,
                today_paper_races=len(day_bets), balance_yen=START-day_spent,
                invested_yen=invested,settled_stake_yen=closed,returned_yen=returned,
                profit_yen=returned-closed,
                roi_percent=round(returned/closed*100,1) if closed else None,
                pending_yen=outstanding,settled_races=sum(x.get('state')=='settled' for x in bets),
                virtual_only=True,daily_budget_resets=True,no_carryover=True)


def kelly_budget(item,available,cal):
    # Fractional Kelly across mutually exclusive 3連単 outcomes, only AFTER validation.
    # No fixed 1,000-yen cap, and no maximum number of races per day.
    raw=[]
    for score,combo,p,odd in item['picks']:
        prob=min(0.999,max(0.0,p/100*cal['probability_scale']))
        fraction=max(0.0,(prob*odd-1)/(odd-1))*0.25
        raw.append((combo,p,odd,fraction))
    sum_f=sum(t[3] for t in raw)
    if sum_f<=0 or available<100:return []
    # Spend at most today's REMAINING daily allowance. Never auto-reinvest payouts.
    target=min(available,math.floor(START*min(sum_f,1.0)/100)*100)
    if target<100:return []
    weights=[row[3]/sum_f for row in raw]
    units=target//100
    allocations=[int(math.floor(units*x)) for x in weights]
    left=units-sum(allocations)
    for i in sorted(range(len(raw)),key=lambda i:(-(units*weights[i]-allocations[i]),i))[:left]:
        allocations[i]+=1
    tickets=[{'combo':combo,'p_percent_model':round(p,4),'odds_at_snapshot':odd,
              'paper_stake_yen':u*100}
             for (combo,p,odd,_),u in zip(raw,allocations) if u>0]
    if sum(t['paper_stake_yen'] for t in tickets)>available:raise SystemExit('FAIL: Kelly overflow')
    return tickets


def deadline(key,hm):
    if not KEY.fullmatch(str(key)) or not re.fullmatch(r'\d{1,2}:\d{2}',str(hm)):return None
    try:
        a=dt.datetime.strptime(key[:8]+' '+hm,'%Y%m%d %H:%M').replace(tzinfo=JST)
        return a.astimezone(UTC)
    except ValueError:return None


def cal_ok(root,snap):
    """No 'profitable' paper wagers until independently certified OOS calibration exists."""
    d=read(root/'data/site_paper_sim/calibration.json') or {}
    return bool(d.get('status')=='VALIDATED_OOS' and d.get('scope')=='SITE_REFERENCE_PAPER_ONLY'
        and d.get('model_id')==snap.get('prediction_kind')
        and d.get('out_of_sample') is True and isinstance(d.get('validation_races'),int)
        and d.get('validation_races')>=100
        and isinstance(d.get('probability_scale'),(int,float))
        and .10 <= d['probability_scale'] <= 1.0
        and isinstance(d.get('roi_lower_95'),(int,float)) and d['roi_lower_95']>1.0
        and isinstance(d.get('evidence_sha256'),str)
        and re.fullmatch(r'[0-9a-f]{64}',d['evidence_sha256']))


def verified_frozen_odds(root,key,snap,taken):
    """Validate immutable PRE_RESULT odds against the frozen snapshot's byte-exact SHA."""
    digest=snap.get('odds_sha256')
    if not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):
        return None,'締切前オッズの証跡なし'
    archived=root/'data/site_prediction_snapshots'/'odds_v214'/f'{key}-{digest}.json'
    live=root/'data/site_odds'/f'{key}.json'
    source=archived if archived.is_file() else live
    try:
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:
            return None,'保存オッズSHA不一致'
        odds_doc=json.loads(raw)
    except (OSError,ValueError):
        return None,'保存オッズ原本なし'
    if not isinstance(odds_doc,dict):
        return None,'オッズ原本の内容不正'
    fetched=parse(odds_doc.get('fetched_at'))
    if (odds_doc.get('race_key')!=key or odds_doc.get('phase')!='PRE_RESULT_PURCHASE_ONLY'
            or not fetched or fetched>taken):
        return None,'オッズ取得時刻／情報源不一致'
    if not 0<=(taken-fetched).total_seconds()<=900:
        return None,'保存時点のオッズが古い'
    odds_values=odds_doc.get('trifecta_odds')
    if not isinstance(odds_values,dict):
        return None,'オッズ原本の内容不正'
    return odds_values,None


def evaluate(root,now,path):
    key=path.stem
    if not KEY.fullmatch(key):return None,'キー不正'
    raw=path.read_bytes()
    snap=read(path)
    if not isinstance(snap,dict) or snap.get('race_key')!=key:return None,'スナップ不正'
    if snap.get('snapshot_window')!='FINAL_15M':return None,'締切前保存なし'
    if snap.get('prediction_kind')!='SITE_REFERENCE_V122':return None,'モデル対象外'
    guard=snap.get('guards') or {}
    if any(guard.get(x) is not False for x in ('results_seen','unlock','scoring')):return None,'保存ガード不一致'
    due=deadline(key,snap.get('deadline'))
    taken=parse(snap.get('saved_at'))
    if not due or not taken or taken>now or not 0<=(due-taken).total_seconds()/60<=16:return None,'予想保存時刻が不適合'
    left=(due-now).total_seconds()/60
    if not 2<=left<=15:return None,'締切前の購入時間外'
    if (now-taken).total_seconds()>600:return None,'予想が10分超経過'
    audit=read(root/f'data/site_prediction_audit/{key}.json') or {}
    if audit.get('pass') is not True or audit.get('latest_snapshot_sha256')!=hashlib.sha256(raw).hexdigest():
        return None,'予想監査／SHA未一致'
    scratch=read(root/f'data/site_scratches_v182/{key}.json') or {}
    checked=parse(scratch.get('checked_at'))
    if scratch.get('race_key')!=key or scratch.get('blocked') is not False or not checked or checked>now:
        return None,'欠場・取消の照合不足'
    if (now-checked).total_seconds()>900 or scratch.get('race_card_source_status')!='ok':
        return None,'欠場・取消の照合が古い'
    # V217_ORIGINAL_ODDS_SHA_VALIDATED: do not substitute updated post-snapshot odds.
    frozen_odds,odds_error=verified_frozen_odds(root,key,snap,taken)
    if odds_error:return None,odds_error
    mode=snap.get('modes',{}).get('hit',{})
    rows=mode.get('tickets')
    if not isinstance(rows,list) or not rows:return None,'保存買い目なし'
    if not cal_ok(root,snap):return None,'予想確率の未見校正が未完了'
    cal=read(root/'data/site_paper_sim/calibration.json')
    scale=cal['probability_scale']
    picks=[]
    seen=set()
    for r in rows:
        if not isinstance(r,dict):continue
        combo=r.get('combo'); p=r.get('p');odds=r.get('odds')
        if not isinstance(combo,str) or not COMBO.fullmatch(combo) or len(set(combo.split('-')))!=3 or combo in seen:continue
        seen.add(combo)
        if not isinstance(p,(int,float)) or not isinstance(odds,(int,float)):continue
        if not math.isfinite(p) or not math.isfinite(odds) or not 0<p<100 or not 8<=odds<=25:continue
        source_odd=frozen_odds.get(combo)
        if not isinstance(source_odd,(int,float)) or not math.isfinite(source_odd):continue
        if abs(float(source_odd)-float(odds))>0.05:continue
        score=p/100*scale*odds
        if score>=1.15:picks.append((score,combo,p,odds))
    picks.sort(key=lambda x:(-x[0],x[1]))
    if not picks:return None,'条件を満たす買い目なし'
    take=picks[:3]
    ev=sum(x[0] for x in take)/len(take)
    if ev<1.20:return None,'保守EV条件未満'
    return {'key':key,'due':due,'saved_at':taken,'data_sha256':hashlib.sha256(raw).hexdigest(),
            'model':snap['prediction_kind'],'venue':snap.get('venue','-'),'race_no':snap.get('race_no','-'),
            'calibration_sha':cal['evidence_sha256'],'picks':take,'ev':ev},None


def summary(root,now,bets,scan=None):
    old=read(root/'data/site_paper_sim/current.json') or {}
    latest=(scan or old.get('scan') or {})
    active=cal_ok(root,{'prediction_kind':'SITE_REFERENCE_V122'})
    return dict(schema='boat-edge-paper-sim-v211',name='AI自走シュミレーション',version=MODEL,
                updated_at=now.isoformat(),mode='PAPER_ONLY',strategy_status='PAPER_ACTIVE' if active else 'CALIBRATION_GATE',
                calibration_status='未見確率校正合格・仮想運用中（利益保証なし）' if active else '未見確率校正待ち（条件成立までは仮想購入しない）',
                money=treasury(bets,now),total_paper_buys=len(bets),scan=latest,
                recent_bets=list(reversed(bets[-30:])),
                policy={'starting_yen':START,'stake_per_race_max_yen':None,'max_buy_races_per_day':None,'daily_budget_yen':START,'day_reset_jst':True,'fractional_kelly':0.25,
                    'stake_unit_yen':100,'allocation':'校正済み確率×保存オッズで1/4 Kelly、当日残枠内','odds_window':'8〜25倍','decision_window':'締切15〜2分前',
                    'out_of_sample_gate':'校正100R以上・下限ROI>100%・証跡必須',
                    'results_policy':'仮想購入確定後にのみ公式結果照合',
                    'risk':'本機能は研究用シミュレーション。実際の購入や利益の保証はありません。'})


def select(root,now,db):
    bets=db['bets']
    exists={x['race_key'] for x in bets}
    today=now.astimezone(JST).strftime('%Y%m%d')
    paths=sorted((root/'data/site_prediction_snapshots').glob(f'{today}-??-??.json'))
    prospective=[];reasons={}; reviews=[]; total=0
    for path in paths:
        key=path.stem
        if key in exists:continue
        data=read(path) or {}
        due=deadline(key,data.get('deadline'))
        if not due or not 2<=(due-now).total_seconds()/60<=15:continue
        total+=1
        result,why=evaluate(root,now,path)
        if result:
            prospective.append(result)
            reviews.append({'race_key':key,'venue':result['venue'],'race_no':result['race_no'],
                            'deadline':data.get('deadline'),'decision':'candidate','reason':'保存根拠・EV条件合格'})
        else:
            reasons[why]=reasons.get(why,0)+1
            reviews.append({'race_key':key,'venue':data.get('venue','－'),'race_no':data.get('race_no','－'),
                            'deadline':data.get('deadline'),'decision':'skip','reason':why})
    prospective.sort(key=lambda x:(-x['ev'],x['due'],x['key']))
    purchased=0
    for item in prospective:
        available=treasury(bets,now)['today_remaining_yen']
        if available<100:break
        cal=read(root/'data/site_paper_sim/calibration.json') or {}
        tickets=kelly_budget(item,available,cal)
        cost=sum(t['paper_stake_yen'] for t in tickets)
        if cost<100 or cost>available:continue
        bets.append(dict(id='V211-'+item['key'],race_key=item['key'],venue=item['venue'],race_no=item['race_no'],
                    model=item['model'],state='pending',decision_at=now.isoformat(),
                    prediction_saved_at=item['saved_at'].isoformat(),deadline_at=item['due'].isoformat(),
                    snapshot_sha256=item['data_sha256'],calibration_evidence_sha256=item['calibration_sha'],
                    model_ev_score=round(item['ev'],4),stake_yen=cost,tickets=tickets,
                    freeze_before_results=True,return_yen=0))
        purchased+=1
    return {'as_of':now.isoformat(),'in_window':total,'eligible':len(prospective),
            'paper_purchases':purchased,'skipped_by_reason':reasons,'reviews':reviews[-36:],
            'decision':'未見確率校正が承認されるまでは購入せず監視のみ'}


def settle(root,now,db):
    closed=0
    for x in db['bets']:
        if x.get('state')!='pending':continue
        key=x['race_key']
        due=parse(x.get('deadline_at'));decision=parse(x.get('decision_at'))
        if not due or not decision or decision>=due or not now>due+dt.timedelta(minutes=2):continue
        # Results are read ONLY for an immutable, PREVIOUSLY written, pre-deadline purchase.
        result=read(root/f'data/site_results/{key}.json')
        if not isinstance(result,dict) or result.get('race_key')!=key or result.get('status')!='confirmed':continue
        result_time=parse(result.get('fetched_at'))
        if not result_time or result_time<=decision:continue
        win=result.get('trifecta')
        pay100=result.get('trifecta_payout_yen_per_100')
        if not isinstance(win,str) or not COMBO.fullmatch(win) or not isinstance(pay100,(int,float)) or pay100<=0:continue
        total=sum(round(t['paper_stake_yen']*pay100/100) for t in x['tickets'] if t['combo']==win)
        x.update(state='settled',return_yen=total,winning_combo=win,payout_per_100_yen=pay100,
                 result_fetched_at=result_time.isoformat(),settled_at=now.isoformat())
        closed+=1
    return closed


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=['select','settle','summary'])
    ap.add_argument('--root',default='.')
    ap.add_argument('--now',default=None)
    args=ap.parse_args()
    root=pathlib.Path(args.root).resolve()
    now=parse(args.now) if args.now else dt.datetime.now(UTC)
    if now is None:ap.error('invalid --now')
    store=root/'data/site_paper_sim/ledger.json'
    db=read(store) or {'schema':'V209_PAPER_LEDGER_v1','starting_yen':START,'bets':[]}
    if db.get('schema')!='V209_PAPER_LEDGER_v1' or db.get('starting_yen')!=START:raise SystemExit('FAIL: ledger schema/start changed')
    ids=[x.get('race_key') for x in db['bets']]
    if len(ids)!=len(set(ids)):raise SystemExit('FAIL: double booking in ledger')
    if args.phase=='select':
        before=len(db['bets'])
        scan=select(root,now,db)
        current_path=root/'data/site_paper_sim/current.json'
        previous=read(current_path) or {}
        fresh=summary(root,now,db['bets'],scan)
        # Skip unchanged empty 5-minute polling writes; start each JST day with a fresh budget.
        quiet=(not scan['in_window'] and not scan['paper_purchases']
            and len(db['bets'])==before
            and previous.get('money',{}).get('day')==fresh['money']['day']
            and previous.get('strategy_status')==fresh['strategy_status']
            and previous.get('money',{}).get('today_spent_yen')==fresh['money']['today_spent_yen'])
        if not store.exists() or len(db['bets'])!=before:
            write(store,db) # immutable prospective purchases must commit before results read
        if not quiet:write(current_path,fresh)
        print('V211_SELECTION_NO_RESULT_READ',json.dumps(scan,ensure_ascii=False), 'unchanged_poll=' + str(quiet))
    elif args.phase=='settle':
        n=settle(root,now,db)
        if n:
            write(store,db)
            write(root/'data/site_paper_sim/current.json',summary(root,now,db['bets']))
        print('V211_SETTLEMENT_FROZEN_ONLY',n)
    else:
        print(json.dumps(summary(root,now,db),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
