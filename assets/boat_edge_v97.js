/* BOAT_EDGE_V97_ODDS_PAYOUT_UX */
(()=>{"use strict";
const cache=new Map();
const yen=n=>Number.isFinite(n)?Math.round(n).toLocaleString()+"円":"－";
const pct=n=>Number.isFinite(n)?Math.round(n).toLocaleString()+"%":"－";
const numText=s=>{const m=String(s||"").replace(/,/g,"").match(/-?\d+(?:\.\d+)?/);return m?Number(m[0]):null};
const raceKey=()=>{const f=window.be90cur?.f||"";return f.match(/(\d{8}-\d{2}-\d{2})/)?.[1]||null};
async function oddsFor(key){
  if(!key)return null;
  const hit=cache.get(key), now=Date.now();
  if(hit&&now-hit.at<15000)return hit.value;
  const value=await fetch(`./data/site_odds/${key}.json?t=${now}`,{cache:"no-store"}).then(async r=>r.ok?r.json():null).catch(()=>null);
  cache.set(key,{at:now,value});return value;
}
function ensureInfo(row){
  let el=row.querySelector(".be97-odds");
  if(!el){el=document.createElement("div");el.className="be97-odds";row.appendChild(el)}
  return el;
}
function augmentRows(doc){
  const rows=[...document.querySelectorAll("#buyBoard .buy-ticket")];
  if(!rows.length)return;
  const odds=doc?.trifecta_odds||{};
  let total=0,minPay=Infinity,maxPay=0,minProfit=Infinity,maxProfit=-Infinity,priced=0;
  for(const row of rows){
    const combo=row.querySelector(".buy-combo")?.textContent?.trim();
    const stake=numText(row.querySelector(".buy-money")?.textContent);
    const o=combo?Number(odds[combo]):NaN;
    if(Number.isFinite(stake))total+=stake;
    const box=ensureInfo(row);
    if(!Number.isFinite(o)||!Number.isFinite(stake)||stake<=0){
      box.innerHTML='<span class="miss">オッズ未取得</span>';
      continue;
    }
    const payout=stake*o;
    const profit=payout;
    priced++;
    minPay=Math.min(minPay,payout);maxPay=Math.max(maxPay,payout);
    box.dataset.payout=String(payout);
    box.dataset.stake=String(stake);
    box.dataset.odds=String(o);
    box.innerHTML=`<span><small>オッズ</small><b>${o.toFixed(1)}倍</b></span><span><small>的中時払戻</small><b>${yen(payout)}</b></span><span><small>回収率</small><b class="be97-roi">計算中</b></span><span><small>損益</small><b class="be97-profit">計算中</b></span>`;
  }
  // total investment must be computed after all rows are scanned.
  for(const row of rows){
    const payout=Number(row.querySelector(".be97-odds")?.dataset?.payout);
    if(!Number.isFinite(payout)||!total)continue;
    const roi=payout/total*100;
    const profit=payout-total;
    minProfit=Math.min(minProfit,profit);maxProfit=Math.max(maxProfit,profit);
    const roiEl=row.querySelector(".be97-roi"), profitEl=row.querySelector(".be97-profit");
    if(roiEl)roiEl.textContent=pct(roi);
    if(profitEl){profitEl.textContent=(profit>=0?"+":"")+yen(profit);profitEl.classList.toggle("plus",profit>=0);profitEl.classList.toggle("minus",profit<0)}
  }
  let summary=document.querySelector("#buyBoard .be97-summary");
  if(!summary){summary=document.createElement("div");summary.className="be97-summary";document.getElementById("buyBoard")?.appendChild(summary)}
  if(priced){
    summary.innerHTML=`<div><small>総投資</small><b>${yen(total)}</b></div><div><small>的中時払戻レンジ</small><b>${yen(minPay)}〜${yen(maxPay)}</b></div><div><small>損益レンジ</small><b>${(minProfit>=0?"+":"")+yen(minProfit)}〜${(maxProfit>=0?"+":"")+yen(maxProfit)}</b></div><p>※各買い目が的中した場合の払戻。オッズは変動するため購入時点の値とズレる場合があります。</p>`;
  }else{
    summary.innerHTML=`<div><small>総投資</small><b>${yen(total)}</b></div><div><small>オッズ</small><b>未取得</b></div><p>公式3連単オッズ取得後に、払戻・損益・回収率を自動表示します。</p>`;
  }
}
let lastKey="",lastStamp=0;
async function run(){
  const key=raceKey();if(!key)return;
  const now=Date.now();
  if(key===lastKey&&now-lastStamp<5000)return;
  lastKey=key;lastStamp=now;
  const doc=await oddsFor(key);
  augmentRows(doc);
}
new MutationObserver(()=>run()).observe(document.documentElement,{subtree:true,childList:true});
setInterval(run,2500);run();
})();
