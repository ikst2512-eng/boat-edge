/* BOAT EDGE V169 -- researched racer x venue, source pinned through Oct 7.
   View only. Cannot alter any prediction, bet allocation, formal Fresh, odds or results. */
(()=>{'use strict';
  const $=(s,base=document)=>base.querySelector(s);
  const esc=x=>String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const VENUES={'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖','07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江','13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山','19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'};
  const race=()=>{try{return typeof state==='undefined'?null:state?.race}catch(_){return null}};
  let cachedDay='',cached=null,pending=null,selected='',lastSig='',renderSeq=0;
  const pct=(a,n)=>Number.isFinite(a)&&n>0?(100*a/n).toFixed(1)+'%':'－';
  const venueCode=r=>String(r?.meta?.venue_code??'').padStart(2,'0');
  function statsFor(s,venue){
    const part=s?.venues?.[venue];if(!part||!part.starts)return null;
    const all=s.all||{};let expected=0;
    for(const [course,row] of Object.entries(part.courses||{})){
      const a=all.courses?.[course];if(!a?.starts)return null;
      expected+=row.starts*a.top3/a.starts;
    }
    const diff=100*(part.top3-expected)/part.starts;
    return {n:part.starts,win:part.wins,top3:part.top3,top2:part.top2,expected:100*expected/part.starts,diff,
      label:part.starts>=12&&diff>=10?'得意場候補':part.starts<12?'出走少・参考':'参考'};
  }
  async function getDay(day){
    if(!/^\d{8}$/.test(day))return null;
    if(day===cachedDay&&cached)return cached;
    if(pending?.day===day)return pending.promise;
    const promise=(async()=>{try{
      const reply=await fetch('./data/site_racer_venue_v169/'+day+'.json?v=169',{cache:'no-store'});
      if(!reply.ok)return null;
      const d=await reply.json();
      if(d.schema_version!=='boat-edge-v169-racer-venue-display-only-v1'||d.status!=='DISPLAY_ONLY_NOT_PREDICTION_CONNECTED'||
         d.site_day!==day||d.as_of_d1!=='2026-10-07'||d.window?.complete!==true||d.window?.days!==92||d.formal_20261008_results_accessed!==false||d.prediction_weights_changed!==false)return null;
      cachedDay=day;cached=d;return d;
    }catch(_){return null;}finally{if(pending?.day===day)pending=null;}})();
    pending={day,promise};return promise;
  }
  function mount(){
    const root=$('#tab-data .section.stack');if(!root)return null;
    let node=$('#be169VenueStats');if(node)return node;
    node=document.createElement('section');node.id='be169VenueStats';node.className='be169-card';
    const before=$('#be165RacerStats');if(before?.parentElement===root)before.insertAdjacentElement('afterend',node);
    else root.appendChild(node);
    node.addEventListener('click',e=>{
      const b=e.target.closest('button[data-be169-reg]');if(!b)return;
      const id=b.dataset.be169Reg;selected=selected===id?'':id;fillDetails();
    });return node;
  }
  function fillDetails(){
    const target=$('#be169Details'),source=cached,rec=source?.racers?.[selected],r=race();
    if(!target)return;
    if(!rec||!r||!selected){target.innerHTML='';return;}
    const name=(r.racers||[]).find(x=>String(x.registration_no)===selected)?.name||selected;
    const ranked=Object.entries(rec.venues||{}).map(([id])=>({id,...statsFor(rec,id)})).filter(x=>Number.isFinite(x.diff))
      .sort((a,b)=>(Number(b.n>=12)-Number(a.n>=12))||b.diff-a.diff||b.n-a.n);
    target.innerHTML='<div class="be169-details"><h4>'+esc(name)+'｜場別ランキング</h4><p>直近3か月・各場の3連対率と、本人のコース別実績で調整した期待値との差。12走未満は参考表示。</p>'+(
      ranked.length?'<div class="be169-scroll"><table><thead><tr><th>場</th><th>出走</th><th>1着率</th><th>3連対率</th><th>コース調整差</th><th>評価</th></tr></thead><tbody>'+ranked.map(s=>
        '<tr><th>'+esc(VENUES[s.id]||s.id)+'</th><td>'+s.n+'走</td><td>'+pct(s.win,s.n)+'</td><td>'+pct(s.top3,s.n)+'</td><td>'+((s.diff>=0?'+':'')+s.diff.toFixed(1))+'pt</td><td>'+esc(s.label)+'</td></tr>'
      ).join('')+'</tbody></table></div>':'対象期間の場別出走サンプルなし')+'</div>';
  }
  async function draw(force=false){
    const rr=race(),parent=$('#tab-data'),host=mount();if(!rr||!host||!parent?.classList.contains('active'))return;
    const day=String(rr.race_key||'').slice(0,8),venue=venueCode(rr);
    const sig=rr.race_key+'|'+rr.meta?.updated_at+'|'+venue;
    if(!force&&lastSig===sig)return;
    lastSig=sig;
    const id=++renderSeq;
    host.innerHTML='<h3>選手別・得意場 / 苦手場</h3><p>開催場別成績を読み込み中…</p>';
    const doc=await getDay(day);if(id!==renderSeq||race()?.race_key!==rr.race_key)return;
    if(!doc){host.innerHTML='<h3>選手別・得意場 / 苦手場</h3><p class="be169-warn">この日の事前集計が未公開。得意場は推定せず、公式の当地成績を確認してな。</p>';return;}
    const rows=(rr.racers||[]).map((x,i)=>({lane:Number(x.lane??i+1),reg:String(x.registration_no||''),name:String(x.name||''),
      values:statsFor(doc.racers?.[String(x.registration_no||'')],venue)}));
    host.innerHTML='<h3>選手別・得意場 / 苦手場 <small>現在地：'+esc(VENUES[venue]||venue)+'</small></h3>'+
      '<p>選手本人の競艇場別3か月成績。<b>3連対率・1着率・出走数</b>を比較できる。差分は本人の実コース構成で補正した参考値。</p>'+
      '<div class="be169-notice">履歴：2026/07/08〜10/07（92日収録）｜10/08正式対象は未参照｜得意場候補は12走以上かつコース調整差 +10pt以上。統計の表示専用で予想確率には未接続。</div>'+
      '<div class="be169-scroll"><table><thead><tr><th>選手</th><th>当地走数</th><th>当地1着</th><th>当地3連対</th><th>コース調整差</th><th>判定</th></tr></thead><tbody>'+rows.map(x=>{
        const s=x.values;
        return '<tr><th><button type="button" data-be169-reg="'+esc(x.reg)+'"><b>'+x.lane+' '+esc(x.name)+'</b> ▾</button></th>'+
          '<td>'+(s?s.n+'走':'－')+'</td><td>'+(s?pct(s.win,s.n):'－')+'</td><td>'+(s?pct(s.top3,s.n):'－')+'</td>'+
          '<td>'+(s?(s.diff>=0?'+':'')+s.diff.toFixed(1)+'pt':'－')+'</td><td class="'+(s?.label==='得意場候補'?'be169-strong':'')+'">'+esc(s?.label||'実績なし')+'</td></tr>';
      }).join('')+'</tbody></table></div><p class="be169-foot">選手名を押すと過去に走った場のランキングを表示。12走未満は信頼性が低く、苦手場も断定しません。順位・買い目・配分は変えていません。</p><div id="be169Details"></div>';
    fillDetails();
  }
  function init(){
    mount();const tab=$('#tab-data'),rr=$('#raceView'),title=$('#raceTitle');
    if(typeof MutationObserver!=='undefined'){
      const obs=new MutationObserver(()=>{if(tab?.classList.contains('active'))draw();});
      for(const el of [tab,rr])if(el)obs.observe(el,{attributes:true,attributeFilter:['class']});
      if(title)obs.observe(title,{childList:true,characterData:true,subtree:true});
    }
    document.addEventListener('visibilitychange',()=>{if(!document.hidden){lastSig='';cached=null;draw(true);}});
    setInterval(()=>{if(tab?.classList.contains('active'))draw();},3500);
  }
  window.BoatEdgeV169={statsFor,draw};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
