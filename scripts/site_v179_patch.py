#!/usr/bin/env python3
"""V179 UI percentage normalization and formal-readiness audit; NO prediction scoring."""
from pathlib import Path
from datetime import datetime,timezone
import json

ROOT=Path('.')
PAGE=ROOT/'index.html'
OUT=ROOT/'data/site_learning/v179_formal_readiness.json'

def require_replace(source,old,new,label):
    if source.count(old)==1:
        return source.replace(old,new,1)
    if old not in source and source.count(new)==1:
        return source
    raise RuntimeError('V179_PATCH_UNEXPECTED '+label+' old='+str(source.count(old))+' new='+str(source.count(new)))

def replace_exact_count(source,old,new,count,label):
    if source.count(old)==count:
        return source.replace(old,new)
    if old not in source and source.count(new)>=count:
        return source
    raise RuntimeError('V179_PATCH_UNEXPECTED '+label+' old='+str(source.count(old))+' new='+str(source.count(new)))

def patch_index(source):
    orig='''  const pA = num(wa?.probability ?? wa?.prob ?? wa?.rate);
  const pB = num(wb?.probability ?? wb?.prob ?? wb?.rate);'''
    norm='''  // V179: internal UI uses percentage units (e.g. 58 means 58%).
  // Formal producer may send either normalized [0,1] or [0,100].
  const pAraw = num(wa?.probability ?? wa?.prob ?? wa?.rate);
  const pBraw = num(wb?.probability ?? wb?.prob ?? wb?.rate);
  const worldSum = pAraw!==null && pBraw!==null ? pAraw+pBraw : null;
  const pA = worldSum!==null && worldSum>0 ? pAraw*100/worldSum : null;
  const pB = worldSum!==null && worldSum>0 ? pBraw*100/worldSum : null;'''
    source=require_replace(source,orig,norm,'WORLD_NORMALIZATION')
    # Verified V178 ranks are the probability authority, not self-reported per-ticket confidence.
    source=require_replace(source,
        '  const grade = der.selectivity?.grade || der.confidence_grade || "A";\n  const mapTickets = (world, budget) => {',
        '  const grade = der.selectivity?.grade || der.confidence_grade || "A";\n  const verifiedTicketPercent = new Map((der.ranked_120||[]).map(x=>[x.combo,Number(x.probability)*100]));\n  const mapTickets = (world, budget) => {',
        'TRIFECTA_PROB_AUTHORITY')
    source=require_replace(source,
        'if(typeof b === "string") return {rank:i+1, combo:b, probability:null, amount:null};',
        'if(typeof b === "string") return {rank:i+1, combo:b, probability:verifiedTicketPercent.get(b)??null, amount:null};',
        'FORMAL_STRING_TICKET')
    source=require_replace(source,
        '        probability:b.confidence ?? b.probability ?? b.p ?? null,',
        '        probability:verifiedTicketPercent.get(b.combo || b.ticket || b.bet) ?? null,',
        'FORMAL_TICKET_PROB')
    source=require_replace(source,
        '''    if(!known){
      const amounts = allocateByWeights(items.map(x=>num(x.probability) || 1), budget);
      items.forEach((x,i)=>x.amount=amounts[i]);
    }''',
        '''    // V178 requires producer-frozen 10,000-yen stakes. Never create fictitious formal stakes.
    if(known!==items.length)return [];''',
        'NO_FORMAL_STAKE_IMPUTATION')
    fixes=[
        ('Math.round(Number(a)*100)+"%"','Math.round(Number(a))+"%"',1,'MAST_A'),
        ('Math.round(Number(b)*100)+"%"','Math.round(Number(b))+"%"',1,'MAST_B'),
        ('Math.round(Number(w.probability)*100)+"%"','Math.round(Number(w.probability))+"%"',1,'BUY_WORLD'),
        ('Math.round(Number(A.probability)*100)+"%"','Math.round(Number(A.probability))+"%"',1,'DIRECT_WORLD_A'),
        ('Math.round(Number(B.probability)*100)+"%"','Math.round(Number(B.probability))+"%"',1,'DIRECT_WORLD_B'),
        ('Math.round(Number(t.probability)*1000)/10+"%"','Math.round(Number(t.probability)*10)/10+"%"',3,'TICKET_PROB')
    ]
    for old,new,n,label in fixes:source=replace_exact_count(source,old,new,n,label)
    return source

def read(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None

def audit(root=ROOT):
    status=read(root/'data/formal_status.json') or {}
    model=read(root/'data/model_status.json') or {}
    bridge=read(root/'data/site_latest_bridge_contract.json') or {}
    raw=root/'data/raw'/str(status.get('target_date','')).replace('-','')
    raw_names=[p.name for p in raw.iterdir() if p.is_file()] if raw.exists() else []
    approved_dir=root/'data/formal_predictions'
    approved_count=sum(1 for _ in approved_dir.glob('*.json')) if approved_dir.is_dir() else 0
    guards=status.get('guards') or {}
    core=(model.get('core7') or {})
    formal=(status.get('formalFirst100') or {})
    pre_guard=(guards.get('results_seen') is False and guards.get('unlock') is False and guards.get('scoring') is False and guards.get('RESULT_UNLOCK_TOKEN') is None)
    same_target=model.get('target_date')==status.get('target_date')
    parent_same=(model.get('formal_parent_sha256')==status.get('formalParentSha'))
    formal_frozen=bool(formal.get('races')==100 and formal.get('freezeManifestSha') and formal.get('coreSha'))
    pre_cohort_ok=bool(pre_guard and same_target and parent_same and core.get('core7_100_ready') is True)
    complete=bool(pre_cohort_ok and formal_frozen and status.get('connected') is True and status.get('predictions_ready') is True and approved_count>0)
    blockers=[]
    if not pre_guard:blockers.append('FORMAL_PRE_RESULT_GUARD_NOT_VERIFIED')
    if not same_target:blockers.append('MODEL_AND_FORMAL_TARGET_DATE_MISMATCH')
    if not parent_same:blockers.append('FORMAL_PARENT_SHA_MISMATCH')
    if core.get('core7_100_ready') is not True:blockers.append('SITE_COLLECTOR_CORE7_BELOW_100')
    if not formal_frozen:blockers.append('FORMAL_FRESH100_FREEZE_MISSING')
    if status.get('connected') is not True or status.get('predictions_ready') is not True:blockers.append('APPROVED_FORMAL_MODEL_NOT_CONNECTED')
    if approved_count==0:blockers.append('NO_PER_RACE_APPROVED_PREDICTION_FILES')
    if not bridge:blockers.append('V177_BRIDGE_CONTRACT_UNAVAILABLE')
    return {
      'schema_version':'boat-edge-v179-formal-readiness-display-audit-v1',
      'scope':'SITE_CONSUMER_AND_PRE_RESULT_STATUS_ONLY_NO_FORMAL_GATE_RUN',
      'target_date':status.get('target_date'),
      'site_model_id':model.get('model'),
      'site_policy_version':(read(root/'data/site_current_state.json') or {}).get('latest_prediction_policy',{}).get('version'),
      'site_core7_eligible':core.get('eligible_count'),
      'site_core7_ready':core.get('core7_100_ready') is True,
      'formal_first100_races':formal.get('races',0),
      'formal_freeze_ready':formal_frozen,
      'formal_approved_prediction_files':approved_count,
      'raw_official_racelist_files':sum(x.endswith('_racelist.html') for x in raw_names),
      'raw_official_beforeinfo_files':sum(x.endswith('_beforeinfo.html') for x in raw_names),
      'model_target_matches_formal':same_target,
      'parent_sha_matches':parent_same,
      'pre_result_guards_pass':pre_guard,
      'site_consumer_ready_to_display_actual_formal_predictions':complete,
      'blockers':blockers,
      'production_prediction_weights_changed':False,
      'formal_current_scoring':False,
      'formal_current_gate_executed':False,
      'note':'Site CORE7=100 is NOT formal Fresh100 freeze; never unlock or fetch result/odds to solve formal readiness. Site reference predictions remain separate.'
    }

def main():
    orig=PAGE.read_text(encoding='utf-8');new=patch_index(orig)
    if new!=orig:PAGE.write_text(new,encoding='utf-8')
    data=audit();OUT.parent.mkdir(parents=True,exist_ok=True)
    blob=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=blob:OUT.write_text(blob,encoding='utf-8')
    print('V179_PROBABILITY_SCALE_SITE_PATCH_PASS')
    print('V179_READINESS',json.dumps({k:data[k] for k in ['site_core7_eligible','formal_first100_races','site_consumer_ready_to_display_actual_formal_predictions','blockers']},ensure_ascii=False))

if __name__=='__main__':main()
