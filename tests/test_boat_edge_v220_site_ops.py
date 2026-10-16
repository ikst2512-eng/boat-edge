from __future__ import annotations
import hashlib
import subprocess
import os
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
        # Older collector data does not imply zero partial source rows.
        assert ok['partial_six_boat_source'] is None
        put(root,'data/health.json',{
            'updated_at':now.isoformat(),'results_seen':False,'unlock':False,'scoring':False,
            'beforeinfo_urgent_15m_targets':4,'beforeinfo_urgent_15m_ok':2,
            'beforeinfo_urgent_15m_published_wait':1,'beforeinfo_urgent_15m_error':1,
            'beforeinfo_urgent_15m_partial':1})
        partial=mod.compute(root,now)['official_beforeinfo_urgent_15m']
        assert partial['status']=='OBSERVED' and partial['partial_six_boat_source']==1
        # A partial count is NOT additional verified success or a fifth category.
        assert partial['targets']==4 and partial['ok']==2 and partial['published_wait']==1
        put(root,'data/health.json',{
            'updated_at':now.isoformat(),'results_seen':False,'unlock':False,'scoring':False,
            'beforeinfo_urgent_15m_targets':4,'beforeinfo_urgent_15m_ok':2,
            'beforeinfo_urgent_15m_published_wait':1,'beforeinfo_urgent_15m_error':1,
            'beforeinfo_urgent_15m_partial':2})
        contradict=mod.compute(root,now)['official_beforeinfo_urgent_15m']
        assert contradict['status']=='UNVERIFIED_OR_STALE'
        assert contradict['partial_six_boat_source'] is None
        assert contradict['ok'] is None
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
        assert missed['not_found_with_observed_gaps']==1
        assert missed['not_found_without_observed_gaps']==0
        assert missed['not_found_last_seen_outside_2_to_10m_window']==1
        assert missed['not_found_last_seen_inside_2_to_10m_window']==0
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

def test_v290_missing_source_vs_freeze_window():
    # No results/payouts; this only inspects already-saved V215 observations.
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);sample(root)
        record=lambda key,last,source_gaps:{
            'race_key':key,'deadline':'08:35','last_seen_at':last,
            'source_gaps_seen':source_gaps}
        rows={
            '20261011-23-02':record('20261011-23-02','2026-10-10T23:29:00+00:00',[]),
            '20261011-23-03':record('20261011-23-03','2026-10-10T23:24:00+00:00',[]),
            '20261011-23-04':record('20261011-23-04','2026-10-10T23:30:00+00:00',['beforeinfo_not_ok']),
            '20261011-23-05':record('20261011-23-05','BAD_TIMESTAMP',None)}
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',{
            'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1',
            'day_jst':DAY,'observations':rows})
        out=mod.freeze_coverage(root,DAY,NOW+timedelta(minutes=40))
        assert out['not_found_after_deadline']==4
        assert out['not_found_without_observed_gaps']==2
        assert out['not_found_with_observed_gaps']==2
        assert out['not_found_last_seen_inside_2_to_10m_window']==2
        assert out['not_found_last_seen_outside_2_to_10m_window']==1
        assert out['not_found_last_seen_unverified']==1
        assert out['not_found_without_gaps_inside_2_to_10m_window']==1
        assert out['observed_gaps_for_currently_missing']=={'beforeinfo_not_ok':1}
        assert 'not proof of eligibility' in out['integrity_note']
        # Today's metrics must not pretend the missing source was verified.
        summary=mod.compute(root,NOW+timedelta(minutes=40))
        assert summary['site_prediction_freeze_observation']['today']==out
    print('V290_MISSING_FREEZE_CAUSE_AND_LAST_OBSERVATION_WINDOW_PASS')

def test_v220_v216_event_nudges_only_existing_fail_closed_recovery():
    # Synthetic contract only: no live dispatch, outcome or formal access.
    wf=(here.parent/'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml').read_text(encoding='utf8')
    header=wf.split('permissions:',1)[0]
    assert header.count('  schedule:')==1
    assert "- cron: '11,26,41,56 * * * *'" in header
    assert '  workflow_run:' in header
    assert "'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'" in header
    assert '    types: [completed]' in header
    assert '    branches: [main]' in header
    job=wf.split('  site-operations:',1)[1].split('    runs-on:',1)[0]
    for marker in (
        "github.ref == 'refs/heads/main'",
        "github.event_name != 'workflow_run'",
        "github.event.workflow_run.conclusion == 'success'",
        "github.event.workflow_run.head_branch == 'main'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
    ):
        assert marker in job, marker
    verify=wf.split('      - name: Verify current versioned site-operations code',1)[1].split('      - name:',1)[0]
    assert "if: github.event_name != 'workflow_run'" in verify
    report=wf.split('      - name: Generate observed pre-result site-operations report',1)[1].split('      - name:',1)[0]
    assert "if: github.event_name != 'workflow_run'" not in report
    assert 'V220_EVENT_REPORT_FRESH_SKIP' in report
    assert 'V220_EVENT_REPORT_STALE_REFRESH_EXISTING_OWNER' in report
    assert 'git log -1 --format=%ct -- data/site_ops_v220/gate1c_current.json' in report
    assert 'report_age < 900' in report
    assert "git add -- data/site_ops_v220/current.json data/site_ops_v220/gate1c_current.json data/site_autopilot/v227_current.json" in report
    recovery=wf.split('      - name: Recover stale collectors or evidence-ready missed V229 without duplicate runs',1)[1]
    assert "--recovery-plan" in recovery
    assert 'auto-update.yml|site-odds.yml' in recovery
    assert 'BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml) cooldown=120' in recovery
    assert 'auto-update.yml|site-odds.yml) cooldown=900' in recovery
    assert 'V220_V229_ALREADY_ACTIVE_NO_DUPLICATE' in recovery
    assert '.status == "in_progress"' in recovery
    assert 'gh workflow run "$wf" --ref main' in recovery
    assert 'gh workflow run V235' not in recovery
    assert 'V220_RECOVERY_SKIPPED_STATUS_UNVERIFIABLE' in recovery
    print('V220_V216_EVENT_SAFE_RELAY_SINGLE_OWNER_PASS')

def test_v220_event_stale_report_gate_uses_original_git_commit_age():
    """Exercise the REAL V220 shell guard: fresh events skip, stale may reuse writer."""
    import textwrap
    wf=(here.parent/'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml').read_text(encoding='utf8')
    block=wf.split('      - name: Generate observed pre-result site-operations report',1)[1].split(
        '      - name: Recover stale collectors',1)[0]
    guard=textwrap.dedent(block.split('        run: |',1)[1].split(
        "          git config user.name",1)[0])
    assert 'V220_EVENT_REPORT_STALE_REFRESH_EXISTING_OWNER' in guard
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        report=root/'data/site_ops_v220/gate1c_current.json'
        report.parent.mkdir(parents=True)
        for label,age_min in (('fresh',2),('stale',45)):
            report.write_text(json.dumps({'fixture':label}),encoding='utf8')
            subprocess.run(['git','add','--','data/site_ops_v220/gate1c_current.json'],
                           cwd=root,check=True)
            at=(datetime.now(timezone.utc)-timedelta(minutes=age_min)).isoformat()
            env={**os.environ,'GIT_AUTHOR_DATE':at,'GIT_COMMITTER_DATE':at,
                 'GITHUB_EVENT_NAME':'workflow_run'}
            subprocess.run(['git','-c','user.name=Fixture',
                            '-c','user.email=test@example.invalid',
                            'commit','-qm',label],cwd=root,env=env,check=True)
            p=subprocess.run(['bash','-c',guard],cwd=root,env=env,
                             capture_output=True,text=True,timeout=8)
            assert p.returncode==0,(label,p.stderr)
            if label=='fresh':
                assert 'V220_EVENT_REPORT_FRESH_SKIP' in p.stdout,p.stdout
                assert 'STALE_REFRESH' not in p.stdout,p.stdout
            else:
                assert 'V220_EVENT_REPORT_STALE_REFRESH_EXISTING_OWNER' in p.stdout,p.stdout
                assert 'FRESH_SKIP' not in p.stdout,p.stdout
            for event in ('schedule','push'):
                scheduled=subprocess.run(['bash','-c',guard],cwd=root,
                                          env={**env,'GITHUB_EVENT_NAME':event},
                                          capture_output=True,text=True,timeout=8)
                assert scheduled.returncode==0,scheduled.stderr
                assert scheduled.stdout.strip()=='',scheduled.stdout
    # Missing report history: do not mistake it for a fresh report.
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        p=subprocess.run(['bash','-c',guard],cwd=root,
                         env={**os.environ,'GITHUB_EVENT_NAME':'workflow_run'},
                         capture_output=True,text=True,timeout=8)
        assert p.returncode==0,p.stderr
        assert 'V220_EVENT_REPORT_STALE_REFRESH_EXISTING_OWNER' in p.stdout,p.stdout
    print('V220_EVENT_REPORT_GIT_COMMIT_AGE_GATE_REAL_BASH_PASS')


def test_v220_skipped_v229_never_suppresses_source_ready_recovery():
    """10/16 10:40 skipped V229 must not veto 10:42 source-ready retry."""
    import shutil
    import subprocess

    wf=(here.parent/'.github/workflows/BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml').read_text(encoding='utf8')
    line=next((v for v in wf.splitlines() if 'jq -e --arg wf "$wf"' in v),None)
    assert line is not None
    assert 'select($wf != "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml" or .conclusion != "skipped")' in line
    assert 'V220_V229_ALREADY_ACTIVE_NO_DUPLICATE' in wf
    assert 'auto-update.yml|site-odds.yml) cooldown=900' in wf
    assert 'BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml) cooldown=120' in wf
    # Prefer executing EXACT production jq rather than reimplementing its
    # filter in Python. A local machine without jq still checks the contract.
    if shutil.which('jq'):
        expression=line.split("'",2)[1]
        now=int(datetime(2026,10,16,1,42,15,tzinfo=timezone.utc).timestamp())
        def suppressed(wf_name,conclusion):
            doc={'workflow_runs':[{'created_at':'2026-10-16T01:40:35Z',
                 'status':'completed','conclusion':conclusion}]}
            result=subprocess.run(['jq','-e','--arg','wf',wf_name,
                                   '--argjson','t',str(now),'--argjson','c','120',
                                   expression],input=json.dumps(doc),text=True,
                                  capture_output=True,check=False)
            assert result.returncode in (0,1),result.stderr
            return result.returncode==0
        v229='BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml'
        assert not suppressed(v229,'skipped')
        assert suppressed(v229,'success')
        assert suppressed(v229,'failure')
        # Collector cooldown must not change even for a skipped run.
        assert suppressed('auto-update.yml','skipped')
    print('V220_SKIPPED_V229_EXCLUDED_ACTIVE_AND_REAL_COOLDOWN_PRESERVED')


def fully_proven_pre_result_fixture(root, now):
    """Synthetic source with matching original official HTML bytes and V182 SHA."""
    stamp=(now-timedelta(minutes=1)).isoformat()
    audit={}; hashes={}
    for role,suffix in [('race_card','racelist'),('beforeinfo','beforeinfo')]:
        data=f'<html>official {KEY} {suffix} evidence</html>'.encode()
        raw=root/f'data/raw/{DAY}/23_01_{suffix}.html'
        raw.parent.mkdir(parents=True,exist_ok=True)
        raw.write_bytes(data)
        hashes[role]=hashlib.sha256(data).hexdigest()
        audit[role]={
            'status':'ok','fetched_at':stamp,'sha256':hashes[role],
            'source':f'https://www.boatrace.jp/owpc/pc/race/{suffix}?hd={DAY}&jcd=23&rno=1'}
    audit['beforeinfo']['six_boat_coverage']={'six_boat_complete':True}
    race={'race_key':KEY,
          'meta':{'date':'2026-10-11','deadline':'08:35',
                  'venue_code':'23','race_no':1,'phase':'PRE_RESULT',
                  'results_seen':False,'unlock':False,'scoring':False},
          'racers':[{'lane':lane} for lane in range(1,7)],
          'source_audit':audit}
    scratch={'race_key':KEY,'schema_version':'boat-edge-v182-scratch-evidence-v1',
             'source_date':DAY,'blocked':False,'checked_at':stamp,
             'race_card_source_status':'ok','official_beforeinfo_source_status':'ok',
             'official_beforeinfo_six_boat_complete':True,
             'suspect_lanes':[],'official_raw_flags':[],
             'race_card_sha256':hashes['race_card'],
             'beforeinfo_sha256':hashes['beforeinfo']}
    combos={f'{a}-{b}-{c}':12.3 for a in range(1,7)
            for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
    odds={'race_key':KEY,'phase':'PRE_RESULT_PURCHASE_ONLY','fetched_at':stamp,
          'results_seen':False,'scoring':False,'available_count':120,
          'verified_official_dom_v167':True,'trifecta_odds':combos}
    put(root,f'data/races/{KEY}.json',race)
    put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
    put(root,f'data/site_odds/{KEY}.json',odds)
    return race,scratch,odds


def test_v410_recover_only_strictly_source_ready_unfrozen_v229_in_2_to_10m():
    # Synthetic PRE_RESULT only: no real-race outcome, network or engine dispatch.
    name='BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml'
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        now=NOW+timedelta(minutes=25)  # 08:30, deadline 08:35
        race,scratch,odds=fully_proven_pre_result_fixture(root,now)
        card=race['source_audit']['race_card']
        stamp=card['fetched_at']
        ready=mod.compute(root,now)
        assert ready['recovery_dispatch_candidates']==[name],ready
        assert ready['current_windows'][0]['missing_evidence']==['frozen_prediction_missing_or_invalid']
        assert name not in mod.compute(root,NOW+timedelta(minutes=19))['recovery_dispatch_candidates']
        assert name not in mod.compute(root,NOW+timedelta(minutes=28,seconds=30))['recovery_dispatch_candidates']
        assert name not in mod.compute(root,NOW+timedelta(minutes=31))['recovery_dispatch_candidates']
        # No repair/overwrite of an existing frozen file, even if unusable.
        put(root,f'data/site_prediction_snapshots/{KEY}.json',{'race_key':KEY,'invalid':True})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        (root/f'data/site_prediction_snapshots/{KEY}.json').unlink()
        # Previously V220 woke V229 even for these source-invalid snapshots:
        # every status/120-count looked green but V229's raw/SHA would veto.
        for field in ('race_card_sha256','beforeinfo_sha256'):
            weak={**scratch}
            weak.pop(field)
            put(root,f'data/site_scratches_v182/{KEY}.json',weak)
            report=mod.compute(root,now)
            assert report['current_windows'][0]['missing_evidence']==['frozen_prediction_missing_or_invalid']
            assert name not in report['recovery_dispatch_candidates']
        put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
        card_good=race['source_audit']['race_card']
        put(root,f'data/races/{KEY}.json',{**race,'source_audit':{
            **race['source_audit'],'race_card':{**card_good,'sha256':'a'*64}}})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        put(root,f'data/races/{KEY}.json',race)
        raw_path=root/f'data/raw/{DAY}/23_01_beforeinfo.html'
        official_raw=raw_path.read_bytes()
        raw_path.write_bytes(official_raw+b'changed')
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        raw_path.write_bytes(official_raw)
        put(root,f'data/site_scratches_v182/{KEY}.json',{
            **scratch,'official_beforeinfo_six_boat_complete':False})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
        assert name in mod.compute(root,now)['recovery_dispatch_candidates']
        # A single missing independently confirmed source must block V229.
        put(root,f'data/races/{KEY}.json',{**race,'source_audit':{'race_card':card,
                             'beforeinfo':{'status':'published_wait','fetched_at':stamp}}})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        put(root,f'data/races/{KEY}.json',race)
        put(root,f'data/site_scratches_v182/{KEY}.json',{**scratch,'blocked':True})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        put(root,f'data/site_scratches_v182/{KEY}.json',scratch)
        put(root,f'data/site_odds/{KEY}.json',{**odds,'verified_official_dom_v167':False})
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        put(root,f'data/site_odds/{KEY}.json',odds)
        # Formal lock must fail closed even if every site source is ready.
        formal={'guards':{'results_seen':True,'unlock':False,
                          'scoring':False,'RESULT_UNLOCK_TOKEN':None},
                'formalFirst100':{'races':0}}
        put(root,'data/formal_status.json',formal)
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        formal['guards']['results_seen']=False
        formal['formalFirst100']['races']=1
        put(root,'data/formal_status.json',formal)
        assert name not in mod.compute(root,now)['recovery_dispatch_candidates']
        formal['formalFirst100']['races']=0
        put(root,'data/formal_status.json',formal)
        assert name in mod.compute(root,now)['recovery_dispatch_candidates']
    print('V410_ONLY_STRICT_EVIDENCE_READY_2_TO_10M_MISSED_V229_RECOVERY_PASS')

def test_recovery_freshness_matches_independent_freeze_boundaries():
    """A 17-minute card needs collection, not a futile V229 invocation."""
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        now=NOW+timedelta(minutes=20)  # 10 minutes before synthetic deadline
        race,scratch,odds=fully_proven_pre_result_fixture(root,now)
        fresh=race['source_audit']['race_card']
        before_fresh=race['source_audit']['beforeinfo']
        freeze='BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml'
        for age,stale in ((960,False),(961,True),(1020,True),(1200,True)):
            card={**fresh,'fetched_at':(now-timedelta(seconds=age)).isoformat()}
            put(root,f'data/races/{KEY}.json',
                {**race,'source_audit':{'race_card':card,'beforeinfo':before_fresh}})
            report=mod.compute(root,now)
            assert ('race_card_stale' in report['current_windows'][0]['missing_evidence']) is stale, age
            assert ('auto-update.yml' in report['recovery_dispatch_candidates']) is stale, age
            assert (freeze in report['recovery_dispatch_candidates']) is not stale, age
        # Beforeinfo, scratch and odds all have the independently enforced
        # 900-second bound. Do not round 901 seconds back into a false PASS.
        for age,stale in ((900,False),(901,True)):
            stamp=(now-timedelta(seconds=age)).isoformat()
            put(root,f'data/races/{KEY}.json',
                {**race,'source_audit':{'race_card':fresh,
                                      'beforeinfo':{**before_fresh,'fetched_at':stamp}}})
            put(root,f'data/site_scratches_v182/{KEY}.json',{**scratch,'checked_at':stamp})
            put(root,f'data/site_odds/{KEY}.json',{**odds,'fetched_at':stamp})
            report=mod.compute(root,now)
            gaps=report['current_windows'][0]['missing_evidence']
            for name in ('beforeinfo_stale','scratch_stale','odds_evidence_stale'):
                assert (name in gaps) is stale, (age,name)
            assert (freeze in report['recovery_dispatch_candidates']) is not stale, age
        assert mod.age_minutes((now+timedelta(seconds=1)).isoformat(),now) is None
        assert not (root/f'data/site_prediction_snapshots/{KEY}.json').exists()
    print('V220_RECOVERY_MATCHES_960S_CARD_900S_OTHER_WITHOUT_ROUNDING_PASS')


def test_gate1c_catalog_exposes_unobserved_deadlines_without_fabricating_eligibility():
    """Show unsampled races, but never turn catalog counts into eligible denominator."""
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        after=NOW+timedelta(minutes=35)  # 08:40 JST; 08:35 and 08:37 matured
        key2=f'{DAY}-23-02'
        key3=f'{DAY}-23-03'
        put(root,'data/today.json',{'date':'2026-10-11','venues':[{'races':[
            {'race_key':KEY,'deadline':'08:35'},
            {'race_key':key2,'deadline':'08:37'},
            {'race_key':key3,'deadline':'09:10'}]}]})
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',{
            'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1',
            'day_jst':DAY,
            'observations':{KEY:{'race_key':KEY,'deadline':'08:35'}}})
        # A saved-but-never-observed candidate must stay OUT of the observed
        # numerator and independent eligible denominator.
        put(root,f'data/site_prediction_snapshots/{key2}.json',{'race_key':key2})
        report=mod.gate1c_first_git_summary(root,DAY,after,lambda *_:('PASS','fake'))
        assert report['catalog_matured_races']==2,report
        assert report['catalog_matured_not_observed']==1,report
        assert report['catalog_matured_not_observed_saved']==1,report
        assert report['catalog_matured_without_snapshot']==1,report
        assert report['catalog_matured_by_hour_jst']=={'08':2},report
        assert report['catalog_matured_not_observed_by_hour_jst']=={'08':1},report
        # Advance until the previously future 09:10 race matures.
        later=mod.gate1c_first_git_summary(
            root,DAY,NOW+timedelta(minutes=70),lambda *_:('PASS','fake'))
        assert later['catalog_matured_by_hour_jst']=={'08':2,'09':1},later
        assert later['catalog_matured_not_observed_by_hour_jst']=={'08':1,'09':1},later
        assert later['eligible_save_rate_percent'] is None
        assert later['acceptance_99_percent_proven'] is False
        assert report['observed_races']==1 and report['matured_races']==1,report
        assert report['independently_source_eligible_denominator'] is None
        assert report['eligible_save_rate_percent'] is None
        assert report['acceptance_99_percent_proven'] is False
        # Duplicated keys, stale day and unsafe catalog symlinks cannot
        # manufacture a deceptively small cohort.
        bad={'date':'2026-10-11','venues':[{'races':[
            {'race_key':KEY,'deadline':'08:35'},
            {'race_key':KEY,'deadline':'08:35'}]}]}
        put(root,'data/today.json',bad)
        repeated=mod.gate1c_first_git_summary(root,DAY,after,lambda *_:('PASS','fake'))
        assert repeated['catalog_matured_races'] is None
        assert repeated['catalog_matured_not_observed'] is None
        assert repeated['catalog_matured_by_hour_jst'] is None
        assert repeated['catalog_matured_not_observed_by_hour_jst'] is None
        bad['date']='2026-10-10'
        put(root,'data/today.json',bad)
        wrong_day=mod.gate1c_first_git_summary(root,DAY,after,lambda *_:('PASS','fake'))
        assert wrong_day['catalog_matured_races'] is None
        assert wrong_day['catalog_matured_by_hour_jst'] is None
        catalog=root/'data/today.json'
        catalog.unlink()
        catalog.symlink_to(root/'data/site_prediction_snapshots'/f'{key2}.json')
        unsafe=mod.gate1c_first_git_summary(root,DAY,after,lambda *_:('PASS','fake'))
        assert unsafe['catalog_matured_races'] is None
        assert unsafe['catalog_matured_by_hour_jst'] is None
        assert unsafe['catalog_matured_not_observed_by_hour_jst'] is None
    print('GATE1C_UNOBSERVED_CATALOG_COVERAGE_NOT_ELIGIBILITY_DENOMINATOR_PASS')


def test_gate1c_previous_day_catalog_recovered_from_original_git_only():
    # Day rollover must not erase the previous day's schedule or silently
    # treat unsampled races as ineligible. All data here is synthetic.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        k2=f'{DAY}-23-02'
        original={'date':'2026-10-11','venues':[{'races':[
            {'race_key':KEY,'deadline':'08:35'},
            {'race_key':k2,'deadline':'08:37'}]}]}
        put(root,'data/today.json',original)
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',{
            'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1','day_jst':DAY,
            'observations':{KEY:{'race_key':KEY,'deadline':'08:35'}}})
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        subprocess.run(['git','add','--','data/today.json'],cwd=root,check=True)
        env={**os.environ,'GIT_AUTHOR_DATE':'2026-10-11T23:56:00+09:00',
             'GIT_COMMITTER_DATE':'2026-10-11T23:56:00+09:00'}
        git=['git','-c','user.name=Fixture',
             '-c','user.email=fixture@example.invalid','commit','-qm']
        subprocess.run(git+['previous original schedule'],cwd=root,env=env,check=True)
        original_commit=subprocess.check_output(
            ['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        # The *current* catalog now refers only to the next day.
        put(root,'data/today.json',{'date':'2026-10-12','venues':[{'races':[
            {'race_key':'20261012-23-01','deadline':'08:35'}]}]})
        subprocess.run(['git','add','--','data/today.json'],cwd=root,check=True)
        env['GIT_AUTHOR_DATE']='2026-10-12T00:25:00+09:00'
        env['GIT_COMMITTER_DATE']=env['GIT_AUTHOR_DATE']
        subprocess.run(git+['rotated next-day schedule'],cwd=root,env=env,check=True)
        at=datetime(2026,10,12,0,35,tzinfo=JST)
        report=mod.gate1c_first_git_summary(root,DAY,at,lambda *_:('PASS','fake'))
        assert report['catalog_matured_races']==2,report
        assert report['catalog_matured_not_observed']==1,report
        assert report['catalog_matured_without_snapshot']==2,report
        assert report['catalog_source_git_commit']==original_commit,report
        assert report['catalog_source_scope']=='PREVIOUS_DAY_SCHEDULE_FROM_PREMIDNIGHT_GIT'
        assert report['catalog_matured_by_hour_jst']=={'08':2},report
        assert report['independently_source_eligible_denominator'] is None
        assert report['eligible_save_rate_percent'] is None
        assert report['acceptance_99_percent_proven'] is False
        # A malformed original schedule must not be promoted as a complete
        # full-day catalog even when its Git commit timestamp is valid.
        # Put a newer pre-midnight synthetic commit on a separate fixture
        # branch (Git log follows only reachable history).
        subprocess.run(['git','checkout','-qb','test-corrupt-prev','HEAD~1'],
                       cwd=root,check=True,capture_output=True)
        put(root,'data/today.json',original|{'venues':[{'races':[
            {'race_key':KEY,'deadline':'08:35'},
            {'race_key':KEY,'deadline':'08:35'}]}]})
        env['GIT_AUTHOR_DATE']='2026-10-11T23:57:00+09:00'
        env['GIT_COMMITTER_DATE']=env['GIT_AUTHOR_DATE']
        subprocess.run(['git','add','--','data/today.json'],cwd=root,check=True)
        subprocess.run(git+['corrupt prior schedule'],cwd=root,env=env,check=True)
        bad=mod.gate1c_first_git_summary(root,DAY,at,lambda *_:('PASS','fake'))
        assert bad['catalog_matured_races'] is None,bad
        assert bad['eligible_save_rate_percent'] is None
    print('GATE1C_PREVIOUS_DAY_ORIGINAL_GIT_CATALOG_NOT_ELIGIBILITY_PASS')


def test_gate1c_first_git_sha_is_not_the_observed_denominator():
    """Pre-result V125 first-add proof is stricter than snapshot existence.

    The fixture has no source-eligible denominator. Results and Formal assets
    intentionally have no bearing on either the proof or the percent claim.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        now=NOW+timedelta(minutes=35)  # synthetic deadline 08:35 has passed
        observed={'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1','day_jst':DAY,
                  'observations':{KEY:{'race_key':KEY,'deadline':'08:35',
                                       'source_gaps_seen':[]}}}
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',observed)
        empty=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS','git-id'))
        assert empty['observed_races']==1 and empty['matured_races']==1
        assert empty['missing_after_deadline']==1
        assert empty['first_git_original_sha_proven']==0
        assert empty['eligible_save_rate_percent'] is None
        snap={'race_key':KEY,'deadline':'08:35',
              'saved_at':'2026-10-11T08:27:00+09:00',
              'guards':{'results_seen':False,'unlock':False,'scoring':False}}
        put(root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        accepted=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS','git-id'))
        assert accepted['snapshots_present']==1
        assert accepted['first_git_original_sha_proven']==1
        assert accepted['eligible_save_rate_percent'] is None
        assert accepted['acceptance_99_percent_proven'] is False
        missing_commit=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS',None))
        assert missing_commit['first_git_original_sha_proven']==0
        assert missing_commit['unverified_reasons']=={'first_git_commit_missing':1}
        rejected=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('first_git_snapshot_bytes_mismatch',None))
        assert rejected['original_not_verified']==1
        assert rejected['unverified_reasons']=={'first_git_snapshot_bytes_mismatch':1}
        # An old or late snapshot must never be promoted by a fake PASS.
        for clock in ('08:24:00','08:34:00'):
            snap['saved_at']='2026-10-11T'+clock+'+09:00'
            put(root,f'data/site_prediction_snapshots/{KEY}.json',snap)
            stale=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS','git-id'))
            assert stale['unverified_reasons']=={'outside_v229_decision_window':1}
        snap['saved_at']='2026-10-11T08:27:00+09:00'
        snap['deadline']='08:34'
        put(root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        wrong=mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS','git-id'))
        assert wrong['unverified_reasons']=={'snapshot_invalid':1}
        put(root,f'data/site_results/{KEY}.json',{'settlement':'DO_NOT_READ'})
        put(root,f'data/formal_predictions/{KEY}.json',{'formal':'DO_NOT_READ'})
        assert mod.gate1c_first_git_summary(root,DAY,now,lambda *_: ('PASS','git-id'))==wrong
        # Pre-deadline observation must not claim a negative or a proof rate.
        pending=mod.gate1c_first_git_summary(root,DAY,NOW,lambda *_: ('PASS','git-id'))
        assert pending['matured_races']==0 and pending['snapshots_present']==0
        assert pending['first_git_original_sha_proven']==0
    print('GATE1C_ONLY_REAL_FIRST_GIT_ORIGINAL_SHA_NUMERATOR_NO_FALSE_99PASS')



def test_gate1c_all_saved_snapshot_files_do_not_hide_unobserved_frozen_races():
    """Both pre-result snapshot files count even if V215 observed just one."""
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        observed={'schema':'BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1','day_jst':DAY,
                  'observations':{KEY:{'race_key':KEY,'deadline':'08:35',
                                       'source_gaps_seen':[]}}}
        put(root,f'data/site_paper_sim/readiness_history_v215/{DAY}.json',observed)
        other=f'{DAY}-23-02'
        first={'race_key':KEY,'deadline':'08:35',
               'saved_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:27:00+09:00',
               'guards':{'results_seen':False,'unlock':False,'scoring':False}}
        second={**first,'race_key':other,'deadline':'08:36',
                'saved_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:28:00+09:00'}
        for key,snap in ((KEY,first),(other,second)):
            put(root,f'data/site_prediction_snapshots/{key}.json',snap)
        at=NOW+timedelta(minutes=35)
        verify=lambda *_:('PASS','first-git-commit')
        old=mod.gate1c_first_git_summary(root,DAY,at,verify)
        full=mod.gate1c_all_saved_originals(root,DAY,at,verify)
        assert old['first_git_original_sha_proven']==1,old
        assert full['snapshot_files_seen']==2,full
        assert full['matured_snapshot_files']==2,full
        assert full['first_git_original_sha_proven']==2,full
        assert full['original_not_verified']==0,full
        assert full['independently_source_eligible_denominator'] is None
        assert full['eligible_save_rate_percent'] is None
        assert full['acceptance_99_percent_proven'] is False
        report=mod.gate1c_read_only_report(root,at,verify)
        assert report['today']['first_git_original_sha_proven']==1
        assert report['all_saved_snapshots_today']['first_git_original_sha_proven']==2
        assert report['all_saved_snapshots_today']['scope']=='ALL_SAVED_SITE_SNAPSHOT_FILES_NOT_ALL_RACES'
        # A malformed or outside-window snapshot must not inflate the count.
        second['saved_at']=f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:35:30+09:00'
        put(root,f'data/site_prediction_snapshots/{other}.json',second)
        invalid=mod.gate1c_all_saved_originals(root,DAY,at,verify)
        assert invalid['first_git_original_sha_proven']==1,invalid
        assert invalid['original_not_verified']==1,invalid
        assert invalid['unverified_reasons']=={'outside_v229_decision_window':1}
    print('GATE1C_ALL_SAVED_SITE_FIRST_GIT_SEPARATE_FROM_OBSERVED_NO_FALSE_99_PASS')


def test_gate1c_all_saved_original_rejects_symlinks_and_missing_first_git():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        base=root/'data/site_prediction_snapshots'
        base.mkdir(parents=True,exist_ok=True)
        path=base/f'{KEY}.json'
        elsewhere=root/'data/site_results/FAKE.json'
        put(root,'data/site_results/FAKE.json',{'RESULT':'DO_NOT_READ'})
        path.symlink_to(elsewhere)
        out=mod.gate1c_all_saved_originals(
            root,DAY,NOW+timedelta(minutes=35),lambda *_:('PASS','untrusted'))
        assert out['first_git_original_sha_proven']==0
        assert out['original_not_verified']==1
        assert out['unverified_reasons']=={'snapshot_invalid_or_symlink':1}
        path.unlink()
        snap={'race_key':KEY,'deadline':'08:35',
              'saved_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:27:00+09:00'}
        put(root,f'data/site_prediction_snapshots/{KEY}.json',snap)
        out=mod.gate1c_all_saved_originals(root,DAY,
                        NOW+timedelta(minutes=35),lambda *_:('PASS',None))
        assert out['first_git_original_sha_proven']==0
        assert out['unverified_reasons']=={'first_git_commit_missing':1}
        pending=mod.gate1c_all_saved_originals(root,DAY,NOW,lambda *_:('PASS','x'))
        assert pending['pending_snapshot_files']==1
        assert pending['first_git_original_sha_proven']==0
    print('GATE1C_ALL_SAVED_SYMLINK_AND_MISSING_GIT_FAIL_CLOSED_PASS')


def test_gate1c_legacy_v229_original_first_git_separate_tier():
    # Synthetic historical PRE_RESULT first-add. NEVER manufacture a new
    # V125 intrinsic receipt or retroactively rewrite a real prediction.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);sample(root)
        saved=f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:28:00+09:00'
        race_sha='a'*64;odds_sha='b'*64
        snap={'race_key':KEY,'deadline':'08:35','snapshot_window':'FINAL_15M',
              'prediction_kind':'SITE_REFERENCE_V122',
              'first_saved_at':saved,'saved_at':saved,
              'race_sha256':race_sha,'odds_sha256':odds_sha,
              'guards':{'results_seen':False,'unlock':False,'scoring':False}}
        snap_path=f'data/site_prediction_snapshots/{KEY}.json'
        audit_path=f'data/site_prediction_audit/{KEY}.json'
        proof_path=f'data/site_autopilot/v229_evidence/{KEY}.json'
        put(root,snap_path,snap)
        snap_hash=hashlib.sha256((root/snap_path).read_bytes()).hexdigest()
        audit={'schema_version':'boat-edge-final15m-audit-v125',
               'scope':'SITE_ONLY_NOT_FORMAL_FRESH','pass':True,
               'atomic_pre_result_audit':True,'race_key':KEY,'revision_count':1,
               'latest_snapshot_sha256':snap_hash,'latest_snapshot_saved_at':saved,
               'source_evidence_file':proof_path,
               'revisions':[{'atomic_pre_result_proof_sha256':'c'*64,
                   'odds_sha256_snapshot':odds_sha,'race_sha256_snapshot':race_sha,
                   'saved_at':saved,'snapshot_sha256':snap_hash}]}
        receipt={'schema':'BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1',
                 'scope':'SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS',
                 'new_snapshot_created_this_run':True,
                 'race_key':KEY,'results_seen':False,'scoring':False,
                 'formal_fresh_unlock':False,'odds_combinations':120,
                 'snapshot_sha256':snap_hash,'snapshot_saved_at':saved,
                 'race_sha256':race_sha,'odds_sha256':odds_sha,
                 'evidence_captured_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:28:01+09:00',
                 'official_beforeinfo_fetched_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:27:57+09:00',
                 'official_race_card_fetched_at':f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:27:52+09:00',
                 'odds_fetched_at':saved,'scratch_checked_at':saved}
        put(root,audit_path,audit);put(root,proof_path,receipt)
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        subprocess.run(['git','add','--',snap_path,audit_path,proof_path],cwd=root,check=True)
        env=dict(os.environ)
        env['GIT_AUTHOR_DATE']=f'{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}T08:28:02+09:00'
        env['GIT_COMMITTER_DATE']=env['GIT_AUTHOR_DATE']
        subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                        'commit','-qm','synthetic source-only immutable first Git add'],
                        cwd=root,env=env,check=True)
        status,sha=mod.gate1c_legacy_v229_original(root,KEY,snap)
        assert status=='LEGACY_V229_FIRST_GIT_PASS' and len(sha)==40,(status,sha)
        at=NOW+timedelta(minutes=35)
        full=mod.gate1c_all_saved_originals(
            root,DAY,at,lambda *_:('historical_v125_revision_mismatch',None))
        assert full['first_git_original_sha_proven']==0,full
        assert full['legacy_v229_first_git_proven_separately']==1,full
        assert full['legacy_v229_keys']==[KEY],full
        assert full['original_not_verified']==1,full
        assert full['unverified_reasons']=={'historical_v125_revision_mismatch':1},full
        assert full['eligible_save_rate_percent'] is None
        assert full['acceptance_99_percent_proven'] is False
        # A later audit alteration, even with a matching edited receipt,
        # cannot pass because the first Git bytes are immutable.
        audit['latest_snapshot_sha256']='f'*64
        put(root,audit_path,audit)
        changed=mod.gate1c_legacy_v229_original(root,KEY,snap)
        assert changed==('LEGACY_CHANGED_AFTER_FIRST_ADD',None),changed
        rejected=mod.gate1c_all_saved_originals(
            root,DAY,at,lambda *_:('historical_v125_revision_mismatch',None))
        assert rejected['legacy_v229_first_git_proven_separately']==0,rejected
        assert rejected['legacy_v229_unverified_reasons']=={'LEGACY_CHANGED_AFTER_FIRST_ADD':1}
        # And no result/formal source is ever opened, even when present.
        put(root,f'data/site_results/{KEY}.json',{'result':'NEVER_READ'})
        assert mod.gate1c_legacy_v229_original(root,KEY,snap)==changed
    print('GATE1C_LEGACY_FIRST_GIT_DISTINCT_FROM_V125_99_AND_TAMPERING_PASS')


if __name__=='__main__':
    test_all()
    test_v271_urgent_health()
    test_v272_source_change_trigger()
    test_v284_freeze_coverage_not_early_false_miss()
    test_v290_missing_source_vs_freeze_window()
    test_v220_v216_event_nudges_only_existing_fail_closed_recovery()
    test_v220_event_stale_report_gate_uses_original_git_commit_age()
    test_v220_skipped_v229_never_suppresses_source_ready_recovery()
    test_v410_recover_only_strictly_source_ready_unfrozen_v229_in_2_to_10m()
    test_recovery_freshness_matches_independent_freeze_boundaries()
    test_gate1c_catalog_exposes_unobserved_deadlines_without_fabricating_eligibility()
    test_gate1c_previous_day_catalog_recovered_from_original_git_only()
    test_gate1c_first_git_sha_is_not_the_observed_denominator()
    test_gate1c_all_saved_snapshot_files_do_not_hide_unobserved_frozen_races()
    test_gate1c_all_saved_original_rejects_symlinks_and_missing_first_git()
    test_gate1c_legacy_v229_original_first_git_separate_tier()
