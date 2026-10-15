from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timedelta,timezone
import importlib.util,sys,json,hashlib,subprocess
script=Path(__file__).resolve().parents[1]/'scripts/site_v186_refresh_scratch.py'
sp=importlib.util.spec_from_file_location('site_v186',script)
m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
now=datetime(2026,10,10,12,0,tzinfo=m.JST)
with TemporaryDirectory() as d:
    root=Path(d);(root/'data/races').mkdir(parents=True);(root/'data/site_scratches_v182').mkdir()
    def put(rno,minutes,card_minutes=1,bt_minutes=1,blocked=False,with_scan=True):
        key=f'20261010-01-{rno:02d}'
        due=now+timedelta(minutes=minutes)
        doc={'race_key':key,'meta':{'date':'2026-10-10','deadline':due.strftime('%H:%M')},
             'source_audit':{'race_card':{'status':'ok','fetched_at':(now-timedelta(minutes=card_minutes)).isoformat()},
                             'beforeinfo':{'status':'ok','fetched_at':(now-timedelta(minutes=bt_minutes)).isoformat()}}}
        (root/'data/races'/f'{key}.json').write_text(json.dumps(doc))
        sd={'race_key':key,'source_date':'20261010','checked_at':(now-timedelta(hours=3)).isoformat(),
            'blocked':blocked,'reason':'確認済みの欠場艇' if blocked else None}
        if with_scan:(root/'data/site_scratches_v182'/f'{key}.json').write_text(json.dumps(sd))
        return key
    ids=[put(1,14),put(2,13,card_minutes=40),put(3,11,bt_minutes=25),put(4,27),put(5,10,with_scan=False),put(6,10,blocked=True)]
    r=m.refresh(root,now)
    assert r['eligible_window']==5,r
    assert r['refreshed']==4,r
    assert r['held_stale_card']==1 and r['held_stale_beforeinfo']==1,r
    assert r['scan_missing']==1 and r['existing_blocked']==3,r
    a=[json.loads((root/'data/site_scratches_v182'/f'{key}.json').read_text()) for key in [ids[0],ids[1],ids[2],ids[5]]]
    assert a[0]['blocked'] is False and a[0]['checked_at']==now.isoformat()
    assert a[1]['blocked'] is True and a[2]['blocked'] is True and a[3]['blocked'] is True
    assert not (root/'data/site_scratches_v182'/f'{ids[4]}.json').exists()
    after=m.refresh(root,now);assert after['refreshed']==0,after
    assert 'BOAT_EDGE_V186' not in (root/'data/races'/f'{ids[0]}.json').read_text()
    # This legacy V182 green has no bound HTML SHA; V186 must never stage it.
    key=ids[0];racepath=root/'data/races'/f'{key}.json'
    scratchpath=root/'data/site_scratches_v182'/f'{key}.json'
    race=json.loads(racepath.read_text());weak=json.loads(scratchpath.read_text())
    assert m.source_bound_green(root/'data',key,race,weak) is False
    # Positive evidence needs matching official source audit, same raw bytes,
    # a six-boat record and no withdrawal evidence.
    raw_dir=root/'data/raw'/key[:8];raw_dir.mkdir(parents=True)
    strong={**weak,'schema_version':'boat-edge-v182-scratch-evidence-v1',
            'official_beforeinfo_six_boat_complete':True,
            'race_card_source_status':'ok',
            'official_beforeinfo_source_status':'ok',
            'suspect_lanes':[],'official_raw_flags':[]}
    for role,suffix,field in [('race_card','racelist','race_card_sha256'),
                              ('beforeinfo','beforeinfo','beforeinfo_sha256')]:
        raw=(f'<html>official {key} {role}</html>').encode()
        path=raw_dir/f'01_01_{suffix}.html';path.write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest()
        race['source_audit'][role]['sha256']=digest
        strong[field]=digest
    assert m.source_bound_green(root/'data',key,race,strong) is True
    for field in ('race_card_sha256','beforeinfo_sha256'):
        changed={**strong,field:'0'*64}
        assert m.source_bound_green(root/'data',key,race,changed) is False
        changed={**strong};changed.pop(field)
        assert m.source_bound_green(root/'data',key,race,changed) is False
    assert m.source_bound_green(root/'data',key,race,{**strong,'blocked':True}) is False
    assert m.source_bound_green(root/'data',key,race,{**strong,'official_beforeinfo_six_boat_complete':False}) is False
    for suffix in ('racelist','beforeinfo'):
        path=raw_dir/f'01_01_{suffix}.html'
        old=path.read_bytes()
        path.write_bytes(old+b'tamper')
        assert m.source_bound_green(root/'data',key,race,strong) is False
        path.write_bytes(old)
    assert m.source_bound_green(root/'data',key,race,strong) is True
print('V186_FRESH_SCRATCH_FUTURE_WINDOW_STALE_CARD_STALE_BEFORE_MISSING_SCAN_BLOCK_PASS')
print('V186_UNBOUND_LEGACY_SCRATCH_GREEN_QUARANTINED_OFFICIAL_SHA_PASS')
