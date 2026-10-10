#!/usr/bin/env python3
"""BOAT EDGE site-only autonomous independent evaluation summary.
Reads ONLY precomputed, provenance-audited site evaluation documents, site readiness,
and the formal STATUS (never formal targets, result files, payouts or unlock endpoints).
NO prediction, wagers, production adoption, formal unlock, or score recomputation.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re

JST = timezone(timedelta(hours=9))
V185_PATH = 'data/site_tail_shadow_v185/evaluation.json'
V199_PATH = 'data/site_shadow_v199/evaluation.json'
FORMAL_PATH = 'data/formal_status.json'
READINESS_PATH = 'data/site_paper_sim/readiness_v215_current.json'
OUT_PATH = 'data/site_autovalidation/current.json'
LEVELS = ('3', '5', '10')
DATE_KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')
SHA = re.compile(r'^[a-f0-9]{64}$')


def canonical(doc):
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def load(root: Path, relative: str):
    path = root / relative
    if not path.is_file():
        return None, 'MISSING', None
    try:
        raw = path.read_bytes()
        doc = json.loads(raw)
    except (OSError, UnicodeError, ValueError):
        return None, 'INVALID_JSON', None
    if not isinstance(doc, dict):
        return None, 'INVALID_OBJECT', None
    return doc, 'OK', hashlib.sha256(raw).hexdigest()


def valid_race_rows(doc, family):
    reasons = []
    expected = ('boat-edge-v185-post-settlement-independent-site-shadow-v1' if family == 'v185'
                else 'boat-edge-v199-independent-future-only-score-v1')
    if doc.get('schema_version') != expected:
        reasons.append('UNEXPECTED_SCHEMA')
    expected_scope = 'SITE_REFERENCE_RESEARCH_NOT_FORMAL_FRESH' if family == 'v185' else 'SITE_REFERENCE_RESEARCH_ONLY_NOT_FORMAL_FRESH'
    if doc.get('scope') != expected_scope:
        reasons.append('RESEARCH_SCOPE_MISMATCH')
    if doc.get('formal_results_accessed') is not False:
        reasons.append('FORMAL_SOURCE_ACCESS_UNKNOWN')
    if doc.get('production_changed' if family == 'v185' else 'production_model_changed') is not False:
        reasons.append('PRODUCTION_ADOPTION_UNVERIFIED')
    if doc.get('invalid') != []:
        reasons.append('UNVERIFIED_FROZEN_ENTRIES')
    if family == 'v185' and doc.get('observed_source') != 'FIRST_COMMITTED_GIT_BLOB_SHA_AND_REPRODUCIBLE_SHADOW':
        reasons.append('INITIAL_COMMIT_PROVENANCE_UNCONFIRMED')
    if family == 'v199' and doc.get('result_access') != 'ONLY_CONFIRMED_SITE_FILE_AFTER_ALL_PRE_RESULT_GIT_CHECKS':
        reasons.append('RESULT_ACCESS_CONTRACT_UNKNOWN')
    rows = doc.get('races')
    if not isinstance(rows, list):
        return None, reasons + ['NO_RACE_ROWS']
    verified = doc.get('settled_verified')
    if not isinstance(verified, int) or isinstance(verified, bool) or verified != len(rows):
        reasons.append('VERIFIED_COUNT_MISMATCH')
    keys = []
    candidates = ('baseline', 'candidate') if family == 'v185' else ('v185', 'head', 'second', 'original', 'combined')
    for row in rows:
        if not isinstance(row, dict):
            reasons.append('RACE_ROW_NOT_OBJECT')
            break
        key = row.get('race_key')
        if not isinstance(key, str) or not DATE_KEY.fullmatch(key) or key[:8] < '20261010':
            reasons.append('NON_PROSPECTIVE_RACE_KEY')
            break
        if row.get('band') not in ('<10', '10-20', '20-50', '>50', 'unknown'):
            reasons.append('PAYOUT_BAND_UNKNOWN')
            break
        h = row.get('hits')
        if not isinstance(h, dict):
            reasons.append('HIT_STRUCTURE_MISSING')
            break
        if any(not isinstance(h.get(model), dict) or
               any(h[model].get(k) is not True and h[model].get(k) is not False for k in LEVELS)
               for model in candidates):
            reasons.append('HIT_VALUES_UNVERIFIED')
            break
        keys.append(key)
    if len(keys) != len(set(keys)):
        reasons.append('DUPLICATE_RACE_KEY')
    # If a scorer recorded anything anomalous, exclude ALL its summaries.
    return (rows if not reasons else None), sorted(set(reasons))


def compare(rows, control, candidate):
    out = {}
    for level in LEVELS:
        old = sum(1 for r in rows if r['hits'][control][level])
        new = sum(1 for r in rows if r['hits'][candidate][level])
        gains = sum(1 for r in rows if r['hits'][candidate][level] and not r['hits'][control][level])
        losses = sum(1 for r in rows if r['hits'][control][level] and not r['hits'][candidate][level])
        out['top' + level] = {'control_hits': old, 'candidate_hits': new,
                              'difference': new-old, 'paired_gains': gains,
                              'paired_losses': losses,
                              'control_rate_percent': round(old*100/len(rows), 2) if rows else None,
                              'candidate_rate_percent': round(new*100/len(rows), 2) if rows else None}
    return out


def lane_report(doc, family, digest):
    if doc is None:
        return {'status': 'UNAVAILABLE', 'source_sha256': digest, 'reasons': ['MISSING_OR_UNREADABLE_EVALUATION'],
                'verified_races': 0, 'race_dates': 0, 'candidate_comparisons': {}}
    rows, issues = valid_race_rows(doc, family)
    if rows is None:
        return {'status': 'FAIL_CLOSED', 'source_sha256': digest, 'reasons': issues,
                'verified_races': 0, 'race_dates': 0, 'candidate_comparisons': {}}
    control = 'baseline' if family == 'v185' else 'v185'
    candidates = ['candidate'] if family == 'v185' else ['head', 'second', 'original', 'combined']
    band = [r for r in rows if r['band'] == '10-20']
    dates = len({r['race_key'][:8] for r in rows})
    comparisons = {}
    for candidate in candidates:
        overall = compare(rows, control, candidate)
        in_band = compare(band, control, candidate)
        # Review status is diagnostic only; never auto-approve or deploy a new model.
        meets_size = len(rows) >= 100 and dates >= 7 and len(band) >= 30
        nonworse = all(overall['top'+k]['difference'] >= 0 for k in LEVELS)
        improved = overall['top5']['difference'] > 0 and in_band['top10']['difference'] >= 0
        review = bool(meets_size and nonworse and improved)
        head = None
        if family == 'v199' and rows and all(
            isinstance(r.get('top1_head_hits'), dict) and
            isinstance(r['top1_head_hits'].get(control), bool) and
            isinstance(r['top1_head_hits'].get(candidate), bool) for r in rows):
            head_control = sum(r['top1_head_hits'][control] for r in rows)
            head_candidate = sum(r['top1_head_hits'][candidate] for r in rows)
            head = {'control_hits': head_control, 'candidate_hits': head_candidate,
                    'difference': head_candidate-head_control}
        comparisons[candidate] = {'all_races': overall, 'confirmed_payout_10_20x': in_band,
                                 'top1_head': head,
                                 'review_status': 'MANUAL_REVIEW_POSSIBLE_NOT_APPROVED' if review else 'INSUFFICIENT_PROSPECTIVE_EVIDENCE',
                                 'automatic_production_adoption': False}
    return {'status': 'VERIFIED_UPSTREAM_SITE_ONLY', 'source_sha256': digest, 'reasons': [],
            'verified_races': len(rows), 'race_dates': dates,
            'confirmed_payout_10_20x_races': len(band),
            'candidate_comparisons': comparisons}


def formal_status(root):
    doc, status, _digest = load(root, FORMAL_PATH)
    if status != 'OK':
        return {'stage': 'UNKNOWN', 'readiness': 'BLOCKED_NO_AUTHORITATIVE_STATUS',
                'formal_first100_frozen': 0, 'auto_unlock': False, 'formal_results_read': False}
    guards = doc.get('guards') or {}
    cohort = doc.get('formalFirst100') or {}
    if not isinstance(guards, dict) or any(guards.get(x) is not False for x in ('results_seen','unlock','scoring')):
        readiness = 'GUARD_STATE_NEEDS_INDEPENDENT_REVIEW'
    elif doc.get('connected') is not True or doc.get('predictions_ready') is not True:
        readiness = 'BLOCKED_MISSING_FORMAL_SOURCES_OR_PROVENANCE'
    else:
        readiness = 'STATUS_ONLY_SEPARATE_FORMAL_GATE_REQUIRED'
    return {'stage': doc.get('stage') if isinstance(doc.get('stage'), str) else 'UNKNOWN',
            'current': doc.get('current') if isinstance(doc.get('current'), str) else 'UNKNOWN',
            'readiness': readiness,
            'source_rows': (doc.get('collector_snapshot') or {}).get('source_rows') or {},
            'formal_first100_frozen': cohort.get('races') if type(cohort.get('races')) is int else 0,
            'auto_unlock': False, 'formal_results_read': False,
            'gate_is_not_implemented_in_this_report': True}


def readiness_status(root, date):
    doc, status, _ = load(root, READINESS_PATH)
    if status != 'OK' or doc.get('day_jst') != date:
        return {'status': 'WAITING_FOR_CURRENT_DAY_DIAGNOSTIC', 'observed_races': 0}
    return {'status': 'DIAGNOSTICS_ONLY',
            'checked_at': doc.get('checked_at'),
            'scheduled_races': doc.get('scheduled_races'),
            'observed_races': doc.get('day_observed_races'),
            'verified_races': doc.get('day_verified_races'),
            'latest_reasons': doc.get('day_latest_reasons') or {}}


def report(root, now):
    date = now.astimezone(JST).strftime('%Y%m%d')
    v185, _status185, sha185 = load(root, V185_PATH)
    v199, _status199, sha199 = load(root, V199_PATH)
    a = lane_report(v185, 'v185', sha185)
    b = lane_report(v199, 'v199', sha199)
    return {
        'schema': 'BOAT_EDGE_SITE_AUTOVALIDATION_V1',
        'date_jst': date,
        'scope': 'SITE_REFERENCE_REPORT_ONLY_FORMAL_FRESH_ISOLATED',
        'status': 'EVIDENCE_REVIEW_REQUIRED' if a['status']=='VERIFIED_UPSTREAM_SITE_ONLY' and b['status']=='VERIFIED_UPSTREAM_SITE_ONLY' else 'EVIDENCE_BLOCKED_OR_MISSING',
        'site_v185': a, 'site_v199': b,
        'readiness': readiness_status(root, date),
        'formal': formal_status(root),
        'next_priorities': ['Increase verified predeadline immutable predictions on future races',
                            'Audit original exhibition and scratch/source availability',
                            'Compare A-head and trifecta Top3/5/10 on strictly matched unseen races',
                            'Obtain independent multi-day evidence before considering model adoption'],
        'payout_band_notice': '10-20x is CONFIRMED RESULT payout band, not a predeadline selected ticket odds band or investment ROI.',
        'performance_claim': 'NOT_PROVEN',
        'paper_wager_authorized': False,
        'production_model_change_authorized': False,
        'formal_fresh_unlock_authorized': False,
        'formal_results_seen_by_this_runner': False,
        'report_is_not_formal_scoring': True,
    }


def store(root, data):
    dest = root / OUT_PATH
    dated = root / 'data/site_autovalidation/daily' / (data['date_jst']+'.json')
    raw = canonical(data)
    digest = hashlib.sha256(raw).hexdigest()
    changed = False
    for path in (dest, dated):
        if path.exists() and path.read_bytes() == raw:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        changed = True
    return {'report_sha256': digest, 'changed': changed, 'path': OUT_PATH, 'daily_path':dated.relative_to(root).as_posix()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--now', default=None, help='ISO timestamp for deterministic regression only')
    parser.add_argument('--dry-run', action='store_true')
    args=parser.parse_args()
    now=datetime.fromisoformat(args.now.replace('Z','+00:00')) if args.now else datetime.now(timezone.utc)
    if now.tzinfo is None: raise SystemExit('V219_REQUIRES_TIMEZONE')
    root=Path(args.root).resolve()
    data=report(root,now)
    result={'scope':data['scope'],'v185_verified':data['site_v185']['verified_races'],
            'v199_verified':data['site_v199']['verified_races'],
            'formal':data['formal']['readiness'],'status':data['status']}
    if not args.dry_run: result.update(store(root,data))
    print('V219_SITE_AUTOVALIDATION_NO_FORMAL_RESULT_READ '+json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__': main()
