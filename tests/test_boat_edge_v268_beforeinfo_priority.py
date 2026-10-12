#!/usr/bin/env python3
"""V268 source-only scheduling regression; never calls official pages or result endpoints."""
import ast
from pathlib import Path

source=Path('.github/workflows/auto-update.yml').read_text(encoding='utf8')
start=source.index('          targets.sort(key=lambda row:')
end=source.index('\n\n          # V272:',start) if '\n\n          # V272:' in source[start:] else source.index('\n\n          def before_task',start)
line=source[start:end]
assert 'abs(row[2])' in line and 'row[0],row[1]' in line
sort_code='\n'.join(x[10:] for x in line.splitlines())
env={'targets':[(19,8,7),(19,9,23),(19,10,110),(19,11,-4),
                (19,12,2),(1,12,7),(19,7,16),(2,4,-22)]}
exec(compile(ast.parse(sort_code),'<V268_SORT_ONLY>','exec'),{'abs':abs},env)
assert [(j,r) for j,r,_ in env['targets']]==[
    (19,12),(1,12),(19,8),(19,7),(19,9),(19,10),(19,11),(2,4)]
assert len(env['targets'])==8
assert 'futs=[ex.submit(before_task,j,r) for j,r,_delta in targets]' in source
assert 'ready=coverage["six_boat_complete"]' in source
assert 'beforeinfo_coverage(parsed)' in source
assert '"published_wait"' in source
print('V268_BEFOREINFO_DEADLINE_PRIORITY_PASS')
