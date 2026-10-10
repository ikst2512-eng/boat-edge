#!/usr/bin/env python3
"""BOAT EDGE V221 conservative workflow deduplication.
Only precisely pinned workflows; no formal targets, results, wagers or site prediction writes.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path('.')
REQUIRED_REPO='ikst2512-eng/boat-edge'
REPO=os.environ.get('GITHUB_REPOSITORY','ikst2512-eng/boat-edge')
JST=dt.timezone(dt.timedelta(hours=9))
NOW=dt.datetime.now(dt.timezone.utc)
RUNS_WINDOW=dt.timedelta(hours=3)
TARGETS={
  'auto-update-5min.yml': {'sha':'72965eef4dd23705bc52043563d20c204d3c0c4b','kind':'legacy_collector'},
  'auto-update-v10.yml': {'sha':'69277f62ef62fbf2c2bad991a4899489671d266f','kind':'legacy_collector'},
  'site-v185-trigger.yml': {'sha':'452b682373a2c5fb1b07b182252a8bcfd0f741da','kind':'duplicate_research_trigger'},
}
PRIMARY={
 'auto-update.yml': 'e57cd8273fecac3026e0e16731264e59fd6cfc59',
 'BOAT_EDGE_V200_SEQUENTIAL_FRESH_FREEZE.yml':'376d55d4d213d0875acf65ae43cf8f16ce12fe8a',
 'BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml':'93f3116aba1989342335f97b51142454b76f7855',
}

def git_blob_sha(name):
    p=ROOT/'.github/workflows'/name
    try:
        b=p.read_bytes()
    except OSError:
        return None
    # GitHub Contents API sha is git blob object SHA-1, not regular file SHA-1.
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def parse(ts):
    try:
        d=dt.datetime.fromisoformat(str(ts).replace('Z','+00:00'))
        return d.astimezone(dt.timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError):
        return None

def api(endpoint,method='GET'):
    cmd=['gh','api']+(['-X',method] if method!='GET' else [])+[f'repos/{REPO}/{endpoint}']
    try:
        proc=subprocess.run(cmd,text=True,capture_output=True,timeout=25,check=False)
    except (OSError,subprocess.SubprocessError) as exc:
        return None,'GH_COMMAND_UNAVAILABLE_OR_TIMEOUT'
    if proc.returncode!=0:
        # Don't leak GitHub tokens or arbitrary stderr into published file.
        return None,'GITHUB_API_FAILED'
    if method!='GET':return {},None
    try:return json.loads(proc.stdout),None
    except (ValueError,TypeError):return None,'API_NON_JSON_RESPONSE'

def latest_good(name,allowed_events):
    d,error=api(f'actions/workflows/{name}/runs?per_page=50')
    if error:return False,error
    if not isinstance(d,dict) or not isinstance(d.get('workflow_runs'),list):return False,'RUNS_RESPONSE_INVALID'
    eligible=[]
    for row in d['workflow_runs']:
        if (row.get('path')!='.github/workflows/'+name or
           row.get('conclusion')!='success' or row.get('status')!='completed' or
           row.get('event') not in allowed_events):continue
        stamp=parse(row.get('created_at'))
        if stamp and dt.timedelta(seconds=0)<=NOW-stamp<=RUNS_WINDOW: eligible.append(stamp)
    return bool(eligible),'SUCCESS_RUN_WITHIN_3H' if eligible else 'NO_RECENT_MATCHING_SUCCESS'

def workflow_state(name):
    d,error=api(f'actions/workflows/{name}')
    if error:return None,error
    if not isinstance(d,dict) or d.get('path')!='.github/workflows/'+name:return None,'WORKFLOW_PATH_MISMATCH'
    return d.get('state'),None

def source_evidence():
    state={'pins':{},'primary_success':{},'data_fresh':False}
    for name,sha in {**TARGETS,**{k:{'sha':v} for k,v in PRIMARY.items()}}.items():
        state['pins'][name]=(git_blob_sha(name)==sha['sha'])
    p=ROOT/'data/today.json'
    try:
        day=json.loads(p.read_text(encoding='utf-8'))
        ts=parse(day.get('updated_at'))
        state['data_fresh']=bool(day.get('date')==NOW.astimezone(JST).strftime('%Y-%m-%d') and
                                 day.get('results_seen') is False and
                                 day.get('unlock') is False and
                                 day.get('scoring') is False and
                                 isinstance(day.get('venues'),list) and
                                 ts and dt.timedelta(seconds=0)<=NOW-ts<=dt.timedelta(hours=2))
    except (OSError,ValueError,TypeError):pass
    for name,events in [('auto-update.yml',{'schedule'}),
                        ('BOAT_EDGE_V200_SEQUENTIAL_FRESH_FREEZE.yml',{'workflow_run'}),
                        ('BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml',{'schedule','workflow_dispatch'})]:
        yes,detail=latest_good(name,events)
        state['primary_success'][name]={'ok':yes,'reason':detail}
    return state

def plan(evidence):
    plans={}
    for name,meta in TARGETS.items():
        if not evidence['pins'].get(name):
            plans[name]='SKIP_TARGET_CHANGED_OR_NOT_PRESENT';continue
        if meta['kind']=='legacy_collector':
            ok=(evidence['pins'].get('auto-update.yml') and evidence['data_fresh'] and
                evidence['primary_success']['auto-update.yml']['ok'])
        else:
            ok=(evidence['pins'].get('BOAT_EDGE_V200_SEQUENTIAL_FRESH_FREEZE.yml') and
                evidence['pins'].get('BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml') and
                evidence['primary_success']['BOAT_EDGE_V200_SEQUENTIAL_FRESH_FREEZE.yml']['ok'] and
                evidence['primary_success']['BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml']['ok'])
        plans[name]='ELIGIBLE_FOR_EXACT_DISABLE' if ok else 'SKIP_REPLACEMENT_NOT_PROVEN_ACTIVE'
    return plans

def load_report(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None

def run():
    if REPO!=REQUIRED_REPO:
        print('V221_REPOSITORY_BINDING_FAILED')
        return 1
    evidence=source_evidence()
    plans=plan(evidence)
    report={
       'schema':'BOAT_EDGE_V221_WORKFLOW_DEDUP_GUARDED_V1',
       'scope':'SITE_AUTOMATION_ONLY_NO_MODEL_NO_RESULTS_NO_FORMAL_ACCESS',
       'day_jst':NOW.astimezone(JST).strftime('%Y%m%d'),
       'checked_at':NOW.isoformat(),
       'protected_workflows':list(PRIMARY),
       'pins_match':evidence['pins'],
       'current_pre_result_source_fresh':evidence['data_fresh'],
       'primary_success':evidence['primary_success'],
       'targets':{},
       'no_model_or_paper_change':True,
       'formal_unlock_or_result_read':False,
    }
    for name in TARGETS:
        reason=plans[name]
        state,error=workflow_state(name)
        record={'decision':reason,'before_state':state,'after_state':state,'action':'NOT_ATTEMPTED'}
        if error:
            record['action']='SKIP_STATUS_UNVERIFIABLE';record['reason']=error
        elif state in ('disabled_manually','disabled_inactivity'):
            record['action']='ALREADY_DISABLED'
        elif state!='active':
            record['action']='SKIP_NOT_ACTIVE_OR_UNKNOWN'
        elif reason!='ELIGIBLE_FOR_EXACT_DISABLE':
            record['action']='SKIP_GUARD_NOT_SATISFIED'
        else:
            _,failure=api(f'actions/workflows/{name}/disable',method='PUT')
            new,error2=workflow_state(name)
            record['after_state']=new
            record['action']='DISABLED_AND_VERIFIED' if failure is None and error2 is None and new in ('disabled_manually','disabled_inactivity') else 'DISABLE_NOT_VERIFIED'
            if failure or error2:record['reason']=failure or error2
        report['targets'][name]=record
    report['disabled_this_run']=sum(x['action']=='DISABLED_AND_VERIFIED' for x in report['targets'].values())
    report['unverified_actions']=[name for name,x in report['targets'].items() if x['action']=='DISABLE_NOT_VERIFIED']
    out=ROOT/'data/site_ops_v221/workflow_dedup_current.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    old=load_report(out)
    if isinstance(old,dict):
        prior=dict(old);current=dict(report)
        prior.pop('checked_at',None);current.pop('checked_at',None)
        if prior==current: content=None
    if content is not None: out.write_text(content,encoding='utf-8')
    print('V221_GUARDED_WORKFLOW_DEDUP_REPORT '+json.dumps({
        'disabled':report['disabled_this_run'],
        'targets':{k:v['action'] for k,v in report['targets'].items()},
        'formal':report['formal_unlock_or_result_read']},ensure_ascii=False))
    return 1 if report['unverified_actions'] else 0

if __name__=='__main__':sys.exit(run())
