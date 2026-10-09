from pathlib import Path
from datetime import datetime,timezone,timedelta
from tempfile import TemporaryDirectory
import importlib.util,sys,json
script=Path(__file__).resolve().parents[1]/'scripts/site_v183_audit.py' if (Path(__file__).resolve().parents[1]/'scripts/site_v183_audit.py').exists() else Path(__file__).parent/'site_v183_audit.py'
spec=importlib.util.spec_from_file_location('v183',script)
m=importlib.util.module_from_spec(spec);sys.modules['v183']=m;spec.loader.exec_module(m)
assert m.band(1000)=='10to20' and m.band(2000)=='10to20' and m.band(2001)=='20to50'
assert m.classify('1-2-3',['1-2-4'])=='third_missing'
assert m.classify('1-2-3',['2-1-3'])=='head_missing'
assert m.classify('1-2-3',['1-2-4','1-4-3'])=='pairing_miss'
with TemporaryDirectory() as d:
  root=Path(d);key='20261010-01-03'
  (root/'data/site_tail_shadow_v180/predictions').mkdir(parents=True)
  (root/'data/site_prediction_snapshots').mkdir(parents=True)
  (root/'data/site_results').mkdir(parents=True)
  pairs=[f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3]
  ranked=[{'combo':v,'score':(120-i)/sum(range(1,121))} for i,v in enumerate(pairs)]
  base=pairs[:10];source_time='2026-10-10T01:55:00+00:00';commit='2026-10-10T01:57:00+00:00'
  data={'schema_version':'boat-edge-v180-site-reference-future-shadow-v1','scope':m.SCOPE,
        'race_key':key,'candidate_id':m.CANDIDATE,'fresh_validation_pass':False,'production_adoption':False,
        'guards':{'results_seen':False,'unlock':False,'scoring':False},
        'source_sha256':'a'*64,'source_race_sha256':'b'*64,
        'source_first_saved_at':source_time,'source_saved_at':source_time,'baseline_top10':base,
        'candidate_ranked_120':ranked}
  for n in m.MODES:
    data[f'baseline_top{n}']=base[:n]
    data[f'candidate_top{n}']=pairs[:n]
  pred=root/'data/site_tail_shadow_v180/predictions'/f'{key}.json'
  pred.write_text(json.dumps(data));(root/'data/site_prediction_snapshots'/f'{key}.json').write_text(json.dumps({'race_key':key,'deadline':'11:00'}))
  def lookup(root,relative):return {'commit':'c'*64,'time':commit}
  p=m.evaluate(root,lookup);assert p['settled_races']==0 and p['pending_results']==1
  (root/'data/site_results'/f'{key}.json').write_text(json.dumps({'status':'confirmed','trifecta':pairs[0],'trifecta_payout_yen_per_100':1540}))
  p=m.evaluate(root,lookup);assert p['settled_races']==1 and p['bands']['10to20']['baseline_hits']['10']==1
  assert p['bands']['10to20']['candidate_hits']['10']==1
  assert m.evaluate(root,lookup)==m.evaluate(root,lookup)
  bad=dict(data);bad['source_saved_at']='2026-10-10T02:20:00+00:00'
  pred.write_text(json.dumps(bad))
  p=m.evaluate(root,lookup);assert p['settled_races']==0 and len(p['invalid_shadows'])==1
  pred.write_text(json.dumps(data))
  p=m.evaluate(root,lambda *args:None);assert p['settled_races']==0 and p['invalid_shadows'][0]['reason']=='NO_INDEPENDENT_ADDITION_COMMIT'
print('V183_TEST_FUTURE_ONLY_NO_EARLY_RESULT_READ_BANDS_PRECOMMIT_TAMPER_PASS')
