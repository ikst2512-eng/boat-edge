/* BOAT_EDGE_V139_PRE_RESULT_INPUT_AUDIT */
(()=>{"use strict";
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));}
function validSite(a,key){
  const item=a?.[key];
  return item?.status==="ok" && Boolean(item?.source && item?.fetched_at && item?.sha256);
}
function derive(race){
  const a=race?.source_audit||{};
  const racers=Array.isArray(race?.racers)?race.racers:[];
  const nos=racers.map(r=>String(r?.registration_no||""));
  const card=a.race_card?.status==="ok" && Boolean(a.race_card?.fetched_at) && racers.length===6 && nos.every(Boolean) && new Set(nos).size===6;
  const official=a.beforeinfo?.status==="ok" && Boolean(a.beforeinfo?.fetched_at) && race?.beforeinfo && Object.keys(race.beforeinfo).length>0;
  // CSV original_exhibition is NOT proof of two-site source binding.
  const both=validSite(a,"boaters_original_exhibition") && validSite(a,"keiteibiyori_original_exhibition");
  const formal=race?.current_model_input?.formal_prediction_ready===true;
  return {
    card: Boolean(card), official:Boolean(official), both:Boolean(both), formalClaimAllowed:false,
    formalityLabel:formal?"正式モデル入力は別途ゲート監査が必要":"サイトは参考予想（正式CURRENT未接続）",
    lastFetch:race?.meta?.updated_at||"時刻未確認",
    raceKey:race?.race_key||"不明"
  };
}
function render(race){
  if(!race?.race_key)return;
  const host=document.querySelector("#raceView .race-summary");
  if(!host)return;
  let box=document.getElementById("be139InputStatus");
  if(!box){
    box=document.createElement("details");box.id="be139InputStatus";
    box.className="be139-input-status";
    const h=host.querySelector(".summary-top");
    if(h)h.insertAdjacentElement("afterend",box);else host.prepend(box);
  }
  const s=derive(race), wasOpen=box.open;
  box.innerHTML=`<summary><b>予想材料の取得状況</b><span>${s.card?"出走表✓":"出走表未確認"} · ${s.official?"公式展示✓":"公式展示待ち"} · ${s.both?"外部2サイト✓":"外部2サイト未照合"}</span></summary>
    <div class="be139-body"><p><b>出走表：</b>${s.card?"6艇確認済み":"取得・6艇照合が未完了"}</p>
    <p><b>公式展示・実進入：</b>${s.official?"事前情報の取得を確認（実進入6艇照合は別途必要）":"未取得または取得時刻未確認"}</p>
    <p><b>BOATERS＋競艇日和：</b>${s.both?"両サイトの出所付き記録あり":"双方の原展示の出所照合は未完了"}</p>
    <p><b>選手別・実コース1年/6か月/3か月：</b>サイト参考予想には未接続</p>
    <p class="be139-warning">${esc(s.formalityLabel)}。未取得項目を「取得済み」とは扱いません。</p>
    <small>レースデータ更新：${esc(s.lastFetch)} ／ ${esc(s.raceKey)}</small></div>`;
  box.open=wasOpen;
}
window.BoatEdgeInputAuditV139={derive,render};
try{if(typeof state!=="undefined" && state?.race)render(state.race);}catch(_){/* no initial race */}
})();
