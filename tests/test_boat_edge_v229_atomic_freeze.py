"""V229 local deterministic guard regressions; no network and no race-result reads."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/'scripts/boat_edge_v229_atomic_freeze.py'
spec=importlib.util.spec_from_file_location('v229',SRC)
# imports original V228 only when its installed source is separately available
import sys
sys.path.insert(0,str(SRC.parent))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
JST=timezone(timedelta(hours=9))
NOW=datetime(2026,10,11,14,15,30,tzinfo=JST).astimezone(timezone.utc)
SAVED=datetime(2026,10,11,14,15,0,tzinfo=JST).astimezone(timezone.utc)
KEY='20261011-09-09'


def iso(x):return x.isoformat()
def write(path,x):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(x,ensure_ascii=False),encoding='utf8')
def fixture(root):
    cards={}
    for role,min_age in [('race_card',5),('beforeinfo',1)]:
        cards[role]={'status':'ok','fetched_at':iso(SAVED-timedelta(minutes=min_age))}
    race={'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},
          'racers':[{'lane':i} for i in range(1,7)],'source_audit':cards}
    rp=root/'data/races'/f'{KEY}.json';write(rp,race)
    scratch={'race_key':KEY,'blocked':False,'race_card_source_status':'ok',
             'official_beforeinfo_source_status':'ok',
             'checked_at':iso(SAVED-timedelta(seconds=30))}
    write(root/'data/site_scratches_v182'/f'{KEY}.json',scratch)
    odds={'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY',
          'fetched_at':iso(SAVED-timedelta(minutes=1)),
          'trifecta_odds':{key:12.5 for key in sorted(v.COMBOS)}}
    data=json.dumps(odds,ensure_ascii=False).encode()
    sha=hashlib.sha256(data).hexdigest()
    op=root/'data/site_prediction_snapshots/odds_v214'/f'{KEY}-{sha}.json'
    op.parent.mkdir(parents=True,exist_ok=True);op.write_bytes(data)
    tickets=[{'combo':'1-2-3','stake_yen':10000,'p':11.0,'odds':12.5}]
    snapshot={'schema_version':'boat-edge-server-site-final-v123','race_key':KEY,
              'snapshot_window':'FINAL_15M','prediction_kind':'SITE_REFERENCE_V122',
              'guards':{'results_seen':False,'unlock':False,'scoring':False},
              'first_saved_at':iso(SAVED-timedelta(milliseconds=1)),
              'saved_at':iso(SAVED),'deadline':'14:20','stake_plan_version':'V141-10000-PROSPECTIVE',
              'odds_sha256':sha,'race_sha256':v.digest(rp),
              'modes':{m:{'tickets':tickets} for m in ('hit','balance','hole','narrow')}}
    write(root/'data/site_prediction_snapshots'/f'{KEY}.json',snapshot)
    return rp,op


class AtomicFreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.rp,self.op=fixture(self.root)

    def test_verifies_real_snapshot_time_sources_and_120_odds(self):
        x=v.validate(self.root,KEY,NOW)
        self.assertEqual(x['odds_combinations'],120)
        self.assertEqual(x['stake_yen_per_mode'],10000)
        self.assertEqual(x['race_sha256'],v.digest(self.rp))
        self.assertTrue(x['new_snapshot_created_this_run'])
        self.assertFalse(x['model_accuracy_proven'])

    def make_adopted_tail_fixture(self):
        from scripts.boat_edge_v254_third_tail import third_tail_candidate
        path=self.root/'data/site_prediction_snapshots'/f'{KEY}.json'
        doc=v.read_obj(path)
        hit=['1-2-3','1-2-4','1-3-2','1-4-2','2-1-3',
             '2-3-1','3-1-2','1-3-4','1-4-3','3-2-1']
        hole=['1-2-5','1-3-5','2-1-4','3-1-4','1-2-3',
              '1-2-4','1-3-2','1-4-2','2-1-3','2-3-1']
        def make(ids):
            counts=len(ids);amounts=[1000]*counts if counts==10 else [3400,3300,3300]
            return [{'combo':c,'p':float(12-i*.3),'odds':12.5,
                     'stake_yen':a} for i,(c,a) in enumerate(zip(ids,amounts))]
        chosen=third_tail_candidate(hit,hole)
        assert chosen is not None and chosen[:7]==hit[:7]
        doc['modes']={
            'hit':{'tickets':make(hit)},
            'balance':{'tickets':make(hit)},
            'hole':{'tickets':make(hole)},
            'narrow':{'tickets':make(hit[:3])},
            'tail':{'tickets':make(chosen)},
        }
        doc['default_display_mode']='tail'
        doc['mode_policy']='PROVISIONAL_V254_THIRD_TAIL10_FIXED_TOP7'
        doc['adopted_ticket_policy']='PROVISIONAL_V254_THIRD_TAIL10_FROM_PREDECLARED_FROZEN_MODES'
        doc['statistical_significance_claim']=False
        doc['formal_current_model_changed']=False
        write(path,doc)
        return path

    def test_v254_best_observed_future_mode_is_exact_source_odds_stake_attested(self):
        sp=self.make_adopted_tail_fixture()
        receipt=v.validate(self.root,KEY,NOW)
        self.assertEqual(receipt['odds_combinations'],120)
        self.assertFalse(receipt['model_accuracy_proven'])
        doc=v.read_obj(sp)
        self.assertEqual(doc['modes']['tail']['tickets'][:7],
                         doc['modes']['hit']['tickets'][:7])
        # Same frozen file must fail closed if even one speculative tail changes.
        doc['modes']['tail']['tickets'][7]['combo']='6-5-4'
        write(sp,doc)
        with self.assertRaisesRegex(AssertionError,'PROVISIONAL_TAIL_RANK_MISMATCH'):
            v.validate(self.root,KEY,NOW)

    def test_v254_tail_requires_signed_marker_and_valid_stake(self):
        sp=self.make_adopted_tail_fixture()
        original=v.read_obj(sp)
        doc=v.read_obj(sp)
        doc['default_display_mode']='hit'
        write(sp,doc)
        with self.assertRaisesRegex(AssertionError,'PROVISIONAL_TAIL_MARKER_INVALID'):
            v.validate(self.root,KEY,NOW)
        doc=v.read_obj(sp);doc.update(original)
        doc['modes']['tail']['tickets'][0]['stake_yen']=900
        write(sp,doc)
        with self.assertRaisesRegex(AssertionError,'PROVISIONAL_TAIL_STAKE_NOT_10000'):
            v.validate(self.root,KEY,NOW)
        doc=v.read_obj(sp);doc.update(original)
        doc['modes']['tail']['tickets'][0]['odds']=1.0
        write(sp,doc)
        with self.assertRaisesRegex(AssertionError,'PROVISIONAL_TAIL_TICKET_UNVERIFIED'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_stale_race_card(self):
        j=v.read_obj(self.rp)
        j['source_audit']['race_card']['fetched_at']=iso(SAVED-timedelta(minutes=17))
        write(self.rp,j)
        sp=self.root/'data/site_prediction_snapshots'/f'{KEY}.json'
        snap=v.read_obj(sp);snap['race_sha256']=v.digest(self.rp);write(sp,snap)
        with self.assertRaisesRegex(AssertionError,'RACE_CARD_NOT_VERIFIED'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_scratch_blocked(self):
        p=self.root/'data/site_scratches_v182'/f'{KEY}.json';j=v.read_obj(p);j['blocked']=True;write(p,j)
        with self.assertRaisesRegex(AssertionError,'SCRATCH_NOT_VERIFIED'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_odds_byte_modification(self):
        self.op.write_bytes(self.op.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'SIDECAR_NOT_IMMUTABLE'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_after_deadline_backfill(self):
        sp=self.root/'data/site_prediction_snapshots'/f'{KEY}.json'
        j=v.read_obj(sp);j['saved_at']=iso(SAVED+timedelta(minutes=5));write(sp,j)
        with self.assertRaisesRegex(AssertionError,'SOURCE_WINDOW_INVALID'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_unverified_stake_plan(self):
        sp=self.root/'data/site_prediction_snapshots'/f'{KEY}.json'
        j=v.read_obj(sp);j['modes']['hit']['tickets'][0]['stake_yen']=9900;write(sp,j)
        with self.assertRaisesRegex(AssertionError,'STAKE_NOT_10000'):
            v.validate(self.root,KEY,NOW)

    def test_refuse_stale_race_sha(self):
        j=v.read_obj(self.rp);j['racers'][0]['lane']=6;write(self.rp,j)
        with self.assertRaisesRegex(AssertionError,'RACE_SHA_MISMATCH'):
            v.validate(self.root,KEY,NOW)

    def test_exact_pinned_source_insertion(self):
        fake='from __future__ import annotations\n'+v.ANCHOR+'\n'+v.WINDOW+'\n'
        with self.assertRaisesRegex(AssertionError,'PROVENANCE_GUARDS_MISSING'):
            v.runner_source(fake)
        good='''# V228_NO_RESULT_READ
# V228_SITE_REFERENCE_ONLY
# V226_IMMUTABLE_ORIGINAL_SNAPSHOT
for race_path in []:
'''+v.ANCHOR+v.WINDOW
        code=v.runner_source(good)
        self.assertIn('V229_FRESH_CARD_BEFORE_FREEZE',code)
        self.assertIn('2<=mins<=10',code)
        with self.assertRaisesRegex(AssertionError,'ANCHOR_DRIFT'):
            v.runner_source(good.replace(v.WINDOW,''))

    def test_evidence_never_overwritten(self):
        p=self.root/'data/site_autopilot/v229_evidence'/f'{KEY}.json'
        v.write_once(p,{'a':1})
        with self.assertRaisesRegex(AssertionError,'ALREADY_EXISTS'):
            v.write_once(p,{'a':2})
        self.assertEqual(v.read_obj(p),{'a':1})

    def test_formal_guards_stay_closed(self):
        root=self.root
        f=root/'data/formal_status.json'
        f.parent.mkdir(parents=True,exist_ok=True)
        write(f,{'guards':{'results_seen':True,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})
        with self.assertRaisesRegex(AssertionError,'V228_FORMAL_LANE_NOT_CLOSED'):
            v.check_formal_closed(root)

if __name__=='__main__':unittest.main()
