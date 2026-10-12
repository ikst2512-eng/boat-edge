/* BOAT EDGE V252: descriptive only. Site-only, prospectively frozen research
   scoreboards. No formal result reads, model promotion, ticket edits, or staking. */
(()=>{'use strict';
 if(window.BoatEdgeV252)return;
 const V236='BOAT_EDGE_V236_HITRATE_SCORE_SUMMARY_V1';
 const V240='BOAT_EDGE_V240_SCORE_SUMMARY_V1';
 const S236='POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH';
 const S240='POST_RESULT_SITE_RESEARCH_NO_FORMAL_ACCESS';
 const KEYS236=['hit10','balance10','scenario7plus3','coverage15'];
 const KEYS240=['hit10','pair_coverage10','second_coverage10'];
 const goodKey=s=>/^20\d{6}-\d{2}-\d{2}$/.test(String(s||''));
 const int=n=>Number.isSafeInteger(n)&&n>=0;
 const notPromoted=d=>d?.production_model_changed===false&&d?.promotion_authorized===false;
 function evaluate(d,schema,scope,keys,paired=false){
   if(!d||d.schema!==schema||d.scope!==scope||!notPromoted(d)||
      (paired&&d.accuracy_improvement_proven!==false)||
      !int(d.scored_total)||d.scored_total===0||!Array.isArray(d.examples)||
      d.examples.length!==d.scored_total||!d.comparisons)return null;
   const seen=new Set(),raceDays=new Set(),rows=d.examples;
   for(const r of rows){
     if(!goodKey(r?.race_key)||seen.has(r.race_key)||!r.outcomes||
        keys.some(k=>typeof r.outcomes[k]!=='boolean'))return null;
     seen.add(r.race_key);raceDays.add(r.race_key.slice(0,8));
   }
   if(raceDays.size!==1)return null; // mixed dates must be clearly represented before aggregation.
   const output=[];
   for(const k of keys){
     const x=d.comparisons[k];
     const n=x?.races,hit=x?.hits??x?.hit,points=x?.points??x?.avg_points;
     if(n!==d.scored_total||!int(hit)||hit>n||!int(points)||points!==(k==='coverage15'?15:10))return null;
     const actual=rows.filter(r=>r.outcomes[k]).length;
     if(actual!==hit)return null;
     const pairedGain=rows.filter(r=>r.outcomes[k]&&!r.outcomes.hit10).length;
     const pairedLoss=rows.filter(r=>!r.outcomes[k]&&r.outcomes.hit10).length;
     if(paired&&(
       x.paired_gain!==pairedGain||x.paired_loss!==pairedLoss||
       x.changed_races!==rows.filter(r=>r.outcomes[k]!==r.outcomes.hit10||k!=='hit10').length
     ))return null;
     output.push({key:k,points,n,hits:hit,rate:100*hit/n,gain:pairedGain,loss:pairedLoss});
   }
   const control=output.find(x=>x.key==='hit10');
   return {day:[...raceDays][0],n:d.scored_total,control,rows:output,
     paired,source:scope,label:paired?'同じ10点の前向き比較':'10点と15点を分けた前向き比較'};
 }
 const check236=d=>evaluate(d,V236,S236,KEYS236,false);
 const check240=d=>evaluate(d,V240,S240,KEYS240,true);
 const labels={hit10:'現行10点',balance10:'バランス10点',
   scenario7plus3:'展開別10点',coverage15:'広め15点',
   pair_coverage10:'2着組合せ10点',second_coverage10:'2着候補10点'};
 const fmt=(n,digits=1)=>Number(n).toFixed(digits);
 function renderBlock(root,data){
   root.replaceChildren();
   if(!data){
     const e=document.createElement('p');
     e.className='v252-warning';e.textContent='取得値と照合対象が一致しないため、この比較は非表示（未確認）。';
     root.append(e);return;
   }
   const label=document.createElement('p');label.className='v252-scope';
   label.textContent=data.label+' ／ 固定・確定照合済み '+data.n+'R ／ '+data.day+
      ' ／ サイト研究専用・正式Freshとは別。';
   root.append(label);
   const table=document.createElement('table');table.className='v252-table';
   const head=document.createElement('thead');const tr=document.createElement('tr');
   for(const h of ['予想方式','点数','的中','率','現行との得失']){
     const th=document.createElement('th');th.textContent=h;tr.append(th);
   }
   head.append(tr);table.append(head);
   const body=document.createElement('tbody');
   for(const r of data.rows){
     const tr=document.createElement('tr');
     const cells=[labels[r.key]||r.key, r.points+'点',r.hits+'/'+r.n+'R',
       fmt(r.rate)+'%',r.key==='hit10'?'比較基準':
       data.paired?'拾えた '+r.gain+'R／失った '+r.loss+'R':
         r.points===10?'比較内訳は別集計': '10点より5点多い（同条件比較不可）'];
     for(const value of cells){const td=document.createElement('td');td.textContent=value;tr.append(td);}
     if(r.key==='hit10')tr.className='v252-control';
     body.append(tr);
   }
   table.append(body);root.append(table);
 }
 async function get(path){
   const res=await fetch('./data/site_autopilot/'+path+'?v252='+Date.now(),{cache:'no-store'});
   if(!res.ok)throw new Error('HTTP '+res.status);
   return res.json();
 }
 let pending=false;
 async function update(){
   const node=document.getElementById('v252Evidence');
   if(!node||pending)return;
   pending=true;
   const status=document.getElementById('v252Status');
   status.textContent='保存済み前向き検証データを照合中';
   const [r236,r240]=await Promise.allSettled([
     get('v236_score_current.json'),get('v240_score_current.json')]);
   const a=r236.status==='fulfilled'?check236(r236.value):null;
   const b=r240.status==='fulfilled'?check240(r240.value):null;
   renderBlock(document.getElementById('v252Equal'),b);
   renderBlock(document.getElementById('v252Wide'),a);
   status.textContent=a&&b?'検証データ照合済み（モデル昇格なし）':'一部データ未確認（モデル昇格なし）';
   pending=false;
 }
 function init(){
   const anchor=document.getElementById('v252Evidence');if(!anchor)return;
   document.getElementById('v252Reload')?.addEventListener('click',update);
   update();setInterval(()=>{if(!document.hidden)update();},120000);
 }
 window.BoatEdgeV252={check236,check240,evaluate,renderBlock,update};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
 else init();
})();
