"""Behavioral regressions and controls from the f5b9b2f review."""

from pathlib import Path
import importlib.util
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reviewed_validator", REPO / "scripts/validate_phase0.py"
)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

PHRASE = "machine-checkable Phase 0 validator"
HEADING = "I14 — Contract changes are explicit"
ROADMAP_ERROR = "roadmap does not require Phase 0 validator"
CODE_WITH_BACKSLASH = "`" + PHRASE + "\\`"
MALFORMED_LINK = "[visible](" + PHRASE + ")"


def texts():
    return {name: validator.read_text(name) for name in validator.REQUIRED_FILES}


def roadmap_errors(replacement):
    contract = texts()
    assert contract["ROADMAP.md"].count(PHRASE) == 1
    contract["ROADMAP.md"] = contract["ROADMAP.md"].replace(PHRASE, replacement)
    return validator.validate_texts(contract)


def ghost_reference(opener, closer):
    return (
        f"[visible][{PHRASE}]\n\n{opener}\n\n"
        f"[{PHRASE}]: /url\n{closer}\n"
    )


class ReviewFindings(unittest.TestCase):
    def test_r1_sibling_fence_heading_is_visible(self):
        self.assertIn(HEADING, validator.markdown_level2_headings(f"- ~~~\n- ## {HEADING}\n"))

    def test_r1_sibling_html_heading_is_visible(self):
        self.assertIn(HEADING, validator.markdown_level2_headings(f"- <div>\n- ## {HEADING}\n"))

    def test_r1_sibling_comment_heading_is_visible(self):
        self.assertIn(HEADING, validator.markdown_level2_headings(f"- <!--\n- ## {HEADING}\n"))

    def test_r1_duplicate_in_sibling_item_is_rejected(self):
        contract = texts()
        contract["INVARIANTS.md"] += f"\n- ~~~\n- ## {HEADING}\n"
        self.assertTrue(any("invariant headings must exactly match" in e for e in validator.validate_texts(contract)))

    def test_r2_code_span_backslash_does_not_expose_prose(self):
        self.assertNotIn(PHRASE, validator.markdown_rendered_prose_text(CODE_WITH_BACKSLASH))

    def test_r2_code_only_roadmap_statement_is_rejected(self):
        self.assertIn(ROADMAP_ERROR, roadmap_errors(CODE_WITH_BACKSLASH))

    def test_r3_malformed_link_destination_remains_visible(self):
        self.assertIn(PHRASE, validator.markdown_rendered_prose_text(MALFORMED_LINK))

    def test_r3_roadmap_malformed_link_literal_is_accepted(self):
        self.assertEqual([], roadmap_errors(MALFORMED_LINK))

    def test_r4_entity_is_decoded_in_prose(self):
        self.assertIn(PHRASE, validator.markdown_rendered_prose_text("machine&#45;checkable Phase 0 validator"))

    def test_r4_emphasis_is_decoded_in_prose(self):
        self.assertIn(PHRASE, validator.markdown_rendered_prose_text("**machine-checkable** Phase 0 validator"))

    def test_r4_readme_equivalent_strong_delimiters_are_accepted(self):
        contract = texts()
        contract["README.md"] = contract["README.md"].replace(
            "**not treated as established fact**", "__not treated as established fact__"
        )
        self.assertEqual([], validator.validate_texts(contract))

    def test_r5_reference_inside_pre_does_not_resolve(self):
        self.assertIn(PHRASE, validator.markdown_rendered_prose_text(ghost_reference("<pre>", "</pre>")))

    def test_r5_reference_inside_comment_does_not_resolve(self):
        self.assertIn(PHRASE, validator.markdown_rendered_prose_text(ghost_reference("<!--", "-->")))

    def test_r5_roadmap_ghost_reference_is_accepted(self):
        contract = texts()
        contract["ROADMAP.md"] = contract["ROADMAP.md"].replace(PHRASE, f"[visible][{PHRASE}]")
        contract["ROADMAP.md"] += f"\n<pre>\n\n[{PHRASE}]: /url\n</pre>\n"
        self.assertEqual([], validator.validate_texts(contract))


class ControlCases(unittest.TestCase):
    def test_same_list_item_fence_keeps_heading_hidden(self):
        self.assertNotIn(HEADING, validator.markdown_level2_headings(f"- ~~~\n  ## {HEADING}\n  ~~~\n"))

    def test_valid_link_title_stays_hidden(self):
        self.assertNotIn(PHRASE, validator.markdown_rendered_prose_text(f'[visible](/url "{PHRASE}")'))

    def test_ordinary_inline_code_stays_hidden(self):
        self.assertNotIn(PHRASE, validator.markdown_rendered_prose_text(f"`{PHRASE}`"))

    def test_real_reference_resolves_and_hides_metadata_label(self):
        self.assertNotIn(PHRASE, validator.markdown_rendered_prose_text(f"[visible][{PHRASE}]\n\n[{PHRASE}]: /url\n"))


if __name__ == "__main__":
    unittest.main()
