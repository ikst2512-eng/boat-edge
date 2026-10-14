/* V253: read-only site research miss taxonomy. No prediction alteration. */
(()=>{'use strict';
if(window.BoatEdgeV253)return;
const schema='BOAT_EDGE_V253_SITE_ONLY_FROZEN_TICKET_MISS_DIAGNOSTICS_V1';
const scope='POST_RESULT_SITE_RESEARCH_ONLY_NO_FORMAL_FRESH_ACCESS';
const keys=['hit','head_absent','second_absent_given_head','third_absent_given_head_second'];
const labels={
 hit:'3連単が買い目内',
 head_absent:'的中の1着艇が買い目の頭にない',
 second_absent_given_head:'1着艇はあるが2着艇の組合せがない',
 third_absent_given_head_second:'1・2着は揃うが3着艇がない'
};
const modes={
 v236:{hit10:'現行10点',balance10:'バランス10点',scenario7plus3:'展開別10点',coverage15:'広め15点'},
 v240:{hit10:'現行10点',pair_coverage10:'2着組合せ10点',second_coverage10:'2着候補10点'}
};
/* V236 V2/V3 freezes contain a separately predeclared headsecond10 comparator.
   It is not a replacement for the four historical displayed modes. */
const v236Policies=[
 'PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST',
 'PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER',
 'PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES'
];
const v236HeadSecondPolicies=v236Policies.slice(1);
function validated(v){
 if(v?.schema!==schema||v?.scope!==scope||v?.formal_result_access!==false||
    v?.production_model_changed!==false||v?.accuracy_improvement_proven!==false||
    v?.model_promotion_authorized!==false||v?.real_or_paper_wagers_placed!==0||
    !Number.isSafeInteger(v?.site_verified_reference_races)||v.site_verified_reference_races<0||
    !v.lanes||typeof v.lanes!=='object')return null;
 const result={};
 for(const lane of ['v236','v240']){
  const x=v.lanes[lane],m=modes[lane];
  if(!x||!Number.isSafeInteger(x.races_verified)||x.races_verified<0||
   x.races_verified>v.site_verified_reference_races||!Array.isArray(x.races)||
   x.races.length!==x.races_verified||!x.miss_categories)return null;
  if(Object.keys(x.miss_categories).length!==Object.keys(m).length)return null;
  const seen=new Set();
  for(const r of x.races){
   const expected=Object.keys(m);
   if(lane==='v236'){
    if(!v236Policies.includes(r?.candidate_policy))return null;
    if(v236HeadSecondPolicies.includes(r.candidate_policy))expected.push('headsecond10');
   }
   if(!/^20\d{6}-\d{2}-\d{2}$/.test(r?.race_key||'')||seen.has(r.race_key)||
      !/^[1-6]-[1-6]-[1-6]$/.test(r.winning_combo||'')||
      new Set(r.winning_combo.split('-')).size!==3||r.date_jst!==r.race_key.slice(0,8)||
      !r.categories||Object.keys(r.categories).length!==expected.length||
      !expected.every(k=>keys.includes(r.categories[k])))return null;
   seen.add(r.race_key);
  }
  for(const name of Object.keys(m)){
   const counts=x.miss_categories[name];
   if(!counts||Object.keys(counts).length!==keys.length||
      keys.some(k=>!Number.isSafeInteger(counts[k])||counts[k]<0)||
      keys.reduce((n,k)=>n+counts[k],0)!==x.races_verified||
      keys.some(k=>x.races.filter(r=>r.categories[name]===k).length!==counts[k]))
      return null;
  }
  if(lane==='v236'){
   const summaries=x.headsecond_by_frozen_policy;
   if(!summaries||Object.keys(summaries).length!==v236HeadSecondPolicies.length)return null;
   for(const policy of v236HeadSecondPolicies){
    const rowSet=x.races.filter(r=>r.candidate_policy===policy);
    const summary=summaries[policy];
    if(!summary||summary.matched_races!==rowSet.length||
       !summary.miss_categories||Object.keys(summary.miss_categories).length!==2)return null;
    for(const name of ['hit10','headsecond10']){
     const counts=summary.miss_categories[name];
     if(!counts||Object.keys(counts).length!==keys.length||
        keys.some(k=>!Number.isSafeInteger(counts[k])||counts[k]<0)||
        keys.reduce((n,k)=>n+counts[k],0)!==rowSet.length||
        keys.some(k=>rowSet.filter(r=>r.categories[name]===k).length!==counts[k]))return null;
    }
   }
  }
  result[lane]=x;
 }
 return result;
}
/* V266: same-race, same-10-ticket paired audit. No cross-cohort or 15pt comparison.
   McNemar two-sided exact sign test on discordant outcomes; descriptive only.
   Never select or promote a production model from this research display. */
function paired(lane,mode){
 const base=lane?.races,allowed=['v236','v240'];
 if(!Array.isArray(base)||!Object.prototype.hasOwnProperty.call(modes.v236,mode)&&
    !Object.prototype.hasOwnProperty.call(modes.v240,mode))return null;
 let gain=0,loss=0,both=0,neither=0;
 for(const row of base){
  const x=row?.categories?.hit10==='hit',y=row?.categories?.[mode]==='hit';
  if(x&&y)both++;else if(!x&&y)gain++;else if(x&&!y)loss++;else neither++;
 }
 const discordant=gain+loss;
 let p=1;
 if(discordant){
  // Exact binomial two-sided P(X <= min(gain,loss)); stable up to 200 races.
  const k=Math.min(gain,loss);
  let term=Math.pow(0.5,discordant),tail=term;
  for(let i=1;i<=k;i++){term*=((discordant-i+1)/i);tail+=term;}
  p=Math.min(1,2*tail);
 }
 return {races:base.length,gain,loss,both,neither,discordant,p_value:p};
}
function element(tag,cls,txt){
 const x=document.createElement(tag);if(cls)x.className=cls;
 if(txt!==undefined)x.textContent=txt;return x;
}
/* V271: research-only priority is calculated from verified frozen tickets.
   A descriptive miss count is never used as a model weight or probability. */
function missPriority(lane){
 const c=lane?.miss_categories?.hit10,n=lane?.races_verified;
 if(!c||!Number.isSafeInteger(n)||n<1)return null;
 const order=[['head_absent','1着候補なし'],['second_absent_given_head','2着組合せ抜け'],
              ['third_absent_given_head_second','3着候補抜け']];
 const sorted=order.map(([key,label])=>({key,label,count:c[key]}))
  .sort((a,b)=>b.count-a.count);
 if(!sorted.every(x=>Number.isSafeInteger(x.count)&&x.count>=0))return null;
 if(sorted[0].count===sorted[1].count)return null;
 return {...sorted[0],total:n,hit:c.hit};
}
function render(v){
 const root=document.getElementById('v253Misses');if(!root)return;
 root.replaceChildren();
 const proof=validated(v);
 if(!proof){
  root.append(element('p','v253-warning','監査証拠の照合待ち。未取得・不一致の件数を推定しません。'));
  return;
 }
 const priority=missPriority(proof.v236);
 if(priority){
  const box=element('div','v271-miss-priority');
  box.append(element('strong','', '現行10点の取りこぼし最多：'+priority.label));
  box.append(element('p','',priority.total+'Rの締切前固定・確定後照合で '+priority.count+
    'R。現行10点の的中は '+priority.hit+'/'+priority.total+
    'R。分類上の最多であり、改善効果・本番採用を意味しません。'));
  const link=element('a','', '3着重点10点の未見検証を見る →');
  link.href='#v254Research';
  if(priority.key==='third_absent_given_head_second')box.append(link);
  root.append(box);
 }
 for(const lane of ['v236','v240']){
  const x=proof[lane],section=element('section','v253-lane');
  section.append(element('h3','',lane==='v236'?'10点と15点（別点数・別評価）':'同じ10点での展開比較'));
  section.append(element('p','v253-scope','締切前固定・確定後照合 '+x.races_verified+
    'R（全サイト照合 '+v.site_verified_reference_races+'Rのうち研究条件が揃った対象）'));
  const table=element('table','v253-table'),head=element('tr');
  for(const txt of ['方式','的中','1着なし','2着抜け','3着抜け'])head.append(element('th','',txt));
  const h=element('thead');h.append(head);table.append(h);
  const body=element('tbody');
  for(const [name,label] of Object.entries(modes[lane])){
   const c=x.miss_categories[name],row=element('tr');
   for(const txt of [label,c.hit+'/'+x.races_verified,c.head_absent,
       c.second_absent_given_head,c.third_absent_given_head_second])
      row.append(element('td','',String(txt)));
   if(name==='hit10')row.className='v253-base';
   body.append(row);
  }
  table.append(body);section.append(table);
  if(lane==='v240'){
   const p=element('div','v253-paired');
   p.append(element('strong','', '同じレース・同じ10点の直接比較'));
   for(const name of ['pair_coverage10','second_coverage10']){
    const z=paired(x,name);
    if(!z)continue;
    p.append(element('p','',modes.v240[name]+'：現行10点だけ外れ・候補だけ的中 '+z.gain+
      'R／現行10点だけ的中・候補だけ外れ '+z.loss+
      'R。両方的中 '+z.both+'R、両方外れ '+z.neither+
      'R。差が出た '+z.discordant+'R、両側正確検定 p='+z.p_value.toFixed(3)+
      '（小標本・研究表示。的中率改善の証明や本番採用ではありません）'));
   }
   section.append(p);
  }
  const recent=x.races.filter(r=>r.categories.hit10!=='hit').slice(-5);
  if(recent.length){
   section.append(element('p','v253-misses-heading','現行10点の直近の取りこぼし（研究対象のみ）'));
   const lines=element('div','v253-recent');
   for(const r of recent.reverse()){
    const item=element('div','v253-recent-row');
    item.append(element('strong','',r.race_key+' / '+r.winning_combo));
    item.append(element('span','',labels[r.categories.hit10]));
    lines.append(item);
   }
   section.append(lines);
  }
  root.append(section);
 }
 root.append(element('p','v253-foot','「1着なし」は実際の1着艇が買い目の1着欄にない意味。「2着抜け」はその1着艇を含む買い目はあるが、1・2着の組合せがない意味。頭予想そのものの正解率とは別です。後付け買い目の修正・モデル変更・実購入はしません。'));
}
async function update(){
 const box=document.getElementById('v253Misses');if(!box)return;
 try{
  const r=await fetch('./data/site_autopilot/v253_miss_diagnostics_current.json?ts='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  render(await r.json());
 }catch(e){render(null)}
}
function start(){
 document.getElementById('v253Reload')?.addEventListener('click',update);
 update();
 setInterval(()=>{if(!document.hidden)update()},120000);
}
window.BoatEdgeV253={validated,paired,missPriority,render,update};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
