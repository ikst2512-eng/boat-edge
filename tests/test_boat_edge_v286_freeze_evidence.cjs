'use strict';
/* V286 mobile-only, no network, no outcome access and no fabricated freeze rate. */
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const asset=fs.readFileSync('assets/boat_edge_v286_freeze_evidence.js','utf8');
const window={};vm.runInNewContext(asset,{window,Date});
const freeze=window.BoatEdgeV286Freeze;
assert(freeze && typeof freeze.summary==='function');
assert.strictEqual(freeze.previousDay('20261013'),'20261012');
assert.strictEqual(freeze.previousDay('20260101'),'20251231');
assert.strictEqual(freeze.previousDay('20260301'),'20260228');
assert.strictEqual(freeze.previousDay('20260230'),null);
assert.strictEqual(freeze.previousDay('2026101X'),null);
const c={
 day_jst:'20261012',scope:'OBSERVED_PREDEADLINE_WINDOWS_ONLY_NOT_ALL_RACES',
 observed_races:104,matured_observed_races:104,
 snapshot_present:63,predeadline_snapshot_with_matching_audit:61,
 snapshot_or_audit_unverified:2,sha_consistent_predeadline_snapshots:0,
 source_changed_after_freeze:61,source_missing_after_freeze:0,
 v229_attestation_record_matched:54,v229_atomic_evidence_matched:0,
 early_missing_later_snapshot_present:38,not_found_after_deadline:41,
 pending_before_deadline:0
};
const ops={schema:'BOAT_EDGE_V220_SITE_AUTONOMOUS_OPERATIONS_V1',scope:'SITE_ONLY_PRE_RESULT_OPERATIONS_NOT_FORMAL_FRESH',
 day_jst:'20261013',site_prediction_freeze_observation:{previous_day:c}};
const ok=freeze.summary(ops,'20261013');
assert.strictEqual(ok.verified,true);
for(const token of ['前日10/12','104R','63R','61R','41R','54R','固定後','SHA'])
 assert(ok.text.includes(token),token);
assert(!/的中率.?向上|合格済み|未見PASS/.test(ok.text));
assert.strictEqual(freeze.summary({...ops,day_jst:'20261012'},'20261013').verified,false);
assert.strictEqual(freeze.summary(null,'20261013').verified,false);
assert.strictEqual(freeze.summary({...ops,site_prediction_freeze_observation:{previous_day:{...c,source_changed_after_freeze:62}}},'20261013').verified,false);
assert.strictEqual(freeze.summary({...ops,site_prediction_freeze_observation:{previous_day:{...c,v229_attestation_record_matched:62}}},'20261013').verified,false);
assert.strictEqual(freeze.summary({...ops,site_prediction_freeze_observation:{previous_day:{...c,not_found_after_deadline:-1}}},'20261013').verified,false);
assert.strictEqual(freeze.summary({...ops,site_prediction_freeze_observation:{previous_day:{...c,day_jst:'20261011'}}},'20261013').verified,false);
const zero=Object.fromEntries(Object.keys(c).map(k=>[k,k==='day_jst'?'20261012':k==='scope'?c.scope:0]));
assert(freeze.summary({...ops,site_prediction_freeze_observation:{previous_day:zero}},'20261013').text.includes('0R'));
const html=fs.readFileSync('autopilot.html','utf8');
assert(html.includes('id="freezeEvidenceV286"'));
assert(html.includes('boat_edge_v286_freeze_evidence.js?v=286'));
assert(html.includes('window.BoatEdgeV286Freeze?.summary(freshOps?ops:null,today)'));
assert(html.includes("put('freezeEvidenceV286','前日の予想固定監査は取得失敗"));
const inline=html.split('<script>')[1]?.split('</script>')[0];
assert(inline && !/syntax unsupported/.test(inline));
new Function(inline);
assert(!/site_results|\/race\/result|\/race\/pay|formal_predictions|odds3t/.test(asset));
console.log('V286_MOBILE_FREEZE_EVIDENCE_DATE_AND_SOURCE_GATES_PASS');
