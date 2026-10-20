#!/usr/bin/env python3
"""V269 deterministic telemetry audit: no network or formal target access."""
import ast
import json
import tempfile
from pathlib import Path
s=Path('.github/workflows/auto-update.yml').read_text(encoding='utf8')
a=s.index('          urgent_keys=[f"')
b=s.index('\n\n          health={',a)
code='\n'.join(line[10:] for line in s[a:b].splitlines())
ast.parse(code)
env={'json':json,'ymd':'20261012','targets':[('19',8,7),('19',9,23),('19',10,12),('19',11,-4),('19',12,2),('01',12,15)],
     'before':{'20261012-19-08':{'status':'ok'},'20261012-19-10':{'status':'published_wait'},
               '20261012-19-12':{'status':'error'},'20261012-01-12':{'status':'ok'}}}
# Comprehensions resolve names from globals, so share the controlled namespace.
with tempfile.TemporaryDirectory() as tmp:
    env['RACES']=Path(tmp)
    exec(compile(ast.parse(code),'<V269_SOURCE_ONLY>','exec'),env,env)
    assert env['urgent_original_saved']==0
    assert env['urgent_original_missing']==4
assert len(env['urgent_keys'])==4
assert env['urgent_ok']==2
assert env['urgent_wait']==1
assert env['urgent_error']==1
for name in ('beforeinfo_urgent_15m_targets','beforeinfo_urgent_15m_ok',
             'beforeinfo_urgent_15m_published_wait','beforeinfo_urgent_15m_error'):
    assert f'"{name}"' in s
assert 'results_seen":False,"unlock":False,"scoring":False' in s
print('V269_URGENT_PRE_RESULT_BEFOREINFO_TELEMETRY_PASS')

# The collector's second independent launch signal is NOT a source of trust;
# its actual upstream run must be verified before granting contents:write.
collector=Path('.github/workflows/auto-update.yml').read_text(encoding='utf8')
assert "workflow_run:" in collector
assert "'BOAT EDGE 3連単オッズ更新 V71'" in collector
assert "github.event.workflow_run.conclusion == 'success'" in collector
assert "github.event.workflow_run.head_branch == 'main'" in collector
assert "github.event.workflow_run.head_repository.full_name == github.repository" in collector
assert "github.ref == 'refs/heads/main'" in collector
odds=Path('.github/workflows/site-odds.yml').read_text(encoding='utf8')
# Legacy versions had no V71 listener. Newer main accepts ONLY a V216
# original schedule completion; V71-triggered V216 runs must not echo back.
odds_header=odds.split("permissions:",1)[0]
if "  workflow_run:" in odds_header:
    assert odds_header.count("  workflow_run:")==1
    assert "      - 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'" in odds_header
    assert "      - 'BOAT EDGE 自動更新'" not in odds_header
    assert "      - 'BOAT EDGE 3連単オッズ更新 V71'" not in odds_header
    for guard in (
        "github.event.workflow_run.conclusion == 'success'",
        "github.event.workflow_run.event == 'schedule'",
        "github.event.workflow_run.head_branch == 'main'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
        "github.event.workflow_run.name == 'BOAT EDGE V216 - Identify Exact Pre-Deadline Source Gaps'",
    ):
        assert guard in odds, "V71_UNSAFE_V216_SOURCE_WAKE_MISSING_GUARD: "+guard
# Urgent status is a single predicate of observed source coverage, not
# the unrelated success of race-card venue discovery.
health_source=collector.split('          health={',1)[1].split(
    '\n          (DATA/"health.json")',1)[0]
health_expr=ast.parse("x={" + '\n'.join(
    row[10:] for row in health_source.splitlines()) )
status_expr=next(value for key,value in zip(
    health_expr.body[0].value.keys, health_expr.body[0].value.values
) if isinstance(key,ast.Constant) and key.value=='status')
readiness_expr=next(value for key,value in zip(
    health_expr.body[0].value.keys, health_expr.body[0].value.values
) if isinstance(key,ast.Constant) and key.value=='predeadline_readiness_status')
def test_status(active,urgent_wait,urgent_error,urgent_keys):
    vars=locals()
    return (eval(compile(ast.Expression(status_expr),'<health>', 'eval'),vars),
            eval(compile(ast.Expression(readiness_expr),'<health>', 'eval'),vars))
assert test_status({'06'},0,0,['20261015-06-01']) == ('ok','READY_URGENT_SOURCE')
assert test_status({'06'},0,2,['20261015-06-01']) == ('source_incomplete','INCOMPLETE_URGENT_SOURCE')
assert test_status({'06'},1,0,['20261015-06-01']) == ('source_incomplete','INCOMPLETE_URGENT_SOURCE')
assert test_status({'06'},0,0,[]) == ('ok','NO_URGENT_RACES')
assert test_status(set(),0,0,[]) == ('source_unavailable','NO_URGENT_RACES')
print('V01_INDEPENDENT_COLLECTOR_TRIGGER_AND_URGENT_HEALTH_PASS')
