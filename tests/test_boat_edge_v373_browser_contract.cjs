'use strict';
/* V373 read-only CI contract: Playwright browser acceptance is a separate gate.
 * This test runs on the existing Node-only V307 runner; it does not certify a
 * real WebKit/iPhone run. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
execFileSync('python3',['-c',"import ast,pathlib; ast.parse(pathlib.Path('tests/browser/test_boat_edge_03_playwright.py').read_text(encoding='utf-8'))"],{encoding:'utf8',timeout:10000});
const js=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const py=fs.readFileSync('tests/browser/test_boat_edge_03_playwright.py','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(js,{window,document,Number,Date,Set,Map,JSON,Math,Intl});
const api=window.BoatEdgeV207;
assert.equal(api.displayOnly,true);
const combos=['1-2-3','1-3-2','2-1-3','2-3-1','3-1-2','3-2-1','4-1-2','4-2-1','5-1-2','6-1-2'];
assert.equal(api.validTickets(combos.map(c=>({querySelector:q=>q==='b'?{textContent:c}:null}))),true);
assert.equal(api.ticketClarity(combos).top3.includes('上位3点'),true);
assert.equal(api.ticketClarity(combos).top5.includes('上位5点'),true);
assert.equal(api.ticketClarity(combos).top10.includes('上位10点'),true);
assert.equal(api.holdPreviousRace('20261014-06-01','20261014-06-02',{},null),true);
assert(js.includes("const rows=$('.be108-ticket-list > .be108-ticket',p);"),'TopK must use all ticket nodes');
assert(!js.includes("const rows=$('.be108-ticket-list > .be108-ticket',p);"),'single-node selector crashed Chromium and WebKit');
assert(js.includes("stop?'配分：買い目を停止・未確認のため非表示'"),'stopped predictions must hide budget');
assert(js.includes("stop?'公式オッズ・想定払戻：買い目停止・未確認のため非表示'"),'stopped predictions must hide odds');
assert(js.includes("!ticketViewSynced?'配分：新レースの値を照合中"),'retain race transition guard');
for(const word of ['sync_playwright','webkit','chromium','is_mobile=True','has_touch=True','timezone_id=\"Asia/Tokyo\"',
 'test_top3_top5_top10_order_and_reference_amount','test_blocked_tickets_hide_amounts_and_odds',
 'test_race_switch_discards_old_list_until_new_dom','test_touch_targets_narrow_mobile',
 'test_six_boat_comparison_original_and_head_focus',
 'BOAT_EDGE_REQUIRED_BROWSERS','BOAT_EDGE_SCREENSHOT_DIR'])assert(py.includes(word),'missing browser matrix item: '+word);
for(const file of ['assets/boat_edge_v207_first_prediction.css','assets/boat_edge_v304_topk_mobile.css'])
 assert(fs.existsSync(file),'missing real production CSS: '+file);
assert(/min-height:44px/.test(css));
assert(!/(?:getPrediction\(|combined_api|payouts\/|formal_results|www\.boatrace\.jp)/.test(py),'browser suite must not reach result or prediction endpoints');
console.log('V373_MOBILE_PLAYWRIGHT_MATRIX_READY_NO_WEBKIT_CLAIM_PASS');