/* BOAT_EDGE_V101_PREDICTION_MODES_HISTORY */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"－").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const n=v=>Number(v);
const pct=v=>Number.isFinite(n(v))?(n(v)<=1?n(v)*100:n(v)).toFixed(1)+"%":"－";
const yen=v=>Number.isFinite(n(v))?Math.round(n(v)).toLocaleString("ja-JP")+"円":"－";
const keyOf=()=>{try{return state?.race?.race_key||null}catch(_){return null}};
const raceOf=()=>{try{return state?.race||null}catch(_){return null}};
const predOf=()=>{try{const r=raceOf();return r&&typeof getPrediction==="function"?getPrediction(r):null}catch(_){return null}};

const SNAP_PREFIX="boatEdgeV101Snapshot:";
const HISTORY_KEY="boatEdgeV101History";
const ACTIVE_MODE_KEY="boatEdgeV101ActiveMode";
const LABELS={
  hit:{name:"的中重視",desc:"候補を広めに残して取りこぼしを減らす",icon:"◎"},
  balance:{name:"バランス重視",desc:"確率とオッズの両方を見て選ぶ",icon:"◐"},
  hole:{name:"穴重視",desc:"予想候補内で高配当寄りを優先",icon:"◆"},
  narrow:{name:"激絞り重視",desc:"確率上位だけを3点に絞る",icon:"⚡"}
};

function normalizeCombo(v){
  if(Array.isArray(v))return v.slice(0,3).join("-");
  const m=String(v||"").match(/([1-6])\D+([1-6])\D+([1-6])/);
  return m?`${m[1]}-${m[2]}-${m[3]}`:null;
}
function allTickets(pred){
  const out=[],seen=new Set();
  for(const [wi,w] of (pred?.worlds||[]).entries()){
    for(const [i,t] of (w?.tickets||[]).entries()){
      const combo=normalizeCombo(t?.combo||t?.trifecta||t?.order);
      if(!combo||seen.has(combo))continue;
      seen.add(combo);
      const raw=n(t?.probability??t?.confidence??t?.prob??t?.p);
      out.push({
        combo,
        p:Number.isFinite(raw)?(raw<=1?raw*100:raw):0,
        amount:Number.isFinite(n(t?.amount))?n(t.amount):0,
        world:w?.key||(wi===0?"A":"B"),
        rank:i+1
      });
    }
  }
  out.sort((a,b)=>b.p-a.p);
  return out;
}
async function J(u){
  try{
    const r=await fetch(u+(u.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});
    return r.ok?await r.json():null;
  }catch(_){return null}
}
async function oddsMap(key){
  const d=await J(`./data/site_odds/${key}.json`);
  return d?.trifecta_odds||d?.odds||{};
}
async function resultFor(key){return await J(`./data/site_results/${key}.json`)}

function confidence(pred,mode,rows){
  const map={S:90,"S+":93,A:82,"A+":86,B:72,"B+":76,C:62,D:52};
  let base=map[String(pred?.grade||"").toUpperCase()]??68;
  const all=allTickets(pred),sum=all.reduce((s,x)=>s+Math.max(x.p,0),0);
  const top3=all.slice(0,3).reduce((s,x)=>s+Math.max(x.p,0),0);
  const concentration=sum>0?top3/sum:0;
  base += Math.round((concentration-.35)*18);
  base += ({hit:5,balance:0,hole:-9,narrow:-5}[mode]||0);
  if(rows.length<=3)base-=2;
  return Math.max(35,Math.min(94,Math.round(base)));
}
function selectModes(pred,odds){
  const all=allTickets(pred);
  const getOdds=x=>{const v=n(odds?.[x.combo]);return Number.isFinite(v)&&v>0?v:null};
  const hit=all.slice(0,Math.min(10,all.length));
  const balance=[...all].sort((a,b)=>{
    const ao=getOdds(a)??1,bo=getOdds(b)??1;
    return (b.p*Math.sqrt(Math.min(bo,80)))-(a.p*Math.sqrt(Math.min(ao,80)));
  }).slice(0,Math.min(6,all.length));
  const vals=all.map(getOdds).filter(Number.isFinite).sort((a,b)=>a-b);
  const median=vals.length?vals[Math.floor(vals.length/2)]:null;
  let hole=[...all].filter(x=>{
    const o=getOdds(x);
    return o!=null && (median==null || o>=median);
  }).sort((a,b)=>{
    const ao=getOdds(a)??1,bo=getOdds(b)??1;
    return (b.p*Math.pow(Math.min(bo,120),.72))-(a.p*Math.pow(Math.min(ao,120),.72));
  }).slice(0,Math.min(6,all.length));
  if(!hole.length)hole=all.slice(Math.min(3,all.length),Math.min(9,all.length));
  const narrow=all.slice(0,Math.min(3,all.length));
  const modes={hit,balance,hole,narrow};
  for(const k of Object.keys(modes)){
    modes[k]=modes[k].map(x=>({...x,odds:getOdds(x)}));
  }
  return modes;
}
function snapshotKey(key){return SNAP_PREFIX+key}
function loadSnapshot(key){
  try{return JSON.parse(localStorage.getItem(snapshotKey(key))||"null")}catch(_){return null}
}
function saveSnapshot(key,race,pred,modes){
  if(loadSnapshot(key))return loadSnapshot(key);
  const payload={
    schema:"boat-edge-v101-local-snapshot-v1",
    race_key:key,
    saved_at:new Date().toISOString(),
    venue:race?.meta?.venue||"",
    race_no:race?.meta?.race_no||"",
    deadline:race?.meta?.deadline||"",
    model_mode:pred?.mode||null,
    grade:pred?.grade||null,
    modes:Object.fromEntries(Object.entries(modes).map(([k,rows])=>[
      k,{confidence:confidence(pred,k,rows),tickets:rows.map(x=>({combo:x.combo,p:x.p,odds:x.odds??null}))}
    ]))
  };
  try{localStorage.setItem(snapshotKey(key),JSON.stringify(payload))}catch(_){}
  return payload;
}
function loadHistory(){
  try{return JSON.parse(localStorage.getItem(HISTORY_KEY)||"[]")}catch(_){return []}
}
function saveHistory(rows){
  try{localStorage.setItem(HISTORY_KEY,JSON.stringify(rows.slice(0,120)))}catch(_){}
}
function settleSnapshot(snapshot,result){
  if(!snapshot||result?.status!=="confirmed")return null;
  const win=normalizeCombo(result.trifecta||result.finish_order);
  if(!win)return null;
  const modeHits={};
  for(const [k,v] of Object.entries(snapshot.modes||{})){
    modeHits[k]=(v.tickets||[]).some(x=>x.combo===win);
  }
  const item={
    race_key:snapshot.race_key,
    venue:snapshot.venue,
    race_no:snapshot.race_no,
    saved_at:snapshot.saved_at,
    winning_combo:win,
    payout:result.trifecta_payout_yen_per_100??null,
    mode_hits:modeHits,
    hit_any:Object.values(modeHits).some(Boolean)
  };
  const rows=loadHistory().filter(x=>x.race_key!==item.race_key);
  rows.unshift(item);saveHistory(rows);
  return item;
}
function activeMode(){
  try{return localStorage.getItem(ACTIVE_MODE_KEY)||"balance"}catch(_){return "balance"}
}
function setActiveMode(k){
  try{localStorage.setItem(ACTIVE_MODE_KEY,k)}catch(_){}
}
function ensurePanel(){
  let el=$("#be101PredictionModes");
  if(el)return el;
  const stack=$("#tab-pred .section.stack");
  if(!stack)return null;
  el=document.createElement("section");
  el.id="be101PredictionModes";
  el.className="be101-panel";
  const buy=$("#buyBoard",stack);
  if(buy)stack.insertBefore(el,buy);else stack.prepend(el);
  return el;
}
function historyHtml(){
  const rows=loadHistory();
  const hits=rows.filter(x=>x.hit_any);
  if(!hits.length)return `<div class="be101-empty">まだ🎯的中履歴はありません。結果前に表示した予想を、確定後に自動照合します。</div>`;
  return hits.slice(0,30).map(x=>{
    const modes=Object.entries(x.mode_hits||{}).filter(([,v])=>v).map(([k])=>LABELS[k]?.name||k).join(" / ");
    return `<div class="be101-history-row"><div><b>🎯 ${esc(x.venue)} ${esc(x.race_no)}R</b><span>${esc(x.winning_combo)}</span></div><div><small>${esc(modes)}</small>${x.payout?`<strong>${yen(x.payout)}/100円</strong>`:""}</div></div>`;
  }).join("");
}
function renderTicketRows(rows,win){
  return rows.map((x,i)=>{
    const hit=win&&x.combo===win;
    return `<div class="be101-ticket ${hit?"hit":""}">
      <span class="be101-rank">${i+1}</span>
      <b>${hit?"🎯 ":""}${esc(x.combo)}</b>
      <span>${pct(x.p)}</span>
      <span>${x.odds?`${x.odds.toFixed(1)}倍`:"オッズ－"}</span>
    </div>`;
  }).join("");
}
async function render(){
  const race=raceOf(),pred=predOf(),key=keyOf();
  if(!race||!pred||!key)return;
  const panel=ensurePanel();if(!panel)return;
  const [odds,result]=await Promise.all([oddsMap(key),resultFor(key)]);
  const modes=selectModes(pred,odds);
  let snap=loadSnapshot(key);
  if(result?.status!=="confirmed"&&!snap)snap=saveSnapshot(key,race,pred,modes);
  const settled=snap&&result?.status==="confirmed"?settleSnapshot(snap,result):null;
  const win=settled?.winning_combo||null;
  let mode=activeMode();if(!LABELS[mode])mode="balance";
  const currentRows=(snap?.modes?.[mode]?.tickets||modes[mode]||[]).map(x=>({
    ...x,odds:x.odds??(Number.isFinite(n(odds?.[x.combo]))?n(odds[x.combo]):null)
  }));
  const conf=snap?.modes?.[mode]?.confidence??confidence(pred,mode,currentRows);
  const hit=settled?.mode_hits?.[mode]===true;

  panel.innerHTML=`
    <div class="be101-head">
      <div><h3>予想スタイル</h3><p>同じ予想候補を目的別に表示</p></div>
      <button id="be101HistoryBtn" type="button">🎯 的中履歴</button>
    </div>
    <div class="be101-mode-tabs">
      ${Object.entries(LABELS).map(([k,v])=>{
        const h=settled?.mode_hits?.[k]===true;
        return `<button type="button" data-mode="${k}" class="${k===mode?"on":""}">${h?"🎯 ":""}${v.name}</button>`;
      }).join("")}
    </div>
    <div class="be101-mode-card ${hit?"hit":""}">
      <div class="be101-mode-top">
        <div><b>${hit?"🎯 ":""}${LABELS[mode].icon} ${LABELS[mode].name}</b><span>${LABELS[mode].desc}</span></div>
        <div class="be101-confidence"><small>内部信頼度</small><strong>${conf}%</strong></div>
      </div>
      <div class="be101-ticket-list">${renderTicketRows(currentRows,win)}</div>
      <p class="be101-note">※信頼度はモデルの勝負度・予想集中度から出す内部評価で、的中保証ではありません。結果前に保存した予想だけ🎯履歴へ残します。</p>
    </div>
    <div id="be101History" class="be101-history" hidden>
      <div class="be101-history-title"><b>🎯 的中履歴</b><span>この端末で結果前に保存した予想</span></div>
      ${historyHtml()}
    </div>`;

  $$(".be101-mode-tabs [data-mode]",panel).forEach(b=>b.onclick=()=>{setActiveMode(b.dataset.mode);render()});
  $("#be101HistoryBtn",panel).onclick=()=>{
    const h=$("#be101History",panel);h.hidden=!h.hidden;
    if(!h.hidden)h.scrollIntoView({behavior:"smooth",block:"nearest"});
  };
}
let last="";
async function tick(){
  const key=keyOf();
  if(!key)return;
  if(key!==last){last=key;await render();return}
  if($("#raceView")?.classList.contains("active"))await render();
}
document.addEventListener("click",e=>{
  if(e.target.closest?.("#raceNav [data-file],#raceTabs [data-tab]"))setTimeout(render,160);
},true);
new MutationObserver(()=>{const k=keyOf();if(k&&k!==last)setTimeout(tick,40)}).observe(document.documentElement,{subtree:true,childList:true});
setInterval(tick,5000);
tick();
})();
