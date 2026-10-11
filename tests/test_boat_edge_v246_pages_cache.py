"""V246 HTML cache-busting references; source-only, no data changes."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='script' and a.get('src'):self.links.append(a['src'])
  if tag=='link' and a.get('href'):self.links.append(a['href'])

class TestV246PagesCache(unittest.TestCase):
 def links(self,path):
  p=Links();p.feed((ROOT/path).read_text(encoding='utf-8'));return p.links
 def test_safari_receives_actual_new_script_urls(self):
  names={'boat_edge_v203_readable.css':'203&rev=244',
         'boat_edge_v203_readable.js':'203&rev=244',
         'boat_edge_v204_prediction.css':'204&rev=244',
         'boat_edge_v204_prediction.js':'204&rev=244',
         'boat_edge_v223_source_visibility.css':'223&rev=244',
         'boat_edge_v223_source_visibility.js':'223&rev=244'}
  found=self.links('index.html')
  for name,q in names.items():
   matched=[x for x in found if name in x]
   self.assertEqual(len(matched),1,name)
   self.assertIn('?v='+q,matched[0])
 def test_paper_browser_uses_new_js(self):
  s=self.links('ai-simulation.html')
  found=[x for x in s if 'boat_edge_v211_paper.js' in x]
  self.assertEqual(len(found),1)
  self.assertIn('?v=211&rev=245',found[0])
if __name__=='__main__':unittest.main()
