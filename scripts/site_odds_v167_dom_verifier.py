"""BOAT EDGE V167: source DOM cross-check for official 3連単 odds.

Compares implicit 20x6 price ordering against explicitly displayed 2nd/3rd
boat labels. On any layout ambiguity: raise, never publish guessed odds.
Does not access result/payout/combined endpoints and does not train models.
"""
from __future__ import annotations
import re
from collections import defaultdict
from bs4 import BeautifulSoup


def expected_by_first():
    return {first: [(second, third) for second in range(1, 7)
                    if second != first for third in range(1, 7)
                    if third not in (first, second)] for first in range(1, 7)}


def _span(cell, field):
    v = cell.get(field, '1')
    try:
        n = int(v)
    except (ValueError, TypeError):
        raise ValueError('invalid ' + field)
    if n < 1 or n > 30:
        raise ValueError('unsupported ' + field)
    return n


def _rows_with_rowspans(table):
    held = {}
    for tr in table.find_all('tr'):
        row = {}
        next_held = {}
        for col, (cell, remaining) in held.items():
            row[col] = cell
            if remaining > 1:
                next_held[col] = (cell, remaining - 1)
        col = 0
        for cell in tr.find_all(['td', 'th'], recursive=False):
            while col in row:
                col += 1
            rowspan = _span(cell, 'rowspan')
            colspan = _span(cell, 'colspan')
            for offset in range(colspan):
                current_col = col + offset
                if current_col in row:
                    raise ValueError('overlapping cells')
                row[current_col] = cell
                if rowspan > 1:
                    next_held[current_col] = (cell, rowspan - 1)
            col += colspan
        held = next_held
        yield row


def _is_odds_cell(cell):
    return cell is not None and ('oddsPoint' in (cell.get('class') or []) or cell.select_one('.oddsPoint') is not None)


def _boat_label(cell):
    if cell is None:
        return None
    val = re.sub(r'\s+', '', cell.get_text(' ', strip=True))
    return int(val) if re.fullmatch(r'[1-6]', val) else None


def verify_official_dom_price_mapping(html: str) -> dict:
    """Return status=PASS, checked=120 or raise ValueError (fail closed).

    This verifies structural mapping, not parity of odds across time: the
    official current value may change between GitHub's fetch and page view.
    """
    soup = BeautifulSoup(html, 'lxml')
    tables = [table for table in soup.select('table') if len(table.select('.oddsPoint')) >= 120]
    if not tables:
        raise ValueError('official odds table with >=120 points not found')
    # The innermost qualifying table is less likely to include unrelated rows.
    tables.sort(key=lambda t: (len(t.select('.oddsPoint')), len(str(t))))
    table = tables[0]
    if len(table.select('.oddsPoint')) != 120:
        raise ValueError('expected exactly 120 oddsPoint cells in one table')
    rows = []
    for row in _rows_with_rowspans(table):
        odds_cols = sorted(k for k, c in row.items() if _is_odds_cell(c))
        if len(odds_cols) == 6:
            extracted = []
            for col in odds_cols:
                second, third = _boat_label(row.get(col - 2)), _boat_label(row.get(col - 1))
                if second is None or third is None:
                    raise ValueError(f'boat labels not explicit at row {len(rows)+1} col {col}')
                txt = re.sub(r'\s+', '', row[col].get_text('', strip=True)).replace(',', '')
                try:
                    value = float(txt)
                except ValueError:
                    # Not available yet: label ordering is still checkable.
                    value = None
                extracted.append((second, third, value))
            rows.append(extracted)
    if len(rows) != 20:
        raise ValueError(f'expected 20 six-lane odds rows; found {len(rows)}')
    expected = expected_by_first()
    mismatches = []
    checked = 0
    available = 0
    for row_i, item in enumerate(rows):
        for first_i, (second, third, price) in enumerate(item):
            first = first_i + 1
            should = expected[first][row_i]
            if (second, third) != should:
                mismatches.append({'first': first, 'row': row_i+1,
                                   'dom': [second, third], 'assumed': list(should)})
            else:
                checked += 1
                if price is not None and price > 0:
                    available += 1
    if mismatches:
        raise ValueError('DOM-to-price mapping mismatch: ' + str(mismatches[:5]))
    # Independent price cross-check: the legacy collector reads the 120
    # oddsPoint elements in DOM order and transposes their 20x6 matrix.
    legacy = [re.sub(r'\s+', '', cell.get_text('',strip=True)).replace(',', '')
              for cell in soup.select('td.oddsPoint')]
    if len(legacy) != 120:
        raise ValueError('legacy td.oddsPoint count not 120')
    numeric_mismatches = []
    for row_i, group in enumerate(rows):
        for first_i, (_, _, price) in enumerate(group):
            raw = legacy[row_i * 6 + first_i]
            try:
                old_price = float(raw)
            except (TypeError, ValueError):
                old_price = None
            if price != old_price:
                numeric_mismatches.append((first_i+1,row_i+1,price,old_price))
    if numeric_mismatches:
        raise ValueError('legacy versus explicit-label price mismatch: '+str(numeric_mismatches[:5]))
    return {'status':'PASS', 'checked':checked, 'available': available,
            'layout':'20 rows x 6 first-lane columns, explicit boat labels',
            'values_not_compared_across_time': True}
