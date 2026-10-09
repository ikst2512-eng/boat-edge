"""Fail closed in FINAL_15M if the on-site scratch scan is stale or absent."""
from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf8')
marker='BOAT_EDGE_V186_SCRATCH_FRESHNESS_FAIL_CLOSED'
if marker not in s:
    source='''    if(Number.isFinite(mins)&&mins>=0&&mins<=15){
      const source=d?.source_audit?.beforeinfo;'''
    replace='''    if(Number.isFinite(mins)&&mins>=0&&mins<=15){
      /* BOAT_EDGE_V186_SCRATCH_FRESHNESS_FAIL_CLOSED */
      const verifiedAt=Date.parse(String(audit?.checked_at||''));
      const age=Date.now()-verifiedAt;
      if(audit?.race_key!==d?.race_key||audit?.blocked!==false||
         !Number.isFinite(verifiedAt)||age< -60000||age>16*60000)
        return '欠場・取消の公式出走確認が未取得または古いため、買い目停止';
      const source=d?.source_audit?.beforeinfo;'''
    assert s.count(source)==1,'V186_SITE_SCRATCH_CONTEXT_MISSING'
    s=s.replace(source,replace,1)
    p.write_text(s,encoding='utf8')
else:
    assert s.count(marker)==1,'V186_MARKER_DUPLICATED'
print('V186_STALE_SCRATCH_UI_HOLD_PASS')
