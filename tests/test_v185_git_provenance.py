from pathlib import Path
from datetime import datetime,timezone,timedelta
from tempfile import TemporaryDirectory
import sys,json,os,subprocess
SCRIPTS=Path(__file__).resolve().parent
if not (SCRIPTS/'site_v180_shadow.py').exists():SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import site_v180_shadow as v180
import site_v185_role_shadow as v185
import site_v185_score as score

KEY='20261010-01-04';JST=timezone(timedelta(hours=9))
NOW=datetime(2026,10,10,12,54,tzinfo=JST).astimezone(timezone.utc)
base=['1-2-3','1-3-2','1-2-4','1-4-2','1-2-5','2-1-3','2-3-1','3-1-2','3-2-1','1-5-2']
hole=['2-1-3','2-3-1','3-1-2','3-2-1','3-1-4','3-4-1','4-1-3','4-3-1','1-2-3','1-3-2','1-2-4','1-4-2']
rows=lambda names:[{'combo':c,'p':max(1,20-i),'odds':9999} for i,c in enumerate(names)]
snap={'schema_version':'boat-edge-server-site-final-v123','snapshot_window':'FINAL_15M','race_key':KEY,
  'prediction_kind':'SITE_REFERENCE_V122','mode_policy':v180.POLICY,
  'first_saved_at':'2026-10-10T03:50:00+00:00','saved_at':'2026-10-10T03:53:20+00:00',
  'deadline':'13:00','minutes_to_deadline':6.6667,'race_sha256':'b'*64,
  'guards':{'results_seen':False,'unlock':False,'scoring':False},
  'modes':{'hit':{'tickets':rows(base)},'hole':{'tickets':rows(hole)}}}
race={'race_key':KEY,'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
 'validation':{'result':None,'result_unlock_token':None},
 'racers':[{'lane':i,'national':{'trio_rate':21+i*9,'quinella_rate':23+i*3},
  'local':{'trio_rate':21+i*8,'quinella_rate':20+i*4},'motor':{'trio_rate':35+i*3},'boat':{'trio_rate':31+i*4}} for i in range(1,7)],
 'beforeinfo':{'racers':[{'lane':i,'exhibition_time':6.8+i*.01} for i in range(1,7)],
  'start_exhibition':[{'lane':i,'st':.10+i*.015} for i in range(1,7)]},
 'original_exhibition':{'labels':['一周','まわり足'], 'boats':[{'lane':i,'values':[36+i*.15,6.2+i*.01]} for i in range(1,7)]}}
scratch={'schema_version':'boat-edge-v182-scratch-evidence-v1','race_key':KEY,'source_date':'20261010',
 'checked_at':'2026-10-10T03:53:00+00:00','blocked':False,'suspect_lanes':[]}

def git(root,*args,date='2026-10-10T03:54:30+00:00'):
 env={**os.environ,'GIT_AUTHOR_DATE':date,'GIT_COMMITTER_DATE':date}
 p=subprocess.run(['git',*args],cwd=root,env=env,text=True,capture_output=True)
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p.stdout

with TemporaryDirectory() as temp:
 root=Path(temp)
 def w(p,data):
  d=root/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(v185.canonical(data));return d
 git(root,'init','-q');git(root,'config','user.name','Test');git(root,'config','user.email','test@example.org')
 w(f'data/site_prediction_snapshots/{KEY}.json',snap)
 w(f'data/races/{KEY}.json',race)
 w(f'data/site_scratches_v182/{KEY}.json',scratch)
 git(root,'add','.');git(root,'commit','-qm','source before race')
 assert v180.cutoff_ok(snap,KEY,NOW)
 x=v185.run(root,NOW,v180);assert x['new_shadow']==1,x
 prediction=root/f'data/site_tail_shadow_v185/predictions/{KEY}.json'
 raw=prediction.read_bytes()
 git(root,'add','.');git(root,'commit','-qm','shadow predeadline',date='2026-10-10T03:55:00+00:00')
 ok,why=score.valid_freeze(root,prediction)
 assert why is None,why
 report=score.scoring(root);assert report['awaiting_result']==1 and report['settled_verified']==0,report
 w(f'data/site_results/{KEY}.json',{'status':'confirmed','trifecta':'1-2-3','trifecta_payout_yen_per_100':1550})
 git(root,'add','.');git(root,'commit','-qm','result after race',date='2026-10-10T04:04:00+00:00')
 report=score.scoring(root)
 assert report['settled_verified']==1 and report['by_band']['10-20']['races']==1,report
 assert report['by_band']['10-20']['hit']['baseline']['10']==1
 # Changed after initial first commit: block scoring and never assign improved accuracy.
 prediction.write_bytes(raw.replace(b'V185_THIRD_ROLE',b'V186_THIRD_ROLE',1))
 report=score.scoring(root);assert report['settled_verified']==0 and report['invalid'][0]['reason']=='MUTATED_SINCE_FIRST_GIT_COMMIT',report
 prediction.write_bytes(raw)
 assert score.scoring(root)['settled_verified']==1
 # A later mutation of the source snapshot does not affect the original committed source.
 (root/f'data/site_prediction_snapshots/{KEY}.json').write_text('{}')
 assert score.scoring(root)['settled_verified']==1
 print('V185_REAL_GIT_INITIAL_COMMIT_PREDEADLINE_SHA_SOURCE_BUNDLE_PASS')
 print('V185_POST_SETTLEMENT_10TO20_SCORING_AND_MUTATION_BLOCK_PASS')
