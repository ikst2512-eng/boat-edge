#!/usr/bin/env python3
"""V170 site reference mode-by-venue descriptive performance. NEVER touches formal Fresh.
Read only V136-audited evaluation and matching frozen website history. No result endpoint.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

VENUES = {
    '01': '桐生', '02': '戸田', '03': '江戸川', '04': '平和島',
    '05': '多摩川', '06': '浜名湖', '07': '蒲郡', '08': '常滑',
    '09': '津', '10': '三国', '11': 'びわこ', '12': '住之江',
    '13': '尼崎', '14': '鳴門', '15': '丸亀', '16': '児島',
    '17': '宮島', '18': '徳山', '19': '下関', '20': '若松',
    '21': '芦屋', '22': '福岡', '23': '唐津', '24': '大村'
}
MODES = {'hit': '的中重視', 'balance': 'バランス', 'hole': '波乱展開', 'narrow': '激絞り'}
DATE_FLOOR = '20261009'
K_PATTERN = re.compile(r'^(\d{8})-(\d{2})-(\d{2})$')
EXPECTED_SCOPE = 'SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH'


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def source_record(evaluation: Path, histories_dir: Path):
    key = evaluation.stem
    mat = K_PATTERN.fullmatch(key)
    if not mat or mat.group(1) < DATE_FLOOR or mat.group(2) not in VENUES:
        raise ValueError('out-of-scope race key')
    eval_data = read_json(evaluation)
    if eval_data.get('schema_version') != 'boat-edge-site-mode-evaluation-v136':
        raise ValueError('wrong evaluation schema')
    if eval_data.get('scope') != EXPECTED_SCOPE or eval_data.get('race_key') != key:
        raise ValueError('not audited site reference')
    history_file = histories_dir / (key + '.json')
    content = history_file.read_bytes()
    if hashlib.sha256(content).hexdigest() != eval_data.get('source_history_sha256'):
        raise ValueError('audited source history SHA mismatch')
    history = json.loads(content)
    snapshot = history.get('snapshot') or {}
    settled = history.get('settlement') or {}
    if history.get('race_key') != key or snapshot.get('race_key') != key:
        raise ValueError('history key mismatch')
    if snapshot.get('prediction_kind') != 'SITE_REFERENCE_V122' or snapshot.get('snapshot_window') != 'FINAL_15M':
        raise ValueError('not a frozen final prediction')
    if snapshot.get('guards') != {'results_seen': False, 'unlock': False, 'scoring': False}:
        raise ValueError('PRE_RESULT guards not preserved')
    if snapshot.get('saved_at') != eval_data.get('snapshot_saved_at'):
        raise ValueError('snapshot timestamp mismatch')
    if datetime.fromisoformat(snapshot['saved_at']) >= datetime.fromisoformat(settled['settled_at']):
        raise ValueError('prediction not frozen prior to settlement')
    if settled.get('winning_combo') != eval_data.get('winning_combo'):
        raise ValueError('winning combo disagreement')
    payout_100 = settled.get('payout')
    if not isinstance(payout_100, int) or payout_100 <= 0:
        raise ValueError('official payout unavailable')
    result = {'race_key': key, 'venue': mat.group(2), 'day': mat.group(1), 'winner_non1': not str(settled['winning_combo']).startswith('1-'), 'modes': {}}
    for mode in MODES:
        expected = eval_data.get('modes', {}).get(mode, {})
        tickets = snapshot.get('modes', {}).get(mode, {}).get('tickets', [])
        if not isinstance(tickets, list) or not tickets:
            raise ValueError(f'{mode}: missing frozen tickets')
        combos = [t.get('combo') for t in tickets]
        stakes = [t.get('stake_yen') for t in tickets]
        if len(set(combos)) != len(combos) or any(not isinstance(s, int) or s < 100 or s % 100 != 0 for s in stakes):
            raise ValueError(f'{mode}: bad frozen ticket')
        if sum(stakes) != 10000:
            raise ValueError(f'{mode}: stake not 10,000')
        winning_indexes = [i for i, c in enumerate(combos) if c == settled['winning_combo']]
        hit = len(winning_indexes) == 1
        if hit != expected.get('hit') or hit != settled.get('mode_hits', {}).get(mode):
            raise ValueError(f'{mode}: outcome parity disagreement')
        if len(tickets) != expected.get('count'):
            raise ValueError(f'{mode}: count parity disagreement')
        if (winning_indexes[0] + 1 if hit else None) != expected.get('ticket_rank'):
            raise ValueError(f'{mode}: ranking parity disagreement')
        returned = payout_100 * stakes[winning_indexes[0]] // 100 if hit else 0
        result['modes'][mode] = {'hit': hit, 'returned_yen': returned}
    return result


def _blank():
    return {'races': 0, 'days': set(), 'non1_races': 0,
            'modes': {k: {'hits': 0, 'non1_hits': 0, 'returned_yen': 0, 'invested_yen': 0} for k in MODES}}


def calc(root: Path):
    evaluated_dir = root / 'data/site_learning/site_mode_evaluations_v136'
    histories_dir = root / 'data/site_prediction_history'
    groups = {k: _blank() for k in VENUES}
    global_stats = _blank()
    seen = set()
    errors = []
    for file in sorted(evaluated_dir.glob('*.json')):
        match = K_PATTERN.fullmatch(file.stem)
        if not match or match.group(1) < DATE_FLOOR:
            # Exclude older cohorts before opening their files, especially formal 10/8.
            continue
        try:
            rec = source_record(file, histories_dir)
            if rec['race_key'] in seen:
                raise ValueError('duplicate race')
            seen.add(rec['race_key'])
        except Exception as e:
            errors.append({'file': file.name, 'reason': str(e)[:120]})
            continue
        for group in (groups[rec['venue']], global_stats):
            group['races'] += 1
            group['days'].add(rec['day'])
            group['non1_races'] += int(rec['winner_non1'])
            for mode, val in rec['modes'].items():
                dest = group['modes'][mode]
                dest['hits'] += int(val['hit'])
                dest['non1_hits'] += int(val['hit'] and rec['winner_non1'])
                dest['returned_yen'] += val['returned_yen']
                dest['invested_yen'] += 10000

    def export(s):
        n = s['races']
        return {'races': n, 'distinct_days': len(s['days']), 'winning_non1_races': s['non1_races'],
                'status': 'REFERENCE_COMPARABLE' if n >= 30 and len(s['days']) >= 3 else ('SMALL_SAMPLE' if n else 'NO_DATA'),
                'modes': {k: {
                    'hits': v['hits'],
                    'hit_rate_pct': round(100*v['hits']/n, 1) if n else None,
                    'non1_hits': v['non1_hits'],
                    'non1_hit_rate_pct': round(100*v['non1_hits']/s['non1_races'], 1) if s['non1_races'] else None,
                    'returned_yen': v['returned_yen'],
                    'invested_yen': v['invested_yen'],
                    'net_yen': v['returned_yen'] - v['invested_yen'],
                    'roi_pct': round(100*v['returned_yen']/v['invested_yen'], 1) if v['invested_yen'] else None,
                } for k, v in s['modes'].items()}}

    out = {'schema_version': 'boat-edge-site-prediction-venue-v170',
           'scope': EXPECTED_SCOPE,
           'source_evaluation': 'V136 audited FINAL_15M (never formal Fresh)',
           'selection_date_floor': '2026-10-09',
           'production_prediction_weights_changed': False,
           'formal_fresh_scoring': False,
           'recognized_venues': 24,
           'audited_races': global_stats['races'],
           'distinct_days': len(global_stats['days']),
           'excluded': len(errors),
           'exclusion_details': errors[:12],
           'certification': 'NONE; reference comparison only, independent Fresh needed',
           'threshold': '30 races AND 3 distinct days for comparative candidate (not certified)',
           'budget_per_mode_race_yen': 10000,
           'overall': export(global_stats),
           'venues': {k: {'venue_code': k, 'name': label, **export(groups[k])} for k, label in VENUES.items()}}
    return out


def main():
    root = Path('.').resolve()
    result = calc(root)
    out = root / 'data/site_learning/mode_venue_accuracy_v170.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'RESEARCH_ONLY', 'audited_races': result['audited_races'], 'distinct_days': result['distinct_days'], 'excluded': result['excluded'], 'with_venue_data': sum(v['races'] > 0 for v in result['venues'].values()), 'output': str(out)}, ensure_ascii=False))
    if result['audited_races'] == 0:
        raise SystemExit('No valid V136 reference records: refuse to publish empty venue confidence report')

if __name__ == '__main__':
    main()
