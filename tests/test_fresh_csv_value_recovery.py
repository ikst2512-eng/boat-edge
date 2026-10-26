"""Execute collector predicates on synthetic CSVs; never read race outcomes."""
import ast
import copy
import math
from pathlib import Path
import textwrap
import unittest

WORKFLOW = Path('.github/workflows/auto-update.yml')


def collector_tree():
    source = WORKFLOW.read_text(encoding='utf-8')
    start = source.index('          def source_is_sparse(role,rows):')
    end = source.index('          def num(', start)
    return ast.parse(textwrap.dedent(source[start:end]))


class ValueRecovery(unittest.TestCase):
    def setUp(self):
        tree = collector_tree()
        names = {'original_complete', 'preview_source_is_incomplete', 'complete_row'}
        functions = [copy.deepcopy(n) for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name in names]
        self.ns = {'math': math, 'pending_codes': {'209901010101'}}
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
                     '<synthetic-collector>', 'exec'), self.ns)
        self.row = {'レースコード': '209901010101', '計測項目1': '一周', '計測項目2': '回り足'}
        self.row.update({f'艇{b}_値{i}': '36.5' for b in range(1, 7) for i in (1, 2)})

    def test_every_advertised_measurement_is_retried_until_valid(self):
        for invalid in ('', '未計測', 'NaN', 'inf'):
            bad = dict(self.row, **{'艇6_値2': invalid})
            self.assertFalse(self.ns['original_complete'](bad))
            self.assertTrue(self.ns['preview_source_is_incomplete']('original_exhibition', [bad]))
            self.assertFalse(self.ns['complete_row']('original_exhibition', bad))
            self.assertTrue(self.ns['complete_row']('original_exhibition', self.row))
            self.assertFalse(self.ns['preview_source_is_incomplete']('original_exhibition', [self.row]))

    def test_gapped_labels_never_count_as_complete(self):
        bad = dict(self.row, **{'計測項目2': '', '計測項目3': '回り足'})
        self.assertFalse(self.ns['complete_row']('original_exhibition', bad))
        self.assertTrue(self.ns['preview_source_is_incomplete']('original_exhibition', [bad]))

    def test_partial_courses_fail_closed_without_aborting_collector(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        start = source.index('              core7=(')
        end = source.index('              # Report precise', start)
        statement = ast.parse(textwrap.dedent(source[start:end]))
        for courses, expected in [([1, 2, None, 4, 5, 6], False),
                                  ([1, 2, 2, 4, 5, 6], False),
                                  ([6, 5, 4, 3, 2, 1], True)]:
            ns = {'source_presence': {'test': True}, 'core7_boat': lambda *a: True,
                  'rc': {}, 'stt': {}, 'tkz': {}, 'courses': courses}
            exec(compile(statement, '<synthetic-core7>', 'exec'), ns)
            self.assertIs(ns['core7'], expected)


if __name__ == '__main__':
    unittest.main()
