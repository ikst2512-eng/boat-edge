"""V183 scoring regression now requires V184 first-commit source and hash binding.
This explicitly replaces the prior fake-commit test, which could not test provenance.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_v184_integrity
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import site_v183_audit as v183
assert v183.band(1000)=='10to20'
assert v183.band(2000)=='10to20'
assert v183.band(2001)=='20to50'
assert v183.classify('1-2-3',['1-2-4'])=='third_missing'
assert v183.classify('1-2-3',['2-1-3'])=='head_missing'
assert v183.classify('1-2-3',['1-2-4','1-4-3'])=='pairing_miss'
print('V183_V184_HARDENED_PROVENANCE_REGRESSION_PASS')
