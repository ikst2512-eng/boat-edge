from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
loc=here.parent/'scripts/boat_edge_v220_site_ops.py'
if not loc.exists():loc=here/'boat_edge_v220_site_ops.py'
spec=importlib.util.spec_from_file_location('siteops',loc)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)
JST=timezone(timedelta(hours=9))
NOW=datetime(2026,10,10,23,5,tzinfo=timezone.utc) # October 11, 08:05 JST, before 唐津1R
DAY='20261011';KEY='20261011-23-01'

def put(root,path,data):
    f=root/path;f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')

def sample(root):
    put(root,'data/today.json',{'date':DAY,'updated_at':'2026-10-11T08:04:00+09:00','venues':[{'venue':'唐津','races':[{'race_key':KEY,'deadline':'08:35'}]}]})
    put(root,'data/site_odds/index.json',{'date':'2026-10-11','updated_at':'2026-10-11T08:04:00+09:00'})
    put(root,'data/site_autovalidation/current.json',{'schema':'BOAT_EDGE_SITE_AUTOVALIDATION_V1','status':'EVIDENCE_REVIEW_REQUIRED'})
    put(root,'data/site_paper_sim/readiness_v215_current.json',{'day_jst':DAY,'day_observed_races':0})
    put(root,'data/site_paper_sim/current.json',{'mode':'PAPER_ONLY','money':{'daily_budget_yen':50000}})
    put(root,'data/formal_status.json',{'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})

def test_all():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);sample(root)
        early=mod.compute(root,NOW)
        assert early['status']=='WAITING_FOR_PREDEADLINE' and early['scheduled_races']==1
        assert not early['recovery_dispatch_candidates']
        assert early['next_race']['watch_from_jst']=='08:20'
        middle=NOW+timedelta(minutes=20) # 08:25 JST, 10m until deadline
        incomplete=mod.compute(root,middle)
        assert incomplete['status']=='NEEDS_ATTENTION'
        assert 'predeadline_incomplete' in incomplete['issues']
        assert 'site-odds.yml' in incomplete['recovery_dispatch_candidates']
        assert 'auto-update.yml' in incomplete['recovery_dispatch_candidates']
        assert 'beforeinfo_unavailable' in incomplete['current_windows'][0]['missing_evidence']
        card={'status':'ok','fetched_at':'2026-10-11T08:23:00+09:00'}
        put(root,f'data/races/{KEY}.json',{'race_key':KEY,'meta':{'phase':'PRE_RESULT','results_seen':False,'unlock':False,'scoring':False},'racers':[{}]*6,'source_audit':{'race_card':card,'beforeinfo':card}})
        scratch={'race_key':KEY,'blocked':False,'checked_at':card['fetched_at'],
                 'race_card_source_status':'ok','official_beforeinfo_source_status':'ok'}
        put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
        combos={f'{a}-{b}-{c}':12.3 for a in range(1,7) for b in range(1,7)
                for c in range(1,7) if len({a,b,c})==3}
        odds={'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY','fetched_at':card['fetched_at'],
              'results_seen':False,'scoring':False,'available_count':120,
              'verified_official_dom_v167':True,'trifecta_odds':combos}
        put(root,f'data/site_odds/{KEY}.json',odds)
        put(root,f'data/site_prediction_snapshots/{KEY}.json',{'race_key':KEY,'snapshot_window':'FINAL_15M','odds_sha256':'x'*64})
        # V267: 120 complete is not the same as official DOM proof, and scratch
        # clearance requires independent official beforeinfo provenance.
        put(root,f'data/site_scratches_v182/{KEY}.json',{**scratch,'official_beforeinfo_source_status':'published_wait'})
        assert 'scratch_stale' in mod.compute(root,middle)['current_windows'][0]['missing_evidence']
        put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
        put(root,f'data/site_odds/{KEY}.json',{**odds,'verified_official_dom_v167':False})
        assert 'odds_official_dom_unverified' in mod.compute(root,middle)['current_windows'][0]['missing_evidence']
        put(root,f'data/site_odds/{KEY}.json',{**odds,'available_count':60})
        assert 'odds_120_incomplete' in mod.compute(root,middle)['current_windows'][0]['missing_evidence']
        put(root,f'data/site_odds/{KEY}.json',{**odds,'trifecta_odds':{**combos,'1-2-3':0}})
        assert 'odds_120_incomplete' in mod.compute(root,middle)['current_windows'][0]['missing_evidence']
        put(root,f'data/site_odds/{KEY}.json',odds)
        complete=mod.compute(root,middle)
        assert complete['status']=='MONITORING_PREDEADLINE' and complete['issues']==[]
        assert complete['recovery_dispatch_candidates']==[]
        # Formal guard changes may only create warnings, never authorize/unlock.
        put(root,'data/formal_status.json',{'guards':{'results_seen':True,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}})
        warn=mod.compute(root,middle)
        assert 'formal_status_requires_manual_safety_review' in warn['issues']
        assert warn['formal_unlock_or_scoring_authorized'] is False
        # Source postdeadline result files MUST NEVER BE READ, even if they exist.
        put(root,f'data/site_results/{KEY}.json',{'outcome':'ignored'})
        assert mod.compute(root,middle)['current_windows']==warn['current_windows']
        state=root/'data/site_ops_v220/current.json'
        assert mod.write_if_changed(state,warn)
        assert not mod.write_if_changed(state,warn)
        assert 'NOT_FORMAL_FRESH' in warn['scope']
    print('V220_TESTS_PASS waiting, window deficits, fail-closed recovery, ready sources, formal separation, deterministic reports')
def test_v271_urgent_health():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        now=NOW
        put(root,'data/health.json',{
            'updated_at':now.isoformat(),'results_seen':False,'unlock':False,'scoring':False,
            'beforeinfo_urgent_15m_targets':4,'beforeinfo_urgent_15m_ok':2,
            'beforeinfo_urgent_15m_published_wait':1,'beforeinfo_urgent_15m_error':1})
        ok=mod.compute(root,now)['official_beforeinfo_urgent_15m']
        assert ok['status']=='OBSERVED' and ok['targets']==4 and ok['ok']==2
        assert ok['published_wait']==1 and ok['error']==1
        put(root,'data/health.json',{
            'updated_at':now.isoformat(),'results_seen':False,'unlock':False,'scoring':False,
            'beforeinfo_urgent_15m_targets':4,'beforeinfo_urgent_15m_ok':2,
            'beforeinfo_urgent_15m_published_wait':1,'beforeinfo_urgent_15m_error':0})
        bad=mod.compute(root,now)['official_beforeinfo_urgent_15m']
        assert bad['status']=='UNVERIFIED_OR_STALE' and bad['ok'] is None
        put(root,'data/health.json',{
            'updated_at':now.isoformat(),'results_seen':True,'unlock':False,'scoring':False,
            'beforeinfo_urgent_15m_targets':4,'beforeinfo_urgent_15m_ok':2,
            'beforeinfo_urgent_15m_published_wait':1,'beforeinfo_urgent_15m_error':1})
        assert mod.compute(root,now)['official_beforeinfo_urgent_15m']['status']=='UNVERIFIED_OR_STALE'
    print('V271_URGENT_TELEMETRY_FAIL_CLOSED_PASS')

def test_v272_source_change_trigger():
    workflow=(here.parent/'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml').read_text(encoding='utf8')
    assert "'scripts/boat_edge_v220_site_ops.py'" in workflow
    assert "'tests/test_boat_edge_v220_site_ops.py'" in workflow
    assert 'PY_V220_INSTALL' not in workflow
    assert 'Verify current versioned site-operations code' in workflow
    print('V272_SOURCE_CHANGE_TRIGGER_PASS')

def test_v284_freeze_coverage_not_early_false_miss():
    """Only already-saved PRE_RESULT evidence may correct an early missing observation."""
    import hashlib
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);sample(root)
        hist={'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1','day_jst':DAY,
              'observations':{KEY:{
                  'race_key':KEY,'deadline':'08:35','venue':'唐津',
                  'first_seen_at':'2026-10-10T23:24:00+00:00',
                  'last_seen_at':'2026-10-10T23:24:00+00:00',
                  'reason':'snapshot_missing','reasons_seen':['snapshot_missing'],
                  'source_gaps_seen':['beforeinfo_not_ok']}}}
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',hist)
        pre=mod.freeze_coverage(root,DAY,NOW+timedelta(minutes=20))
        assert pre['observed_races']==1
        assert pre['pending_before_deadline']==1 and pre['not_found_after_deadline']==0
        after=NOW+timedelta(minutes=35)
        missed=mod.freeze_coverage(root,DAY,after)
        assert missed['not_found_after_deadline']==1
        assert missed['observed_gaps_for_currently_missing']=={'beforeinfo_not_ok':1}
        # A subsequent valid freeze must correct the initial 'snapshot_missing' state.
        race_file=root/f'data/races/{KEY}.json'
        race_file.parent.mkdir(parents=True,exist_ok=True)
        race_file.write_bytes(b'PRE_RESULT_RACER_SOURCE')
        race_sha=hashlib.sha256(race_file.read_bytes()).hexdigest()
        frozen={'race_key':KEY,'snapshot_window':'FINAL_15M',
                'saved_at':'2026-10-11T08:27:00+09:00','deadline':'08:35',
                'race_sha256':race_sha,
                'guards':{'results_seen':False,'unlock':False,'scoring':False}}
        put(root,f'data/site_prediction_snapshots/{KEY}.json',frozen)
        snap_file=root/f'data/site_prediction_snapshots/{KEY}.json'
        digest=hashlib.sha256(snap_file.read_bytes()).hexdigest()
        put(root,f'data/site_prediction_audit/{KEY}.json',{
            'race_key':KEY,'pass':True,'latest_snapshot_sha256':digest})
        recovered=mod.freeze_coverage(root,DAY,after)
        assert recovered['snapshot_present']==1
        assert recovered['sha_consistent_predeadline_snapshots']==1
        assert recovered['predeadline_snapshot_with_matching_audit']==1
        assert recovered['source_changed_after_freeze']==0
        assert recovered['early_missing_later_snapshot_present']==1
        assert recovered['not_found_after_deadline']==0
        assert recovered['v229_atomic_evidence_matched']==0
        put(root,f'data/site_autopilot/v229_evidence/{KEY}.json',{
            'schema':'BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1',
            'race_key':KEY,'snapshot_sha256':digest,'race_sha256':race_sha,
            'evidence_captured_at':'2026-10-11T08:27:05+09:00',
            'new_snapshot_created_this_run':True,
            'results_seen':False,'formal_fresh_unlock':False,'scoring':False})
        atomic=mod.freeze_coverage(root,DAY,after)
        assert atomic['v229_atomic_evidence_matched']==1
        assert atomic['v229_attestation_record_matched']==1
        # Existing outcome files must never affect this read-only metric.
        put(root,f'data/site_results/{KEY}.json',{'outcome':'FORBIDDEN_TO_READ'})
        assert mod.freeze_coverage(root,DAY,after)==atomic
        race_file.write_bytes(b'BAD_POST_FREEZE_MUTATION')
        changed=mod.freeze_coverage(root,DAY,after)
        assert changed['snapshot_or_audit_unverified']==0
        assert changed['source_changed_after_freeze']==1
        assert changed['predeadline_snapshot_with_matching_audit']==1
        assert changed['v229_attestation_record_matched']==1
        assert changed['v229_atomic_evidence_matched']==0
        assert changed['sha_consistent_predeadline_snapshots']==0
        # A recorded V229 at-freeze attestation remains a historical record;
        # it must never be misrepresented as proof current source bytes survived.
        race_file.unlink()
        missing=mod.freeze_coverage(root,DAY,after)
        assert missing['source_missing_after_freeze']==1
        assert missing['v229_attestation_record_matched']==1
        assert missing['v229_atomic_evidence_matched']==0
        race_file.write_bytes(b'PRE_RESULT_RACER_SOURCE')
        frozen['guards']['results_seen']=True
        put(root,f'data/site_prediction_snapshots/{KEY}.json',frozen)
        unsafe=mod.freeze_coverage(root,DAY,after)
        assert unsafe['snapshot_or_audit_unverified']==1
        assert unsafe['predeadline_snapshot_with_matching_audit']==0
        assert unsafe['v229_attestation_record_matched']==0
        summary=mod.compute(root,after)
        assert summary['site_prediction_freeze_observation']['today']['snapshot_present']==1
        assert summary['site_prediction_freeze_observation']['previous_day']['status']=='NO_PRE_RESULT_OBSERVATIONS'
    print('V284_NO_EARLY_MISSING_AS_FINAL_FROZEN_SHA_AUDIT_PASS')
    print('V285_SNAPSHOT_METADATA_SOURCE_DRIFT_AND_V229_RECORD_SEPARATED_PASS')

if __name__=='__main__':
    test_all()
    test_v271_urgent_health()
    test_v272_source_change_trigger()
    test_v284_freeze_coverage_not_early_false_miss()
