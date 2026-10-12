#!/usr/bin/env python3
"""Check tracked V236/V237 workflow source pins without reading race data."""
import ast
import hashlib
from pathlib import Path
import re


def verify(root):
    total = 0
    for filename in ('v236.yml', 'v237.yml'):
        text = (root / '.github/workflows' / filename).read_text()
        match = re.search(r'^          source_pins = (\{[^\n]+\})$', text, re.M)
        if not match:
            raise RuntimeError('MISSING_SOURCE_PINS_' + filename)
        pins = ast.literal_eval(match.group(1))
        if not isinstance(pins, dict) or not pins:
            raise RuntimeError('INVALID_SOURCE_PINS_' + filename)
        for name, expected in pins.items():
            path = root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise RuntimeError('TRACKED_SOURCE_PIN_MISMATCH_' + name)
            total += 1
    print('TRACKED_WORKFLOW_SOURCE_PINS_PASS', total)


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
