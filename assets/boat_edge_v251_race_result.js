/* BOAT EDGE V251 — site-only proof-backed selected-race outcome.
 * Displays verified post-result site research separately from formally sealed Fresh.
 * No prediction, stake, odds, scratch, source, or result mutation. */
(function(root){
'use strict';
const REPORT='./data/site_autopilot/v241_results_current.json';
const SCHEMA='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1';
const SCOPE='VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH';
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const TRIPLE=/^[1-6]-[1-6]-[1-6]$/;
const PREFIX='./results-detail.html?race=';
const yen=n=>(typeof n==='number'&&Number.isSafeInteger(n)&&n>=0)?'¥'+n.toLocaleString('ja-JP'):'未確認';
const validKey=k=>typeof k==='string'&&KEY.test(k);
const validCombo=x=>typeof x==='string'&&TRIPLE.test(x)&&new Set(x.split('-')).size===3;
function verifiedReport(d){
 return Boolean(d&&d.schema===SCHEMA&&d.scope===SCOPE&&d.formal_result_access===false&&
 d.production_model_changed===false&&d.real_or_paper_wagers_placed===0&&
 Number.isSafeInteger(d.settled_verified_races)&&d.settled_verified_races>=0&&
 Array.isArray(d.rows)&&d.rows.length===d.settled_verified_races);
}
function verifiedRow(r){
 if(!r||!validKey(r.race_key)||!validCombo(r.winning_combo)||r.post_result_verified!==true||
 !Number.isSafeInteger(r.official_payout_per_100_yen)||r.official_payout_per_100_yen<=0||
 !/^[a-f0-9]{64}$/i.test(String(r.precommitted_sha256||''))||
 !/^[a-f0-9]{40}$/i.test(String(r.first_frozen_commit||''))||
 !r.mode_outcomes||!r.mode_outcomes.hit)return false;
 const hit=r.mode_outcomes.hit;
 if(r.top10_hit!==hit.hit||typeof r.head_hit!=='boolean'||r.head_hit!==(String(r.head_prediction)===r.winning_combo[0])||
 typeof hit.hit!=='boolean'||hit.stake_yen!==10000||
 !Number.isSafeInteger(hit.hypothetical_return_yen)||hit.hypothetical_return_yen<0||
 hit.hypothetical_profit_yen!==hit.hypothetical_return_yen-10000)return false;
 return ['hit','balance','hole','narrow'].every(m=>{
   const o=r.mode_outcomes[m];
   return o&&typeof o.hit==='boolean'&&o.stake_yen===10000&&
   Number.isSafeInteger(o.hypothetical_return_yen)&&o.hypothetical_return_yen>=0&&
   o.hypothetical_profit_yen===o.hypothetical_return_yen-10000;
 });
}
function resultFor(report,key){
 if(!verifiedReport(report)||!validKey(key))return null;
 const matching=report.rows.filter(r=>r.race_key===key);
 return matching.length===1&&verifiedRow(matching[0])?matching[0]:null;
}
if(typeof module!=='undefined'&&module.exports){
 module.exports={validKey,validCombo,verifiedReport,verifiedRow,resultFor,yen};
}
if(typeof document==='undefined'||typeof window==='undefined')return;
if(window.BoatEdgeV251)return;
let report=null, status='loading', loadedAt=0, inflight=false, currentKey='',signature='';
const find=(s,parent=document)=>parent.querySelector(s);
const text=(target,s)=>{if(target)target.textContent=String(s)};
const el=(tag,cls,contents)=>{
 const e=document.createElement(tag);
 if(cls)e.className=cls;
 if(contents!==undefined)e.textContent=String(contents);
 return e;
};
function selectedRace(){try{return typeof state==='undefined'?null:state?.race||null}catch(_){return null}}
function place(){
 const host=find('#raceView .race-summary');
 if(!host)return null;
 let box=find('#be251Outcome',host);
 if(box)return box;
 box=el('section','be251-outcome');
 box.id='be251Outcome';box.setAttribute('aria-label','選択中レースの検証済み結果');
 const title=el('div','be251-title');
 title.append(el('strong','', 'このレースの結果・的中'),el('span','be251-type','サイト参考予想のみ'));
 const body=el('div','be251-body','結果照合データを確認中…');
 body.setAttribute('aria-live','polite');
 box.append(title,body);
 const nav=find('#be249Focus',host)||find('.summary-top',host);
 if(nav)nav.insertAdjacentElement('afterend',box);else host.prepend(box);
 return box;
}
function view(){
 const host=find('#raceView');
 return host&&host.classList.contains('active');
}
function createChips(combo){
 const line=el('div','be251-chips');
 for(const n of combo.split('-')){
  const chip=el('b','be251-boat',n);
  chip.dataset.n=n;line.appendChild(chip);
 }
 return line;
}
function link(label,key){
 const a=el('a','be251-link',label);
 a.href=validKey(key)?PREFIX+encodeURIComponent(key):'./results.html';
 return a;
}
function render(){
 if(!view())return;
 const race=selectedRace(),key=race?.race_key||'';
 if(!validKey(key)){find('#be251Outcome')?.remove();currentKey='';signature='';return}
 const row=resultFor(report,key);
 const newSignature=JSON.stringify([key,status,report?.settled_verified_races||0,row?.precommitted_sha256||'',row?.mode_outcomes?.hit?.hit,row?.official_payout_per_100_yen]);
 if(newSignature===signature&&find('#be251Outcome'))return;
 signature=newSignature;currentKey=key;
 const box=place();
 if(!box)return;
 const body=find('.be251-body',box);
 body.replaceChildren();
 if(status!=='ok'){
  body.append(el('p','be251-muted',status==='loading'?'検証済み結果を照合中…':'結果データを確認できません。🎯は表示しません。'));
  const actions=el('div','be251-actions');actions.append(link('結果一覧を開く',null));body.append(actions);
  return;
 }
 if(!row){
  body.append(el('p','be251-muted','このレースのサイト参考予想は、まだ確定照合履歴に登録されていません。不的中を意味するものではありません。'));
  const actions=el('div','be251-actions');actions.append(link('結果・払戻の一覧',null));body.append(actions);
  return;
 }
 const mode=row.mode_outcomes.hit;
 const badge=el('div',mode.hit?'be251-badge good':'be251-badge miss',mode.hit?'🎯 3連単的中':'3連単不的中');
 const line=el('div','be251-race-result');line.append(badge,createChips(row.winning_combo));
 const pay=el('div','be251-money');
 const p=el('div');p.append(el('small','','公式100円払戻'),el('b','',yen(row.official_payout_per_100_yen)));
 const q=el('div');q.append(el('small','','仮想1万円の払戻'),el('b','',yen(mode.hypothetical_return_yen)));
 const u=el('div');u.className=mode.hypothetical_profit_yen>=0?'gain':'loss';
 u.append(el('small','','仮想損益'),el('b','',(mode.hypothetical_profit_yen>=0?'+':'−')+yen(Math.abs(mode.hypothetical_profit_yen))));
 pay.append(p,q,u);
 const note=el('p','be251-muted','1着予想 '+String(row.head_prediction)+'号艇：'+(row.head_hit?'頭的中':'頭外れ')+' ／ 締切前固定・サイト限定研究・実購入なし');
 const actions=el('div','be251-actions');
 actions.append(link('このRの買い目・配分を見る ›',key),link('結果一覧',null));
 body.append(line,pay,note,actions);
}
async function load(){
 if(inflight)return;
 inflight=true;const start=Date.now();
 try{
  const res=await fetch(REPORT+'?t='+start,{cache:'no-store'});
  if(!res.ok)throw Error('HTTP '+res.status);
  const data=await res.json();
  if(!verifiedReport(data)||!data.rows.every(verifiedRow))throw Error('UNVERIFIED_SITE_REPORT');
  report=data;status='ok';
 }catch(_){report=null;status='unavailable'}
 finally{inflight=false;loadedAt=Date.now();signature='';render()}
}
function tick(){
 if(!view())return;
 render();
 if(!inflight&&Date.now()-loadedAt>90000)load();
}
function start(){
 tick();load();
 window.setInterval(()=>{if(!document.hidden)tick()},2500);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick()});
}
window.BoatEdgeV251={refresh:load,version:'V251-READONLY-SITE-RESULT'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:{});
