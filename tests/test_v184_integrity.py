from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timezone,timedelta
import sys,subprocess,os,json,hashlib,importlib.util
S=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(S))
import site_v180_shadow as sh
import site_v183_audit as v183
from site_v184_integrity import verify_shadow_commit_binding

def cmd(args,cwd,env=None):
    return subprocess.run(args,cwd=cwd,env=env,text=True,capture_output=True,check=True).stdout

def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(sh.canon(x))
with TemporaryDirectory() as td:
    root=Path(td);cmd(['git','init','-q'],root);cmd(['git','config','user.email','test@example.com'],root);cmd(['git','config','user.name','Test'],root)
    key='20261010-01-03';deadline='11:00';ts='2026-10-10T01:55:00+00:00';first='2026-10-10T01:52:00+00:00'
    combos=[f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3]
    hit=[{'combo':c,'p':float(10-i),'stake_yen':1000} for i,c in enumerate(combos[:10])]
    hole=[{'combo':c,'p':float(18-i),'stake_yen':600} for i,c in enumerate(combos[30:42])]
    snap={'schema_version':'boat-edge-server-site-final-v123','snapshot_window':'FINAL_15M','race_key':key,'prediction_kind':'SITE_REFERENCE_V122','mode_policy':sh.POLICY,
        'deadline':deadline,'saved_at':ts,'first_saved_at':first,'minutes_to_deadline':5.,'race_sha256':'a'*64,'guards':{'results_seen':False,'unlock':False,'scoring':False},
        'modes':{'hit':{'tickets':hit},'hole':{'tickets':hole}}}
    src=root/'data/site_prediction_snapshots'/f'{key}.json';save(src,snap)
    freeze=sh.freeze(snap,key,src.read_bytes());dest=root/'data/site_tail_shadow_v180/predictions'/f'{key}.json';save(dest,freeze)
    saved_bytes=dest.read_bytes();expected_hash=hashlib.sha256(src.read_bytes()).hexdigest();assert freeze['source_sha256']==expected_hash
    env=dict(os.environ,GIT_AUTHOR_DATE='2026-10-10T01:56:00+00:00',GIT_COMMITTER_DATE='2026-10-10T01:56:00+00:00')
    cmd(['git','add','.'],root);cmd(['git','commit','-q','-m','freeze before deadline'],root,env)
    lookup=v183.source_commit(root,dest.relative_to(root).as_posix())
    yes,why,original=verify_shadow_commit_binding(root,dest.relative_to(root).as_posix(),dest.read_bytes(),freeze,lookup)
    assert yes and why=='PASS' and original['saved_at']==ts,(yes,why)
    result=root/'data/site_results'/f'{key}.json';save(result,{'status':'confirmed','trifecta':freeze['baseline_top10'][0],'trifecta_payout_yen_per_100':1500})
    original_report=v183.evaluate(root)
    assert original_report['settled_races']==1 and original_report['bands']['10to20']['races']==1,original_report
    changed=dict(freeze);changed['research_note']='changed AFTER frozen'
    save(dest,changed)
    bad=v183.evaluate(root)
    assert bad['settled_races']==0 and bad['invalid_shadows'][0]['reason']=='V184_SHADOW_EDITED_AFTER_FIRST_COMMIT',bad
    dest.write_bytes(saved_bytes)
    altered=dict(snap);altered['deadline']='10:00';save(src,altered)
    # V184 validates the snapshot originally COMMITTED, never the later mutable replacement.
    good=v183.evaluate(root);assert good['settled_races']==1,good
    # New commit changes the ORIGINAL source at the shadow's first adding tree: source must match hash.
    # A different candidate under the existing first-commit timestamp cannot pass.
    wrong=dict(freeze);wrong['source_sha256']='c'*64;save(dest,wrong)
    bad=v183.evaluate(root);assert bad['settled_races']==0
    dest.write_bytes(saved_bytes)
    assert v183.evaluate(root)==v183.evaluate(root)
print('V184_GIT_FIRST_ADD_BYTES_SOURCE_SHA_RECOMPUTE_MUTATION_NEGATIVE_PASS')
