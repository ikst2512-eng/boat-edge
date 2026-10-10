"""V219 deterministic, fail-closed, no-result-I/O regression tests."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

PATH=Path(__file__).with_name('boat_edge_autovalidation.py')
if not PATH.is_file():PATH=Path(__file__).resolve().parents[1]/'scripts/boat_edge_autovalidation.py'
spec=importlib.util.spec_from_file_location('boat_edge_autovalidation', PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW=datetime(2026,10,11,6,0,tzinfo=timezone.utc)


def write(root,path,obj):
    p=root/path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,sort_keys=True),encoding='utf-8')


def rows(family, n=4):
    arr=[]
    for i in range(n):
        race={'race_key':f'20261010-01-{i+1:02d}', 'band':'10-20' if i%2 else '20-50', 'hits':{}}
        for label in (('baseline','candidate') if family=='v185' else ('v185','head','second','original','combined')):
            race['hits'][label]={k:False for k in m.LEVELS}
        if family=='v185':
            if i==0:race['hits']['candidate']['5']=True
        elif i==0:race['hits']['head']['5']=True
        arr.append(race)
    return arr


def doc(family, n=4):
    if family=='v185':
        return {'schema_version':'boat-edge-v185-post-settlement-independent-site-shadow-v1',
                'scope':'SITE_REFERENCE_RESEARCH_NOT_FORMAL_FRESH',
                'formal_results_accessed':False, 'production_changed':False,'invalid':[],
                'observed_source':'FIRST_COMMITTED_GIT_BLOB_SHA_AND_REPRODUCIBLE_SHADOW',
                'settled_verified':n,'races':rows(family,n)}
    return {'schema_version':'boat-edge-v199-independent-future-only-score-v1',
            'scope':'SITE_REFERENCE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
            'formal_results_accessed':False, 'production_model_changed':False,'invalid':[],
            'result_access':'ONLY_CONFIRMED_SITE_FILE_AFTER_ALL_PRE_RESULT_GIT_CHECKS',
            'settled_verified':n,'races':rows(family,n)}


def main():
    with tempfile.TemporaryDirectory() as x:
        root=Path(x)
        # A fake formal RESULT file must remain completely untouched.
        formal_results=root/'data/formal/target_RESULT_FORBIDDEN.json'
        formal_results.parent.mkdir(parents=True)
        formal_results.write_text('{INVALID AND UNREADABLE}')
        write(root,m.V185_PATH,doc('v185'))
        write(root,m.V199_PATH,doc('v199'))
        write(root,m.FORMAL_PATH,{'connected':False,'predictions_ready':False,
                                 'current':'FORMAL_5_SOURCE_BLOCKED','stage':'5 sources missing',
                                 'guards':{'results_seen':False,'unlock':False,'scoring':False},
                                 'formalFirst100':{'races':0},'collector_snapshot':{'source_rows':{'stt':0}}})
        data=m.report(root,NOW)
        assert data['site_v185']['verified_races']==4
        assert data['site_v199']['verified_races']==4
        assert data['site_v185']['candidate_comparisons']['candidate']['all_races']['top5']['difference']==1
        assert data['site_v185']['candidate_comparisons']['candidate']['review_status']=='INSUFFICIENT_PROSPECTIVE_EVIDENCE'
        assert data['formal']['readiness']=='BLOCKED_MISSING_FORMAL_SOURCES_OR_PROVENANCE'
        assert data['formal_fresh_unlock_authorized'] is False
        assert data['production_model_change_authorized'] is False
        a=m.store(root,data)
        b=m.store(root,m.report(root,NOW))
        assert a['changed'] is True and b['changed'] is False
        assert a['report_sha256']==b['report_sha256']
        assert formal_results.read_text()=='{INVALID AND UNREADABLE}'
        # Invalid scorer signal blocks its entire report, not only the flagged rows.
        bad=doc('v185');bad['invalid']=[{'reason':'MUTATED_BEFORE_FIRST_COMMIT'}]
        write(root,m.V185_PATH,bad)
        data=m.report(root,NOW)
        assert data['site_v185']['verified_races']==0
        assert data['site_v185']['status']=='FAIL_CLOSED'
        assert data['performance_claim']=='NOT_PROVEN'
        # No result-file backfill, or invented last observed state on day change.
        write(root,m.V185_PATH,doc('v185'))
        d2=doc('v199');d2['races'][1]['race_key']=d2['races'][0]['race_key']
        write(root,m.V199_PATH,d2)
        assert m.report(root,NOW)['site_v199']['status']=='FAIL_CLOSED'
        write(root,m.V199_PATH,doc('v199'))
        write(root,m.READINESS_PATH,{'day_jst':'20261010','day_observed_races':123})
        assert m.report(root,NOW)['readiness']['status']=='WAITING_FOR_CURRENT_DAY_DIAGNOSTIC'
        # No evaluated file is not PASS.
        (root/m.V185_PATH).unlink()
        assert m.report(root,NOW)['status']=='EVIDENCE_BLOCKED_OR_MISSING'
        # A score document claiming formal-target access is rejected.
        false=doc('v185');false['formal_results_accessed']=True
        write(root,m.V185_PATH,false)
        assert m.report(root,NOW)['site_v185']['status']=='FAIL_CLOSED'
        # The resulting report contains no future betting/promotion path.
        assert not data['paper_wager_authorized'] and not data['production_model_change_authorized']
    print('V219_TEST_PASS: deterministic dual-run, paired Top5, source provenance, formal isolation, invalid/missing fail-closed, no auto adoption')

if __name__=='__main__':main()
