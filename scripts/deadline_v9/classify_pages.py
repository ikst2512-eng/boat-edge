"""Research-only classification of stored official race-list HTML. Never unlocks formal scoring."""
import argparse, json, re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from verify_artifacts import verify

JST=timezone(timedelta(hours=9))
class TableReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.row=None;self.cell=None;self.depth=0;self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[];self.depth=0
        if self.row is not None and tag in ('td','th'):
            if self.cell is None:self.cell=[];self.depth=1
            else:self.depth+=1
    def handle_data(self,data):
        self.text.append(data)
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.depth-=1
            if self.depth==0:
                self.row.append(' '.join(''.join(self.cell).split()))
                self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row);self.row=None;self.cell=None;self.depth=0

def classify(root,report_file):
    root=Path(root)
    base=verify(root,report_file)
    report=json.loads(Path(report_file).read_text(encoding='utf8'))
    out=[]
    for rec in report['captures']:
        venue=rec['venue_code'];race=rec['race_number_requested'];sha=rec['sha256']
        status='INTEGRITY_UNVERIFIED';deadline=None;changed_notice=False
        if base['status']=='CAPTURE_INTEGRITY_PASS_RESEARCH_ONLY':
            raw=(root/'snapshots'/report['date_jst']/venue/(sha+'.html')).read_bytes()
            parser=TableReader()
            parser.feed(raw.decode('utf-8',errors='replace'))
            page=' '.join(parser.text)
            changed_notice='締切予定時刻が変更' in page
            if 'データがありません' in page:
                status='NO_RACE_DATA'
            else:
                matched=[r for r in parser.rows if any('締切予定時刻' in c for c in r)]
                times=[]
                if len(matched)==1:
                    row=matched[0]
                    times=[c for c in row if re.fullmatch(r'(?:[01]?[0-9]|2[0-3]):[0-5][0-9]',c)]
                if len(times)!=12:
                    status='DEADLINE_PARSE_UNVERIFIED'
                else:
                    clock=times[race-1]
                    deadline=datetime.strptime(report['date_jst']+clock,'%Y%m%d%H:%M').replace(tzinfo=JST)
                    observed=datetime.fromisoformat(rec['capture_finished_at_jst'])
                    status='NOT_PRE_DEADLINE' if observed>=deadline else 'PRE_DEADLINE_CANDIDATE_RESEARCH_ONLY'
        out.append({'venue_code':venue,'race_number':race,'deadline_display_jst':deadline.strftime('%H:%M') if deadline else None,'status':status,'deadline_change_notice':changed_notice,'formal_eligible':False})
    return {'schema':'V13_RESEARCH_ONLY','capture_integrity':base['status'],'classifications':out,
            'counts':{k:sum(x['status']==k for x in out) for k in sorted(set(x['status'] for x in out))},
            'formal_eligible':False,'results_seen':False,'scoring':'NOT_RUN','unlock':'LOCKED'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--report',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    result=classify(a.root,a.report)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result['counts'],ensure_ascii=False))
    if result['capture_integrity']!='CAPTURE_INTEGRITY_PASS_RESEARCH_ONLY':raise SystemExit(2)
