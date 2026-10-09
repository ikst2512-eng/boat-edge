import importlib.util, tempfile, json
from pathlib import Path
from datetime import datetime,timezone,timedelta
s=importlib.util.spec_from_file_location('v180','scripts/site_v180_shadow.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
now=datetime(2026,10,10,3,54,tzinfo=timezone.utc) # JST 12:54, deadline 13:00
key='20261010-01-04'
base=['1-2-3','1-3-2','1-2-4','1-4-2','1-2-5','2-1-3','2-3-1','3-1-2','3-2-1','1-5-2']
hole=['2-1-3','2-3-1','3-1-2','3-2-1','3-1-4','3-4-1','4-1-3','4-3-1','1-2-3','1-3-2','1-2-4','1-4-2']
rows=lambda names:[{'combo':c,'p':max(1,20-i),'odds':9999} for i,c in enumerate(names)]
snap={'schema_version':'boat-edge-server-site-final-v123','snapshot_window':'FINAL_15M','race_key':key,
'prediction_kind':'SITE_REFERENCE_V122','mode_policy':m.POLICY,
'first_saved_at':'2026-10-10T03:50:00+00:00','saved_at':'2026-10-10T03:53:20+00:00',
'deadline':'13:00','minutes_to_deadline':6.6667,'race_sha256':'b'*64,
'guards':{'results_seen':False,'unlock':False,'scoring':False},
'modes':{'hit':{'tickets':rows(base)},'hole':{'tickets':rows(hole)}}}
assert m.cutoff_ok(snap,key,now)
sh=m.freeze(snap,key,m.canon(snap));assert len(sh['candidate_ranked_120'])==120
assert sh['candidate_ranked_120'][0]['score']>=sh['candidate_ranked_120'][-1]['score']
assert len(sh['candidate_top10'])==len(set(sh['candidate_top10']))==10
assert sh['baseline_top10']==base
assert m.canon(sh)==m.canon(m.freeze(snap,key,m.canon(snap)))
a=m.candidate_rows(snap); snap2=json.loads(json.dumps(snap));
for group in ('hit','hole'):
    for row in snap2['modes'][group]['tickets']: row['odds']=0.01
assert m.candidate_rows(snap2)==a,'odds cannot affect ordering'
assert not m.cutoff_ok(snap,key,now+timedelta(minutes=7)),'after-deadline reject'
assert not m.cutoff_ok(snap,key,now-timedelta(minutes=20)),'pre-final window reject'
assert not m.cutoff_ok(snap,key,now+timedelta(days=1)),'no retroactive prediction'
assert not m.cutoff_ok({**snap,'guards':{'results_seen':True,'unlock':False,'scoring':False}},key,now)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);src=root/'data/site_prediction_snapshots';src.mkdir(parents=True)
 (src/(key+'.json')).write_bytes(m.canon(snap))
 first=m.run(root,now);assert first['newly_frozen']==1
 dest=root/'data/site_tail_shadow_v180/predictions'/f'{key}.json'
 saved=dest.read_bytes();second=m.run(root,now);assert second['newly_frozen']==0 and dest.read_bytes()==saved
 third=m.run(root,now+timedelta(minutes=7));assert third['newly_frozen']==0 and dest.read_bytes()==saved
 assert json.loads(saved)['source_sha256']==m.sha(m.canon(snap))
print('V180_PRE_RESULT_PROSPECTIVE_SHADOW_120WAY_AND_ODDS_INDEPENDENCE_PASS')
print('V180_CUTOFF_15MIN_GUARDS_IMMUTABLE_REPLAY_PASS')
