#!/usr/bin/env python3
"""Forward-only proof tests. All simulated timestamps and results are TEST FIXTURES, not observed returns."""
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import tempfile

HERE=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('paper_engine',HERE/'scripts/boat_edge_v211_paper_sim.py')
paper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper)
JST=dt.timezone(dt.timedelta(hours=9))
KEY='20261011-23-01'
TAKEN=dt.datetime(2026,10,11,8,22,tzinfo=JST).astimezone(dt.timezone.utc)
NOW=dt.datetime(2026,10,11,8,24,tzinfo=JST).astimezone(dt.timezone.utc)

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    path.write_text(content,encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def odds_doc(odd=13.0,fetched='2026-10-11T08:20:00+09:00',phase='PRE_RESULT_PURCHASE_ONLY'):
    return dict(race_key=KEY,phase=phase,fetched_at=fetched,trifecta_odds={'1-2-3':odd})

def prepare(root):
    live=root/'data/site_odds'/f'{KEY}.json'
    digest=write(live,odds_doc())
    archived=root/'data/site_prediction_snapshots'/'odds_v214'/f'{KEY}-{digest}.json'
    archived.parent.mkdir(parents=True,exist_ok=True)
    archived.write_bytes(live.read_bytes())
    snap=dict(race_key=KEY,snapshot_window='FINAL_15M',prediction_kind='SITE_REFERENCE_V122',
              guards={'results_seen':False,'unlock':False,'scoring':False},
              saved_at=TAKEN.isoformat(),deadline='08:35',odds_sha256=digest,
              modes={'hit':{'tickets':[{'combo':'1-2-3','p':15.0,'odds':13.0}]}},venue='唐津',race_no=1)
    snap_path=root/'data/site_prediction_snapshots'/f'{KEY}.json'
    snap_sha=write(snap_path,snap)
    write(root/'data/site_prediction_audit'/f'{KEY}.json',
          dict(pass_=True,latest_snapshot_sha256=snap_sha))
    # Keys in provenance documents must use their real schema names.
    write(root/'data/site_prediction_audit'/f'{KEY}.json',
          {'pass':True,'latest_snapshot_sha256':snap_sha})
    write(root/'data/site_scratches_v182'/f'{KEY}.json',
          dict(race_key=KEY,blocked=False,checked_at='2026-10-11T08:21:00+09:00',race_card_source_status='ok'))
    write(root/'data/site_paper_sim/calibration.json',
          dict(status='VALIDATED_OOS',scope='SITE_REFERENCE_PAPER_ONLY',model_id='SITE_REFERENCE_V122',
               out_of_sample=True,validation_races=100,probability_scale=1.0,roi_lower_95=1.05,
               evidence_sha256='a'*64))
    return live,archived,snap,snap_path

with tempfile.TemporaryDirectory() as p:
    root=pathlib.Path(p)
    live,archived,snap,snap_path=prepare(root)
    write(live,odds_doc(7.4,fetched='2026-10-11T08:23:00+09:00'))
    verified,reason=paper.verified_frozen_odds(root,KEY,snap,TAKEN)
    assert reason is None and verified['1-2-3']==13.0,(verified,reason)
    candidate,reason=paper.evaluate(root,NOW,snap_path)
    assert reason is None and len(candidate['picks'])==1 and candidate['picks'][0][3]==13.0,reason
    # Never re-price a frozen 13x selection at a newer live 7.4x price.
    saved_bytes=archived.read_bytes()
    archived.unlink()
    _,reason=paper.evaluate(root,NOW,snap_path)
    assert reason=='保存オッズSHA不一致',reason
    archived.write_bytes(saved_bytes)
    snap['modes']['hit']['tickets'][0]['odds']=14.2
    snap_sha=write(snap_path,snap)
    write(root/'data/site_prediction_audit'/f'{KEY}.json',{'pass':True,'latest_snapshot_sha256':snap_sha})
    _,reason=paper.evaluate(root,NOW,snap_path)
    assert reason=='条件を満たす買い目なし',reason
    snap['modes']['hit']['tickets'][0]['odds']=13.0
    snap_sha=write(snap_path,snap)
    write(root/'data/site_prediction_audit'/f'{KEY}.json',{'pass':True,'latest_snapshot_sha256':snap_sha})
    archived.unlink()
    write(live,odds_doc())
    verified,reason=paper.verified_frozen_odds(root,KEY,snap,TAKEN)
    assert reason is None and verified['1-2-3']==13.0,reason
    write(live,odds_doc(fetched='2026-10-11T08:23:00+09:00'))
    snap['odds_sha256']=hashlib.sha256(live.read_bytes()).hexdigest()
    _,reason=paper.verified_frozen_odds(root,KEY,snap,TAKEN)
    assert reason=='オッズ取得時刻／情報源不一致',reason
    write(live,odds_doc(fetched='2026-10-11T08:00:00+09:00'))
    snap['odds_sha256']=hashlib.sha256(live.read_bytes()).hexdigest()
    _,reason=paper.verified_frozen_odds(root,KEY,snap,TAKEN)
    assert reason=='保存時点のオッズが古い',reason
    write(live,odds_doc(phase='POST_RESULT'))
    snap['odds_sha256']=hashlib.sha256(live.read_bytes()).hexdigest()
    _,reason=paper.verified_frozen_odds(root,KEY,snap,TAKEN)
    assert reason=='オッズ取得時刻／情報源不一致',reason
print('V217_TESTS_PASS: original SHA, frozen vs changed live, odds mismatch, timestamp, age, postresult, legacy exact fallback')
