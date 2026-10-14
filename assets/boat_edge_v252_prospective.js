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
   const days=[...raceDays].sort();if(!days.length)return null;
   if(lane==='v236'){
     const summaries=p.headsecond_by_frozen_policy;
     if(!summaries||Object.keys(summaries).length!==forwardPolicies.length)return null;
     for(const policy of forwardPolicies){
       const matched=p.races.filter(r=>r.candidate_policy===policy);
       const entry=summaries[policy];
       if(!entry||entry.matched_races!==matched.length||
          !entry.miss_categories||Object.keys(entry.miss_categories).length!==2)return null;
       for(const mode of ['hit10','headsecond10']){
         const counts=entry.miss_categories[mode];
         if(!counts||Object.keys(counts).length!==cats.length||
            cats.some(k=>!int(counts[k]))||
            cats.reduce((n,k)=>n+counts[k],0)!==matched.length||
            cats.some(k=>matched.filter(r=>r.categories[mode]===k).length!==counts[k]))return null;
       }
     }
   }
   const output=[];
   for(const k of keys){
     const x=d.comparisons[k];
     const n=x?.races,hit=x?.hits??x?.hit,points=x?.points??x?.avg_points;
     if(n!==d.scored_total||!int(hit)||hit>n||!int(points)||points!==(k==='coverage15'?15:10))return null;
     const actual=rows.filter(r=>r.outcomes[k]).length;
     if(actual!==hit||!Number.isFinite(x.hit_rate_percent)||Math.abs(x.hit_rate_percent-100*hit/n)>0.1)return null;
     const pairedGain=rows.filter(r=>r.outcomes[k]&&!r.outcomes.hit10).length;
     const pairedLoss=rows.filter(r=>!r.outcomes[k]&&r.outcomes.hit10).length;
     if(paired&&(
       x.paired_gain!==pairedGain||x.paired_loss!==pairedLoss||
       !int(x.changed_races)||x.changed_races>n||(k==='hit10'&&x.changed_races!==0)
     ))return null;
     output.push({key:k,points,n,hits:hit,rate:100*hit/n,gain:pairedGain,loss:pairedLoss});
   }
   const control=output.find(x=>x.key==='hit10');
   return {day:days.length===1?days[0]:days[0]+'〜'+days[days.length-1],days,n:d.scored_total,control,rows:output,
     paired,source:scope,label:paired?'同じ10点の前向き比較':'10点と15点を分けた前向き比較'};
 }
 /* V257: V253 is a complete SHA/timestamp/result-crosschecked *site-only*
    research report, not a truncated example slice. Recompute the full-cohort
    comparison from individual classified ticket outcomes (never from odds). */
 const MISSSCHEMA='BOAT_EDGE_V253_SITE_ONLY_FROZEN_TICKET_MISS_DIAGNOSTICS_V1';
 const MISSCOPE='POST_RESULT_SITE_RESEARCH_ONLY_NO_FORMAL_FRESH_ACCESS';
 const cats=['hit','head_absent','second_absent_given_head','third_absent_given_head_second'];
 const v236Policies=[
  'PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST',
  'PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER',
  'PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES'
 ];
 const forwardPolicies=v236Policies.slice(1);
 function completeLane(d,lane,keys,paired){
   const p=d?.lanes?.[lane],n=p?.races_verified;
   if(!int(n)||n===0||n>d.site_verified_reference_races||
      !Array.isArray(p.races)||p.races.length!==n||!p.miss_categories||
      Object.keys(p.miss_categories).length!==keys.length)return null;
   const seen=new Set(),days=new Set();
   for(const r of p.races){
     const expected=keys.slice();
     if(lane==='v236'){
       if(!v236Policies.includes(r?.candidate_policy))return null;
       if(forwardPolicies.includes(r.candidate_policy))expected.push('headsecond10');
     }
     if(!goodKey(r?.race_key)||seen.has(r.race_key)||
        r.date_jst!==r.race_key.slice(0,8)||
        !/^([1-6]-){2}[1-6]$/.test(r.winning_combo||'')||
        new Set(r.winning_combo.split('-')).size!==3||
        !r.categories||Object.keys(r.categories).length!==expected.length||
        expected.some(k=>!cats.includes(r.categories[k])))return null;
     seen.add(r.race_key);days.add(r.date_jst);
   }
   const output=[];
   for(const k of keys){
     const counts=p.miss_categories[k],points=k==='coverage15'?15:10;
     if(!counts||Object.keys(counts).length!==cats.length||
        cats.some(c=>!int(counts[c]))||
        cats.reduce((a,c)=>a+counts[c],0)!==n||
        cats.some(c=>p.races.filter(r=>r.categories[k]===c).length!==counts[c]))return null;
     const gain=p.races.filter(r=>r.categories[k]==='hit'&&r.categories.hit10!=='hit').length;
     const loss=p.races.filter(r=>r.categories[k]!=='hit'&&r.categories.hit10==='hit').length;
     output.push({key:k,n,points,hits:counts.hit,rate:100*counts.hit/n,gain,loss});
   }
   const sortedDays=[...days].sort(),first=sortedDays[0],last=sortedDays[sortedDays.length-1];
   return {day:first===last?first:first+'〜'+last,days:sortedDays,n,
     control:output.find(r=>r.key==='hit10'),rows:output,paired,source:MISSCOPE,
     label:paired?'同じ10点・Git保存SHA照合済み':'10点と15点・Git保存SHA照合済み'};
 }
 function fromFullMissProof(d){
   if(!d||d.schema!==MISSSCHEMA||d.scope!==MISSCOPE||
      d.formal_result_access!==false||d.production_model_changed!==false||
      d.accuracy_improvement_proven!==false||d.model_promotion_authorized!==false||
      d.real_or_paper_wagers_placed!==0||!int(d.site_verified_reference_races)||
      !d.lanes||Object.keys(d.lanes).length!==2)return null;
   const a=completeLane(d,'v236',KEYS236,false);
   const b=completeLane(d,'v240',KEYS240,true);
   if(!a||!b)return null;
   return {a,b};
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
   const [r253,r236,r240]=await Promise.allSettled([
     get('v253_miss_diagnostics_current.json'),
     get('v236_score_current.json'),get('v240_score_current.json')]);
   const full=r253.status==='fulfilled'?fromFullMissProof(r253.value):null;
   // The fully crosschecked V253 lanes stay available even after upstream
   // summary "examples" are truncated at 20/25 rows.
   const a=full?.a||(r236.status==='fulfilled'?check236(r236.value):null);
   const b=full?.b||(r240.status==='fulfilled'?check240(r240.value):null);
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
 window.BoatEdgeV252={check236,check240,evaluate,fromFullMissProof,renderBlock,update};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
 else init();
})();
