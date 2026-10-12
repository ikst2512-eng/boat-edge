'use strict';
/* Synthetic, read-only navigation tests. No historical races, odds, results or network. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/boat_edge_v249_focus.js', 'utf8');
const dom = new Map();
const calls=[];
let active = 'pred';
let reducedMotion = false;
function element(name,section){return {
 getClientRects(){return section === active ? [1] : []},
 scrollIntoView(options){calls.push({target:name,options})}
}}
function buttons(){return ['pred','scenario','before'].map(section => [
 '#raceTabs [data-tab="'+section+'"]', {click(){active=section}}
 ]);}
for(const [name,element] of buttons())dom.set(name,element);
for(const [key,tab] of [
 ['#be207Top','pred'],['#be204Overview','pred'],['#buyBoard','pred'],
 ['#tab-pred .be203-cards','pred'],['#be206Quick','pred'],['#boats','pred'],['#tab-pred','pred'],
 ['#scenarioFlow','scenario'],['#scenarioHero','scenario'],['#tab-scenario','scenario'],
 ['#tab-before .section','before'],['#tab-before','before']
 ])dom.set(key,element(key,tab));
const document={readyState:'loading',addEventListener(){},querySelector(q){return dom.get(q)||null}};
const window={setInterval(){},setTimeout(f){f()},matchMedia(){return {matches:reducedMotion}}};
vm.runInNewContext(source,{window,document,console},{filename:'boat_edge_v249_focus.js'});
const api=window.BoatEdgeV249;
assert.equal(api.version,'V337-RACE-SCOPED-EVIDENCE-ONLY');
assert.equal(api.navigate('racers'),true);
assert.equal(active,'pred');
assert.equal(calls.at(-1).target,'#tab-pred .be203-cards');
dom.delete('#tab-pred .be203-cards');
assert.equal(api.navigate('racers'),true);
assert.equal(calls.at(-1).target,'#be206Quick');
dom.delete('#be206Quick');
assert.equal(api.navigate('racers'),true);
assert.equal(calls.at(-1).target,'#boats');
dom.delete('#boats');
assert.equal(api.navigate('racers'),true);
assert.equal(calls.at(-1).target,'#tab-pred');
assert.equal(api.navigate('scenario'),true);
assert.equal(active,'scenario');
assert.equal(calls.at(-1).target,'#scenarioFlow');
assert.equal(api.navigate('before'),true);
assert.equal(active,'before');
assert.equal(calls.at(-1).target,'#tab-before .section');
assert.equal(api.navigate('tickets'),true);
assert.equal(calls.at(-1).target,'#be207Top');
reducedMotion=true;
assert.equal(api.navigate('before'),true);
assert.equal(calls.at(-1).options.behavior,'auto');
const n=calls.length;
assert.equal(api.navigate('bogus'),false);
assert.equal(calls.length,n);
assert(!/fetch\(|loadRace\(|rankPredictions\(|updateOdds\(|history\.pushState\(|RESULT_UNLOCK_TOKEN|results_seen/.test(source));
const css=fs.readFileSync('assets/boat_edge_v249_focus.css','utf8');
assert(css.includes('#raceView #tab-pred .be203-cards'));
assert(css.includes('scroll-margin-top:210px'));
if(fs.existsSync('index.html')){
 const html=fs.readFileSync('index.html','utf8');
 assert(html.includes('./assets/boat_edge_v249_focus.js?v=337'));
 assert(html.includes('./assets/boat_edge_v249_focus.css?v=337'));
} // Development CI's sparse checkout omits index.html; check it when available.
console.log('V297_NAV_VISIBLE_TARGET_FALLBACK_REDUCED_MOTION_PASS');
