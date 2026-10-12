#!/usr/bin/env python3
"""V274 static collector regression: no HTTP, prediction, payout or formal result reads."""
from pathlib import Path
import ast

workflow=Path('.github/workflows/auto-update.yml').read_text(encoding='utf-8')
head=workflow.index("          python - <<'PY'\n")+len("          python - <<'PY'\n")
tail=workflow.index("\n          PY\n",head)
first=workflow[head:tail]
code='\n'.join(line[10:] for line in first.splitlines())
ast.parse(code)

loc=lambda text: first.index(text)
assert loc('urgent_beforeinfo=') < loc('before={}'), 'urgent targets must be computed'
assert loc('before={}') < loc('race_results={}'), 'urgent official beforeinfo must precede all bulk racelists'
assert loc('race_results={}') < loc('summary={'), 'race cards must complete before publication'
assert 'futs=[ex.submit(before_task,j,r) for j,r,_delta in targets]' in first
assert 'futs=[ex.submit(race_task,j,r) for j in active for r in range(1,13)]' in first
assert '"fetched_at":rr.get("fetched_at") if rr.get("ok") else None' in first
assert '"fetched_at":bf.get("fetched_at") if bf and bf.get("ok") else None' in first
assert '"fetched_at":datetime.now(JST).isoformat(timespec="seconds")' in first
assert 'Cached venue probe was fetched before bulk collection' in first
assert '"fetched_at":iso}' in first
assert '"results_seen":False,"unlock":False,"scoring":False' in first
assert 'result_unlock_token":None,"result":None' in first
assert '/race/result' not in first and '/race/odds' not in first and '/race/pay' not in first
print('V274_PRE_RESULT_URGENT_FIRST_SOURCE_TIMESTAMP_LOCK_PASS')
