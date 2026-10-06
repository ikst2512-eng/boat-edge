/* BOAT_EDGE_SITE_V59_RESULTS_LEARNING */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const KEY="boat_edge_v57_learning_log";
const now=()=>new Date().toISOString();
function logs(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}}
function save(a){try{localStorage.setItem(KEY,JSON.stringify(a.slice(-1000)))}catch(_){}}
function normCombo(v){
 if(Array.isArray(v)) return v.slice(0,3).join("-");
 const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);
 return m?`${m[1]}-${m[2]}-${m[3]}`:null;
}
function flattenTickets(pred){
 const out=[], seen=new Set();
 const worlds=[
  ["A",pred?.worldA||pred?.world_a||pred?.pattern_a],
  ["B",pred?.worldB||pred?.world_b||pred?.pattern_b]
 ];
 for(const [world,w] of worlds){
  const arr=w?.tickets||w?.bets||w?.combinations||[];
  for(const t of arr){
   const combo=normCombo(t?.combo||t?.combination||t?.ticket||t?.trifecta||t);
   if(!combo||seen.has(combo))continue;
   seen.add(combo);
   const p=Number(t?.probability??t?.prob??t?.p??t?.rate);
   const stake=Number(t?.amount??t?.stake??t?.yen);
   out.push({combo,world,probability:Number.isFinite(p)?p:null,stake:Number.isFinite(stake)?stake:null});
  }
 }
 // fallback prediction in current index uses worldA/worldB tickets; if unavailable, parse visible ticket text.
 if(!out.length){
   const text=$("#tab-pred")?.innerText||"";
   for(const m of text.matchAll(/([1-6])\s*[-－]\s*([1-6])\s*[-－]\s*([1-6])(?:[^\n%]*?(\d+(?:\.\d+)?)\s*%)?/g)){
     const combo=`${m[1]}-${m[2]}-${m[3]}`; if(seen.has(combo))continue; seen.add(combo);
     out.push({combo,world:null,probability:m[4]?Number(m[4]):null,stake:null});
   }
 }
 out.sort((a,b)=>(b.probability??-1)-(a.probability??-1));
 return out;
}
function currentRace(){
 try{return typeof state!=="undefined"?state.race:null}catch(_){return null}
}
function currentPrediction(race){
 try{return typeof getPrediction==="function"&&race?getPrediction(race):null}catch(_){return null}
}
function ensureStructuredSnapshot(){
 const race=currentRace(); if(!race?.race_key)return null;
 const a=logs(); let snap=a.find(x=>x.type==="prediction_snapshot_v59"&&x.key===race.race_key);
 if(snap)return snap;
 const pred=currentPrediction(race), tickets=flattenTickets(pred);
 snap={type:"prediction_snapshot_v59",key:race.race_key,saved_at:now(),version:"V59",
       model:pred?.model||race?.derived?.model||race?.current_model_input?.model||null,
       tickets:tickets.map((x,i)=>({...x,rank:i+1})),
       decision:pred?.decision||race?.derived?.decision||null};
 a.push(snap); save(a); return snap;
}
async function fetchResult(key){
 if(!key)return null;
 try{
  const r=await fetch(`./data/site_results/${key}.json?t=${Date.now()}`,{cache:"no-store"});
  if(!r.ok)return null;
  const d=await r.json();
  return d?.status==="confirmed"?d:null;
 }catch(_){return null}
}
function evaluation(snap,res){
 const win=normCombo(res?.trifecta||res?.finish_order);
 const tickets=snap?.tickets||[];
 const ix=tickets.findIndex(x=>x.combo===win);
 const hit=ix>=0;
 const ticket=hit?tickets[ix]:null;
 const payout100=Number(res?.trifecta_payout_yen_per_100);
 const stake=Number(ticket?.stake);
 const actualPayout=hit&&Number.isFinite(payout100)&&Number.isFinite(stake)?Math.floor(payout100*(stake/100)):null;
 const totalStake=tickets.reduce((s,x)=>s+(Number.isFinite(Number(x.stake))?Number(x.stake):0),0);
 const profit=actualPayout!==null&&totalStake>0?actualPayout-totalStake:null;
 return {winning_combo:win,winning_rank:hit?ix+1:null,hit,payout100:Number.isFinite(payout100)?payout100:null,
         hit_stake:Number.isFinite(stake)?stake:null,total_stake:totalStake||null,actual_payout:actualPayout,profit};
}
function persistEval(key,ev,res){
 const a=logs(); const i=a.findIndex(x=>x.type==="result_evaluation_v59"&&x.key===key);
 const row={type:"result_evaluation_v59",key,evaluated_at:now(),version:"V59",...ev,result:res};
 if(i>=0)a[i]=row;else a.push(row); save(a);
}
function panel(){
 let p=$("#be59Result");
 if(!p){p=document.createElement("section");p.id="be59Result";const host=$("#tab-pred .section")||$("#tab-pred");host?.prepend(p)}
 return p;
}
function money(v){return v===null||v===undefined?"未取得":`${Number(v).toLocaleString("ja-JP")}円`}
function renderPending(){
 const p=panel(); if(!p)return;
 p.innerHTML=`<div class="be59-card pending"><small>レース結果</small><strong>結果待ち</strong><p>結果公開後、自動で的中判定・払戻・収支を反映します。</p></div>`;
}
function renderResult(ev,res,snap){
 const p=panel();if(!p)return;
 const rank=ev.winning_rank?`${ev.winning_rank}位`:"表示買い目外";
 const cls=ev.hit?"hit":"miss";
 p.innerHTML=`<div class="be59-card ${cls}">
 <div class="be59-top"><div><small>確定結果</small><strong>${esc(ev.winning_combo)}</strong></div><b>${ev.hit?"的中":"不的中"}</b></div>
 <div class="be59-grid">
   <div><span>正解の予測順位</span><strong>${esc(rank)}</strong></div>
   <div><span>3連単払戻（100円）</span><strong>${money(ev.payout100)}</strong></div>
   <div><span>購入額</span><strong>${money(ev.total_stake)}</strong></div>
   <div><span>実払戻</span><strong>${money(ev.actual_payout)}</strong></div>
   <div><span>収支</span><strong>${ev.profit===null?"未計算":`${ev.profit>=0?"+":""}${ev.profit.toLocaleString("ja-JP")}円`}</strong></div>
 </div>
 <p class="be59-note">${ev.hit?"予想時点で保存した買い目と確定結果を照合。":"予想時点の保存内容は変更せず、確定結果だけを後から照合しています。"}</p>
 </div>`;
}
async function run(){
 const race=currentRace(); if(!race?.race_key)return;
 const snap=ensureStructuredSnapshot(); const res=await fetchResult(race.race_key);
 if(!res){renderPending();return}
 const ev=evaluation(snap,res);persistEval(race.race_key,ev,res);renderResult(ev,res,snap);
}
function hook(){
 if(typeof renderRace==="function"&&!renderRace.__be59){
  const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(()=>run());return x};renderRace.__be59=true;
 }
 if(currentRace())run();
 setInterval(()=>{if(document.visibilityState==="visible"&&currentRace())run()},60000);
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")run()});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();