"""Behavioral policy, recurring review failures, CLI and performance checks."""
from pathlib import Path
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract_validator', ROOT / 'scripts/validate_phase0.py')
assert spec and spec.loader
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
PHRASE = 'machine-checkable Phase 0 validator'
ERROR = 'roadmap does not require Phase 0 validator'
HEADING = 'I14 — Contract changes are explicit'


def texts():
    return {p: v.read_text(p) for p in v.REQUIRED_FILES}


def roadmap_errors(fragment):
    contract = texts()
    contract['ROADMAP.md'] = contract['ROADMAP.md'].replace(PHRASE, 'removed') + '\n\n' + fragment
    return v.validate_texts(contract)


class MarkdownContractTests(unittest.TestCase):
    def test_current_review_comment_container_exit(self):
        fragment = f'[visible][{PHRASE}]\n\n> <!--\n[{PHRASE}]: /url'
        self.assertIn(ERROR, roadmap_errors(fragment))

    def test_current_review_numeric_entity_requires_semicolon(self):
        self.assertIn(ERROR, roadmap_errors('machine&#45checkable Phase 0 validator'))
        self.assertEqual([], roadmap_errors('machine&#45;checkable Phase 0 validator'))

    def test_current_review_underscore_flanking(self):
        self.assertIn(ERROR, roadmap_errors('machine__-checkable__ Phase 0 validator'))
        self.assertEqual([], roadmap_errors('__machine-checkable__ Phase 0 validator'))

    def test_current_review_heading_cannot_lazily_continue_comment(self):
        self.assertEqual([], roadmap_errors(f'> ## heading <!--\n{PHRASE} -->'))
        self.assertIn(ERROR, roadmap_errors(f'> paragraph <!--\n{PHRASE} -->'))

    def test_excluded_content_cannot_satisfy_or_manufacture_phrase(self):
        hidden = [f'`{PHRASE}`', f'    {PHRASE}', f'~~~\n{PHRASE}\n~~~',
                  f'![{PHRASE}](/url)', f'<!-- {PHRASE} -->',
                  f'<pre>\n{PHRASE}\n</pre>', f'[visible](/url "{PHRASE}")',
                  f'[hidden]: /url "{PHRASE}"',
                  'machine`code`-checkable Phase 0 validator',
                  'machine![alt](/url)-checkable Phase 0 validator',
                  'machine<!-- hidden -->-checkable Phase 0 validator',
                  'machine<span>-checkable</span> Phase 0 validator']
        for source in hidden:
            with self.subTest(source=source):
                self.assertIn(ERROR, roadmap_errors(source))

    def test_text_blocks_never_join(self):
        for source in ['machine-checkable Phase 0\n\nvalidator',
                       '- machine-checkable Phase 0\n- validator',
                       '## machine-checkable Phase 0\n## validator',
                       '> machine-checkable Phase 0\n\nvalidator',
                       'machine-checkable Phase 0\n\n> validator']:
            with self.subTest(source=source):
                self.assertIn(ERROR, roadmap_errors(source))
        self.assertEqual([], roadmap_errors('machine-checkable Phase 0\nvalidator'))

    def test_heading_policy_accepts_decoded_atx_and_excludes_setext(self):
        self.assertEqual((HEADING,), v.markdown_level2_headings(
            '## **I14** &#8212; Contract changes are explicit'))
        self.assertEqual((), v.markdown_level2_headings(HEADING + '\n---'))
        self.assertIn(ERROR, roadmap_errors(PHRASE + '\n---'))
        for document, title, error in [('INVARIANTS.md',HEADING,'invariant headings'),
                                      ('HYPOTHESES.md','H1 — Specification Primacy','hypothesis headings')]:
            contract = texts()
            contract[document] += f'\n- ~~~\n- ## {title}\n'
            self.assertTrue(any(error in e for e in v.validate_texts(contract)))

    def test_generated_container_ownership_matrix(self):
        # Each marker starts a sibling item; indentation retains the same item.
        # These expected values follow the container rule, not parser output.
        for quote in ('', '> ', '> > '):
            for marker in ('- ', '+ ', '* ', '1. ', '2. ', '-\t', '1.\t'):
                for opener in ('~~~', '```', '<div>', '<pre>', '<!--', '<?x'):
                    indent = 4 if '\t' in marker else len(marker)
                    for sibling in (True, False):
                        prefix = marker if sibling else ' ' * indent
                        source = f'{quote}{marker}{opener}\n{quote}{prefix}## {HEADING}\n'
                        with self.subTest(source=source):
                            self.assertEqual(sibling, HEADING in v.markdown_level2_headings(source))

    def test_code_delimiter_backslash_matrix(self):
        for width in (1, 2, 3, 4):
            for backslashes in (0, 1, 2, 3):
                delimiter = '`' * width
                source = delimiter + PHRASE + '\\' * backslashes + delimiter
                with self.subTest(source=source):
                    self.assertIn(ERROR, roadmap_errors(source))

    def test_one_parse_per_required_file(self):
        with patch.object(v.PARSER, 'parse', wraps=v.PARSER.parse) as parse:
            self.assertEqual([], v.validate_texts(texts()))
        self.assertEqual(len(v.REQUIRED_FILES), parse.call_count)

    def test_bounded_long_paragraph(self):
        # A subprocess timeout bounds regressions without millisecond assumptions.
        code = """import importlib.util
s=importlib.util.spec_from_file_location('v', 'scripts/validate_phase0.py')
v=importlib.util.module_from_spec(s); s.loader.exec_module(v)
source='ordinary `code` continuation\\n' * 16000
prose=v.markdown_rendered_prose_text(source)
assert 'code' not in prose
assert prose.count('ordinary') == 16000
"""
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)


class FileAndCLITests(unittest.TestCase):
    def test_loading_failures_are_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in v.REQUIRED_FILES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(v.read_text(name), encoding='utf-8')
            for name, content, expected in [('README.md', b'', 'required file is empty'),
                                           ('README.md', b'\xff', 'cannot read required file')]:
                (root / name).write_bytes(content)
                with patch.object(v, 'ROOT', root):
                    self.assertTrue(any(expected in e for e in v.validate_repo()))
            (root / 'README.md').unlink()
            with patch.object(v, 'ROOT', root):
                self.assertIn('missing required file: README.md', v.validate_repo())
            (root / 'README.md').mkdir()
            with patch.object(v, 'ROOT', root):
                self.assertTrue(any('cannot read required file: README.md' in e for e in v.validate_repo()))

    def test_cli_success_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, '-B', str(ROOT/'scripts/validate_phase0.py')],
                                    cwd=temporary, capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('Phase 0 research contract: OK\n', result.stdout)

    def test_cli_failure_status_and_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'scripts').mkdir()
            shutil.copyfile(ROOT/'scripts/validate_phase0.py', root/'scripts/validate_phase0.py')
            for name in v.REQUIRED_FILES:
                target=root/name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(v.read_text(name), encoding='utf-8')
            for content, expected in [(b'', 'required file is empty: README.md'),
                                      (b'\xff', 'cannot read required file: README.md')]:
                (root/'README.md').write_bytes(content)
                result=subprocess.run([sys.executable,'-B',str(root/'scripts/validate_phase0.py')],
                                      capture_output=True,text=True,timeout=15)
                self.assertEqual(1,result.returncode)
                self.assertIn(expected,result.stderr)
                self.assertNotIn('Traceback',result.stderr)


if __name__ == '__main__':
    unittest.main()
