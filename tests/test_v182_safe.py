import os,sys,tempfile,subprocess,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'scripts'
if not P.exists():P=Path(__file__).resolve().parent

def run(args,cwd):
    p=subprocess.run([sys.executable,*args],cwd=cwd,text=True,capture_output=True)
    if p.returncode:raise AssertionError(f'{args}: {p.stdout}\n{p.stderr}')
    return p.stdout
with tempfile.TemporaryDirectory() as td:
    root=Path(td);(root/'assets').mkdir(parents=True);(root/'scripts').mkdir()
    index='''function getPrediction(d){return buildFallbackPrediction(d)}\nfunction computeScores(d){return []}\nasync function loadRace(){\n    let race=await r.json();\n    await refreshFormalStatus();\n}\nasync function be162RefreshVisibleRace(){\n    if(signature(race)===signature(original))return;\n    const overlay=await loadFormalOverlay(key);\n    renderRace(mergeFormalOverlay(race,overlay),{silent:true});\n}'''
    js='''async function afterRace(race){\n  const pred=predOf(race);\n  markStandouts();\n}\n'''
    server='''for race_path in sorted(RACES.glob(f"{TODAY}-*.json")):\n    race=read_json(race_path)\n    if not race:continue\n    key=race.get("race_key") or race_path.stem\n    meta=race.get("meta") or {}\n'''
    (root/'index.html').write_text(index);(root/'assets/boat_edge_v108.js').write_text(js)
    (root/'scripts/site_final_history_v133.py').write_text(server)
    out=run([str(P/'site_v182_patch.py')],root)
    assert 'APPLIED' in out
    for k in ['index.html','assets/boat_edge_v108.js','scripts/site_final_history_v133.py']:
        assert 'V182' in (root/k).read_text()
    s=(root/'index.html').read_text();assert 'be182FetchScratch' in s and 'buy' not in s[:20]
    p=subprocess.run(['node','--check',str(root/'assets/boat_edge_v108.js')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert run([str(P/'site_v182_patch.py')],root).strip().endswith('APPLIED')
    d=root/'data';(d/'races').mkdir(parents=True);(d/'raw/20261010').mkdir(parents=True)
    (d/'model_status.json').write_text('{"target_date":"2026-10-10"}')
    normal=[{'lane':i,'name':f'boater{i}'} for i in range(1,7)]
    for rid,rows,html in [(1,normal,'no scratch'),(2,[dict(x) for x in normal],'<p>欠場</p>'),(3,normal[:5],'no scratch')]:
        if rid==1:rows=[dict(x) for x in normal];rows[3]['status']='欠場'
        key=f'20261010-01-{rid:02d}'
        (d/'races'/f'{key}.json').write_text(json.dumps({'race_key':key,'racers':rows,'source_audit':{'race_card':{'status':'ok'}}}))
        (d/'raw/20261010'/f'01_{rid:02d}_racelist.html').write_text(html)
    r=run([str(P/'site_v182_scratch_scan.py')],root)
    assert 'V182_SCRATCH_SCAN' in r
    for rid in [1,2,3]:
        a=json.loads((d/'site_scratches_v182'/f'20261010-01-{rid:02d}.json').read_text());assert a['blocked'] is True
    # No fake odds, payouts, or historical conclusions are generated from fixture.
print('V182_TEST_PATCH_IDEMPOTENT_PARSER_MISSING6_AND_STATUS_BLOCK_PASS')
