#!/usr/bin/env python3
"""Offline V288 source-HTML structure test. No HTTP, results, payouts or formal unlock."""
import ast
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

source=Path('.github/workflows/auto-update.yml').read_text(encoding='utf8')
def extract(start_token,end_token):
    a=source.index(start_token)
    b=source.index(end_token,a)
    code='\n'.join(line[10:] for line in source[a:b].splitlines())
    ast.parse(code)
    return code

parsing=extract('          def parse_before(soup):','\n          errors=[]')
coverage=extract('          def beforeinfo_coverage(parsed):','\n          def before_task(j,rno):')
def txt(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',value or '')).strip()
scope={'re':re,'txt':txt}
exec(compile(parsing+'\n'+coverage,'<v288_source_only>','exec'),scope,scope)
parse=scope['parse_before']
gate=scope['beforeinfo_coverage']

# Archived official PRE_RESULT HTML files are structural test fixtures only.
# No result, payout, or formal prediction files are loaded.
for path in ('data/raw/20261012/14_01_beforeinfo.html',
             'data/raw/20261012/01_03_beforeinfo.html'):
    raw=Path(path).read_text(encoding='utf8')
    parsed=parse(BeautifulSoup(raw,'lxml'))
    status=gate(parsed)
    assert status['six_boat_complete'] is True,(path,status,parsed['start_exhibition'])
    assert status['exhibition_lanes']==6 and status['start_exhibition_lanes']==6
    assert [x['lane'] for x in parsed['start_exhibition']]==list(range(1,7))
    assert all(6<=float(x['exhibition_time'])<=8.5 for x in parsed['racers'])

# The actual archived official 14-01 page encodes ST as classed spans.
p=parse(BeautifulSoup(Path('data/raw/20261012/14_01_beforeinfo.html').read_text(),'lxml'))
assert [x['st'] for x in p['start_exhibition']]==['.06','.09','.02','F.02','F.09','.01']
assert p['racers'][0]['exhibition_time']==6.79
# A NEXT table may contain similar numbers; never steal ST from it.
wrong=BeautifulSoup('''<table><tr><th>スタート展示</th></tr>
<tr><td>データ公開待ち</td></tr></table>
<table><tr><td><div class="table1_boatImage1">
<span class="table1_boatImage1Number">1</span>
<span class="table1_boatImage1Time">.01</span></div></td></tr></table>''','lxml')
assert parse(wrong)['start_exhibition']==[]
# Keep the exact F or signed token. Avoid making up a positive start.
signed=BeautifulSoup('''<table><thead><tr><th>スタート展示</th></tr></thead><tbody>
<tr><td><div class="table1_boatImage1">
<span class="table1_boatImage1Number">4</span>
<span class="table1_boatImage1Time">-0.02</span></div></td></tr></tbody></table>''','lxml')
assert parse(signed)['start_exhibition']==[{'lane':4,'st':'-0.02'}]
# The collector's six-boat completeness check must accept the SAME ST token
# formats as its HTML parser. Otherwise fully populated official ST may be
# mislabeled as "publication pending" and never frozen prospectively.
signed_rows=[{'lane':i,'st':('.06' if i<4 else ('F.02' if i==4 else ('-0.02' if i==5 else '0.01')))}
             for i in range(1,7)]
signed_parsed={'racers':p['racers'],'start_exhibition':signed_rows}
signed_state=gate(signed_parsed)
assert signed_state['six_boat_complete'] is True,signed_state
assert signed_state['start_exhibition_lanes']==6
for rejected_st in ('', '0.3ms','-.','F.123', '0.999','unknown'):
    broken=[dict(x) for x in signed_rows]
    broken[4]['st']=rejected_st
    assert gate({'racers':p['racers'],'start_exhibition':broken})['six_boat_complete'] is False,rejected_st

# Invalid and duplicate evidence must not become a verified six-lane source.
m=dict(p)
m['start_exhibition']=p['start_exhibition']+[p['start_exhibition'][0]]
assert gate(m)['six_boat_complete'] is False
m=dict(p)
m['racers']=p['racers']+[p['racers'][0]]
assert gate(m)['six_boat_complete'] is False
m=dict(p)
m['start_exhibition']=[x for x in p['start_exhibition'] if x['lane']!=6]
assert gate(m)['six_boat_complete'] is False
assert "'results_seen':False" not in parsing or 'race/result' not in parsing
print('V288_OFFICIAL_ARCHIVED_PRE_RESULT_HTML_START_ST_SIX_BOAT_PASS')
