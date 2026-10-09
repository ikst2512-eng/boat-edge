from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, importlib.util, sys, tempfile

SRC=Path(__file__).resolve().parent/'site_v185_role_shadow.py'
if not SRC.exists():SRC=Path(__file__).resolve().parents[1]/'scripts/site_v185_role_shadow.py'
spec=importlib.util.spec_from_file_location('v185',SRC);v=importlib.util.module_from_spec(spec);sys.modules['v185']=v;spec.loader.exec_module(v)
JST=timezone(timedelta(hours=9))
KEY='20261010-01-05'
NOW=datetime(2026,10,10,10,56,tzinfo=JST).astimezone(timezone.utc)
rank=[f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3]
weights={k:(12 if k.startswith('1-') else 2) for k in rank}
sw=sum(weights.values())
base=[{'combo':k,'score':weights[k]/sw} for k in rank]
class FakeV180:
    @staticmethod
    def cutoff_ok(snap,key,now):return snap.get('race_key')==key and (now-datetime(2026,10,10,10,55,tzinfo=JST).astimezone(timezone.utc)).total_seconds()>0
    @staticmethod
    def candidate_rows(snap):return base
with tempfile.TemporaryDirectory() as td:
    root=Path(td);(root/'data/site_prediction_snapshots').mkdir(parents=True)
    (root/'data/races').mkdir(parents=True);(root/'data/site_scratches_v182').mkdir(parents=True)
    bets=[{'combo':s,'p':10.,'stake_yen':1000} for s in rank[:10]]
    snap={'schema_version':'boat-edge-server-site-final-v123','race_key':KEY,
          'saved_at':datetime(2026,10,10,10,55,tzinfo=JST).isoformat(),
          'first_saved_at':datetime(2026,10,10,10,52,tzinfo=JST).isoformat(),
          'deadline':'11:00','mode_policy':v.REQUIRED_POLICY,'modes':{'hit':{'tickets':bets}}}
    r={'race_key':KEY,'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
       'validation':{'result':None,'result_unlock_token':None},
       'racers':[{'lane':i,'national':{'trio_rate':25+i*8,'quinella_rate':20+i*3},
                  'local':{'trio_rate':20+i*9,'quinella_rate':12+i*5},
                  'motor':{'trio_rate':30+i*5},'boat':{'trio_rate':25+i*4}} for i in range(1,7)],
       'beforeinfo':{'racers':[{'lane':i,'exhibition_time':6.78+i*.025} for i in range(1,7)],
                     'start_exhibition':[{'lane':i,'st':.1+i*.02} for i in range(1,7)]},
       'original_exhibition':{'labels':['一周','まわり足'],
           'boats':[{'lane':i,'values':[36.1+i*.13,6.2+i*.03]} for i in range(1,7)]}}
    scratch={'race_key':KEY,'source_date':'20261010','checked_at':datetime(2026,10,10,10,54,tzinfo=JST).isoformat(),
            'blocked':False,'suspect_lanes':[]}
    def write(rel,obj):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False))
    write(f'data/site_prediction_snapshots/{KEY}.json',snap)
    write(f'data/races/{KEY}.json',r)
    write(f'data/site_scratches_v182/{KEY}.json',scratch)
    args=v.valid_input(root,KEY,NOW,FakeV180)
    assert args is not None
    result=v.build(*args,FakeV180)
    assert result and len(result['candidate_ranked_120'])==120
    assert len(result['candidate_top10'])==10
    assert result['candidate_id']==v.IDENT
    assert len(result['source_features_used'])>=5
    assert result['candidate_ranked_120']!=base,'No tail role influence'
    for head in range(1,7):
        h=str(head);b=sum(x['score'] for x in base if x['combo'].startswith(h+'-'))
        a=sum(x['score'] for x in result['candidate_ranked_120'] if x['combo'].startswith(h+'-'))
        assert abs(a-b)<1e-9,'Head mass must stay constant'
    assert v.canonical(result)==v.canonical(v.build(*args,FakeV180))
    out=v.run(root,NOW,FakeV180);assert out['new_shadow']==1
    target=root/'data/site_tail_shadow_v185/predictions'/f'{KEY}.json'
    first=target.read_bytes();assert v.run(root,NOW,FakeV180)['already_immutable']==1
    assert target.read_bytes()==first
    # Missing scratch or explicit scratch cannot start new prediction.
    target.unlink();scratch['blocked']=True;write(f'data/site_scratches_v182/{KEY}.json',scratch)
    assert v.run(root,NOW,FakeV180)['new_shadow']==0
    scratch['blocked']=False;write(f'data/site_scratches_v182/{KEY}.json',scratch)
    r['meta']['results_seen']=True;write(f'data/races/{KEY}.json',r)
    assert v.run(root,NOW,FakeV180)['new_shadow']==0
    r['meta']['results_seen']=False;write(f'data/races/{KEY}.json',r)
    # No old-date retrospective freeze or after-deadline freeze.
    assert v.run(root,datetime(2026,10,10,11,0,tzinfo=JST).astimezone(timezone.utc),FakeV180)['new_shadow']==0
    # Real absence of result/odds files in test - model computes without them.
    assert not (root/'data/site_results').exists() and not (root/'data/site_odds').exists()
print('V185_TEST_PRE_RESULT_ONLY_ROLE_SEPARATION_HEAD_MASS_AND_IMMUTABLE_PASS')
