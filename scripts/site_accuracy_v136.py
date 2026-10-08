
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, collections

BASE=Path(".")
HISTORY=BASE/"data/site_prediction_history"
RESULTS=BASE/"data/site_results"
AUDIT=BASE/"data/site_prediction_audit/index.json"
OUT=BASE/"data/site_learning/mode_accuracy_v136.json"
DETAIL=BASE/"data/site_learning/site_mode_evaluations_v136"
MODES=("hit","balance","hole","narrow")
POLICY="BALANCE10_WAVE12_15_18_V133_FIXED"
LABELS={"hit":"的中重視","balance":"バランス","hole":"波乱展開","narrow":"激絞り"}

def get(p):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError,ValueError):return None

def iso(v):
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError):return None

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

audit=get(AUDIT) or {}
audited=audit.get("audited") or {}
counts=collections.Counter()
by_mode={m:{"label":LABELS[m],"evaluated":0,"hits":0,"misses":0,"hit_rate_percent":None} for m in MODES}
by_head={"1":{"evaluated":0,"hits":{m:0 for m in MODES}},"2-6":{"evaluated":0,"hits":{m:0 for m in MODES}}}
evidence=[]
DETAIL.mkdir(parents=True,exist_ok=True)
for hp in sorted(HISTORY.glob("20??????-??-??.json")):
    h=get(hp) or {}
    snap=h.get("snapshot") or {}
    if snap.get("mode_policy")!=POLICY:continue
    key=str(snap.get("race_key") or hp.stem)
    settlement=h.get("settlement") or {}
    if not settlement:
        counts["unsettled"]+=1
        continue
    if snap.get("schema_version")!="boat-edge-server-site-final-v123" or snap.get("snapshot_window")!="FINAL_15M":
        counts["invalid_snapshot_contract"]+=1
        continue
    if snap.get("prediction_kind")!="SITE_REFERENCE_V122":
        counts["not_reference_prediction"]+=1
        continue
    guards=snap.get("guards") or {}
    if any(guards.get(x) is not False for x in ("results_seen","unlock","scoring")):
        counts["pre_result_guard_invalid"]+=1
        continue
    try:remaining=float(snap["minutes_to_deadline"])
    except (ValueError,TypeError,KeyError):remaining=-1
    if not 0<=remaining<=16:
        counts["deadline_window_invalid"]+=1
        continue
    first=iso(snap.get("first_saved_at"))
    saved=iso(snap.get("saved_at"))
    settled=iso(settlement.get("settled_at"))
    if not first or not saved or not settled or not first<=saved<settled:
        counts["temporal_order_invalid"]+=1
        continue
    proof=audited.get(key) or {}
    if proof.get("pass") is not True or proof.get("latest_snapshot_saved_at")!=snap.get("saved_at"):
        counts["awaiting_matching_v125_audit"]+=1
        continue
    result_path=RESULTS/f"{key}.json"
    result=get(result_path) or {}
    winning=result.get("trifecta")
    if result.get("status")!="confirmed" or not isinstance(winning,str):
        counts["confirmed_result_missing"]+=1
        continue
    if winning!=settlement.get("winning_combo"):
        counts["result_settlement_mismatch"]+=1
        continue
    group="1" if winning.startswith("1-") else "2-6"
    cases={}
    valid=True
    for mode in MODES:
        items=((snap.get("modes") or {}).get(mode) or {}).get("tickets") or []
        combos=[row.get("combo") for row in items if isinstance(row,dict)]
        if not combos or any(not isinstance(c,str) for c in combos) or len(set(combos))!=len(combos):
            valid=False;break
        if mode=="hit" and len(combos)!=10:valid=False;break
        if mode=="balance" and len(combos)!=10:valid=False;break
        if mode=="narrow" and len(combos)!=3:valid=False;break
        if mode=="hole" and len(combos) not in (12,15,18):valid=False;break
        hit=winning in combos
        if (settlement.get("mode_hits") or {}).get(mode) is not hit:
            valid=False;break
        cases[mode]={"hit":hit,"count":len(combos),"ticket_rank":combos.index(winning)+1 if hit else None}
    if not valid:
        counts["tickets_or_settlement_invalid"]+=1
        continue
    entry={
        "schema_version":"boat-edge-site-mode-evaluation-v136",
        "scope":"SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH",
        "race_key":key,
        "snapshot_saved_at":snap["saved_at"],
        "snapshot_first_saved_at":snap["first_saved_at"],
        "settled_at":settlement["settled_at"],
        "remaining_at_snapshot_minutes":remaining,
        "mode_policy":POLICY,
        "winning_combo":winning,
        "official_result_source":result.get("source"),
        "source_history_sha256":digest(hp),
        "source_result_sha256":digest(result_path),
        "used_inputs":snap.get("used_inputs") or [],
        "grade":snap.get("grade"),
        "winning_head_group":group,
        "modes":cases
    }
    dp=DETAIL/f"{key}.json"
    blob=json.dumps(entry,ensure_ascii=False,indent=2)+"\n"
    if not dp.exists() or dp.read_text(encoding="utf-8")!=blob:
        dp.write_text(blob,encoding="utf-8")
    evidence.append(entry)
    by_head[group]["evaluated"]+=1
    for mode in MODES:
        by_mode[mode]["evaluated"]+=1
        by_mode[mode]["hits"]+=int(cases[mode]["hit"])
        by_mode[mode]["misses"]+=int(not cases[mode]["hit"])
        by_head[group]["hits"][mode]+=int(cases[mode]["hit"])

for mode in MODES:
    x=by_mode[mode]
    if x["evaluated"]:
        x["hit_rate_percent"]=round(100*x["hits"]/x["evaluated"],1)

summary={
    "schema_version":"boat-edge-site-mode-accuracy-v136",
    "scope":"SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH",
    "formal_current_scoring":False,
    "production_prediction_weights_changed":False,
    "predictions_evaluated":len(evidence),
    "mode_policy":POLICY,
    "modes":by_mode,
    "by_winning_head":by_head,
    "excluded_reasons":dict(sorted(counts.items())),
    "method":"Only V133 prospective FINAL_15M snapshots with matching V125 audit and confirmed official result; no race/result endpoint consulted, no historical prediction backfill.",
    "rank_120_available":False,
    "latest_settlement":max((e["settled_at"] for e in evidence),default=None),
    "example_race_keys":[e["race_key"] for e in evidence[:10]],
    "note":"Descriptive observed hit rates, not proven predictive improvement. Site reference predictions are separate from formal Fresh validation."
}
OUT.parent.mkdir(parents=True,exist_ok=True)
blob=json.dumps(summary,ensure_ascii=False,indent=2)+"\n"
if not OUT.exists() or OUT.read_text(encoding="utf-8")!=blob:
    OUT.write_text(blob,encoding="utf-8")
print(json.dumps({"evaluated":len(evidence),"modes":by_mode,"excluded":dict(counts)},ensure_ascii=False))
