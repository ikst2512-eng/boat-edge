#!/usr/bin/env python3
"""V275 evidence preservation: source syntax, immutability decisions and guard wiring.

Never downloads odds, visits results/payouts or touches formal Fresh records.
"""
from pathlib import Path
import ast
import tempfile
import sys

# Running "python3 tests/<test>.py" puts tests/, not the repo root, on sys.path.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.boat_edge_v275_frozen_protection import protected_site_snapshot

wf=Path(".github/workflows/auto-update.yml").read_text(encoding="utf-8")


def inline_code(stage):
    section=wf.split("      - name: "+stage+"\n",1)[1]
    raw=section.split("          python - <<'PY'\n",1)[1].split("\n          PY\n",1)[0]
    code="\n".join(line[10:] for line in raw.splitlines())
    ast.parse(code)
    return code


first=inline_code("PRE_RESULT耐障害取得")
second=inline_code("5ソース同期・CURRENT準備監査")
module="from scripts.boat_edge_v275_frozen_protection import protected_site_snapshot"
gate="from scripts.boat_edge_v288_deadline_source_lock import source_write_allowed"
assert gate in first and gate in second
assert module in first and module in second
assert first.count("if not source_write_allowed(DATA,key,clock,datetime.now(JST)):")>=3
assert first.count("if protected_site_snapshot(DATA,key):snapshot_protected+=1")==1
assert 'if not source_write_allowed(DATA,key,clock,datetime.now(JST)):\n' in first
assert 'if not source_write_allowed(DATA,race_key,clock,datetime.now(JST)):' in second
assert first.index("if not source_write_allowed(DATA,key,clock,datetime.now(JST)):") < first.index("doc={")
assert second.index("if not source_write_allowed(DATA,race_key,clock,datetime.now(JST)):") < second.index('audit=doc.setdefault("source_audit",{})')
assert '"site_snapshot_immutable_races":snapshot_protected' in first
assert '"site_snapshot_immutable_races":protected_count' in second
assert 'if (doc.get("current_model_input") or {}).get("core7_ready") is True:' in second
assert '"beforeinfo_status":old_before.get("status","protected_source_unavailable")' in first
assert 'from scripts.boat_edge_v275_frozen_protection' in first

with tempfile.TemporaryDirectory() as temp:
    data=Path(temp)
    key="20261013-19-08"
    assert protected_site_snapshot(data,key) is False
    freeze=data/"site_prediction_snapshots"/(key+".json")
    freeze.parent.mkdir(parents=True)
    freeze.write_bytes(b"{invalid but immutable}")
    assert protected_site_snapshot(data,key) is True, "Malformed freeze must still protect source"
    assert freeze.read_bytes()==b"{invalid but immutable}"
    for name in ("20261013-19-08/../../x","bad","20261013-19-08.json"):
        try:protected_site_snapshot(data,name)
        except ValueError:pass
        else:raise AssertionError("V275_INVALID_RACE_KEY_ACCEPTED "+name)

# Do not depend on any result status, user funds, or prediction model version.
assert "/race/result" not in first and "/race/pay" not in first
assert "formalFirst100" in second and '"results_seen":False,"unlock":False,"scoring":False' in first
print("V275_FROZEN_PRE_RESULT_EVIDENCE_PRESERVATION_PASS")
