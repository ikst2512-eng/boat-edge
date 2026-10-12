'use strict';
/* A25: no inferred BOATERS or 競艇日和 verification from one imported CSV. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('assets/boat_edge_v203_readable.js','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(source,{window,document,Date,Number,Math,Map,Set,JSON}, {filename:'v260-original-evidence.js'});
const api=window.BoatEdgeV203;
assert.equal(typeof api.independentExhibitionAudit,'function');
const key='20261012-14-09';
const stamp='2026-10-12T13:30:00+09:00',sha='a'.repeat(64);
const original={status:'ok',source:'https://boatracecsv.github.io/data/previews/original_exhibition/2026/10/12.csv',fetched_at:stamp,sha256:sha};
const official={status:'ok',source:'https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd=20261012&jcd=14&rno=9',fetched_at:stamp,sha256:sha};
const race={race_key:key,meta:{deadline:'14:00'},source_audit:{beforeinfo:official,original_exhibition:original}};
const isolated=api.independentExhibitionAudit(race);
assert(isolated.boaters.includes('未取得'));
assert(isolated.keiteibiyori.includes('未取得'));
assert(isolated.official.includes('取得'));
assert(isolated.csv.includes('取得'));
assert(!isolated.boaters.includes('個別取得履歴あり'));
assert(!isolated.keiteibiyori.includes('個別取得履歴あり'));
const common={status:'ok',fetched_at:stamp,sha256:sha,source:'https://example.org/independent-original-exhibition',race_key:key};
const enriched={...race,source_audit:{...race.source_audit,original_exhibition_sources:{
 boaters:{...common,provider:'BOATERS'},
 keiteibiyori:{...common,provider:'競艇日和'}}}};
const observed=api.independentExhibitionAudit(enriched);
assert(observed.boaters.includes('個別取得履歴あり'));
assert(observed.keiteibiyori.includes('個別取得履歴あり'));
assert(observed.boaters.includes('数値相互照合は未証明'));
assert(observed.keiteibiyori.includes('数値相互照合は未証明'));
const late={...enriched,source_audit:{...enriched.source_audit,original_exhibition_sources:{
 ...enriched.source_audit.original_exhibition_sources,
 boaters:{...common,provider:'BOATERS',fetched_at:'2026-10-12T14:02:00+09:00'}}}};
assert(api.independentExhibitionAudit(late).boaters.includes('締切後取得・予想根拠外'));
const spoof={...enriched,source_audit:{...enriched.source_audit,original_exhibition_sources:{
 boaters:{...common,provider:'競艇日和'},
 keiteibiyori:{...common,provider:'競艇日和',sha256:'not-a-hash'}}}};
const denied=api.independentExhibitionAudit(spoof);
assert(denied.boaters.includes('未取得'));
assert(denied.keiteibiyori.includes('未取得'));
const css=fs.readFileSync('assets/boat_edge_v203_readable.css','utf8');
const html=fs.readFileSync('index.html','utf8');
assert(source.includes('BOATERS</b>'));
assert(source.includes('競艇日和</b>'));
assert(source.includes('公式直前情報</b>'));
assert(source.includes('オリ展CSV</b>'));
assert(source.includes('数値の一致確認・独立照合は証拠が揃うまで未確認'));
assert(css.includes('BOAT_EDGE_A25_V260_DISTINCT_ORIGINAL_EXHIBITION_SOURCES'));
assert(html.includes('boat_edge_v203_readable.js?v=203&amp;rev=244&amp;patch=247&amp;patch2=250&amp;a25=1'));
assert(html.includes('boat_edge_v203_readable.css?v=203&amp;rev=244&amp;patch=247&amp;patch2=250&amp;a23=1&amp;a25=1'));
console.log('A25_V260_INDEPENDENT_EXHIBITION_PROVENANCE_PASS');
