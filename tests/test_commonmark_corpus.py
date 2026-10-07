"""Official corpus and independently specified adapter projections."""
from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('corpus_validator', ROOT/'scripts/validate_phase0.py')
assert spec and spec.loader
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
CORPUS = json.loads((ROOT/'tests/fixtures/commonmark-0.31.2-spec.json').read_text(encoding='utf-8'))


class CommonMarkCorpusTests(unittest.TestCase):
    def test_official_html_semantics(self):
        for case in CORPUS:
            with self.subTest(example=case['example'], section=case['section']):
                actual = v.PARSER.render(case['markdown'])
                # An empty quote has no text: this newline is renderer formatting.
                actual = actual.replace('<blockquote></blockquote>', '<blockquote>\n</blockquote>')
                self.assertEqual(case['html'], actual)

    def test_adapter_against_explicit_official_example_projections(self):
        # Expected headings/prose are hand checked against the supplied HTML,
        # with code/HTML/metadata exclusions and Setext policy applied.
        expected = {
            19: ((), ''), 23: ((), 'foo'), 24: ((), ''), 35: ((), ''),
            42: ((), '`one\ntwo`'), 49: ((), 'Foo ***'), 51: ((), ''),
            62: (('foo',), '\n'.join(['foo']*6)), 63: ((), '####### foo'),
            65: ((), '## foo'), 69: ((), ''), 70: ((), 'foo # bar'),
            84: ((), ''), 126: ((), ''), 164: ((), ''), 170: ((), 'okay'),
            171: ((), ''), 189: ((), ''), 204: ((), 'foo'), 205: ((), 'Foo'),
            206: ((), 'αγω'), 211: ((), '[foo]'), 218: ((), 'foo'),
            296: ((), 'foo\nbar'), 328: ((), ''), 329: ((), ''),
            330: ((), ''), 332: ((), ''), 344: ((), '`'),
            346: ((), 'https://foo.bar.`baz`'), 348: ((), '`foo'),
            354: ((), '*$*alpha.\n*£*bravo.\n*€*charlie.'),
            356: ((), '5678'), 360: ((), 'foo_bar_'),
            481: ((), '__ahttps://foo.bar/?q=__'), 482: ((), 'link'),
            510: ((), 'link'), 511: ((), '[link] (/uri)'),
            539: ((), 'foo'), 540: ((), 'ẞ'),
        }
        for case in CORPUS:
            if case['example'] in expected:
                with self.subTest(example=case['example']):
                    headings, prose = expected[case['example']]
                    doc = v.parse_document(case['markdown'])
                    self.assertEqual(headings, tuple(h.title for h in doc.headings))
                    self.assertEqual(prose, '\n'.join(p.text for p in doc.prose))


if __name__ == '__main__':
    unittest.main()
