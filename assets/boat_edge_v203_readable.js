/* BOAT EDGE V203: race display refinement ONLY. No model, bet, odds calculation or result reads. */
(()=>{'use strict';
  if(window.BoatEdgeV203)return;
  const $=(s,r=document)=>r.querySelector(s);
  const esc=x=>String(x??'－').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n=x=>x===null||x===undefined||String(x).trim()===''?null:Number.isFinite(Number(x))?Number(x):null;
  const val=(x,d=2)=>n(x)===null?'－':Number(x).toFixed(d);
  const time=x=>{const d=x?new Date(x):null;return d&&Number.isFinite(d.getTime())?d.toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}):'時刻不明'};
  const safeKey=s=>/^20\d{6}-\d{2}-\d{2}$/.test(String(s||''));
  const src=(r,k)=>{const s=r?.source_audit?.[k];return Boolean(s?.status==='ok'&&s?.fetched_at&&s?.sha256&&Number.isFinite(Date.parse(s.fetched_at)))};
  const race=()=>{try{return typeof state!=='undefined'?state?.race:null}catch(_){return null}};
  const deadline=r=>{const key=String(r?.race_key||''),h=String(r?.meta?.deadline||'');return safeKey(key)&&/^\d{1,2}:\d{2}$/.test(h)?Date.parse(key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8)+'T'+h+':00+09:00'):NaN};
  const when=(r,k)=>{
    const s=r?.source_audit?.[k];if(!src(r,k))return '未取得／取得証跡なし';
    const t=Date.parse(s.fetched_at),due=deadline(r);
    return time(s.fetched_at)+'取得'+(Number.isFinite(due)?(t>=due?'（締切後・予想には不使用）':'（締切前・予測使用は未確認）'):'（締切照合不可）');
  };
  let selectedKey='',scratch=null,scratchError='',fullStats=false,fullTable=false,observer=null,inDraw=false,lastSig='';
  function scratchHint(r){
    const notice=$('#be182ScratchStop');
    if(notice?.isConnected)return {type:'stop',label:'買い目停止',description:notice.textContent||'出走可否の確認待ち'};
    const rows=Array.isArray(r?.racers)?r.racers:[];
    if(rows.length!==6)return {type:'stop',label:'出走表不足',description:'6艇が揃っていないため、出走可否を確認してください'};
    if(rows.some(p=>p?.scratched===true||p?.withdrawn===true||p?.cancelled===true||p?.canceled===true||p?.absent===true||/欠場|出走取消|取消|不出走|scratched|withdrawn/i.test([p?.scratch_status,p?.race_status,p?.status,p?.entry_status,p?.raw_text].filter(x=>typeof x==='string').join(' '))))
      return {type:'stop',label:'欠場・取消の疑い',description:'選手情報に出走不可の信号あり。買い目停止の表示を確認してください'};
    const a=scratch?.race_key===r.race_key?scratch:(r?.scratch_audit?.race_key===r.race_key?r.scratch_audit:null);
    if(a?.blocked===true)return {type:'stop',label:'欠場・取消の疑い',description:a.reason||'出走可否の確認が必要'};
    if(a?.blocked===false&&Number.isFinite(Date.parse(a.checked_at||''))){
      const age=(Date.now()-Date.parse(a.checked_at))/60000;
      if(age>=-1&&age<=16)return {type:'partial',label:'取消信号なし（確認時点）',description:time(a.checked_at)+'照合。出走確定・購入安全の保証ではありません'};
      return {type:'pending',label:'欠場・取消の再確認待ち',description:time(a.checked_at)+'の照合履歴あり。現在の出走可否を保証しません'};
    }
    return {type:'pending',label:'欠場・取消 未照合',description:scratchError?'取消確認データを読み込めませんでした。買い目停止ルールを優先':'6艇の登録と、出走可否の確定確認は別です'};
  }
  function getRows(r){
    const racers=Array.isArray(r?.racers)?r.racers:[];
    const ex=src(r,'beforeinfo'),stt=src(r,'stt'),ori=src(r,'original_exhibition');
    const before=new Map((r?.beforeinfo?.racers||[]).map(x=>[Number(x?.lane),x]));
    const starts=new Map((r?.beforeinfo?.start_exhibition||[]).map(x=>[Number(x?.lane),x]));
    const entries=new Map((r?.actual_entry||[]).map(x=>[Number(x?.lane),x]));
    const orig=r?.original_exhibition,labels=Array.isArray(orig?.labels)?orig.labels:[];
    const o=new Map((orig?.boats||[]).map(x=>[Number(x?.lane),x?.values||[]]));
    return racers.map((p,i)=>{
      const lane=Number(p?.lane||i+1),b=before.get(lane)||{},s=starts.get(lane)||{},t=entries.get(lane)||{},values=o.get(lane)||[];
      const oe=k=>ori&&labels.includes(k)?n(values[labels.indexOf(k)]):null;
      const sRaw=ex?s.st:stt?(t.exhibition_st_raw??t.exhibition_st):null;
      const course=ex?n(s.course):stt?n(t.course):null;
      return {lane,name:p?.name||'選手未取得',grade:p?.class||'－',course:course>=1&&course<=6?course:null,st:n(sRaw),f:ex?s.exhibition_f===true:stt?t.exhibition_f===true:false,
        time:ex?n(b.exhibition_time):null,lap:oe('一周'),turn:oe('まわり足'),straight:oe('直線'),avg:n(p?.avg_st),
        national:p?.national||{},local:p?.local||{},motor:p?.motor||{},boat:p?.boat||{},
        source:ex?'公式展示':stt?'STT':'未取得'};
    });
  }
  const distinctBest=(rows,field,margin)=>{
    const sorted=rows.map(x=>field==='st'&&(x.f===true||n(x.st)<0)?null:n(x[field])).filter(x=>x!==null).sort((a,b)=>a-b);
    return sorted.length>=4&&sorted[1]-sorted[0]>=margin?sorted[0]:null;
  };
  const red=(v,best)=>best!==null&&n(v)!==null&&Math.abs(Number(v)-best)<1e-7?' be203-red':'';
  function header(r){
    const s=scratchHint(r),ex=src(r,'beforeinfo'),stt=src(r,'stt'),ori=src(r,'original_exhibition'),w=ex?r.beforeinfo?.weather||{}:{};
    const water=[['風',n(w.wind_speed_ms)!==null?val(w.wind_speed_ms,1)+'m/s':'－'],['波',n(w.wave_cm)!==null?val(w.wave_cm,0)+'cm':'－']];
    const badges=[['展示タイム',ex,'beforeinfo'],['展示ST・進入',ex||stt,ex?'beforeinfo':'stt'],['オリ展CSV',ori,'original_exhibition']];
    return `<div class="be203-health be203-${s.type}" role="status"><strong>${esc(s.label)}</strong><span>${esc(s.description)}</span></div>`+
      `<div class="be203-source">${badges.map(([label,yes,key])=>`<span class="${yes?'present':'absent'}">${esc(label)}：${esc(yes?when(r,key):'未取得')}</span>`).join('')}</div>`+
      `<div class="be203-water">${water.map(([k,v])=>`<span>${esc(k)} <b>${esc(v)}</b></span>`).join('')}<small>オリ展CSVはBOATERS・競艇日和の二重照合とは別</small></div>`;
  }
  function cards(r){
    const rows=getRows(r),lap=distinctBest(rows,'lap',.08),turn=distinctBest(rows,'turn',.04),straight=distinctBest(rows,'straight',.04),st=distinctBest(rows,'st',.03);
    return `<div class="be203-heading"><strong>直前の6艇比較</strong><small>選手ごとに見やすく整理</small></div>`+
      `<div class="be203-cards">${rows.map(x=>`<article class="be203-card">
        <div class="be203-name"><span class="be203-lane be203-l${x.lane}">${x.lane}</span><b>${esc(x.name)}</b><small>${esc(x.grade)} / 展示進入 ${x.course??'－'}コース</small></div>
        <div class="be203-metrics">
          <div><small>展示ST</small><b class="${red(x.st,st)}">${x.f&&x.st!==null?'F'+val(Math.abs(x.st)):val(x.st)}</b></div>
          <div><small>展示タイム</small><b>${val(x.time)}</b></div>
          <div><small>1周</small><b class="${red(x.lap,lap)}">${val(x.lap)}</b></div>
          <div><small>まわり足</small><b class="${red(x.turn,turn)}">${val(x.turn)}</b></div>
          <div><small>直線</small><b class="${red(x.straight,straight)}">${val(x.straight)}</b></div>
        </div>
        <div class="be203-statmini"><span>全国 <b>${val(x.national.win_rate)}</b></span><span>当地 <b>${val(x.local.win_rate)}</b></span><span>M2連 <b>${val(x.motor.quinella_rate,1)}%</b></span></div>
        ${fullStats?`<div class="be203-stats"><span>平均ST <b>${val(x.avg)}</b></span><span>全国2連 <b>${val(x.national.quinella_rate,1)}%</b></span><span>全国3連 <b>${val(x.national.trio_rate,1)}%</b></span><span>当地2連 <b>${val(x.local.quinella_rate,1)}%</b></span><span>当地3連 <b>${val(x.local.trio_rate,1)}%</b></span><span>M3連 <b>${val(x.motor.trio_rate,1)}%</b></span><span>B2連 <b>${val(x.boat.quinella_rate,1)}%</b></span><span>B3連 <b>${val(x.boat.trio_rate,1)}%</b></span></div>`:''}
      </article>`).join('')}</div>`+
      `<div class="be203-actions"><button type="button" data-be203-action="stats">${fullStats?'詳細成績を閉じる':'全国・当地／モーター詳細を見る'}</button><button type="button" data-be203-action="full">${fullTable?'全項目の表を閉じる':'全項目の表を開く'}</button></div>`+
      `<div class="be203-help">「－」は取得・照合できていない値。赤は実測差が明確な1位のみ。展示進入は本番の実進入ではありません。<br>買い目・1万円配分・的中判定は上の予想スタイルに表示し、この画面から再計算しません。</div>`;
  }
  function sync(force=false){
    if(inDraw)return;
    const r=race(),host=$('#be202Essential');if(!host||!safeKey(r?.race_key))return;
    const sig=JSON.stringify([r.race_key,r.meta?.updated_at,r.source_audit?.beforeinfo?.fetched_at,r.source_audit?.stt?.fetched_at,r.source_audit?.original_exhibition?.fetched_at,scratch?.race_key,scratch?.checked_at,scratch?.blocked,Boolean($('#be182ScratchStop')),fullStats,fullTable]);
    if(!force&&lastSig===sig&&$('#be203Layout',host))return;
    inDraw=true;
    try{
      let box=$('#be203Layout',host);if(!box){box=document.createElement('section');box.id='be203Layout';box.className='be203-layout';}
      box.innerHTML=header(r)+cards(r);
      const table=$('.be202-table-scroll',host);
      if(table)host.insertBefore(box,table);else host.append(box);
      document.documentElement.classList.add('be203-active');
      document.documentElement.classList.toggle('be203-fulltable',fullTable);
      lastSig=sig;
    }finally{inDraw=false;}
  }
  async function fetchScratch(r){
    if(!safeKey(r?.race_key))return;
    const key=r.race_key;selectedKey=key;scratch=null;scratchError='';lastSig='';
    try{
      const res=await fetch(`./data/site_scratches_v182/${key}.json?ui203=${Date.now()}`,{cache:'no-store'});
      if(!res.ok)throw Error('HTTP '+res.status);
      const d=await res.json();if(d?.race_key===key&&typeof d.blocked==='boolean'&&Number.isFinite(Date.parse(d.checked_at||''))){if(selectedKey===key)scratch=d;}
      else throw Error('invalid scratch evidence');
    }catch(_){if(selectedKey===key)scratchError='unavailable';}
    if(selectedKey===key)sync(true);
  }
  let lastObserved='';
  function tick(){
    const r=race();if(!safeKey(r?.race_key))return;
    if(lastObserved!==r.race_key){lastObserved=r.race_key;fullStats=false;fullTable=false;fetchScratch(r);}
    sync();
  }
  function start(){
    document.addEventListener('click',e=>{
      const b=e.target.closest?.('#be203Layout [data-be203-action]');if(!b)return;
      if(b.dataset.be203Action==='stats')fullStats=!fullStats;
      if(b.dataset.be203Action==='full')fullTable=!fullTable;
      sync(true);
    });
    const root=$('#tab-pred .section.stack');
    if(root){observer=new MutationObserver(()=>{if(!inDraw)tick();});observer.observe(root,{childList:true,subtree:true});}
    tick();
    setInterval(()=>{if(!document.hidden)tick();},4000);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden){tick();if(safeKey(race()?.race_key))fetchScratch(race());}});
  }
  window.BoatEdgeV203={getRows,scratchHint,when,sync};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
