'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'assets/boat_edge_v202_display.js'), 'utf8');
const context = { window: {}, document: { readyState: 'loading', addEventListener() {} }, console };
vm.runInNewContext(script, context, { filename: 'boat_edge_v202_display.js' });
const api = context.window.BoatEdgeV202;
// Source-pinned projections of saved PRE_RESULT races, not fabricated positive measurements.
// Production CI sparse-checkout excludes data/races; keep this regression self-contained.
const saved = {
  '20261013-06-01': {
    race_key: '20261013-06-01',
    source_audit: { original_exhibition: {
      status: 'ok', fetched_at: '2026-10-13T10:54:55+09:00',
      sha256: '6c818e28816901ee305904668937c24198928c2779c71ea3eedbc41c23bcb672'
    }},
    racers: Array.from({length: 6}, (_, i) => ({lane: i + 1, name: ['伊達 正利','渡邊 伸太郎','佐竹 友樹','鈴木 結平太','萬 正嗣','岸本 雄貴'][i]})),
    original_exhibition: {
      labels: ['一周','まわり足','直線'],
      boats: [[37.23,5.33,8.2],[37.11,5.24,8.1],[36.95,5.12,8.16],[37.16,5.38,8.07],[37.95,5.57,8.11],[38.06,5.75,7.91]].map((values, i) => ({lane:i+1, values}))
    }
  },
  '20261013-04-01': {
    race_key: '20261013-04-01',
    source_audit: { original_exhibition: {
      status: 'missing', fetched_at: null,
      sha256: 'e3382de5fe8f043fd0dcb1b008d4b33a072b3cd6c48d3f2159b4cebc62b9520f'
    }},
    racers: Array.from({length: 6}, (_, i) => ({lane:i+1}))
  }
};
function race(id) { return structuredClone(saved[id]); }
test('浜名湖1R: independently audited original exhibition maps to six visible row values', () => {
  const data = race('20261013-06-01');
  assert.equal(api.sourceOK(data, 'original_exhibition'), true);
  assert.deepEqual(Array.from(data.original_exhibition.labels), ['一周', 'まわり足', '直線']);
  assert.equal(data.original_exhibition.boats.length, 6);
  const result = api.makeRows(data);
  assert.equal(result.rows.length, 6);
  assert.ok(result.original);
  const one = result.rows.find(r => r.lane === 1);
  assert.equal(one.lap, 37.23);
  assert.equal(one.turn, 5.33);
  assert.equal(one.straight, 8.2);
  for (const row of result.rows) {
    assert.ok(Number.isFinite(row.lap));
    assert.ok(Number.isFinite(row.turn));
    assert.ok(Number.isFinite(row.straight));
  }
});
test('平和島1R: absent original exhibition never leaks fabricated values', () => {
  const data = race('20261013-04-01');
  assert.equal(api.sourceOK(data, 'original_exhibition'), false);
  const result = api.makeRows(data);
  assert.equal(result.original, null);
  assert.equal(result.rows.length, 6);
  for (const row of result.rows) {
    assert.equal(row.lap, null);
    assert.equal(row.turn, null);
    assert.equal(row.straight, null);
  }
});
test('source status alone is insufficient without fetched timestamp', () => {
  const data = race('20261013-06-01');
  data.source_audit.original_exhibition.fetched_at = null;
  assert.equal(api.sourceOK(data, 'original_exhibition'), false);
  assert.equal(api.makeRows(data).rows[0].lap, null);
});

test('V202 markup renders audited 1周/まわり足/直線 values, not only internal rows', () => {
  const markup = api.html(race('20261013-06-01'), null, null);
  assert.match(markup, /<th>1周<\/th><th>まわり足<\/th><th>直線<\/th>/);
  assert.match(markup, /37\.23<\/span><\/td><td><span class="be202-val [^"]*">5\.33<\/span><\/td><td><span class="be202-val [^"]*">8\.20<\/span>/);
  assert.match(markup, /オリ展 取得済/);
});
test('V202 markup keeps missing original exhibition blank and labels it uncollected', () => {
  const markup = api.html(race('20261013-04-01'), null, null);
  assert.match(markup, /オリ展 未取得/);
  assert.doesNotMatch(markup, /37\.23|5\.33|8\.20/);
});

test('V346 never presents unverified saved course, ST, or exhibition time as current', () => {
  const data = race('20261013-04-01');
  data.beforeinfo = {
    racers: [{lane:1,exhibition_time:6.42,tilt:-0.5}],
    start_exhibition: [{lane:1,course:2,st:0.11}]
  };
  data.actual_entry = [{lane:1,course:3,exhibition_st_raw:0.08}];
  const row = api.makeRows(data).rows[0];
  assert.equal(row.course, null);
  assert.equal(row.st, null);
  assert.equal(row.displayTime, null);
  const markup = api.html(data, null, null);
  assert.match(markup, /公式展示 未取得/);
  assert.match(markup, /展示ST 未取得/);
  assert.doesNotMatch(markup, /6\.42|0\.11|0\.08/);
});
test('V346 verified beforeinfo still renders exhibition course ST and time', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: [{lane:1,exhibition_time:6.42}],
    start_exhibition: [{lane:1,course:2,st:0.11}]
  };
  const row = api.makeRows(data).rows[0];
  assert.equal(row.course, 2);
  assert.equal(row.st, 0.11);
  assert.equal(row.displayTime, 6.42);
});

test('V347 partial five-boat original exhibition cannot claim fully acquired', () => {
  const data = race('20261013-06-01');
  data.original_exhibition.boats.pop();
  const markup = api.html(data, null, null);
  assert.match(markup, /オリ展 未取得/);
  assert.doesNotMatch(markup, /オリ展 取得済/);
});
test('V347 duplicate lanes cannot fake complete original exhibition', () => {
  const data = race('20261013-06-01');
  data.original_exhibition.boats[5].lane = 1;
  assert.match(api.html(data, null, null), /オリ展 未取得/);
});
test('V347 four-boat official exhibition and ST cannot claim fully acquired', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: Array.from({length:4}, (_,i)=>({lane:i+1,exhibition_time:6.5})),
    start_exhibition: Array.from({length:4}, (_,i)=>({lane:i+1,course:i+1,st:0.12}))
  };
  const markup = api.html(data, null, null);
  assert.match(markup, /公式展示 未取得/);
  assert.match(markup, /展示ST 未取得/);
});
test('V347 six unique official exhibition lanes show complete badges', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: Array.from({length:6}, (_,i)=>({lane:i+1,exhibition_time:6.5})),
    start_exhibition: Array.from({length:6}, (_,i)=>({lane:i+1,course:i+1,st:0.12}))
  };
  const markup = api.html(data, null, null);
  assert.match(markup, /公式展示 取得済/);
  assert.match(markup, /展示ST 取得済/);
});

test('V348 missing one original exhibition metric cannot claim fully acquired', () => {
  const data = race('20261013-06-01');
  data.original_exhibition.boats[3].values[1] = null;
  const markup = api.html(data, null, null);
  assert.match(markup, /オリ展 未取得/);
  assert.equal(api.makeRows(data).rows[3].turn, null);
});
test('V348 missing required metric label cannot claim fully acquired', () => {
  const data = race('20261013-06-01');
  data.original_exhibition.labels = ['一周','まわり足','別指標'];
  assert.match(api.html(data, null, null), /オリ展 未取得/);
});
test('V348 all six lanes with three valid original metrics retain acquired badge', () => {
  assert.match(api.html(race('20261013-06-01'), null, null), /オリ展 取得済/);
});

test('V349 missing official exhibition time on one lane cannot claim complete', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: Array.from({length:6}, (_,i)=>({lane:i+1,exhibition_time:i===4?null:6.5})),
    start_exhibition: Array.from({length:6}, (_,i)=>({lane:i+1,course:i+1,st:0.12}))
  };
  const markup = api.html(data, null, null);
  assert.match(markup, /公式展示 未取得/);
  assert.match(markup, /展示ST 取得済/);
});
test('V349 missing exhibition ST on one lane cannot claim complete', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: Array.from({length:6}, (_,i)=>({lane:i+1,exhibition_time:6.5})),
    start_exhibition: Array.from({length:6}, (_,i)=>({lane:i+1,course:i+1,st:i===3?null:0.12}))
  };
  const markup = api.html(data, null, null);
  assert.match(markup, /公式展示 取得済/);
  assert.match(markup, /展示ST 未取得/);
});

test('V350 fractional and out-of-range course numbers are not shown as valid', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {start_exhibition:[
    {lane:1,course:2.5,st:0.12},{lane:2,course:7,st:0.11},
    {lane:3,course:3,st:0.10}
  ]};
  const rows = api.makeRows(data).rows;
  assert.equal(rows[0].course, null);
  assert.equal(rows[1].course, null);
  assert.equal(rows[2].course, 3);
});

test('V351 invalid exhibition ST becomes null while numeric ST is retained', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {start_exhibition:[
    {lane:1,course:1,st:'invalid'},
    {lane:2,course:2,st:'0.13'},
    {lane:3,course:3,st:null}
  ]};
  const rows = api.makeRows(data).rows;
  assert.equal(rows[0].st, null);
  assert.equal(rows[1].st, 0.13);
  assert.equal(rows[2].st, null);
});

test('V352 whitespace ST is missing both in rows and acquisition badge', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {
    racers: Array.from({length:6},(_,i)=>({lane:i+1,exhibition_time:6.5})),
    start_exhibition: Array.from({length:6},(_,i)=>({lane:i+1,course:i+1,st:i===2?'   ':'0.12'}))
  };
  assert.equal(api.makeRows(data).rows[2].st, null);
  assert.equal(api.makeRows(data).rows[0].st, 0.12);
  assert.match(api.html(data,null,null), /展示ST 未取得/);
});

test('V353 conflicting duplicated course positions are not presented as verified', () => {
  const data = race('20261013-04-01');
  data.source_audit.beforeinfo = {status:'ok',fetched_at:'2026-10-13T10:30:00+09:00'};
  data.beforeinfo = {start_exhibition:[
    {lane:1,course:2,st:0.12},
    {lane:2,course:2,st:0.11},
    {lane:3,course:3,st:0.10}
  ]};
  const rows = api.makeRows(data).rows;
  assert.equal(rows[0].course, null);
  assert.equal(rows[1].course, null);
  assert.equal(rows[2].course, 3);
  assert.equal(rows[0].st, 0.12);
});
