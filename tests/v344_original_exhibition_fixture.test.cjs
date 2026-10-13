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
function race(id) {
  return JSON.parse(fs.readFileSync(path.join(root, 'data/races', id + '.json'), 'utf8'));
}
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
