#!/usr/bin/env python3
"""V288 regression: official source-only racing deadline is a hard write cutoff.

Fixture and static source checks only. Never uses results, payouts, odds or network.
"""
from __future__ import annotations
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.boat_edge_v288_deadline_source_lock import source_write_allowed, JST

KEY="20261013-14-01"
NOW=datetime(2026,10,13,8,34,59,tzinfo=JST)
with tempfile.TemporaryDirectory() as tmp:
    data=Path(tmp)
    assert source_write_allowed(data,KEY,"08:35",NOW) is True
    assert source_write_allowed(data,KEY,"08:35",NOW.astimezone(timezone.utc)) is True
    assert source_write_allowed(data,KEY,"08:35",NOW+timedelta(seconds=1)) is False
    assert source_write_allowed(data,KEY,"08:35",NOW+timedelta(hours=1)) is False
    assert source_write_allowed(data,KEY,"08:35",NOW+timedelta(days=1)) is False
    assert source_write_allowed(data,KEY,None,NOW) is False
    assert source_write_allowed(data,KEY,"",NOW) is False
    assert source_write_allowed(data,KEY,"24:00",NOW) is False
    assert source_write_allowed(data,KEY,"8:35",NOW) is False
    assert source_write_allowed(data,KEY,"08:35",NOW.replace(tzinfo=None)) is False
    # Existing immutable snapshot blocks even an upcoming race, and a broken
    # snapshot cannot be treated as permission to repair/retroactively rewrite.
    snap=data/"site_prediction_snapshots"/(KEY+".json")
    snap.parent.mkdir(parents=True)
    snap.write_bytes(b"NOT VALID JSON BUT STILL IMMUTABLE")
    assert source_write_allowed(data,KEY,"08:35",NOW) is False
    assert snap.read_bytes()==b"NOT VALID JSON BUT STILL IMMUTABLE"
    snap.unlink()
    assert source_write_allowed(data,"20261013-14-01","08:35",NOW) is True
    for unsafe in ("bad","20261013-14-01/../../x","20261013-14-01.json"):
        try:source_write_allowed(data,unsafe,"08:35",NOW)
        except ValueError:pass
        else:raise AssertionError("V288_UNSAFE_RACE_KEY_ACCEPTED "+unsafe)

wf=Path(".github/workflows/auto-update.yml").read_text(encoding="utf8")
def inline(stage):
    block=wf.split("      - name: "+stage+"\n",1)[1]
    raw=block.split("          python - <<'PY'\n",1)[1].split("\n          PY\n",1)[0]
    src="\n".join(row[10:] for row in raw.splitlines())
    ast.parse(src)
    return src

first=inline("PRE_RESULT耐障害取得")
second=inline("5ソース同期・CURRENT準備監査")
imp="from scripts.boat_edge_v288_deadline_source_lock import source_write_allowed"
assert imp in first and imp in second
assert 'if 0<=delta<=150:targets.append((j,rno,delta))' in first
assert 'if -30<=delta<=150:' not in first
assert first.index('if not source_write_allowed(DATA,key,clock,datetime.now(JST)):') < first.index('url=f"{BASE}/owpc/pc/race/beforeinfo')
assert first.count('if not source_write_allowed(DATA,key,clock,datetime.now(JST)):')>=5
assert first.count('if source_write_allowed(DATA,key,clock,datetime.now(JST)):')==0
assert first.index('if not source_write_allowed(DATA,key,clock,datetime.now(JST)):') < first.index('race_results={}')
assert first.index('if not source_write_allowed(DATA,key,clock,datetime.now(JST)):') < first.index('doc={')
assert first.count('deadline_elapsed_during_fetch')==2
assert 'if not source_write_allowed(DATA,race_key,clock,datetime.now(JST)):' in second
assert second.index('if not source_write_allowed(DATA,race_key,clock,datetime.now(JST)):') < second.index('audit=doc.setdefault("source_audit",{})')
assert '"site_deadline_or_unknown_locked_races":deadline_locked' in first
assert '"race_cards_held_unchanged":sum(bool(x.get("preserved"))' in first
assert '"results_seen":False,"unlock":False,"scoring":False' in first
assert 'formalFirst100' in second
assert '/race/result' not in first and '/race/pay' not in first
assert '/race/result' not in second and '/race/pay' not in second
print("V288_FINISHED_RACE_SOURCE_LOCK_NO_BACKFILL_PASS")
