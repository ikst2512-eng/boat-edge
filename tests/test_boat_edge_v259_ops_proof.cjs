'use strict';
/* V259: offline verification of current PRE_RESULT snapshot provenance only.
   No external requests, no result/payout/combined access, no model changes. */
const assert=require('assert');
const fs=require('fs');
const crypto=require('crypto');
const {due,upcoming,assess}=require('../assets/boat_edge_v259_ops_proof.js');
const key='20261012-09-09',clock='14:32',saved='2026-10-12T05:24:36+00:00';
const combo=(a,b,c)=>a+'-'+b+'-'+c;
const modes=Object.fromEntries(['hit','balance','hole','narrow'].map(name=>[name,{
 tickets:[{combo:combo(1,2,3),stake_yen:10000}]
}]));
const snapshot={schema_version:'boat-edge-server-site-final-v123',snapshot_window:'FINAL_15M',
 prediction_kind:'SITE_REFERENCE_V122',race_key:key,first_saved_at:saved,saved_at:saved,deadline:clock,
 guards:{results_seen:false,unlock:false,scoring:false},stake_plan_version:'V141-10000-PROSPECTIVE',
 race_sha256:'a'.repeat(64),odds_sha256:'b'.repeat(64),modes};
const raw=Buffer.from(JSON.stringify(snapshot)),hash=crypto.createHash('sha256').update(raw).digest('hex');
const audit={race_key:key,pass:true,revision_count:1,latest_snapshot_sha256:hash,latest_snapshot_saved_at:saved,first_audited_at:'2026-10-12T05:24:36.050+00:00',revisions:[{snapshot_sha256:hash}]};
const evidence={race_key:key,schema:'BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1',
 scope:'SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS',snapshot_sha256:hash,snapshot_saved_at:saved,
 new_snapshot_created_this_run:true,results_seen:false,formal_fresh_unlock:false,scoring:false,
 evidence_captured_at:'2026-10-12T05:24:36.050+00:00',official_race_card_fetched_at:'2026-10-12T05:24:16+00:00',
 official_beforeinfo_fetched_at:'2026-10-12T05:24:25+00:00',scratch_checked_at:'2026-10-12T05:24:35+00:00',
 odds_fetched_at:'2026-10-12T05:24:35+00:00',scratch_sha256:'d'.repeat(64),
 odds_combinations:120,stake_yen_per_mode:10000,
 race_sha256:snapshot.race_sha256,odds_sha256:snapshot.odds_sha256};
const check=(snap=snapshot,au=audit,ev=evidence,digest=hash,deadline=clock)=>
 assess(key,deadline,snap,au,ev,digest);
assert.equal(due(key,clock),Date.parse('2026-10-12T14:32:00+09:00'));
assert(Number.isNaN(due(key,'25:80')));
assert.equal(check().state,'verified');
assert.equal(check(null).state,'missing');
assert.equal(check(snapshot,null).state,'unverified');
assert.equal(check(snapshot,audit,evidence,'c'.repeat(64)).state,'invalid');
assert.equal(check({...snapshot,guards:{...snapshot.guards,unlock:true}}).state,'invalid');
assert.equal(check({...snapshot,saved_at:'2026-10-12T05:33:00+00:00'}).state,'invalid');
assert.equal(check({...snapshot,modes:{...modes,hit:{tickets:[{combo:'1-2-3',stake_yen:9000}]}}}).state,'invalid');
assert.equal(check(snapshot,{...audit,revision_count:2}).state,'invalid');
assert.equal(check(snapshot,audit,{...evidence,results_seen:true}).state,'invalid');
assert.equal(check(snapshot,audit,{...evidence,odds_combinations:60}).state,'invalid');
assert.equal(check({...snapshot,modes:{...modes,hit:{tickets:[{combo:'1-1-2',stake_yen:10000}]}}}).state,'invalid','repeated boat is not a valid 3連単 ticket');
assert.equal(check({...snapshot,modes:{...modes,hit:{tickets:[{combo:'9-2-3',stake_yen:10000}]}}}).state,'invalid','out of range boat number');
assert.equal(check(snapshot,{...audit,first_audited_at:'2026-10-12T05:36:00+00:00'}).state,'invalid','audit recorded only after the cutoff');
assert.equal(check(snapshot,audit,{...evidence,evidence_captured_at:'2026-10-12T05:36:00+00:00'}).state,'invalid','evidence created after cutoff');
assert.equal(check(snapshot,audit,{...evidence,odds_fetched_at:'2026-10-12T05:08:00+00:00'}).state,'invalid','odds source exceeds verified 15min window');
assert.equal(check(snapshot,audit,{...evidence,official_beforeinfo_fetched_at:'2026-10-12T05:25:00+00:00'}).state,'invalid','beforeinfo timestamp cannot be later than the snapshot');
assert.equal(check(snapshot,audit,{...evidence,scratch_sha256:'missing'}).state,'invalid','scratch SHA must be present');
assert.equal(check(snapshot,{...audit,revisions:[{snapshot_sha256:'a'.repeat(64)}]}).state,'invalid','revision manifest must match snapshot bytes');
const sched={date:'2026-10-12',venues:[
 {venue:'津',races:[{race_key:'20261012-09-09',deadline:'14:32'},{race_key:'20261012-09-10',deadline:'15:00'}]},
 {venue:'徳山',races:[{race_key:'20261012-18-12',deadline:'14:29'}]}
]};
const at=Date.parse('2026-10-12T14:26:00+09:00');
const chosen=upcoming(sched,at,3);
assert.deepEqual(chosen.map(r=>r.key),['20261012-18-12','20261012-09-09','20261012-09-10']);
assert.deepEqual(upcoming(sched,Date.parse('2026-10-13T14:26:00+09:00')),[]);
assert.deepEqual(upcoming(sched,Date.parse('2026-10-12T15:01:00+09:00')),[]);
const asset=fs.readFileSync('assets/boat_edge_v259_ops_proof.js','utf8');
for(const forbidden of [
 'data/site_results/', '/race/result', '/race/odds3t',
 'data/formal_predictions/', 'site_payouts/', 'combined_api'
])assert(!asset.includes(forbidden),'V259 browser must not open blocked endpoints: '+forbidden);
assert(asset.includes("window.crypto.subtle.digest('SHA-256',buffer)"));
assert(asset.includes("no-store"));
assert(!asset.includes('snapshot.store('));
console.log('V259_PRE_RESULT_PROVENANCE_MONITOR_PASS: verified, stale, invalid, no-bet, SHA, future selection, formal lock');
