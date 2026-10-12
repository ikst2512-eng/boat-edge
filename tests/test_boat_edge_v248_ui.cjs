'use strict';
/* V248: isolate client read-only logic; no network, wager writes or formal result access. */
const assert=require('assert'),fs=require('fs'),vm=require('vm');
function load(path,windowObj={}){
 const listeners={};
 const doc={readyState:'loading',visibilityState:'visible',addEventListener(ev,fn){listeners[ev]=fn},
  querySelector(){return null},querySelectorAll(){return []},
  createElement(){return {style:{},dataset:{},setAttribute(){},textContent:''}}};
 const window={...windowObj};
 vm.runInNewContext(fs.readFileSync(path,'utf8'),{window,document:doc,
  console,Date,setTimeout(){},clearTimeout(){},setInterval(){},clearInterval(){},
  queueMicrotask(){},fetch:async()=>{throw Error('NO_NETWORK_DURING_TEST')}},{filename:path});
 return window;
}
const odds=load('assets/boat_edge_v166_refresh.js',
 {BoatEdgeV222Odds:{validate(doc,r,now){return {quality:doc.quality}}}}).BoatEdgeV166Refresh.oddsLabel;
const race={race_key:'20261012-02-05'},now=Date.parse('2026-10-12T11:00:00+09:00');
const packet={race_key:race.race_key,fetched_at:'2026-10-12T10:55:00+09:00',quality:'fresh'};
assert.match(odds(packet,race,now),/BOAT RACE公式/);
assert.match(odds(packet,race,now),/10:55/);
assert.match(odds(packet,race,now),/リアルタイムではない/);
assert.match(odds({...packet,quality:'stale'},race,now),/古い保存値/);
assert.match(odds({...packet,quality:'past_deadline'},race,now),/締切済み/);
assert.match(odds({...packet,quality:'invalid'},race,now),/表示不可/);
assert.match(odds({...packet,race_key:'other'},race,now),/未確認/);
const controlJs=fs.readFileSync('assets/boat_edge_v166_refresh.js','utf8');
assert.match(controlJs,/duplicate\.hidden=true/);
assert.match(controlJs,/duplica\w*\.tabIndex=-1/);
assert.match(controlJs,/BoatEdgeV223Source\?\.refresh/);
assert(!controlJs.includes('収集は別途5分周期'));
const p=load('assets/boat_edge_v211_paper.js').BoatEdgeV211PaperEvidence;
const pending={state:'pending',decision_at:'2026-10-12T10:40:00+09:00',stake_yen:500,
 tickets:[{combo:'1-2-3',paper_stake_yen:200},{combo:'1-3-2',paper_stake_yen:300}]};
const settled={...pending,state:'settled',return_yen:1250};
assert.strictEqual(p.verifiedBet(pending),true);
assert.strictEqual(p.verifiedBet(settled),true); // official-style payout need not be a 100-yen multiple
assert.strictEqual(p.verifiedBet({...settled,return_yen:1300}),true);
assert.strictEqual(p.verifiedBet({...pending,stake_yen:600}),false);
assert.strictEqual(p.verifiedBet({...pending,tickets:[{combo:'1-1-2',paper_stake_yen:500}]}),false);
const proof={verified:true,current:true,count:0,spent:0};
const paper={mode:'PAPER_ONLY',money:{pending_yen:0,settled_stake_yen:0},recent_bets:[]};
assert.strictEqual(p.paperStates(paper,proof).kind,'no-bet');
assert.strictEqual(p.paperStates({...paper,recent_bets:[pending]},proof).kind,'pending');
assert.strictEqual(p.paperStates({...paper,recent_bets:[{...settled,return_yen:1300}]},proof).kind,'settled');
assert.strictEqual(p.paperStates({...paper,recent_bets:[{...pending,stake_yen:600}]},proof).kind,'unknown');
assert.strictEqual(p.paperStates({...paper,money:{...paper.money,pending_yen:null}},proof).kind,'unknown');
const top=load('assets/boat_edge_v204_prediction.js').BoatEdgeV204.topKExplanation;
const combos=['1-2-3','1-3-2','1-2-4','1-4-2','2-1-3','2-3-1','3-1-2','3-2-1','4-1-2','4-2-1'];
const rows=combos.map(c=>({querySelector(s){return s==='b'?{textContent:c}:null}}));
const got=top(rows);
assert.match(got.top3,/1-2-3/);
assert.match(got.top5,/2-1-3/);
assert.match(got.top10,/4-2-1/);
assert.match(got.head,/1号艇/);
assert.match(got.caution,/頭の的中確率：未校正/);
assert.match(got.caution,/3連単の的中確率：未校正/);
assert.match(top(rows.slice(0,5)).top10,/確認待ち/);
assert.match(top([rows[0],rows[0],...rows.slice(2)]).top3,/確認待ち/);
const ui=fs.readFileSync('assets/boat_edge_v204_prediction.js','utf8');
assert(ui.includes('be248-tops-grid'));
assert(!ui.includes('accuracy_improvement_proven=true'));
const {execFileSync}=require('child_process');
for(const [file,args,expected] of [
 ['tests/test_boat_edge_v254_odds_cutoff.cjs',[],'V254_ODDS_DISPLAY_PASS'],
 ['tests/test_boat_edge_v222_live_odds.cjs',['assets/boat_edge_v222_live_odds.js'],'V222_PASS'],
 ['tests/test_boat_edge_v256_formal_result_gate.cjs',[],'V256_FORMAL_RESULT_UNSEEN_GUARD_PASS'],
 ['tests/test_boat_edge_v258_stale_race.cjs',[],'V258_STALE_RACE_RENDER_PASS'],
 ['tests/test_boat_edge_v259_ops_proof.cjs',[],'V260_PROVENANCE_SOURCE_TIME_AND_TRIFECTA_GUARD_PASS'],
 ['tests/test_boat_edge_v263_odds_snapshot_proof.cjs',[],'V263_ARCHIVED_120_OFFICIAL_ODDS_FROZEN_TICKET_PARITY_PASS'],
 ['tests/test_boat_edge_v264_missing_source.cjs',[],'V264_PRE_RESULT_MISSING_SOURCE_EXPLAIN_PASS'],
 ['tests/test_boat_edge_v266_paired_miss.cjs',[],'V266_PAIRED_SAME_RACE_MISS_EXACT_TEST_PASS']
]){
 const output=execFileSync(process.execPath,[file,...args],{encoding:'utf8',timeout:20000});
 assert(output.includes(expected),'Missing isolated odds/lock test PASS: '+file);
}
const python=execFileSync('python3',['tests/test_boat_edge_v265_readiness_sources.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert.strictEqual(python,'');
const priority=execFileSync('python3',['tests/test_boat_edge_v268_beforeinfo_priority.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(priority.includes('V268_BEFOREINFO_DEADLINE_PRIORITY_PASS'));
const urgentTelemetry=execFileSync('python3',['tests/test_boat_edge_v269_urgent_telemetry.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(urgentTelemetry.includes('V269_URGENT_PRE_RESULT_BEFOREINFO_TELEMETRY_PASS'));
const noReinstall=execFileSync('python3',['tests/test_boat_edge_v270_no_reinstall.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(noReinstall.includes('V270_NO_OBSOLETE_SITE_OPS_REINSTALL_PASS'));
const urgentFirst=execFileSync('python3',['tests/test_boat_edge_v274_urgent_first.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(urgentFirst.includes('V274_PRE_RESULT_URGENT_FIRST_SOURCE_TIMESTAMP_LOCK_PASS'));
const frozenEvidence=execFileSync('python3',['tests/test_boat_edge_v275_frozen_protection.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(frozenEvidence.includes('V275_FROZEN_PRE_RESULT_EVIDENCE_PRESERVATION_PASS'));
const scheduleOwner=execFileSync('python3',['tests/test_boat_edge_v276_schedule_owner.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(scheduleOwner.includes('V276_SINGLE_FAST_SOURCE_SCHEDULE_OWNER_PASS'));
const frozenRemoteGate=execFileSync('python3',['tests/test_boat_edge_v277_snapshot_push_guard.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(frozenRemoteGate.includes('V277_CONCURRENT_POST_FREEZE_SOURCE_PUSH_FAIL_CLOSED_PASS'));
const freezeCoverage=execFileSync('python3',['tests/test_boat_edge_v220_site_ops.py'],{encoding:'utf8',timeout:20000,stdio:['ignore','pipe','pipe']});
assert(freezeCoverage.includes('V284_NO_EARLY_MISSING_AS_FINAL_FROZEN_SHA_AUDIT_PASS'));
assert(freezeCoverage.includes('V285_SNAPSHOT_METADATA_SOURCE_DRIFT_AND_V229_RECORD_SEPARATED_PASS'));
console.log('V248_A13_A14_A15_A16_EVIDENCE_SAFE_TESTS_PASS');
