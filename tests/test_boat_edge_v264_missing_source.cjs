'use strict';
/* V264: explain predeadline missing fixed predictions from existing PRE_RESULT inputs.
   Never reconstruct old bets, import results or turn missing evidence into success. */
const assert=require('assert'),fs=require('fs');
const {missingReasons}=require('../assets/boat_edge_v259_ops_proof.js');
const key='20261012-22-10',deadline='15:40',now=Date.parse('2026-10-12T15:33:00+09:00');
const race={
 race_key:key,
 meta:{phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
 racers:Array.from({length:6},(_,i)=>({lane:i+1})),
 source_audit:{race_card:{status:'ok',fetched_at:'2026-10-12T15:30:00+09:00'},
  beforeinfo:{status:'ok',fetched_at:'2026-10-12T15:30:00+09:00'}}
};
const scratch={race_key:key,blocked:false,race_card_source_status:'ok',
 official_beforeinfo_source_status:'ok',checked_at:'2026-10-12T15:31:00+09:00'};
const combos={};
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)if(a!==b&&a!==c&&b!==c)combos[a+'-'+b+'-'+c]=12.3;
const odds={race_key:key,phase:'PRE_RESULT_PURCHASE_ONLY',results_seen:false,scoring:false,
 verified_official_dom_v167:true,available_count:120,trifecta_odds:combos,
 fetched_at:'2026-10-12T15:32:00+09:00'};
const reasons=(r=race,s=scratch,o=odds,at=now)=>missingReasons(key,deadline,r,s,o,at);
assert.deepEqual(reasons(),['入力は取得済み・固定予想の保存証跡待ち']);
assert.deepEqual(reasons(race,scratch,{...odds,verified_official_dom_v167:undefined}),['公式DOM照合の記録待ち']);
assert(reasons({...race,source_audit:{...race.source_audit,beforeinfo:{status:'published_wait'}}}).includes('公式直前情報の取得待ち'));
assert(reasons(race,{...scratch,blocked:true}).includes('欠場・取消の安全確認待ち'));
assert(reasons({...race,meta:{...race.meta,results_seen:true}}).includes('6艇出走・結果未見データの確認待ち'));
assert(reasons(race,scratch,{...odds,available_count:60}).includes('3連単120通り・保存時刻の確認待ち'));
assert(reasons(race,scratch,{...odds,trifecta_odds:{...combos,'1-2-3':0}}).includes('3連単120通り・保存時刻の確認待ち'));
assert(reasons(race,scratch,{...odds,trifecta_odds:{...combos,'1-1-2':12}}).includes('3連単120通り・保存時刻の確認待ち'));
assert(reasons(race,scratch,{...odds,fetched_at:'2026-10-12T15:10:00+09:00'}).includes('3連単120通り・保存時刻の確認待ち'));
assert.deepEqual(reasons(race,scratch,odds,Date.parse('2026-10-12T15:28:00+09:00')),['締切10分前の固定時間帯待ち']);
assert.deepEqual(reasons(race,scratch,odds,Date.parse('2026-10-12T15:39:00+09:00')),['固定期限内の保存証跡なし（後付け禁止）']);
assert.deepEqual(reasons(race,scratch,odds,Date.parse('2026-10-12T15:41:00+09:00')),['締切済み・未保存を後から復元しません']);
assert.deepEqual(missingReasons('../invalid',deadline,race,scratch,odds,now),['レース指定不正']);
const content=fs.readFileSync('assets/boat_edge_v259_ops_proof.js','utf8');
for(const forbidden of ['data/site_results/','data/formal_predictions/','race/result','payouts/'])assert(!content.includes(forbidden));
assert(content.includes("if(res.status!==404)return {state:'unverified'"));
assert(content.includes("json('./data/site_scratches_v182/'+r.key+'.json')"));
console.log('V264_PRE_RESULT_MISSING_SOURCE_EXPLAIN_PASS: 14 offline safety cases; no retroactive predictions');
