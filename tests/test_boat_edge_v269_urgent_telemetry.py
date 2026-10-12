#!/usr/bin/env python3
"""V269 deterministic telemetry audit: no network or formal target access."""
import ast
from pathlib import Path
s=Path('.github/workflows/auto-update.yml').read_text(encoding='utf8')
a=s.index('          urgent_keys=[f"')
b=s.index('\n\n          health={',a)
code='\n'.join(line[10:] for line in s[a:b].splitlines())
ast.parse(code)
env={'ymd':'20261012','targets':[(19,8,7),(19,9,23),(19,10,12),(19,11,-4),(19,12,2),(1,12,15)],
     'before':{'20261012-19-08':{'status':'ok'},'20261012-19-10':{'status':'published_wait'},
               '20261012-19-12':{'status':'error'},'20261012-01-12':{'status':'ok'}}}
exec(compile(ast.parse(code),'<V269_SOURCE_ONLY>','exec'),{},env)
assert len(env['urgent_keys'])==4
assert env['urgent_ok']==2
assert env['urgent_wait']==1
assert env['urgent_error']==1
for name in ('beforeinfo_urgent_15m_targets','beforeinfo_urgent_15m_ok',
             'beforeinfo_urgent_15m_published_wait','beforeinfo_urgent_15m_error'):
    assert f'"{name}"' in s
assert 'results_seen":False,"unlock":False,"scoring":False' in s
print('V269_URGENT_PRE_RESULT_BEFOREINFO_TELEMETRY_PASS')
