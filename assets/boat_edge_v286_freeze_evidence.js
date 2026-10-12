/* V286 read-only prior-day immutable-freeze evidence. No prediction, results, payout or network requests. */
(function(root){'use strict';
const SCHEMA='BOAT_EDGE_V220_SITE_AUTONOMOUS_OPERATIONS_V1';
const SCOPE='OBSERVED_PREDEADLINE_WINDOWS_ONLY_NOT_ALL_RACES';
const C=['observed_races','matured_observed_races','snapshot_present','predeadline_snapshot_with_matching_audit',
  'snapshot_or_audit_unverified','sha_consistent_predeadline_snapshots',
  'source_changed_after_freeze','source_missing_after_freeze',
  'v229_attestation_record_matched','v229_atomic_evidence_matched',
  'early_missing_later_snapshot_present','not_found_after_deadline','pending_before_deadline'];
const valid=n=>Number.isSafeInteger(n)&&n>=0;
function previousDay(today){
 if(!/^20\d{6}$/.test(String(today)))return null;
 const str=String(today),y=Number(str.slice(0,4)),m=Number(str.slice(4,6)),d=Number(str.slice(6,8));
 const date=new Date(Date.UTC(y,m-1,d));
 if(date.getUTCFullYear()!==y||date.getUTCMonth()!==m-1||date.getUTCDate()!==d)return null;
 date.setUTCDate(date.getUTCDate()-1);
 return date.toISOString().slice(0,10).replace(/-/g,'');
}
function summary(ops,today){
 const fallback={verified:false,text:'前日の予想固定監査を確認できません。古いデータや未検証件数は表示しません。'};
 const previous=previousDay(today);
 if(!previous||ops?.schema!==SCHEMA||ops.day_jst!==today||
    ops.scope!=='SITE_ONLY_PRE_RESULT_OPERATIONS_NOT_FORMAL_FRESH')return fallback;
 const c=ops.site_prediction_freeze_observation?.previous_day;
 if(!c||c.day_jst!==previous||c.scope!==SCOPE||!C.every(k=>valid(c[k])))return fallback;
 if(c.observed_races!==c.snapshot_present+c.not_found_after_deadline+c.pending_before_deadline ||
    c.matured_observed_races>c.observed_races||
    c.snapshot_present!==c.predeadline_snapshot_with_matching_audit+c.snapshot_or_audit_unverified||
    c.predeadline_snapshot_with_matching_audit!==
      c.sha_consistent_predeadline_snapshots+c.source_changed_after_freeze+c.source_missing_after_freeze||
    c.v229_attestation_record_matched>c.predeadline_snapshot_with_matching_audit||
    c.v229_atomic_evidence_matched>c.sha_consistent_predeadline_snapshots||
    c.v229_atomic_evidence_matched>c.v229_attestation_record_matched||
    c.early_missing_later_snapshot_present>c.snapshot_present)return fallback;
 // V291: the new source-gap and runner-time counts are optional for
 // older snapshots, but if any are supplied the complete set must reconcile.
 // "no observed gap" is NEVER interpreted as "source ready".
 const F=['not_found_with_observed_gaps','not_found_without_observed_gaps',
   'not_found_last_seen_inside_2_to_10m_window',
   'not_found_last_seen_outside_2_to_10m_window',
   'not_found_last_seen_unverified',
   'not_found_without_gaps_inside_2_to_10m_window'];
 const newKeys=F.filter(k=>Object.prototype.hasOwnProperty.call(c,k));
 const hasV290=newKeys.length===F.length;
 if(newKeys.length && !hasV290)return fallback;
 if(hasV290&&(!F.every(k=>valid(c[k]))||
   c.not_found_with_observed_gaps+c.not_found_without_observed_gaps!==c.not_found_after_deadline||
   c.not_found_last_seen_inside_2_to_10m_window+
     c.not_found_last_seen_outside_2_to_10m_window+
     c.not_found_last_seen_unverified!==c.not_found_after_deadline||
   c.not_found_without_gaps_inside_2_to_10m_window>c.not_found_without_observed_gaps||
   c.not_found_without_gaps_inside_2_to_10m_window>c.not_found_last_seen_inside_2_to_10m_window))
    return fallback;
 if(c.observed_races===0)return {verified:true,text:'前日 '+previous+' は締切前の監視記録が0R。固定率を判定できません。'};
 const prev=previous.slice(4,6)+'/'+previous.slice(6,8);
 const pieces=[
  '前日'+prev+'の監視対象 '+c.observed_races+'R',
  '予想ファイルあり '+c.snapshot_present+'R',
  '保存時刻・監査SHA整合 '+c.predeadline_snapshot_with_matching_audit+'R',
  '固定後の出走データSHA相違 '+c.source_changed_after_freeze+'R',
  '固定後の出走データ欠落 '+c.source_missing_after_freeze+'R',
  '締切後も予想ファイルなし '+c.not_found_after_deadline+'R',
  'V229同時監査記録の一致 '+c.v229_attestation_record_matched+'R'
 ];
 if(hasV290)pieces.push(
  '未固定・ソース不足の観測あり '+c.not_found_with_observed_gaps+'R',
  '未固定・ソース不足の観測なし '+c.not_found_without_observed_gaps+'R',
  '未固定・最後の観測が凍結2～10分内 '+c.not_found_last_seen_inside_2_to_10m_window+'R',
  'うちソース不足の観測なし '+c.not_found_without_gaps_inside_2_to_10m_window+'R'
 );
 const text=pieces.join(' ／ ')+
  '。観測で不足が見つからなくても必要な入力や予想固定の成功は未証明。V215の観測時刻はV229の実行証拠ではありません。同時監査記録は現在の出走データ整合や正式Freshの合格を意味しません。';
 return {verified:true,text};
}
root.BoatEdgeV286Freeze=Object.freeze({summary,previousDay});
})(window);
