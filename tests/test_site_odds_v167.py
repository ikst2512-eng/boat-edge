import unittest
from bs4 import BeautifulSoup
from scripts.site_odds_v167_dom_verifier import verify_official_dom_price_mapping, expected_by_first


def build_sample(incorrect=False):
    pairs=expected_by_first()
    rows=['<table class="odds3t"><thead><tr><th colspan="18">Official odds</th></tr></thead><tbody>']
    for row in range(20):
        bits=['<tr>']
        for first in range(1, 7):
            second, third=pairs[first][row]
            if incorrect and first==2 and row==7:
                third=6 if third != 6 and second!=6 else 5
            if row%4==0:
                bits.append(f'<td rowspan="4">{second}</td>')
            bits.extend((f'<td>{third}</td>', f'<td class="oddsPoint">{first*100+row+0.1:.1f}</td>'))
        bits.append('</tr>')
        rows.append(''.join(bits))
    rows.append('</tbody></table>')
    return ''.join(rows)


class V167Test(unittest.TestCase):
    def test_120_mapping_pass(self):
        result=verify_official_dom_price_mapping(build_sample())
        self.assertEqual((result['status'],result['checked'],result['available']),('PASS',120,120))
    def test_wrong_third_label_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mapping mismatch'):
            verify_official_dom_price_mapping(build_sample(incorrect=True))
    def test_truncated_page_rejected(self):
        with self.assertRaisesRegex(ValueError, '120'):
            verify_official_dom_price_mapping('<table><tr><td class="oddsPoint">2.2</td></tr></table>')
    def test_missing_label_rejected(self):
        html=build_sample().replace('<td>3</td><td class="oddsPoint">100.1</td>', '<td>—</td><td class="oddsPoint">100.1</td>',1)
        with self.assertRaisesRegex(ValueError, 'boat labels'):
            verify_official_dom_price_mapping(html)
    def test_rowspan_boundary(self):
        out=verify_official_dom_price_mapping(build_sample().replace('"oddsPoint"','"oddsPoint is-odds"'))
        self.assertEqual(out['checked'],120)
    def test_invalid_row_layout_rejected(self):
        html=build_sample().replace('<td rowspan="4">2</td>','<td rowspan="1">2</td>',1)
        with self.assertRaises(ValueError):
            verify_official_dom_price_mapping(html)

if __name__=='__main__': unittest.main()
