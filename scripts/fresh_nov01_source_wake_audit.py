#!/usr/bin/env python3
"""Read-only investigation of Nov 1 stale collector/odds/V216 evidence.
Workflow API run metadata is not proof an official source was available.
"""
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

START=datetime.fromisoformat("2026-11-01T01:40:00+00:00")
END=datetime.fromisoformat("2026-11-01T06:20:00+00:00")
WORKFLOWS=("auto-update.yml", "site-odds.yml",
           "BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml",
           "BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml")
def audit(repo, token, get_json, max_pages=10):
    if not repo or not token:
        raise ValueError("MISSING_READ_AUTH")
    report={"schema":"BOAT_EDGE_NOV01_SOURCE_WAKE_AUDIT_V1",
            "start_utc":START.isoformat(),"end_utc":END.isoformat(),
            "results_accessed":False,"formal_unlock_authorized":False,
            "workflows":{},"complete":True}
    for workflow in WORKFLOWS:
        runs=[]
        exhausted=False
        for page in range(1,max_pages+1):
            url=(f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs"
                 f"?per_page=100&page={page}&created=2026-11-01..2026-11-01")
            data=get_json(url,token)
            rows=data.get("workflow_runs")
            if not isinstance(rows,list):
                raise ValueError("INVALID_RUNS_RESPONSE")
            for run in rows:
                created=run.get("created_at")
                if not created: continue
                t=datetime.fromisoformat(created.replace("Z","+00:00"))
                if START<=t<=END:
                    runs.append({k:run.get(k) for k in ("id","event","created_at",
                        "run_started_at","updated_at","status","conclusion","html_url")})
            if len(rows)<100:
                exhausted=True
                break
        if not exhausted: report["complete"]=False
        runs.sort(key=lambda x:(x["created_at"],x["id"]))
        report["workflows"][workflow]={"runs":runs,"pagination_exhausted":exhausted,
              "number_created_in_window":len(runs),
              "scheduled_created":sum(x["event"]=="schedule" for x in runs),
              "failed":sum(x["conclusion"]=="failure" for x in runs),
              "cancelled":sum(x["conclusion"]=="cancelled" for x in runs)}
    return report
def github_json(url,token):
    req=Request(url,headers={"Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json"})
    with urlopen(req,timeout=20) as response:return json.load(response)
if __name__=="__main__":
    result=audit(os.getenv("GITHUB_REPOSITORY",""),
                 os.getenv("GH_READONLY_TOKEN",""),github_json)
    with open("nov01_source_wake_gap_audit.json","w") as fp:
        json.dump(result,fp,indent=2);fp.write("\n")
    print(json.dumps(result))
