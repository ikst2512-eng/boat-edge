/* BOAT EDGE V165 | racer-specific historical actual-course facts, DISPLAY ONLY.
   Frozen source: V146 through 2026-10-07. No site prediction weights touched. */
(()=>{'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const SOURCES={three:'3m',six:'6m',year:'1y'};
  const METHODS=['逃げ','差し','まくり','まくり差し','抜き','恵まれ'];
  let windowKey='3m',scope='entry',cachedDay='',cachedData=null,cacheUntil=0,loading=null;
  let selectedLane=0,lastRender='',requestSeq=0;
  const num=v=>(v===null||v===undefined||String(v).trim()===''||!Number.isFinite(Number(v)))?null:Number(v);
  const fPercent=v=>v===null?'－':v.toFixed(1)+'%';
  const ratio=(a,b)=>b>0&&num(a)!==null?100*a/b:null;
  const currentRace=()=>{try{return typeof state==='undefined'?null:state.race}catch(_){return null}};
  const entryMap=race=>{
    const entries=race?.actual_entry||[],m=new Map(),seen=new Set();
    if(entries.length!==6)return null;
    for(const e of entries){const lane=num(e.lane),course=num(e.course);
      if(!Number.isInteger(lane)||!Number.isInteger(course)||lane<1||lane>6||course<1||course>6||m.has(lane)||seen.has(course))return null;
      m.set(lane,course);seen.add(course);
    }
    return m.size===6?m:null;
  };
  const combine=parts=>{
    if(!parts.length)return null;
    let starts=0,wins=0,top2=0,top3=0,stTotal=0,stN=0;const methods={};
    for(const p of parts){
      if(!p||!Number.isInteger(p.starts)||p.starts<0)continue;
      starts+=p.starts;wins+=p.wins;top2+=p.top2;top3+=p.top3;
      if(num(p.avg_st)!==null&&p.st_n>0){stTotal+=p.avg_st*p.st_n;stN+=p.st_n;}
      for(const [k,v] of Object.entries(p.win_methods||{}))if(METHODS.includes(k)&&Number.isInteger(v)&&v>=0)methods[k]=(methods[k]||0)+v;
    }
    if(!starts)return null;
    return {starts,wins,top2,top3,st_n:stN,avg_st:stN?stTotal/stN:null,win_methods:methods};
  };
  const statFor=(rec,course,windowName,all)=>{
    if(!rec||!rec.courses)return null;
    if(all)return combine(Object.values(rec.courses).map(x=>x?.[windowName]).filter(Boolean));
    const p=rec.courses[String(course)]?.[windowName];
    return p&&p.starts>0?p:null;
  };
  const rateTrio=s=>s?ratio(s.top3,s.starts):null;
  const rateWin=s=>s?ratio(s.wins,s.starts):null;
  const strongLane=(rows,key,minGap)=>{
    const s=rows.filter(x=>x.stats&&x.stats.starts>=5).map(x=>({lane:x.lane,value:key==='win'?rateWin(x.stats):rateTrio(x.stats)}))
      .filter(x=>x.value!==null).sort((a,b)=>b.value-a.value);
    return s.length>1&&s[0].value-s[1].value>=minGap?s[0].lane:0;
  };
  async function loadDay(day){
    if(!/^\d{8}$/.test(day))return null;
    if(cachedDay===day&&cachedData&&Date.now()<cacheUntil)return cachedData;
    if(loading?.day===day)return loading.promise;
    const promise=(async()=>{try{
      const r=await fetch('./data/site_racer_recent_v165/'+day+'.json?v=165',{cache:'no-store'});
      if(!r.ok)return null;
      const x=await r.json();
      if(x.schema_version!=='boat-edge-site-racer-course-display-v165'||x.status!=='DISPLAY_ONLY_RESEARCH_NOT_PREDICTION_CONNECTED'||
        x.site_date!==day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8)||
        x.source?.as_of_d1!=='2026-10-07'||typeof x.racers!=='object')return null;
      cachedDay=day;cachedData=x;cacheUntil=Date.now()+120000;return x;
    }catch(_){return null}finally{if(loading?.day===day)loading=null;}})();
    loading={day,promise};return promise;
  }
  function mount(){
    const parent=$('#tab-data .section.stack');if(!parent)return null;
    let e=$('#be165RacerStats');if(e)return e;
    e=document.createElement('section');e.id='be165RacerStats';
    const v163=$('#be163MethodStats');
    if(v163&&v163.parentElement===parent)v163.insertAdjacentElement('afterend',e);
    else parent.insertBefore(e,parent.firstChild);
    e.addEventListener('click',event=>{
      const w=event.target.closest('[data-be165-window]');
      if(w){windowKey=w.dataset.be165Window;selectedLane=0;lastRender='';draw(true);return;}
      const s=event.target.closest('[data-be165-scope]');
      if(s){scope=s.dataset.be165Scope;selectedLane=0;lastRender='';draw(true);return;}
      const lane=event.target.closest('[data-be165-lane]');
      if(lane){const n=Number(lane.dataset.be165Lane);selectedLane=(n===selectedLane?0:n);drawDetails();}
    });
    return e;
  }
  function layout(race,source){
    const map=entryMap(race),useAll=scope==='all',rows=[];
    for(let i=0;i<(race.racers||[]).length;i++){
      const r=race.racers[i],lane=Number(r.lane??i+1),reg=String(r.registration_no??''),course=map?.get(lane)??lane;
      rows.push({lane,name:r.name||'',reg,course,stats:statFor(source.racers?.[reg],course,windowKey,useAll)});
    }
    return {rows,map};
  }
  function drawDetails(){
    const target=$('#be165Details'),race=currentRace();if(!target||!race)return;
    const source=cachedData;if(!source||selectedLane<=0){target.innerHTML='';return;}
    const r=(race.racers||[]).find((x,i)=>Number(x.lane??i+1)===selectedLane);
    if(!r){target.innerHTML='';return;}
    const reg=String(r.registration_no||''),map=entryMap(race),course=map?.get(selectedLane)??selectedLane;
    const s=statFor(source.racers?.[reg],course,windowKey,scope==='all');
    if(!s){target.innerHTML='<div class="be165-details">この条件での実績サンプルなし（0%とは扱いません）</div>';return;}
    const methodTotal=Object.values(s.win_methods||{}).reduce((a,b)=>a+b,0);
    target.innerHTML='<div class="be165-details"><h4>'+esc(selectedLane+'号艇 '+r.name)+' — '+(scope==='all'?'全実進入コース':course+'コース')+' / '+esc(windowKey)+' / '+s.starts+'走</h4>'+
      '<p class="be165-note">決まり手率の分母は「1着になった'+s.wins+'回」。出走全体に対する率ではありません。決まり手不詳 '+Math.max(0,s.wins-methodTotal)+'回。</p>'+
      '<div class="be165-method-list">'+METHODS.map(k=>{
        const n=s.win_methods?.[k]||0;
        return '<div><strong>'+esc(k)+'　'+(s.wins>0?(100*n/s.wins).toFixed(1)+'%':'－')+'</strong><small>'+n+'回 / 1着 '+s.wins+'回</small></div>';
      }).join('')+'</div></div>';
  }
  async function draw(force=false){
    const tab=$('#tab-data'),race=currentRace(),host=mount();
    if(!host||!race||!tab?.classList.contains('active'))return;
    const day=String(race.race_key||'').slice(0,8);
    if(!/^\d{8}$/.test(day))return;
    const sig=[day,race.race_key,race.meta?.updated_at,windowKey,scope].join('|');
    if(!force&&lastRender===sig)return;
    lastRender=sig;
    const seq=++requestSeq;
    host.innerHTML='<div class="be165-head"><h3>選手別・実コース成績</h3><small>履歴照合中…</small></div>';
    const data=await loadDay(day);
    if(seq!==requestSeq||currentRace()?.race_key!==race.race_key)return;
    if(!data){host.innerHTML='<div class="be165-head"><h3>選手別・実コース成績</h3></div><p class="be165-alert">この日の事前集計は未公開。個人の率を推定表示しません。</p>';return;}
    const end=data.source.as_of_d1||'－',cover=data.source.coverage?.[windowKey]||{}, {rows,map}=layout(race,data);
    const strongTrio=strongLane(rows,'trio',5),strongWin=strongLane(rows,'win',5);
    const sampleDate=windowKey==='3m'?'直近3か月':windowKey==='6m'?'直近6か月':'直近1年';
    const complete=cover.complete===true;
    host.innerHTML='<div class="be165-head"><h3>選手別・実コース成績</h3><small>履歴更新 '+esc(end)+'</small></div>'+
      '<p class="be165-note">選手本人が過去に実際に走った進入コース別成績。3連対率・1着率・平均STと決まり手を出走数つきで表示。</p>'+
      '<div class="be165-controls">'+[['3m','3か月'],['6m','6か月'],['1y','1年']].map(([k,label])=>'<button type="button" data-be165-window="'+k+'" class="'+(k===windowKey?'on':'')+'">'+label+'</button>').join('')+
      '<button type="button" data-be165-scope="entry" class="'+(scope==='entry'?'on':'')+'">今回の進入</button><button type="button" data-be165-scope="all" class="'+(scope==='all'?'on':'')+'">全コース合算</button></div>'+
      '<div class="be165-alert">'+esc(sampleDate)+'：履歴 '+esc(cover.days_with_both_sources??'－')+'/'+esc(cover.expected_calendar_days??'－')+'日'+(complete?'（全日収録）':'（欠損日あり・参考）')+'。'+
      (scope==='entry'?(map?'今回の展示進入に対応（本番の実進入確定ではありません）。':'実進入が未確定のため枠番＝コースの仮表示。'):'進入1〜6コースを合算。')+
      ' 直近10走の時系列集計は現データにはないため非表示。</div>'+
      '<div class="be165-scroll"><table class="be165-table"><thead><tr><th>艇・選手</th><th>進入</th><th>出走</th><th>1着率</th><th>2連対率</th><th>3連対率</th><th>平均ST</th></tr></thead><tbody>'+
      rows.map(r=>{const s=r.stats;
        return '<tr><th><button type="button" class="be165-row-button" data-be165-lane="'+r.lane+'"><span class="be165-boat">'+r.lane+'</span>'+esc(r.name)+' ▾</button></th>'+
          '<td>'+(scope==='all'?'全':r.course)+'コース</td><td>'+(s?s.starts+'走':'－')+'</td>'+
          '<td class="'+(r.lane===strongWin?'be165-strong':'')+'">'+fPercent(rateWin(s))+(s?'<span class="be165-sub">'+s.wins+'/'+s.starts+'</span>':'')+'</td>'+
          '<td>'+fPercent(s?ratio(s.top2,s.starts):null)+'</td>'+
          '<td class="'+(r.lane===strongTrio?'be165-strong':'')+'">'+fPercent(rateTrio(s))+(s?'<span class="be165-sub">'+s.top3+'/'+s.starts+'</span>':'')+'</td>'+
          '<td>'+(s&&s.st_n>0&&num(s.avg_st)!==null?Number(s.avg_st).toFixed(3):'－')+'</td></tr>';
      }).join('')+'</tbody></table></div><p class="be165-note">選手名を押すと逃げ・差し・まくり・まくり差しなどの決まり手内訳。サンプル5走未満は強調対象外。正式予想・買い目の確率には未接続。</p><div id="be165Details"></div>';
    drawDetails();
  }
  function init(){
    mount();
    const race=$('#raceView'),tab=$('#tab-data'),title=$('#raceTitle');
    if(typeof MutationObserver!=='undefined'){
      const obs=new MutationObserver(()=>{if(tab?.classList.contains('active'))draw();});
      for(const e of [race,tab])if(e)obs.observe(e,{attributes:true,attributeFilter:['class']});
      if(title)obs.observe(title,{childList:true,characterData:true,subtree:true});
    }
    document.addEventListener('visibilitychange',()=>{if(!document.hidden){lastRender='';draw(true);}});
    setInterval(()=>{if(tab?.classList.contains('active'))draw();},3000);
  }
  window.BoatEdgeV165={entryMap,combine,statFor,rateTrio,rateWin,strongLane};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
