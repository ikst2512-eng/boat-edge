"""Reject guessed lane assignments, accept only explicit six-boat start table."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from parse_explicit_start_order import parse_explicit_start_order as parse

def page(rows):
    body="".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"%x for x in rows)
    return ('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+body+'</table></html>').encode()

class StartOrderTests(unittest.TestCase):
    def test_explicit_swapped_order(self):
        self.assertEqual(parse(page([(1,2,'.10'),(2,1,'.11'),(3,3,'.12'),(4,4,'.13'),(5,5,'.14'),(6,6,'.15')])),[2,1,3,4,5,6])
    def test_missing_boat_labels(self):
        self.assertIsNone(parse(page([(i,'','.10') for i in range(1,7)])))
    def test_duplicate_boats(self):
        self.assertIsNone(parse(page([(i,1,'.10') for i in range(1,7)])))
    def test_missing_course(self):
        self.assertIsNone(parse(page([(1,1,'.10'),(2,2,'.10'),(3,3,'.10'),(4,4,'.10'),(5,5,'.10')])))
    def test_other_table_not_accepted(self):
        self.assertIsNone(parse('<html><table><tr><th>枠</th><th>並び</th><th>ST</th></tr></table></html>'.encode('utf-8')))
    def test_explicit_accessible_image_labels(self):
        order=[2,1,3,4,5,6]
        body=''.join(f'<tr><td>{i}</td><td><img alt="{order[i-1]}号艇" src="figure.png"></td><td>.12</td></tr>' for i in range(1,7))
        raw=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+body+'</table></html>').encode()
        self.assertEqual(parse(raw),order)
    def test_cp932_encoded_official_labels(self):
        order=[2,1,3,4,5,6]
        body=''.join(f'<tr><td>{i}</td><td>{order[i-1]}号艇</td><td>.12</td></tr>' for i in range(1,7))
        html='<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+body+'</table></html>'
        self.assertEqual(parse(html.encode('cp932')),order)
    def test_invalid_bytes_fail_closed(self):
        self.assertIsNone(parse(b'\\x81'))
    def test_image_filename_does_not_count(self):
        body=''.join(f'<tr><td>{i}</td><td><img src="boat_{i}.png"></td><td>.12</td></tr>' for i in range(1,7))
        raw=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+body+'</table></html>').encode()
        self.assertIsNone(parse(raw))
    def test_conflicting_image_labels_are_rejected(self):
        body=''.join(f'<tr><td>{i}</td><td><img alt="{i}号艇" aria-label="6号艇" src="x.png"></td><td>.12</td></tr>' for i in range(1,7))
        raw=('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'+body+'</table></html>').encode()
        self.assertIsNone(parse(raw))
    def test_images_not_assumed_to_be_boat_labels(self):
        self.assertIsNone(parse('<html><table><tr><th>コース</th><th>並び</th><th>ST</th></tr>'.encode('utf-8')+b''.join(b'<tr><td>'+str(i).encode()+b'</td><td><img src="boat'+str(i).encode()+b'.png"></td><td>.10</td></tr>' for i in range(1,7))+b'</table></html>'))
if __name__=='__main__': unittest.main()
