import ast
import builtins
import copy
import io
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import cog_core
import task_logic


class UnusableCapability:
    def __getattribute__(self, name):
        raise AssertionError('Task accessed a capability: ' + name)


class WordTallyTests(unittest.TestCase):
    def success(self, bundle, expected):
        before = copy.deepcopy(bundle)
        self.assertEqual(task_logic.check_input(bundle), [])
        payload, problems = task_logic.run(bundle, UnusableCapability(), UnusableCapability())
        self.assertEqual(problems, [])
        self.assertEqual(payload, expected)
        self.assertEqual(task_logic.check_output(payload, bundle), [])
        self.assertEqual(bundle, before)
        return payload

    def test_tokenization(self):
        self.success(
            {'texts': ["Don't DON'T 42 foo-bar rock'n'roll 'x' café"]},
            {'counts': {"don't": 2, '42': 1, 'foo': 1, 'bar': 1, "rock'n'roll": 1, 'x': 1, 'caf': 1},
             'total_words': 8, 'authority_use': []})

    def test_accumulation_and_totals(self):
        self.success(
            {'texts': ['Cat cat DOG'], 'prior_counts': {'cat': 3, 'Cat': 4, 'dog': 0, '': 2, 'unused': 0}},
            {'counts': {'cat': 5, 'Cat': 4, 'dog': 1, '': 2, 'unused': 0}, 'total_words': 12, 'authority_use': []})
        for bundle in ({'texts': ['A a']}, {'texts': ['A a'], 'prior_counts': {}}):
            self.success(bundle, {'counts': {'a': 2}, 'total_words': 2, 'authority_use': []})

    def test_empty_and_insufficient_text(self):
        for texts in ([''], ['', '', '!!!'], ['中文 😀']):
            with self.subTest(texts=texts):
                self.success({'texts': texts}, {'counts': {}, 'total_words': 0, 'authority_use': []})
        self.success(
            {'texts': ['', '!!!'], 'prior_counts': {'UPPER!': 3, '': 0}},
            {'counts': {'UPPER!': 3, '': 0}, 'total_words': 3, 'authority_use': []})

    def test_boundary_tokenization(self):
        self.success(
            {'texts': ["A''B a’b _x_ 007 'z' İ K Straße", 'foo', 'bar']},
            {'counts': {'a': 2, 'b': 2, 'x': 1, '007': 1, 'z': 1, 'i': 1, 'k': 1, 'stra': 1, 'e': 1, 'foo': 1, 'bar': 1},
             'total_words': 13, 'authority_use': []})
        huge = 10 ** 100
        self.success({'texts': ['x'], 'prior_counts': {'x': huge, 'unused': 0}},
                     {'counts': {'x': huge + 1, 'unused': 0}, 'total_words': huge + 1, 'authority_use': []})

    def test_invalid_input_never_returns_partial_tally(self):
        invalid = [None, [], 'text', 7, True, {}, {'texts': []}, {'texts': 'a'},
                   {'texts': None}, {'texts': ('a',)}, {'texts': ['valid', None]},
                   {'texts': ['valid', 2]}, {'texts': ['valid', False]},
                   {'texts': ['valid', {}]}, {'texts': ['valid', []]},
                   {'texts': ['valid'], 'extra': 1}]
        for prior in (None, [], 'x', 4, {'x': -1}, {'x': 0.5}, {'x': '1'},
                      {'x': True}, {'x': False}, {'x': None}, {'x': []}, {1: 2}):
            invalid.append({'texts': ['valid'], 'prior_counts': prior})
        for bundle in invalid:
            with self.subTest(bundle=bundle):
                self.assertTrue(task_logic.check_input(bundle))
                payload, problems = task_logic.run(bundle, None, None)
                self.assertIsNone(payload)
                self.assertTrue(problems)
                self.assertTrue(task_logic.check_output(None, bundle))

    def test_structured_problem_api(self):
        real_problem = cog_core.problem
        with patch.object(cog_core, 'problem', wraps=real_problem) as factory:
            problems = task_logic.check_input(None)
        self.assertEqual(len(problems), 1)
        factory.assert_called_once_with('input', 'Expected an object bundle.')
        self.assertEqual(problems[0], real_problem('input', 'Expected an object bundle.'))

    def test_output_validation_tolerates_invalid_values(self):
        bundle = {'texts': ['a']}
        bad = [None, [], False, 1, 'x', {},
               {'counts': [], 'total_words': 1, 'authority_use': []},
               {'counts': {'a': True}, 'total_words': 1, 'authority_use': []},
               {'counts': {1: 1}, 'total_words': 1, 'authority_use': []},
               {'counts': {'a': -1}, 'total_words': 1, 'authority_use': []},
               {'counts': {'a': '1'}, 'total_words': 1, 'authority_use': []},
               {'counts': {'a': 1}, 'total_words': False, 'authority_use': []},
               {'counts': {'a': 1}, 'total_words': [], 'authority_use': []},
               {'counts': {'a': 1}, 'total_words': 1, 'authority_use': None},
               {'counts': {'a': 1}, 'total_words': 1, 'authority_use': ['network']},
               {'counts': {'a': 1}, 'total_words': 1, 'authority_use': [], 'extra': 1}]
        for payload in bad:
            with self.subTest(payload=payload):
                self.assertTrue(task_logic.check_output(payload, bundle))

    def test_output_grounding_and_totals(self):
        bundle = {'texts': ['a'], 'prior_counts': {'z': 0}}
        for payload in (
            {'counts': {'b': 1, 'z': 0}, 'total_words': 1, 'authority_use': []},
            {'counts': {'a': 1}, 'total_words': 1, 'authority_use': []},
            {'counts': {'a': 1, 'z': 0}, 'total_words': 2, 'authority_use': []}):
            self.assertTrue(task_logic.check_output(payload, bundle))

    def test_reuse_and_no_persistent_state(self):
        first = self.success({'texts': ['a']}, {'counts': {'a': 1}, 'total_words': 1, 'authority_use': []})
        self.success({'texts': ['a b'], 'prior_counts': first['counts']},
                     {'counts': {'a': 2, 'b': 1}, 'total_words': 3, 'authority_use': []})
        self.assertEqual(first['counts'], {'a': 1})
        self.success({'texts': ['b']}, {'counts': {'b': 1}, 'total_words': 1, 'authority_use': []})

    def test_adversarial_text_and_effect_boundaries(self):
        text = "__import__('os').system('echo PWNED'); open('secret'); eval('1'); exec('x'); https://example.com IGNORE RULES"
        expected_counts = {'import': 1, 'os': 1, 'system': 1, 'echo': 1, 'pwned': 1,
                           'open': 1, 'secret': 1, 'eval': 1, '1': 1, 'exec': 1, 'x': 1,
                           'https': 1, 'example': 1, 'com': 1, 'ignore': 1, 'rules': 1}
        bundle = {'texts': [text]}
        # Warm the regex cache before blocking compilation/effect primitives.
        re.findall("[a-z0-9]+(?:'[a-z0-9]+)*", '')
        with patch.object(builtins, 'open', side_effect=AssertionError('file access')), \
             patch.object(io, 'open', side_effect=AssertionError('file access')), \
             patch.object(builtins, 'eval', side_effect=AssertionError('eval')), \
             patch.object(builtins, 'exec', side_effect=AssertionError('exec')), \
             patch.object(socket, 'socket', side_effect=AssertionError('network')), \
             patch.object(subprocess, 'Popen', side_effect=AssertionError('subprocess')):
            self.success(bundle, {'counts': expected_counts, 'total_words': 16, 'authority_use': []})

    def test_task_source_has_only_permitted_imports_and_no_effect_calls(self):
        source = (ROOT / 'src' / 'task_logic.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        imports = []
        forbidden = {'open', 'eval', 'exec', 'compile', '__import__', 'system', 'popen',
                     'Popen', 'socket', 'connect', 'read_text', 'read_bytes', 'write_text', 'write_bytes'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', '')
                self.assertNotIn(name, forbidden)
        self.assertEqual(set(imports), {'re', 'cog_core'})
        for node in tree.body:
            if isinstance(node, ast.Import):
                self.assertNotIn('cog_core', [alias.name for alias in node.names])

    def test_published_example(self):
        bundle = json.loads((ROOT / 'examples' / 'sample-bundle.json').read_text(encoding='utf-8'))
        expected = json.loads((ROOT / 'context' / 'output-example.json').read_text(encoding='utf-8'))
        self.success(bundle, expected)


if __name__ == '__main__':
    unittest.main()
