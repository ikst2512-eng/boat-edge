
/* BOAT_EDGE_V136_SITE_ACCURACY_POST_RESULT */
(()=>{"use strict";
let running=false;
const labels={hit:"的中重視",balance:"バランス",hole:"波乱展開",narrow:"激絞り"};
function target(){
  const host=document.getElementById("auditView");
  if(!host)return null;
  let panel=document.getElementById("be136SiteAccuracy");
  if(!panel){
    panel=document.createElement("section");
    panel.id="be136SiteAccuracy";
    panel.className="section be136-accuracy";
    panel.innerHTML='<div class="card be136-shell"><div class="be136-title"><b>参考予想・実戦的中率</b><span>締切前保存 → 結果確定</span></div><p>評価データを読み込み中…</p></div>';
    host.insertBefore(panel,host.firstChild);
  }
  return panel.querySelector(".be136-shell");
}
async function render(){
  if(running)return;
  const root=target();if(!root)return;
  running=true;
  try{
    const url=`./data/site_learning/mode_accuracy_v136.json?v=${Math.floor(Date.now()/60000)}`;
    const res=await fetch(url,{cache:"no-store"});
    if(!res.ok)throw new Error("not published");
    const d=await res.json();
    if(d.schema_version!=="boat-edge-site-mode-accuracy-v136")throw new Error("schema");
    const n=Number(d.predictions_evaluated||0);
    const cards=Object.entries(labels).map(([k,label])=>{
      const r=d.modes?.[k]||{};
      const rate=Number.isFinite(Number(r.hit_rate_percent))&&r.hit_rate_percent!==null?`${r.hit_rate_percent}%`:"—";
      return `<div class="be136-mode"><strong>${label}</strong><b>${rate}</b><small>${Number(r.hits||0)}/${Number(r.evaluated||0)}R 的中</small></div>`;
    }).join("");
    /* BE137_AUDITED_WINNING_HEAD_SPLIT */
    // The split comes exclusively from the post-settlement V136 audited summary.
    const groups=[["1","1号艇が1着"],["2-6","2〜6号艇が1着"]];
    const splitRows=groups.map(([group,label])=>{
      const stats=d.by_winning_head?.[group]||{};
      const total=Number(stats.evaluated||0);
      const sub=Object.entries(labels).map(([key,name])=>{
        const hits=Math.max(0,Math.min(total,Number(stats.hits?.[key]||0)));
        const rate=total>0?(100*hits/total).toFixed(1)+"%":"—";
        return `<span class="be137-split-mode"><small>${name}</small><b>${rate}</b><small>${hits}/${total}R</small></span>`;
      }).join("");
      return `<div class="be137-split-group"><div class="be137-split-heading"><b>${label}</b><small>${total}R</small></div><div class="be137-split-grid">${sub}</div></div>`;
    }).join("");
    root.innerHTML=`<div class="be136-title"><b>参考予想・実戦的中率</b><span>締切前保存 → 結果確定</span></div>
      <div class="be136-count">監査済み確定レース <strong>${n}R</strong></div>
      <div class="be136-modes">${cards}</div>
      <details class="be137-split"><summary>1号艇・その他の1着別に的中率を見る</summary>
        <p class="be137-explain">勝った艇の号艇別集計です。「逃げ」の決まり手率ではありません。</p>
        <div class="be137-split-groups">${splitRows}</div>
      </details>
      <p class="be136-note">サイト参考予想の実績で、正式CURRENTの未見Fresh検証とは別集計。少数サンプルの的中率だけでは精度向上を証明できません。</p>`;
  }catch(e){
    root.innerHTML='<div class="be136-title"><b>参考予想・実戦的中率</b></div><p class="be136-note">採点データの公開待ち。締切前保存と結果確定の監査が揃ったレースだけ表示します。</p>';
  }finally{running=false}
}
function install(){
  target();
  render();
  document.addEventListener("click",e=>{
    if(e.target.closest?.('.bottomnav [data-view="auditView"]'))render();
  });
  document.addEventListener("visibilitychange",()=>{
    if(document.visibilityState==="visible"&&document.getElementById("auditView")?.classList.contains("active"))render();
  });
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
