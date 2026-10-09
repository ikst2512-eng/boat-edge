from pathlib import Path
import re

ip=Path('index.html'); s=ip.read_text(encoding='utf8')
marker='/* BOAT_EDGE_V182_SCRATCH_FAIL_CLOSED */'
if marker not in s:
    inject=r'''/* BOAT_EDGE_V182_SCRATCH_FAIL_CLOSED */
function be182StopReason(d){
  const audit=d?.scratch_audit;
  if(audit?.blocked===true)return audit?.reason||'公式出走情報で欠場・取消または出走表不完全を確認';
  // A missing/aged official beforeinfo in the FINAL_15M is not evidence of safety.
  const date=String(d?.meta?.date||''), deadline=String(d?.meta?.deadline||'');
  if(/^\d{4}-\d{2}-\d{2}$/.test(date)&&/^\d{1,2}:\d{2}$/.test(deadline)){
    const due=Date.parse(date+'T'+deadline+':00+09:00');
    const mins=(due-Date.now())/60000;
    if(Number.isFinite(mins)&&mins>=0&&mins<=15){
      const source=d?.source_audit?.beforeinfo;
      const age=source?.fetched_at?Date.now()-Date.parse(source.fetched_at):Infinity;
      if(source?.status!=='ok'||!Number.isFinite(age)||age>15*60000)
        return '締切直前の公式直前情報が未確認・古いため買い目停止';
    }
  }
  const racers=d?.racers;
  if(!Array.isArray(racers)||racers.length!==6)return '出走表が6艇揃っていないため予想停止';
  if(racers.some(r=>{
    const status=[r?.scratch_status,r?.race_status,r?.status,r?.entry_status,r?.raw_text]
      .filter(x=>typeof x==='string').join(' ');
    return r?.scratched===true||r?.withdrawn===true||r?.cancelled===true||
      r?.canceled===true||r?.absent===true||/欠場|出走取消|取消|不出走|scratched|withdrawn/i.test(status);
  }))return '選手欄に欠場・取消の表示あり';
  return null;
}
async function be182FetchScratch(d){
  if(!/^\d{8}-\d{2}-\d{2}$/.test(String(d?.race_key||'')))return d;
  try{
    const r=await fetch(`./data/site_scratches_v182/${d.race_key}.json?t=${Date.now()}`,{cache:'no-store'});
    if(r.ok){const a=await r.json();if(a.race_key===d.race_key)d.scratch_audit=a;}
  }catch(_){/* source unavailable: never infer an actual scratch from missing file */}
  return d;
}
function be182HoldPrediction(d,reason){
  return {mode:'blocked',label:'出走可否の確認待ち：買い目停止',
    decision:'買い目停止',grade:'保留',reason,
    worlds:[],scores:computeScores(d),reasoning:{note:reason},
    updateLabel:d?.meta?.updated_at||'出走情報更新待ち'};
}
'''
    needle='function getPrediction(d){'
    assert s.count(needle)==1,'V182_INDEX_GETPREDICTION_MISMATCH'
    s=s.replace(needle,inject+needle+'\n  const stop=be182StopReason(d);if(stop)return be182HoldPrediction(d,stop);',1)
    src='''    let race=await r.json();
    await refreshFormalStatus();'''
    dst='''    let race=await r.json();
    race=await be182FetchScratch(race);
    await refreshFormalStatus();'''
    assert s.count(src)==1,'V182_INDEX_LOAD_RACE_MISMATCH'
    s=s.replace(src,dst,1)
    old='''    if(signature(race)===signature(original))return;
    const overlay=await loadFormalOverlay(key);'''
    new='''    const audited=await be182FetchScratch(race);
    if(signature(audited)===signature(original)&&
       JSON.stringify(audited.scratch_audit||null)===JSON.stringify(original?.scratch_audit||null))return;
    const overlay=await loadFormalOverlay(key);'''
    assert s.count(old)==1,'V182_INDEX_REFRESH_MISMATCH'
    s=s.replace(old,new,1)
    old='''    renderRace(mergeFormalOverlay(race,overlay),{silent:true});'''
    new='''    renderRace(mergeFormalOverlay(audited,overlay),{silent:true});'''
    assert s.count(old)==1,'V182_INDEX_RENDER_FRESH_MISMATCH'
    s=s.replace(old,new,1)
    ip.write_text(s,encoding='utf8')

jp=Path('assets/boat_edge_v108.js');j=jp.read_text(encoding='utf8')
if marker not in j:
    needle='''  const pred=predOf(race);
  markStandouts();'''
    repl='''  const pred=predOf(race);
  /* BOAT_EDGE_V182_SCRATCH_FAIL_CLOSED */
  const stop=typeof be182StopReason==='function'?be182StopReason(race):null;
  if(stop||pred?.mode==='blocked'){
    for(const id of ['be108PredictionModes','be108MainPick'])document.getElementById(id)?.remove();
    for(const id of ['buyBoard','directMode','raceCommand']){
      const box=document.getElementById(id);if(!box)continue;
      box.innerHTML='<div class="be182-scratch-block" role="status"><b>欠場・取消確認／買い目停止</b><span>6艇・出走可否を再確認するまで購入対象外です。保存済みの過去予想は改変しません。</span></div>';
      box.hidden=false;box.dataset.be182Blocked='true';
    }
    const stack=$("#tab-pred .section.stack");
    if(stack){let note=$("#be182ScratchStop");if(!note){note=document.createElement('div');note.id='be182ScratchStop';stack.prepend(note)}
      note.textContent='欠場・取消／直前データ不十分：予想と買い目を停止中。'+(stop||'');
      note.style.cssText='padding:14px;border:2px solid #c23131;border-radius:10px;background:#fff1f1;color:#7b1717;font-weight:800';
    }
    return; // No snapshot capture, mode generation, or result lookup for a blocked race.
  }
  document.getElementById('be182ScratchStop')?.remove();
  for(const id of ['buyBoard','directMode','raceCommand']){
    const box=document.getElementById(id);if(box?.dataset.be182Blocked==='true'){
      box.hidden=false;delete box.dataset.be182Blocked;
    }
  }
  markStandouts();'''
    assert j.count(needle)==1,'V182_JS_AFTER_RACE_MISMATCH'
    j=j.replace(needle,repl,1)
    jp.write_text(j,encoding='utf8')

sp=Path('scripts/site_final_history_v133.py');py=sp.read_text(encoding='utf8')
if 'V182_SCRATCH_GUARD_FOR_NEW_SNAPSHOTS' not in py:
    needle='''    key=race.get("race_key") or race_path.stem
    meta=race.get("meta") or {}'''
    repl='''    key=race.get("race_key") or race_path.stem
    # V182_SCRATCH_GUARD_FOR_NEW_SNAPSHOTS: fail closed on explicit scratches;
    # never overwrite stored snapshots or alter historical betting records.
    scratches=read_json(ROOT/"data/site_scratches_v182"/f"{key}.json") or {}
    racers=race.get("racers") or []
    blocked_scratches=scratches.get("race_key")==key and scratches.get("blocked") is True
    from_recs=any((r.get("scratched") is True or r.get("withdrawn") is True or
          r.get("absent") is True or r.get("cancelled") is True or
          re.search(r"欠場|出走取消|取消|不出走|scratched|withdrawn",str(r.get("status") or "")+" "+str(r.get("raw_text") or ""),re.I)) for r in racers)
    raw_date=key.split('-')[0];vv=key.split('-')[1];rr=key.split('-')[2]
    raw_race=ROOT/"data/raw"/raw_date/f"{vv}_{rr}_racelist.html"
    raw_before=ROOT/"data/raw"/raw_date/f"{vv}_{rr}_beforeinfo.html"
    raw_scratch=any(p.exists() and re.search(r"欠場|出走取消|不出走|scratched|withdrawn",p.read_text(encoding="utf8",errors="replace"),re.I)
        for p in (raw_race,raw_before))
    if len(racers)!=6 or blocked_scratches or from_recs or raw_scratch:
        continue
    meta=race.get("meta") or {}
    # Last-window official source must be current; do not freeze an unverified buy list.
    bf=(race.get('source_audit') or {}).get('beforeinfo') or {}
    if bf.get('status')!='ok':continue
    try:
        fetched=datetime.fromisoformat(str(bf.get('fetched_at')))
        if (NOW-fetched).total_seconds()>15*60:continue
    except Exception:continue'''
    assert py.count(needle)==1,'V182_SERVER_LOOP_MISMATCH'
    py=py.replace(needle,repl,1)
    sp.write_text(py,encoding='utf8')
print('V182_INDEX_JS_SERVER_SCRATCH_FAIL_CLOSED_APPLIED')
