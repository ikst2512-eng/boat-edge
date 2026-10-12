'use strict';
/* A28: no cosmetic change may hide six racer facts, scratch or source state. */
const assert=require('node:assert/strict'),fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const js=fs.readFileSync('assets/boat_edge_v203_readable.js','utf8');
const pred=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v263_race_readability.css','utf8');
assert(html.includes('boat_edge_v263_race_readability.css?v=263'));
assert(css.includes('BOAT EDGE V263 A28'));
for(const selector of [
 '#raceView #raceTitle','#raceView #deadlineBig',
 '#be207Top .be207-condition','#be207Top[data-status="stop"] .be207-condition',
 '#be207Top .be207-freeze','#be207Top .be207-listhead',
 '#be108PredictionModes .be118-resultbar',
 '#be203Layout .be203-health.be203-stop',
 '#be203Layout .be203-source .present','#be203Layout .be203-source .absent'
])assert(css.includes(selector),selector+' must remain visible and readable');
assert(!/\bdisplay\s*:\s*none\s*!?/i.test(css),'never hide data under A28 style');
assert(!/\bvisibility\s*:\s*hidden/i.test(css),'never conceal source');
assert(!/\bopacity\s*:\s*0\s*[;}]/i.test(css));
assert(html.includes('id="deadlineBig"'));
assert(html.includes('id="raceView"'));
assert(js.includes('<div class="be203-cards">'),'six cards retained');
assert(js.includes('<article class="be203-card">'),'all six racer cards still built');
assert(js.includes('be258QuickSix(rows,localWin,motor2)'),'source-bounded six-boat summary retained');
assert(js.includes('independentExhibitionAudit(r)'),'independent source state retained');
assert(pred.includes('be259-head-coverage'),'head/Top3/5/10 strip retained');
assert((html.match(/id="refreshTopBtn"/g)||[]).length===1);
console.log('V263_A28_MOBILE_VISIBLE_SCRATCH_RESULT_DEADLINE_SOURCE_PASS');
