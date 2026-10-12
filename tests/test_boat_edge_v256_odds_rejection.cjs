'use strict';
/* V256: never render formerly valid prices after official partial/no-bet marker.
 * This isolated runtime test does not access results, payouts or remote URLs.
 */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('assets/boat_edge_v108.js','utf8');
const start = source.indexOf('function be166OddsStatus(key,postResult){');
const end = source.indexOf('\nasync function resultFor(key){',start);
assert(start>=0&&end>start,'exact odds status and oddsFor implementation present');
const runtime = source.slice(start,end);
const key = '20261012-14-09', deadline='12:19';
const url = 'https://www.boatrace.jp/owpc/pc/race/odds3t?hd=20261012&jcd=14&rno=9';
const rejected = {
  schema_version:'boat-edge-site-odds-v71',race_key:key,source_url:url,
  phase:'PRE_RESULT_PURCHASE_ONLY',results_seen:false,scoring:false,
  odds_validation:'REJECTED_NO_BET',no_bet:true,
  checked_at:'2026-10-12T11:47:45+09:00',fetched_at:null,deadline,
  available_count:0,observed_numeric_count:60,
  scratch_status:'UNVERIFIED',trifecta_odds:{}
};
const ctx={
 packet:JSON.parse(JSON.stringify(rejected)),
 activeRace:{race_key:key,meta:{deadline}},
 Date:class FixedTime extends Date {
   static now(){return Date.parse('2026-10-12T12:05:00+09:00')}
 },
 JSON, Number, Math, String, Map, Set, Object
};
const harness=`
'use strict';
const be166OddsMeta=new Map();
const be166OddsPrice=v=>(v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))&&Number(v)>0)?Number(v):null;
const esc=v=>String(v).replace(/[&<>"]/g,'');
function raceOf(){return activeRace}
async function J(){return packet}
${runtime}
globalThis.unit={oddsFor,status:be166OddsStatus,meta:be166OddsMeta};
`;
vm.runInNewContext(harness,ctx,{filename:'v256-odds-test-harness.js'});
(async()=>{
  const none=await ctx.unit.oddsFor(key);
  assert.equal(Object.keys(none).length,0,'rejection document contains no prices');
  assert.equal(ctx.unit.meta.get(key).status,'unverified');
  const status=ctx.unit.status(key,false);
  assert(status.includes('120通り中60通り'),status);
  assert(status.includes('購入対象外'),status);
  assert(status.includes('欠場・取消は未確認'),status);
  assert(status.includes('以前の価格も表示しません'),status);
  assert(!status.includes('欠場確定'),status);

  ctx.packet={...rejected,trifecta_odds:{'1-2-3':10.5}};
  const tampered=await ctx.unit.oddsFor(key);
  assert.equal(Object.keys(tampered).length,0,'tampered rejection never renders odds');
  assert.equal(ctx.unit.meta.get(key).status,'invalid');

  ctx.packet={...rejected,race_key:'20261012-14-08'};
  assert.equal(Object.keys(await ctx.unit.oddsFor(key)).length,0);
  assert.equal(ctx.unit.meta.get(key).status,'invalid');

  ctx.packet={...rejected,observed_numeric_count:null};
  assert.equal(Object.keys(await ctx.unit.oddsFor(key)).length,0);
  assert(ctx.unit.status(key,false).includes('有効な倍率を確認できません'));

  console.log('V256_ODDS_REJECTION_UI_PASS: blank prices, 60/120 warning, scratch unknown, tamper fail-closed');
})().catch(err=>{console.error(err);process.exitCode=1});
