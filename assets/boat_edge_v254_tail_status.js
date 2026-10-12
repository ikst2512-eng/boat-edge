/* V254 future-only 10-ticket third-leg shadow; presentation only. */
(()=>{'use strict';
if(window.BoatEdgeV254)return;
const schemaPre='BOAT_EDGE_V254_FUTURE_THIRD_TAIL_PRE_SUMMARY_V1';
const schemaScore='BOAT_EDGE_V254_FUTURE_THIRD_TAIL_SCORE_SUMMARY_V1';
const validPre=x=>x?.schema===schemaPre&&x?.scope==='PRE_RESULT_FUTURE_SITE_RESEARCH_NOT_FORMAL_FRESH'&&
 x.result_access===false&&x.production_model_changed===false&&
 x.accuracy_improvement_proven===false&&x.model_promotion_authorized===false&&
 /^20\d{6}$/.test(x.day_jst||'')&&
 [x.frozen_today,x.third_tail_novel_races_today,x.third_tail_novel_tickets_today].every(n=>Number.isSafeInteger(n)&&n>=0)&&
 x.third_tail_novel_races_today<=x.frozen_today&&x.third_tail_novel_tickets_today<=3*x.frozen_today;
const validScore=x=>{
 if(x?.schema!==schemaScore||x?.scope!=='POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH'||
 x.formal_result_access!==false||x.production_model_changed!==false||
 x.accuracy_improvement_proven!==false||x.model_promotion_authorized!==false||
 x.real_or_paper_wagers_placed!==0||!Number.isSafeInteger(x.scored_total)||
 x.scored_total<0||!Array.isArray(x.examples)||x.examples.length>30||
 !x.comparisons)return false;
 const a=x.comparisons.hit10,b=x.comparisons.third_tail10,n=x.scored_total;
 return a?.races===n&&b?.races===n&&a.points===10&&b.points===10&&
 [a.hits,b.hits,b.paired_gain,b.paired_loss,x.affected_races].every(z=>Number.isSafeInteger(z)&&z>=0&&z<=n)&&
 b.hits-a.hits===b.paired_gain-b.paired_loss&&x.affected_races>=b.paired_gain+b.paired_loss&&
 x.examples.every(r=>/^20\d{6}-\d{2}-\d{2}$/.test(r.race_key||'')&&
  typeof r.outcomes?.hit10==='boolean'&&typeof r.outcomes?.third_tail10==='boolean'&&
  Number.isSafeInteger(r.novel_tickets)&&r.novel_tickets>=0&&r.novel_tickets<=3);
};
async function fetchData(file){
 try{const r=await fetch('./data/site_autopilot/'+file+'?v254='+Date.now(),{cache:'no-store'});
 if(!r.ok)return null;return await r.json()}catch(e){return null}
}
async function update(){
 const box=document.getElementById('v254State');if(!box)return;
 const [pre,score]=await Promise.all([fetchData('v254_pre_current.json'),fetchData('v254_score_current.json')]);
 const proofPre=validPre(pre),proofScore=validScore(score);
 if(!proofPre&&!proofScore){box.textContent='締切前保存と確定後の比較結果を確認中。未取得は0件扱いせず、本番モデルも変更しません。';return}
 let s='';
 if(proofPre)s+='締切前に固定 '+pre.frozen_today+'R（'+pre.day_jst+'）／ 3着入替候補があったレース '+pre.third_tail_novel_races_today+'R。';
 else s+='締切前の保存記録：未確認。';
 if(proofScore){
  const n=score.scored_total,a=score.comparisons.hit10,b=score.comparisons.third_tail10;
  s+=n?' 確定後の同条件比較 '+n+'R：現行10点 '+a.hits+'/'+n+
   '、3着重点10点 '+b.hits+'/'+n+'。新規的中 '+b.paired_gain+
   'R／失った的中 '+b.paired_loss+'R。':' 確定後の未見比較は0R（保存された研究記録のみ）。';
 }else s+=' 確定後の未見比較：取得待ち。';
 box.textContent=s+' どの候補も精度改善は未証明・本番採用なし。';
}
function start(){
 document.getElementById('v254Reload')?.addEventListener('click',update);update();
 setInterval(()=>{if(!document.hidden)update()},120000);
}
window.BoatEdgeV254={validPre,validScore,update};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
