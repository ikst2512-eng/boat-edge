"""V186 - Revivify near-deadline V182 scratch verification, no predictions/results.

The V182 scanner intentionally writes only when evidence changes; this leaves
checked_at stale and makes V185's <=16m data eligibility fail. This refreshes
verification timestamps only when a newly executed V182 scan has just run.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json, re

JST=timezone(timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')

def utc(v):
    try:
        d=datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError,ValueError):return None

def refresh(root:Path, now:datetime):
    now=now.astimezone(JST)
    today=now.strftime('%Y%m%d')
    root=Path(root)
    count={'eligible_window':0,'refreshed':0,'held_stale_card':0,'held_stale_beforeinfo':0,
           'scan_missing':0,'existing_blocked':0,'not_due':0}
    for rp in sorted((root/'data/races').glob(f'{today}-??-??.json')):
        key=rp.stem
        if not KEY.fullmatch(key):continue
        try:race=json.loads(rp.read_text(encoding='utf8'))
        except (OSError,ValueError,UnicodeError):continue
        meta=race.get('meta') or {}
        deadline=utc(str(meta.get('date'))+'T'+str(meta.get('deadline'))+':00+09:00')
        if deadline is None:
            count['not_due']+=1;continue
        mins=(deadline-now.astimezone(timezone.utc)).total_seconds()/60
        if not (0<=mins<=26):
            count['not_due']+=1;continue
        count['eligible_window']+=1
        src=root/'data/site_scratches_v182'/f'{key}.json'
        if not src.is_file():
            count['scan_missing']+=1
            # NEVER generate a green verification document in absence of V182 scan.
            continue
        try:doc=json.loads(src.read_text(encoding='utf8'))
        except (OSError,ValueError,UnicodeError):count['scan_missing']+=1;continue
        if doc.get('race_key')!=key or doc.get('source_date')!=today:
            count['scan_missing']+=1;continue
        audit=race.get('source_audit') or {}
        card=audit.get('race_card') or {}
        card_time=utc(card.get('fetched_at'))
        if card.get('status')!='ok' or not card_time or (now-card_time).total_seconds()>16*60 or card_time>now+timedelta(minutes=1):
            doc['blocked']=True
            reason='公式出走表の取得が未確認または16分以上古い'
            if reason not in str(doc.get('reason') or ''):doc['reason']=' / '.join(x for x in [doc.get('reason'),reason] if x)
            count['held_stale_card']+=1
        if mins<=15:
            before=audit.get('beforeinfo') or {}
            bt=utc(before.get('fetched_at'))
            if before.get('status')!='ok' or not bt or (now-bt).total_seconds()>15*60 or bt>now+timedelta(minutes=1):
                doc['blocked']=True
                reason='締切15分前の公式直前情報が未確認または15分以上古い'
                if reason not in str(doc.get('reason') or ''):doc['reason']=' / '.join(x for x in [doc.get('reason'),reason] if x)
                count['held_stale_beforeinfo']+=1
        if doc.get('blocked') is True:count['existing_blocked']+=1
        doc['checked_at']=now.isoformat()
        content=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
        if not src.exists() or src.read_text(encoding='utf8')!=content:
            src.write_text(content,encoding='utf8');count['refreshed']+=1
    return count

if __name__=='__main__':
    from argparse import ArgumentParser
    p=ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));a=p.parse_args()
    print('V186_FRESH_SCRATCH '+json.dumps(refresh(a.repo,datetime.now(timezone.utc)),ensure_ascii=False,sort_keys=True))
