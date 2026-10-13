import datetime as dt,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from boat_edge_v232_pre_result_cohort import verified,collect,SCHEMA,JST,UTC,COMBOS

NOW=dt.datetime(2026,10,11,6,8,0,tzinfo=UTC)
KEY='20261011-09-10'

def write(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root,now=NOW):
    key=KEY
    due=dt.datetime(2026,10,11,6,12,tzinfo=UTC)
    saved=due-dt.timedelta(minutes=6)
    audit_at=saved+dt.timedelta(seconds=30)
    snapkey=root/'data/site_prediction_snapshots'/f'{key}.json'
    source={'race_key':key,'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
       'racers':[{'lane':i} for i in range(1,7)],
       'source_audit':{src:{'status':'ok','fetched_at':(saved-dt.timedelta(minutes=2)).isoformat()} for src in ('race_card','beforeinfo')}}
    racesha=write(root/'data/races'/f'{key}.json',source)
    scratch={'race_key':key,'blocked':False,'race_card_source_status':'ok','official_beforeinfo_source_status':'ok',
             'checked_at':(saved-dt.timedelta(seconds=50)).isoformat()}
    write(root/'data/site_scratches_v182'/f'{key}.json',scratch)
    odds={s:float(10+i%21) for i,s in enumerate(sorted(COMBOS))}
    oddsrow={'race_key':key,'phase':'PRE_RESULT_PURCHASE_ONLY',
             'fetched_at':(saved-dt.timedelta(minutes=1)).isoformat(),'trifecta_odds':odds}
    odpath=root/'data/site_prediction_snapshots/odds_v214'/'temp.json'
    oddsha=write(odpath,oddsrow)
    odpath.rename(odpath.with_name(f'{key}-{oddsha}.json'))
    combos=list(sorted(COMBOS))[:12]
    def tickets(n):
        return [{'combo':c,'p':float(17-i/2),'odds':odds[c],
                 'stake_yen':(10000//n//100*100)+(10000-(10000//n//100*100)*n if i==0 else 0)} for i,c in enumerate(combos[:n])]
    snap={'schema_version':'boat-edge-server-site-final-v123','race_key':key,'snapshot_window':'FINAL_15M',
        'prediction_kind':'SITE_REFERENCE_V122','selection_policy':'TEST','deadline':'15:12',
        'saved_at':saved.isoformat(),'first_saved_at':saved.isoformat(),
        'race_sha256':racesha,'odds_sha256':oddsha,'stake_plan_version':'V141-10000-PROSPECTIVE',
        'guards':{'results_seen':False,'unlock':False,'scoring':False},'venue':'津',
        'modes':{mode:{'tickets':tickets(n)} for mode,n in (('hit',10),('balance',10),('hole',12),('narrow',3))}}
    snapsha=write(snapkey,snap)
    write(root/'data/site_prediction_audit'/f'{key}.json',{'pass':True,'latest_snapshot_sha256':snapsha,
          'first_audited_at':audit_at.isoformat()})
    write(root/'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},
          'formalFirst100':{'races':0}})
    return snapkey

class Cohort(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.snap=fixture(self.root)
    def tearDown(self):self.t.cleanup()
    def test_pre_result_proof_captures_head_top3_5_10_and_band(self):
        proof,why=verified(self.root,KEY,NOW)
        self.assertIsNone(why);self.assertEqual(proof['schema'],SCHEMA)
        self.assertEqual(len(proof['top3']),3);self.assertEqual(len(proof['top5']),5)
        self.assertEqual(len(proof['top10']),10)
        self.assertTrue(proof['head_top1'] in '123456')
        self.assertEqual(proof['odds_combinations_verified'],120)
        self.assertFalse(proof['paper_purchases_authorized'])
    def test_idempotent_immutable_cohort(self):
        report=collect(self.root,NOW);self.assertEqual(report['frozen_research_races_today'],1)
        saved=self.root/'data/site_autopilot/v232_cohort'/f'{KEY}.json'
        buf=saved.read_bytes();collect(self.root,NOW+dt.timedelta(seconds=4))
        self.assertEqual(buf,saved.read_bytes())
    def test_window_diagnostic_counts_without_backfilling(self):
        import datetime as dt
        report=collect(self.root,NOW)
        self.assertEqual(report['snapshot_window_diagnostic'],
                         {'total':1,'missing_deadline':0,'before_window':0,'after_window':0})
        later=collect(self.root,NOW+dt.timedelta(minutes=16))
        self.assertEqual(later['snapshot_window_diagnostic']['after_window'],1)
        self.assertEqual(later['new_research_races_this_run'],0)
        self.assertEqual(later['frozen_research_races_today'],1)
        self.assertFalse(later['accuracy_improvement_proven'])

    def test_formal_gate_not_closed_aborts_without_write(self):
        f=self.root/'data/formal_status.json';d=json.loads(f.read_text());d['guards']['unlock']=True;write(f,d)
        with self.assertRaisesRegex(RuntimeError,'FORMAL_GUARD'):collect(self.root,NOW)
        self.assertFalse((self.root/'data/site_autopilot/v232_current.json').exists())
    def test_cannot_enrol_after_deadline(self):
        d,e=verified(self.root,KEY,NOW+dt.timedelta(minutes=8));self.assertIsNone(d)
        self.assertEqual(e,'not_prospectively_in_window')
    def test_rejects_updated_race_source(self):
        f=self.root/'data/races'/f'{KEY}.json';o=json.loads(f.read_text());o['extra']='changed';write(f,o)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'race_bytes_changed_since_prediction')
    def test_source_proven_same_run_enrolment_without_prior_v125_audit(self):
        (self.root/'data/site_prediction_audit'/f'{KEY}.json').unlink()
        proof,why=verified(self.root,KEY,NOW)
        self.assertIsNone(why)
        self.assertEqual(proof['audit_evidence_type'],'V232_SELF_CONTAINED_SHA_AND_SOURCE_PRE_RESULT')
        self.assertFalse((self.root/'data/site_prediction_audit'/f'{KEY}.json').exists())
    def test_rejects_late_audit(self):
        f=self.root/'data/site_prediction_audit'/f'{KEY}.json';o=json.loads(f.read_text());o['first_audited_at']='2026-10-11T06:13:00+00:00';write(f,o)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'sha_audit_missing_or_late')
    def test_rejects_scratch_post_saved(self):
        f=self.root/'data/site_scratches_v182'/f'{KEY}.json';o=json.loads(f.read_text());o['checked_at']='2026-10-11T06:10:00+00:00';write(f,o)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'scratch_not_certified_before_prediction')
    def test_rejects_odds_sidecar_mutation(self):
        f=next((self.root/'data/site_prediction_snapshots/odds_v214').glob('*.json'))
        o=json.loads(f.read_text());o['trifecta_odds']['1-2-3']=9999;write(f,o)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'odds_sidecar_missing_or_modified')
    def test_rejects_fabricated_stake(self):
        f=self.snap;o=json.loads(f.read_text());o['modes']['hit']['tickets'][0]['stake_yen']=0
        sha=write(f,o);audit=self.root/'data/site_prediction_audit'/f'{KEY}.json';j=json.loads(audit.read_text());j['latest_snapshot_sha256']=sha;write(audit,j)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'stake_not_10000_hit')
    def test_rejects_wrong_snapshot_hash(self):
        f=self.root/'data/site_prediction_audit'/f'{KEY}.json';j=json.loads(f.read_text());j['latest_snapshot_sha256']='a'*64;write(f,j)
        d,e=verified(self.root,KEY,NOW);self.assertIsNone(d);self.assertEqual(e,'sha_audit_missing_or_late')
    def test_no_result_payout_or_formal_prediction_open(self):
        import inspect
        import boat_edge_v232_pre_result_cohort as m
        source=inspect.getsource(m)
        self.assertNotIn("root/'data/site_results'",source)
        self.assertNotIn("root/'data/payout'",source)
        self.assertNotIn("root/'data/formal_predictions'",source)

if __name__=='__main__':unittest.main()
