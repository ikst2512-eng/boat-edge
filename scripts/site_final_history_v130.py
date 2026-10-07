
from __future__ import annotations
import json, math, hashlib, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path(".")
JST=timezone(timedelta(hours=9))
NOW=datetime.now(timezone.utc)
TODAY=(NOW.astimezone(JST)).strftime("%Y%m%d")
RACES=ROOT/"data/races"
ODDS=ROOT/"data/site_odds"
RESULTS=ROOT/"data/site_results"
COURSE=ROOT/"data/site_course_stats"
SNAPS=ROOT/"data/site_prediction_snapshots"
HIST=ROOT/"data/site_prediction_history"
FORMAL_DIRS=[ROOT/"data/formal_predictions",ROOT/"data/formal"]
SNAPS.mkdir(parents=True,exist_ok=True)
HIST.mkdir(parents=True,exist_ok=True)

def read_json(p:Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def write_if_changed(p:Path,obj):
    text=json.dumps(obj,ensure_ascii=False,indent=2)
    old=p.read_text(encoding="utf-8") if p.exists() else None
    if old==text:
        return False
    p.write_text(text,encoding="utf-8")
    return True

def sha256_file(p:Path):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception:
        return None

def num(v):
    if v is None or (isinstance(v,str) and not v.strip()):
        return None
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def lane_no(r,i):
    try:return int(r.get("lane") or (i+1))
    except:return i+1

def normalize_combo(v):
    if isinstance(v,list):
        return "-".join(str(x) for x in v[:3])
    s=str(v or "")
    m=re.search(r"([1-6])\D+([1-6])\D+([1-6])",s)
    return "-".join(m.groups()) if m else None

def get_before_maps(d):
    bf=d.get("beforeinfo") or {}
    starts={}
    for i,x in enumerate(bf.get("start_exhibition") or []):
        lane=int(x.get("lane") or i+1)
        starts[lane]=num(x.get("st"))
    racers={}
    for i,x in enumerate(bf.get("racers") or []):
        lane=int(x.get("lane") or i+1)
        racers[lane]=x
    actual={}
    for i,x in enumerate(d.get("actual_entry") or []):
        lane=int(x.get("lane") or i+1)
        c=x.get("course",x.get("actual_course",x.get("entry_course")))
        try:c=int(c)
        except:continue
        actual[lane]=c
    return bf,starts,racers,actual

def normalize_exhibition(rows):
    vals=[num(x.get("exhibition_time")) for x in rows]
    vals=[x for x in vals if x is not None]
    if not vals:return {}
    lo,hi=min(vals),max(vals)
    rng=max(hi-lo,.01)
    out={}
    for x in rows:
        t=num(x.get("exhibition_time"))
        lane=x.get("lane")
        if t is not None and lane is not None:
            out[int(lane)]=max(0,1-((t-lo)/rng))
    return out

def compute_scores(d):
    bf,starts,bf_racers,actual=get_before_maps(d)
    ex_norm=normalize_exhibition(bf.get("racers") or [])
    out=[]
    for i,r in enumerate(d.get("racers") or []):
        lane=lane_no(r,i)
        nat=r.get("national") or {}
        loc=r.get("local") or {}
        mot=r.get("motor") or {}
        boat=r.get("boat") or {}
        avg_st=num(r.get("avg_st"))
        nat_win=num(nat.get("win_rate")) or 0
        nat_q=num(nat.get("quinella_rate")) or 0
        loc_win=num(loc.get("win_rate")) or 0
        loc_q=num(loc.get("quinella_rate")) or 0
        mot_q=num(mot.get("quinella_rate")) or 0
        boat_q=num(boat.get("quinella_rate")) or 0
        before=bf_racers.get(lane) or {}
        ex_score=(ex_norm.get(lane,0))*8 if lane in ex_norm else 0
        st_ex=starts.get(lane)
        ex_start_score=0 if st_ex is None else max(0,(.25-st_ex)*28)
        avg_st_score=0 if avg_st is None else max(0,(.24-avg_st)*42)
        lane_base={1:9.5,2:7.0,3:5.8,4:5.2,5:3.2,6:2.2}.get(lane,0)
        tilt=num(before.get("tilt"))
        tilt_score=0 if tilt is None else max(-1,min(2.5,tilt))
        actual_course=actual.get(lane)
        attack_base=0 if actual_course is None else {1:.5,2:5.4,3:6.2,4:6.8,5:4.0,6:3.0}.get(actual_course,0)
        inside_base=8 if lane==1 else (0 if actual_course is None else max(0,5-abs(actual_course-2)))
        machine=mot_q*.11+boat_q*.07
        klass=str(r.get("class") or "")
        class_bonus=2.4 if "A1" in klass else 1.4 if "A2" in klass else .5 if "B1" in klass else 0
        base=nat_win*2.8+nat_q*.18+loc_win*1.9+loc_q*.12+machine+avg_st_score+ex_score+ex_start_score+lane_base+class_bonus+tilt_score
        out.append({
            "lane":lane,"actualCourse":actual_course,"baseScore":base,
            "insideScore":base+inside_base+(6 if lane==1 else 0),
            "attackScore":base+attack_base+(2.5 if actual_course in (3,4) else 0)
        })
    return sorted(out,key=lambda x:x["lane"])

def grade_from_spread(x):
    return "A" if x>=9 else "B+" if x>=6 else "B" if x>=4 else "C+" if x>=2.5 else "C"

def top_unique(rows,n):
    out=[];seen=set()
    for x in rows:
        if x["combo"] in seen:continue
        seen.add(x["combo"]);out.append(x)
        if len(out)>=n:break
    return out

def build_fallback(d):
    scores=compute_scores(d)
    if not scores:return None
    one=next((x for x in scores if x["lane"]==1),scores[0])
    challengers=sorted([x for x in scores if x["lane"]!=1],key=lambda x:x["attackScore"],reverse=True)
    supporters=sorted(scores,key=lambda x:x["baseScore"],reverse=True)
    strongest=challengers[0] if challengers else (supporters[1] if len(supporters)>1 else one)
    diff=one["insideScore"]-strongest["attackScore"]
    pa=max(35,min(78,55+diff*2.2)); pb=100-pa

    ac=[]
    seconds=[x for x in supporters if x["lane"]!=1]
    for i,s in enumerate(seconds):
        for j,t in enumerate(seconds):
            if i==j:continue
            w=one["insideScore"]*1.2+s["baseScore"]+t["baseScore"]+(.5 if s["lane"]<t["lane"] else 0)
            ac.append({"combo":f'1-{s["lane"]}-{t["lane"]}',"weight":w})
    atop=top_unique(sorted(ac,key=lambda x:x["weight"],reverse=True),5)
    asum=sum(x["weight"] for x in atop) or 1
    at=[{"rank":i+1,"combo":x["combo"],"probability":x["weight"]/asum*pa} for i,x in enumerate(atop)]

    bc=[]
    for h in challengers[:3]:
        others=[x for x in supporters if x["lane"]!=h["lane"]]
        pref=next((x for x in others if x["lane"]==1),None)
        rest=[x for x in others if x["lane"]!=1]
        for s in others[:5]:
            for t in others[:5]:
                if t["lane"]==s["lane"]:continue
                prefer_in=(1.2 if s["lane"]==1 else 0)+(.8 if t["lane"]==1 else 0)
                w=h["attackScore"]*1.25+s["baseScore"]+t["baseScore"]+prefer_in+(1.5 if (h["actualCourse"] or 0)>=3 else 0)
                bc.append({"combo":f'{h["lane"]}-{s["lane"]}-{t["lane"]}',"weight":w})
        if pref:
            for r in rest[:3]:
                bc.append({"combo":f'{h["lane"]}-1-{r["lane"]}',"weight":h["attackScore"]*1.35+pref["baseScore"]+r["baseScore"]+3})
                bc.append({"combo":f'{h["lane"]}-{r["lane"]}-1',"weight":h["attackScore"]*1.2+pref["baseScore"]+r["baseScore"]+2.2})
    btop=top_unique(sorted(bc,key=lambda x:x["weight"],reverse=True),5)
    bsum=sum(x["weight"] for x in btop) or 1
    bt=[{"rank":i+1,"combo":x["combo"],"probability":x["weight"]/bsum*pb} for i,x in enumerate(btop)]
    return {"mode":"temp","grade":grade_from_spread(abs(diff)),"worlds":[
        {"key":"A","probability":pa,"tickets":at},
        {"key":"B","probability":pb,"tickets":bt}
    ]}

def normalize_formal(raw):
    if not isinstance(raw,dict):return None
    if raw.get("derived"):
        return {"derived":raw["derived"],"formal_meta":raw.get("formal_meta") or raw.get("meta")}
    pred=raw.get("prediction") or {}
    if pred.get("derived"):
        return {"derived":pred["derived"],"formal_meta":raw.get("meta")}
    wa=raw.get("world_a") or raw.get("pattern_a") or pred.get("world_a") or pred.get("pattern_a")
    wb=raw.get("world_b") or raw.get("pattern_b") or pred.get("world_b") or pred.get("pattern_b")
    if wa or wb:
        return {"derived":{
            "world_a":wa,"world_b":wb,
            "decision":raw.get("decision") or pred.get("decision"),
            "confidence_grade":raw.get("confidence_grade") or raw.get("grade") or pred.get("confidence_grade"),
            "model":raw.get("model") or pred.get("model")
        },"formal_meta":raw.get("meta")}
    return None

def merge_formal(race,key):
    for base in FORMAL_DIRS:
        raw=read_json(base/f"{key}.json")
        norm=normalize_formal(raw)
        if norm:
            x=dict(race);x["derived"]=norm["derived"];x["formal_meta"]=norm.get("formal_meta")
            return x
    return race

def has_formal(d):
    der=d.get("derived") or {}
    worlds=[der.get(k) for k in ("world_a","world_b","pattern_a","pattern_b") if der.get(k)]
    ready=False
    for w in worlds:
        if (w.get("tickets") or w.get("bets") or w.get("combinations")):
            ready=True;break
    g=(d.get("formal_meta") or {}).get("guards") or der.get("guards")
    guard_ok=True if not g else (g.get("results_seen") is False and g.get("scoring") is not True)
    return ready and guard_ok

def formal_pred(d):
    der=d.get("derived") or {}
    wa=der.get("world_a") or der.get("pattern_a")
    wb=der.get("world_b") or der.get("pattern_b")
    def rows(w,key):
        out=[]
        for i,b in enumerate((w or {}).get("tickets") or (w or {}).get("bets") or (w or {}).get("combinations") or []):
            if isinstance(b,str):
                combo=b;p=None
            else:
                combo=b.get("combo") or b.get("ticket") or b.get("bet")
                p=b.get("confidence",b.get("probability",b.get("p")))
            out.append({"rank":i+1,"combo":combo,"probability":p})
        return out
    pa=num((wa or {}).get("probability",(wa or {}).get("prob",(wa or {}).get("rate"))))
    pb=num((wb or {}).get("probability",(wb or {}).get("prob",(wb or {}).get("rate"))))
    return {"mode":"formal","grade":der.get("confidence_grade") or "A","worlds":[
        {"key":"A","probability":pa,"tickets":rows(wa,"A")},
        {"key":"B","probability":pb,"tickets":rows(wb,"B")}
    ]}

def all_tickets(pred):
    out=[];seen=set()
    for wi,w in enumerate(pred.get("worlds") or []):
        key=w.get("key") or ("A" if wi==0 else "B")
        for i,t in enumerate(w.get("tickets") or []):
            combo=normalize_combo(t.get("combo") or t.get("trifecta") or t.get("order"))
            if not combo or combo in seen:continue
            seen.add(combo)
            raw=num(t.get("probability",t.get("confidence",t.get("prob",t.get("p")))))
            p=0 if raw is None else (raw*100 if raw<=1 else raw)
            out.append({"combo":combo,"p":p,"world":key,"rank":i+1})
    return sorted(out,key=lambda x:x["p"],reverse=True)

def mean(vals):
    vals=[float(x) for x in vals if x is not None and math.isfinite(float(x))]
    return sum(vals)/len(vals) if vals else None

def clamp(v,a,b):return max(a,min(b,v))

def scenario_adjust(race,pred):
    allrows=all_tickets(pred)
    if pred.get("mode")=="formal":
        return {"tickets":allrows,"used":["正式CURRENT"],"applied":False}
    key=race.get("race_key") or ""
    jcd=str((race.get("meta") or {}).get("venue_code") or (key.split("-")[1] if "-" in key else "")).zfill(2)
    stats=read_json(COURSE/f"{jcd}.json") or {}
    actual={}
    for x in race.get("actual_entry") or []:
        try:
            lane=int(x.get("lane")); course=int(x.get("course",x.get("actual_course",x.get("entry_course"))))
            if 1<=lane<=6 and 1<=course<=6:actual[lane]=course
        except:pass
    use_actual=len(actual)==6

    exst={}
    for x in race.get("actual_entry") or []:
        try:
            lane=int(x.get("lane")); v=num(x.get("exhibition_st"))
            if v is not None:exst[lane]=v
        except:pass
    for x in (race.get("beforeinfo") or {}).get("start_exhibition") or []:
        try:
            lane=int(x.get("lane")); v=num(x.get("st"))
            if v is not None and lane not in exst:exst[lane]=v
        except:pass

    extime={}
    for x in (race.get("beforeinfo") or {}).get("racers") or []:
        try:
            lane=int(x.get("lane")); v=num(x.get("exhibition_time"))
            if v is not None:extime[lane]=v
        except:pass

    labels=[str(x or "") for x in ((race.get("original_exhibition") or {}).get("labels") or [])]
    orig={}
    for b in (race.get("original_exhibition") or {}).get("boats") or []:
        try:lane=int(b.get("lane"))
        except:continue
        row={}
        for i,v in enumerate(b.get("values") or []):
            x=num(v)
            if x is not None:row[labels[i] if i<len(labels) else f"metric_{i}"]=x
        orig[lane]=row

    racers={lane_no(r,i):r for i,r in enumerate(race.get("racers") or [])}
    avg_st_mean=mean([num(r.get("avg_st")) for r in racers.values()])
    ex_st_mean=mean(list(exst.values()))
    ex_time_vals=list(extime.values())
    ex_time_mean=mean(ex_time_vals)
    ex_time_range=(max(ex_time_vals)-min(ex_time_vals)) if len(ex_time_vals)>=2 else 0

    orig_scores={}
    for lab in labels:
        vals=[(lane,num(row.get(lab))) for lane,row in orig.items()]
        vals=[x for x in vals if x[1] is not None]
        if len(vals)<2:continue
        lo=min(v for _,v in vals); hi=max(v for _,v in vals); rng=max(hi-lo,.001)
        for lane,v in vals:
            orig_scores.setdefault(lane,[]).append(1-((v-lo)/rng))

    courses=(stats.get("courses") or {})
    course_to_lane={}
    for lane in range(1,7):
        course_to_lane[actual[lane] if use_actual else lane]=lane

    used=[]
    if courses:used.append("当地3か月コース")
    if use_actual:used.append("実進入")
    if len(exst)>=4:used.append("展示ST")
    if len(extime)>=4:used.append("展示タイム")
    if len(orig)>=4:used.append("オリ展")

    def method_fit(c,course):
        if not c:return None
        if course==1:return num(c.get("escape"))
        if course==2:return max(num(c.get("sashi")) or 0,num(c.get("makuri")) or 0)
        if course in (3,4):return max(num(c.get("makuri")) or 0,num(c.get("makuri_sashi")) or 0)
        return num(c.get("makuri_sashi"))

    def lane_factor(lane):
        r=racers.get(lane) or {}
        course=actual.get(lane) if use_actual else lane
        c=courses.get(str(course)) or {}
        f=1.0
        first=num(c.get("first_rate"))
        if first is not None:
            rs=[num(x.get("first_rate")) for x in courses.values()]
            m=mean(rs)
            if m is not None:f*=1+clamp(((first-m)/100)*.45,-.10,.18)
        fit=method_fit(c,course)
        if fit is not None:
            f*=1+clamp(((fit/100)-.45)*.15,-.05,.08)
            if course==4 and max(num(c.get("makuri")) or 0,num(c.get("makuri_sashi")) or 0)>=50:f*=1.035
        ast=num(r.get("avg_st"))
        if ast is not None and avg_st_mean is not None:f*=1+clamp((avg_st_mean-ast)*.90,-.06,.06)
        est=exst.get(lane)
        if est is not None and ex_st_mean is not None:
            f*=1+clamp((ex_st_mean-est)*.65,-.08,.08)
            neigh=[]
            for cc in (course-1,course+1):
                other=course_to_lane.get(cc)
                if other in exst:neigh.append(exst[other])
            nm=mean(neigh)
            if nm is not None:f*=1+clamp((nm-est)*.45,-.04,.05)
        et=extime.get(lane)
        if et is not None and ex_time_mean is not None and ex_time_range>.001:
            f*=1+clamp(((ex_time_mean-et)/ex_time_range)*.07,-.05,.07)
        os=orig_scores.get(lane) or []
        om=mean(os)
        if om is not None:f*=1+clamp((om-.5)*.12,-.06,.06)
        return clamp(f,.78,1.30)

    enriched=[]
    for x in allrows:
        p=[int(z) for z in x["combo"].split("-")]
        factor=(lane_factor(p[0])**.70)*(lane_factor(p[1])**.19)*(lane_factor(p[2])**.11)
        y=dict(x);y["raw"]=max(.001,x["p"])*factor
        enriched.append(y)
    old_sum=sum(x["p"] for x in allrows) or 100
    raw_sum=sum(x["raw"] for x in enriched) or 1
    for x in enriched:x["p"]=x["raw"]/raw_sum*old_sum
    enriched.sort(key=lambda x:x["p"],reverse=True)
    return {"tickets":enriched,"used":used,"applied":True}

def modes_from_tickets(allrows,odds):
    def od(x):
        v=num(odds.get(x["combo"]))
        return v if v is not None and v>0 else None
    primary=(allrows[0]["combo"].split("-")[0] if allrows else None)
    alt=[x for x in allrows if x["combo"].split("-")[0]!=primary] if primary else []
    primary_rows=[x for x in allrows if x["combo"].split("-")[0]==primary] if primary else list(allrows)
    alt_heads={x["combo"].split("-")[0] for x in alt}
    total=sum(float(x.get("p") or 0) for x in allrows) or 1
    alt_share=sum(float(x.get("p") or 0) for x in alt)/total
    target=10 if len(alt_heads)>=2 or alt_share>=.38 else 8
    wave=[];seen=set()
    for x in alt+primary_rows:
        if x["combo"] in seen:continue
        seen.add(x["combo"]);wave.append(x)
        if len(wave)>=min(target,len(allrows)):break
    modes={
        "hit":allrows[:10],
        "balance":allrows[:6],
        "hole":wave,
        "narrow":allrows[:3]
    }
    return {k:[dict(x,odds=od(x)) for x in v] for k,v in modes.items()}

def confidence(pred,mode,rows):
    mp={"S":90,"S+":93,"A":82,"A+":86,"B":72,"B+":76,"C":62,"D":52}
    base=mp.get(str(pred.get("grade") or "").upper(),68)
    a=all_tickets(pred); total=sum(x["p"] for x in a); top=sum(x["p"] for x in a[:3])
    base+=round(((top/total if total else 0)-.35)*18)+{"hit":5,"balance":0,"hole":-5,"narrow":-5}.get(mode,0)
    if len(rows)<=3:base-=2
    return max(35,min(94,round(base)))

changed=0;snapshots=0;settled=0
for race_path in sorted(RACES.glob(f"{TODAY}-*.json")):
    race=read_json(race_path)
    if not race:continue
    key=race.get("race_key") or race_path.stem
    meta=race.get("meta") or {}
    if meta.get("results_seen") is True or meta.get("unlock") is True or meta.get("scoring") is True:
        continue
    result=read_json(RESULTS/f"{key}.json")
    if result and result.get("status")=="confirmed":
        continue
    date=str(meta.get("date") or "")
    deadline=str(meta.get("deadline") or "")
    try:
        dl=datetime.fromisoformat(f"{date}T{deadline}:00+09:00").astimezone(timezone.utc)
    except Exception:
        continue
    mins=(dl-NOW).total_seconds()/60
    if not (0<=mins<=15.999):
        continue

    race=merge_formal(race,key)
    pred=formal_pred(race) if has_formal(race) else build_fallback(race)
    if not pred:continue
    adjusted=scenario_adjust(race,pred)

    odds_doc=read_json(ODDS/f"{key}.json") or {}
    odds=odds_doc.get("trifecta_odds") or {}
    modes=modes_from_tickets(adjusted["tickets"],odds)
    old=read_json(SNAPS/f"{key}.json") or {}
    policy="FORMAL_CURRENT" if pred.get("mode")=="formal" else "V122_SCENARIO_AWARE_PROBABILITY_FIRST"
    snap={
        "schema_version":"boat-edge-server-site-final-v123",
        "snapshot_window":"FINAL_15M",
        "race_key":key,
        "prediction_kind":"FORMAL_CURRENT" if pred.get("mode")=="formal" else "SITE_REFERENCE_V122",
        "selection_policy":policy,
        "mode_policy":"ADAPTIVE_WAVE_8_10",
        "used_inputs":adjusted.get("used") or [],
        "first_saved_at":old.get("first_saved_at") or datetime.now(timezone.utc).isoformat(),
        "saved_at":datetime.now(timezone.utc).isoformat(),
        "minutes_to_deadline":round(mins,2),
        "venue":meta.get("venue") or "",
        "venue_code":meta.get("venue_code") or key.split("-")[1],
        "race_no":meta.get("race_no") or int(key.split("-")[2]),
        "deadline":meta.get("deadline"),
        "grade":pred.get("grade"),
        "race_sha256":sha256_file(race_path),
        "odds_sha256":sha256_file(ODDS/f"{key}.json"),
        "guards":{"results_seen":False,"unlock":False,"scoring":False},
        "modes":{
            k:{
                "confidence":confidence(pred,k,rows),
                "tickets":[{"combo":x["combo"],"p":x["p"],"odds":x.get("odds")} for x in rows]
            } for k,rows in modes.items()
        }
    }
    if write_if_changed(SNAPS/f"{key}.json",snap):
        changed+=1;snapshots+=1

for sp in sorted(SNAPS.glob("????????-??-??.json")):
    snap=read_json(sp)
    if not snap:continue
    key=sp.stem
    result=read_json(RESULTS/f"{key}.json")
    if not result or result.get("status")!="confirmed":continue
    win=normalize_combo(result.get("trifecta") or result.get("finish_order"))
    if not win:continue
    hp=HIST/f"{key}.json"
    prev=read_json(hp) or {}
    mode_hits={k:any(x.get("combo")==win for x in (v.get("tickets") or [])) for k,v in (snap.get("modes") or {}).items()}
    settlement={
        "settled_at":((prev.get("settlement") or {}).get("settled_at") or datetime.now(timezone.utc).isoformat()),
        "winning_combo":win,
        "payout":result.get("trifecta_payout_yen_per_100"),
        "mode_hits":mode_hits,
        "hit_any":any(mode_hits.values())
    }
    payload={"schema_version":"boat-edge-server-site-history-v123","race_key":key,"snapshot":snap,"settlement":settlement}
    if write_if_changed(hp,payload):
        changed+=1;settled+=1

races={}
for hp in sorted(HIST.glob("????????-??-??.json")):
    d=read_json(hp)
    if not d:continue
    s=d.get("snapshot") or {};t=d.get("settlement") or {}
    races[d["race_key"]]={
        "race_key":d["race_key"],"venue":s.get("venue",""),"venue_code":s.get("venue_code",""),
        "race_no":s.get("race_no"),"deadline":s.get("deadline"),"final_saved_at":s.get("saved_at"),
        "prediction_kind":s.get("prediction_kind"),"selection_policy":s.get("selection_policy"),
        "used_inputs":s.get("used_inputs") or [],
        "winning_combo":t.get("winning_combo"),"payout":t.get("payout"),
        "mode_hits":t.get("mode_hits") or {},"hit_any":bool(t.get("hit_any")),
        "settled_at":t.get("settled_at")
    }

index_path=HIST/"index.json"
old_idx=read_json(index_path) or {}
base={
    "schema_version":"boat-edge-server-site-history-index-v123",
    "start_date":old_idx.get("start_date") or TODAY,
    "note":"Prospective PRE_RESULT FINAL_15M only. No retrospective prediction backfill.",
    "selection_policy":"MATCH_CURRENT_UI_V130_OR_FORMAL_CURRENT",
    "races":races
}
old_cmp=dict(old_idx);old_cmp.pop("updated_at",None)
idx=dict(base)
idx["updated_at"]=(datetime.now(timezone.utc).isoformat() if old_cmp!=base else old_idx.get("updated_at") or datetime.now(timezone.utc).isoformat())
if write_if_changed(index_path,idx):changed+=1

print(json.dumps({
    "today":TODAY,"snapshots_updated":snapshots,"histories_updated":settled,
    "history_count":len(races),"files_changed":changed,
    "selection_policy":"MATCH_CURRENT_UI_V130_OR_FORMAL_CURRENT"
},ensure_ascii=False))
