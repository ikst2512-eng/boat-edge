from pathlib import Path
from datetime import datetime,timezone,timedelta
import re,json
ROOT=Path('.');BASE=ROOT/'data';NOW=datetime.now(timezone(timedelta(hours=9)))
model=json.loads((BASE/'model_status.json').read_text(encoding='utf8'))
raw_date=str(model.get('target_date') or NOW.strftime('%Y-%m-%d')).replace('-','')
assert re.fullmatch(r'\d{8}',raw_date)
OUT=BASE/'site_scratches_v182';OUT.mkdir(parents=True,exist_ok=True)
PATS=re.compile(r'欠場|出走取消|出走取り消し|不出走|欠航|scratched|withdrawn',re.I)
BANNED_STATUS=re.compile(r'欠場|出走取消|取消|不出走|scratched|withdrawn',re.I)
counts={'total':0,'blocked':0,'incomplete':0,'html_status':0,'field_status':0,'raw_unavailable':0}
for rp in sorted((BASE/'races').glob(f'{raw_date}-??-??.json')):
    d=json.loads(rp.read_text(encoding='utf8'));key=rp.stem
    racers=d.get('racers') or []
    audit=d.get('source_audit') or {}
    status=[];lanes=[];raw_sources=[]
    if len(racers)!=6:
        status.append('出走表の選手が6艇揃っていません');counts['incomplete']+=1
    meta=d.get('meta') or {}
    try:
        due=datetime.fromisoformat(str(meta.get('date'))+'T'+str(meta.get('deadline'))+':00+09:00')
        remain=(due-NOW).total_seconds()/60
    except (TypeError,ValueError):remain=None
    if remain is not None and 0<=remain<=15:
        bf=(audit.get('beforeinfo') or {})
        try: age=(NOW-datetime.fromisoformat(bf['fetched_at'])).total_seconds()/60
        except (TypeError,ValueError,KeyError):age=float('inf')
        if bf.get('status')!='ok' or age>15:
            status.append('締切15分前なのに公式直前情報が未取得・古い：出走可否の確認待ち')
    for row in racers:
        fields=[row.get('status'),row.get('race_status'),row.get('entry_status'),row.get('scratch_status'),row.get('raw_text')]
        flagged=any(row.get(f) is True for f in ['scratched','withdrawn','absent','cancelled','canceled']) or any(BANNED_STATUS.search(v) for v in fields if isinstance(v,str))
        if flagged:lanes.append(row.get('lane'))
    if lanes:status.append('選手行に欠場・取消の明示情報あり');counts['field_status']+=1
    vv,rr=key.split('-')[1:]
    for typ in ['racelist','beforeinfo']:
        if typ=='beforeinfo' and (audit.get('beforeinfo') or {}).get('status')!='ok':continue
        path=BASE/'raw'/raw_date/f'{vv}_{rr}_{typ}.html'
        if not path.exists():continue
        source=path.read_text(encoding='utf8',errors='replace')
        if PATS.search(source):raw_sources.append(typ)
    if raw_sources:status.append('取得済み公式HTMLに欠場・取消の表記あり（艇番未確定の場合はレース全体を保留）');counts['html_status']+=1
    if not (BASE/'raw'/raw_date/f'{vv}_{rr}_racelist.html').exists():counts['raw_unavailable']+=1
    if status:counts['blocked']+=1
    doc={'schema_version':'boat-edge-v182-scratch-evidence-v1','race_key':key,
         'source_date':raw_date,'checked_at':NOW.isoformat(),
         'blocked':bool(status),'reason':' / '.join(status) if status else None,
         'suspect_lanes':lanes,'official_raw_flags':raw_sources,
         'race_card_source_status':(audit.get('race_card') or {}).get('status'),
         'official_beforeinfo_source_status':(audit.get('beforeinfo') or {}).get('status'),
         'limitations':'No scratch signal detected is not certified 6-boat participation; raw collector freshness limits detection.'}
    dest=OUT/f'{key}.json';content=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    # Retain old document when evidence unchanged, avoid meaningless Git churn.
    if dest.exists():
        old=json.loads(dest.read_text(encoding='utf8'))
        if all(old.get(k)==doc.get(k) for k in doc if k!='checked_at'):continue
    dest.write_text(content,encoding='utf8');counts['total']+=1
print('V182_SCRATCH_SCAN '+json.dumps(counts,ensure_ascii=False))
