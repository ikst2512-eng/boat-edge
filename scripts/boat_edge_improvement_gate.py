#!/usr/bin/env python3
"""Read-only BOAT EDGE improvement gate: classify evidence, never auto-promote."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

def inspect(root: Path) -> dict:
    def read(rel):
        try:
            v=json.loads((root/rel).read_text(encoding="utf-8"))
            return v if isinstance(v,dict) else {}
        except (OSError, ValueError, UnicodeError):
            return {}
    health=read("data/health.json")
    formal=read("data/formal_status.json")
    fast=read("data/site_autopilot/v230_fast_current.json")
    blockers=[]
    warnings=[]
    guards=formal.get("guards") or {}
    if not formal:
        blockers.append("FORMAL_STATUS_MISSING")
    elif any(guards.get(k) is not False for k in ("results_seen","unlock","scoring")) or guards.get("RESULT_UNLOCK_TOKEN") is not None:
        blockers.append("FORMAL_PRE_RESULT_GUARD_BROKEN")
    if not health:
        warnings.append("HEALTH_MISSING")
    else:
        card_total=health.get("race_cards_total")
        card_ok=health.get("race_cards_ok")
        if (type(card_total) is int and card_total>0 and type(card_ok) is int
                and 0<=card_ok<=card_total and card_ok/card_total<0.8):
            warnings.append("RACE_CARD_LOW_COVERAGE")
        targets=health.get("beforeinfo_targets")
        obtained=health.get("beforeinfo_ok")
        if (type(targets) is int and targets>0 and type(obtained) is int
                and 0<=obtained<=targets and obtained/targets<0.8):
            warnings.append("BEFOREINFO_LOW_COVERAGE")
        if (type(health.get("original_exhibition_urgent_15m_missing")) is int
                and health["original_exhibition_urgent_15m_missing"]>0):
            warnings.append("ORIGINAL_EXHIBITION_MISSING")
    if fast:
        if type(fast.get("fetch_wall_seconds")) in (int,float):
            t=fast["fetch_wall_seconds"]
            if math.isfinite(t) and t>45:
                warnings.append("FETCH_STAGE_SLOW")
        if type(fast.get("freeze_wall_seconds")) in (int,float):
            t=fast["freeze_wall_seconds"]
            if math.isfinite(t) and t>15:
                warnings.append("FREEZE_STAGE_SLOW")
        if fast.get("network_error",0)>0:
            warnings.append("OFFICIAL_NETWORK_FAILURE")
        if fast.get("odds_incomplete",0)>0:
            warnings.append("OFFICIAL_ODDS_INCOMPLETE")
    else:
        warnings.append("FAST_LANE_DIAGNOSTICS_MISSING")
    priorities=[
        {"problem":w,"action":{
            "RACE_CARD_LOW_COVERAGE":"調査: 開催場一覧/レース出走表の発見と取得成功率",
            "BEFOREINFO_LOW_COVERAGE":"調査: 公開時刻・レース別直前情報と取得失敗理由",
            "ORIGINAL_EXHIBITION_MISSING":"調査: 正規の公式提供元と6艇実数値の締切前受信",
            "FETCH_STAGE_SLOW":"調査: レースごとの通信時間と公式側遅延",
            "FREEZE_STAGE_SLOW":"調査: 初回保存監査の処理時間",
            "OFFICIAL_NETWORK_FAILURE":"調査: 接続失敗の種類・時間・頻度",
            "OFFICIAL_ODDS_INCOMPLETE":"調査: 120通り公開タイミングとDOM検証",
            "HEALTH_MISSING":"確認: health出力が存在するか",
            "FAST_LANE_DIAGNOSTICS_MISSING":"確認: V230計測ログ生成の有無",
        }.get(w,"確認: 未分類の警告")} for w in warnings]
    return {"schema":"boat-edge-improvement-gate-v1","decision":"FAIL_CLOSED" if blockers else "OBSERVE",
            "blockers":blockers,"warnings":warnings,"priorities":priorities,
            "production_changed":False,"formal_certified":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    result=inspect(args.root)
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(payload,encoding="utf-8")
    print(payload,end="")
    return 1 if result["blockers"] else 0

if __name__=="__main__":
    raise SystemExit(main())
