'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {view, dayJst} = require('../assets/boat_edge_v271_health.js');
const fixture = () => ({schema:'BOAT_EDGE_V237_SITE_SELF_DRIVE_HEALTH_V1', day_jst:'20261012',
  formal_guard_closed:true, formal_results_read_by_v237:false, production_model_changed:false,
  model_promotion_authorized:false, accuracy_improvement_proven:false,
  current_reference:{registered_today:3,settled_total:19,head_hits:10,top3_hits:4,top5_hits:5,top10_hits:7},
  research_candidates:{pre_result_registered_today:2},
  simulator:{virtual_only:true,daily_budget_yen:50000,current_day_verified:true,source_day_jst:'20261012',
    today_spent_yen:10000,today_remaining_yen:40000},
  odds_band_at_freeze:{hits:1,eligible_races:5}});
test('JST midnight switches day independently of browser timezone', () => {
  assert.equal(dayJst('2026-10-11T15:00:00Z'), '20261012');
  assert.equal(dayJst('2026-10-11T14:59:59Z'), '20261011');
});
test('current report shows observed rates and validated daily balance', () => {
  const v = view(fixture(), '2026-10-11T15:30:00Z');
  assert.equal(v.spent, '10,000円'); assert.equal(v.remaining, '40,000円');
  assert.equal(v.metrics[3][1], '7/19（36.8%）'); assert.equal(v.band, '1/5（20.0%）');
});
test('an old health file never relabels yesterday as today', () => {
  const v = view(fixture(), '2026-10-12T15:00:00Z');
  assert.equal(v.registered, '更新待ち'); assert.equal(v.candidates, '更新待ち');
  assert.equal(v.spent, '本日分の更新待ち'); assert.equal(v.remaining, '—');
});
test('current report with old wallet does not invent zero spend', () => {
  const d=fixture();d.simulator.source_day_jst='20261011';
  assert.equal(view(d,'2026-10-11T15:30:00Z').spent,'本日分の更新待ち');
});
test('locked formal scope and virtual cap are mandatory', () => {
  for (const mutate of [d=>d.formal_guard_closed=false,d=>d.model_promotion_authorized=true,
    d=>d.simulator.virtual_only=false,d=>d.simulator.today_spent_yen=50100]) {
    const d=fixture();mutate(d);assert.throws(()=>view(d,'2026-10-11T15:30:00Z'));
  }
});
test('zero races and missing odds-band data do not show fake hit rates', () => {
  const d=fixture();d.current_reference.settled_total=0;delete d.odds_band_at_freeze;
  const v=view(d,'2026-10-11T15:30:00Z');assert.equal(v.band,'採点待ち');
  assert.equal(v.metrics[0][1],'採点待ち');
});
test('manual refresh clears rows, preserves the button and hides invalid reports', async () => {
  const fs=require('node:fs'),vm=require('node:vm');
  const nodes=new Map();
  const element=()=>({children:[],listeners:{},hidden:false,disabled:false,textContent:'',
    append(child){this.children.push(child);},replaceChildren(){this.children=[];},
    addEventListener(type,listener){this.listeners[type]=listener;}});
  const document={getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);},
    createElement:element};
  let data=fixture();
  data.day_jst=dayJst(new Date());data.simulator.source_day_jst=data.day_jst;
  data.research_candidates.comparisons=Object.fromEntries(['hit10','balance10','scenario7plus3','coverage15']
    .map(key=>[key,{hits:0,races:0}]));
  const context={document,Date,fetch:async()=>({ok:true,json:async()=>data})};
  vm.runInNewContext(fs.readFileSync(require.resolve('../assets/boat_edge_v271_health.js'),'utf8'),context);
  await new Promise(resolve=>setImmediate(resolve));
  const button=document.getElementById('refreshHealth');
  assert.equal(document.getElementById('observed').children.length,4);
  await button.listeners.click();
  assert.equal(document.getElementById('observed').children.length,4);
  assert.equal(document.getElementById('rates').children.length,4);
  assert.equal(button.disabled,false);
  data={...data,formal_guard_closed:false};
  await button.listeners.click();
  assert.equal(document.getElementById('stats').hidden,true);
  assert.equal(button.disabled,false);
  assert.match(document.getElementById('message').textContent,/表示できません/);
});
