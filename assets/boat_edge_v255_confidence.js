/* V255 empirical calibration disclaimer, entirely site-only and read-only. */
(()=>{'use strict';
if(window.BoatEdgeV255)return;
const SCHEMA='BOAT_EDGE_V255_SITE_ONLY_UNCALIBRATED_CONFIDENCE_AUDIT_V1';
const SCOPE='SETTLED_SITE_REFERENCE_PROSPECTIVE_PROOF_NOT_FORMAL_FRESH';
const okInt=x=>Number.isSafeInteger(x)&&x>=0;
function validate(v){
 if(v?.schema!==SCHEMA||v?.scope!==SCOPE||
  v.formal_result_access!==false||v.production_model_changed!==false||
  v.accuracy_improvement_proven!==false||v.model_promotion_authorized!==false||
  v.real_or_paper_wagers_placed!==0||!okInt(v.site_settled_reference_races)||
  !okInt(v.prospective_source_verified_races)||
  v.prospective_source_verified_races>v.site_settled_reference_races||
  !Array.isArray(v.rows)||v.rows.length!==v.prospective_source_verified_races||
  !v.head||!v.top10||!v.hit10_frozen_relative_weight)return null;
 const n=v.prospective_source_verified_races;
 const seen=new Set();
 for(const r of v.rows){
  if(!/^20\d{6}-\d{2}-\d{2}$/.test(r?.race_key||'')||seen.has(r.race_key)||
   r.day_jst!==r.race_key.slice(0,8)||
   typeof r.head_hit!=='boolean'||typeof r.top10_hit!=='boolean'||
   typeof r.relative_weight_normalized_near_100!=='boolean'||
   !Number.isFinite(r.relative_weight_total)||r.relative_weight_total<0||
   !Number.isFinite(r.relative_weight_max)||r.relative_weight_max<0||
   !Number.isFinite(r.relative_weight_min)||r.relative_weight_min<0)return null;
  seen.add(r.race_key);
 }
 for(const [key,flag] of [['head','head_hit'],['top10','top10_hit']]){
  const x=v[key];
  const hits=v.rows.filter(r=>r[flag]).length;
  if(!okInt(x.hits)||x.hits!==hits||x.races!==n||
   (n>0&&(!Number.isFinite(x.rate_percent)||Math.abs(x.rate_percent-hits*100/n)>0.02))||
   (n===0&&x.rate_percent!==null))return null;
  if(n>0&&(!Array.isArray(x.wilson_95_percent)||x.wilson_95_percent.length!==2||
   x.wilson_95_percent.some(z=>!Number.isFinite(z)||z<0||z>100)||
   x.wilson_95_percent[0]>x.wilson_95_percent[1]))return null;
 }
 const w=v.hit10_frozen_relative_weight;
 if(w.verified_races!==n||!okInt(w.normalized_to_100_in_races)||
  w.normalized_to_100_in_races!==v.rows.filter(r=>r.relative_weight_normalized_near_100).length||
  w.normalized_to_100_in_races>n||
  w.all_normalized!==(n>0&&w.normalized_to_100_in_races===n)||
  w.interpretation!=='TEN_TICKET_RELATIVE_WEIGHTS_NOT_120_OUTCOME_PROBABILITY')return null;
 return v;
}
function render(v){
 const node=document.getElementById('v255Confidence');
 if(!node)return;
 const proof=validate(v);
 if(!proof){node.textContent='未校正スコアの検証データを取得できません。保存済みの評価値を実際の的中確率として扱いません。';return;}
 const n=proof.prospective_source_verified_races;
 if(n===0){node.textContent='締切前固定・結果照合の条件を満たすサンプルは0R。スコアの的中確率は未校正です。';return;}
 const w=proof.hit10_frozen_relative_weight;
 const x=proof.head,y=proof.top10;
 const ci=v=>v.wilson_95_percent?'（95% Wilson区間 '+v.wilson_95_percent[0]+'〜'+v.wilson_95_percent[1]+'%）':'';
 node.textContent='照合済み '+n+'R／全サイト確定 '+proof.site_settled_reference_races+
 'R。頭予想 '+x.hits+'/'+n+'R＝'+x.rate_percent+'% '+ci(x)+
 '。3連単Top10 '+y.hits+'/'+n+'R＝'+y.rate_percent+'% '+ci(y)+
 '。予想Top10内の相対値が合計約100%になる保存レース '+w.normalized_to_100_in_races+'/'+n+
 'R。これは10点内で正規化された相対値で、120通りに対する的中確率ではありません。内部スコアもランク由来で未校正。複数日の独立未見検証を待つため本番モデル・購入方針は変更しません。';
}
async function update(){
 try{
  const r=await fetch('./data/site_autopilot/v255_confidence_current.json?ts='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  render(await r.json());
 }catch(e){render(null)}
}
function start(){
 document.getElementById('v255Reload')?.addEventListener('click',update);
 update();
 setInterval(()=>{if(!document.hidden)update()},120000);
}
window.BoatEdgeV255={validate,render,update};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
