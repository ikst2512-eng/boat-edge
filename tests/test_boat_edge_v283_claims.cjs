const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v283_claims.js','utf8');
const w={};vm.runInNewContext(js,{window:w,Date});const v=w.BoatEdgeV283Claims;
const now=Date.parse('2026-10-13T01:48:00+09:00');
const base={asOf:'2026-10-13T01:45:00+09:00',connected:false,predictions_ready:false,
 formalFirst100:{races:0},guards:{results_seen:false,unlock:false,scoring:false,RESULT_UNLOCK_TOKEN:null}};
assert.equal(v.claim(base,now).closed,true);
assert.match(v.claim(base,now).text,/Actions PASS/);assert.match(v.claim(base,now).text,/Pages SUCCESS/);
assert.match(v.claim(base,now).text,/Safari/);assert.match(v.claim(base,now).text,/0\/100R/);
for(const mut of [
 d=>d.guards.results_seen=true,d=>d.guards.unlock=true,d=>d.guards.scoring=true,
 d=>d.guards.RESULT_UNLOCK_TOKEN='bad',d=>d.formalFirst100.races=1,
 d=>d.connected=true,d=>d.predictions_ready=true,
 d=>d.asOf='2026-10-12T01:45:00+09:00',d=>d.asOf='invalid']) {
 const x=JSON.parse(JSON.stringify(base));mut(x);assert.equal(v.claim(x,now).closed,false);
 assert.match(v.claim(x,now).text,/未確認/);
}
assert.equal(v.claim(null,now).closed,false);
const page=fs.readFileSync('autopilot.html','utf8');
assert(page.includes('id="v283Proof"'));assert(page.includes('boat_edge_v283_claims.js?v=283'));
assert(page.includes('BoatEdgeV283Claims?.claim?.(formalNow)'));
assert(!js.includes('fetch('));assert(!js.includes('results.json'));assert(!js.includes('payout'));
assert(fs.readFileSync('BOAT_EDGE_AUTODEV_TASKS.md','utf8').includes('- [x] A32 |'));
new Function(page.match(/<script>\s*([\s\S]*?)<\/script>/)[1]);
console.log('V283_UI_ONLY_CLAIMS_AND_FORMAL_LOCK_PASS');