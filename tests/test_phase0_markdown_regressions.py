from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_phase0.py"

spec = importlib.util.spec_from_file_location("validate_phase0_regressions", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def contract_texts() -> dict[str, str]:
    return {relative: module.read_text(relative) for relative in module.REQUIRED_FILES}


class MarkdownParserRegressionMatrix(unittest.TestCase):
    def test_heading_container_matrix(self) -> None:
        heading = "I14 — Contract changes are explicit"
        cases = (
            ("top-level", f"## {heading}", True),
            ("bullet", f"- ## {heading}", True),
            ("blockquote", f"> ## {heading}", True),
            ("ordered-one-interrupts", f"paragraph\n1. ## {heading}", True),
            ("ordered-two-does-not-interrupt", f"paragraph\n2. ## {heading}", False),
            ("four-space-padding", f"-    ## {heading}", True),
            ("five-space-padding-is-code", f"-     ## {heading}", False),
            ("tab-plus-two-spaces-is-code", f"-\t  ## {heading}", False),
        )

        for name, markdown, expected in cases:
            with self.subTest(name=name):
                headings = module.markdown_level2_headings(markdown)
                self.assertEqual(expected, heading in headings)

    def test_tab_overshoot_is_preserved(self) -> None:
        self.assertEqual(
            "    /url",
            module._strip_columns_prefix("\t  /url", 2),
        )

    def test_list_scoped_html_matrix(self) -> None:
        cases = (
            (
                "generic-html-after-interrupting-bullet",
                "paragraph\n- <span>\n  ## I14 — Contract changes are explicit\n\n",
                True,
            ),
            (
                "dedent-ends-list-html",
                "- <div>\n## I14 — Contract changes are explicit",
                False,
            ),
            (
                "indented-heading-stays-in-list-html",
                "- <div>\n  ## I14 — Contract changes are explicit\n\n",
                True,
            ),
        )

        for name, suffix, should_hide in cases:
            with self.subTest(name=name):
                texts = contract_texts()
                texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
                    "## I14 — Contract changes are explicit",
                    "## Contract changes are explicit",
                    1,
                )
                texts["INVARIANTS.md"] += "\n" + suffix
                errors = module.validate_texts(texts)
                has_invariant_error = any(
                    "invariant headings must exactly match" in error
                    for error in errors
                )
                self.assertEqual(should_hide, has_invariant_error)

    def test_blockquote_scoped_html_stays_active(self) -> None:
        markdown = (
            "> <div>\n"
            "> ## I14 — Contract changes are explicit\n"
            ">\n"
        )
        self.assertEqual((), module.markdown_level2_headings(markdown))

    def test_reference_definition_closes_paragraph_state(self) -> None:
        markdown = (
            "[hidden]: /url\n"
            "2. ## I14 — Contract changes are explicit\n"
        )
        self.assertIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_tab_marker_padding_preserves_visual_indent(self) -> None:
        context = module._list_item_context(
            "-\t  ## I14 — Contract changes are explicit"
        )
        self.assertIsNotNone(context)
        assert context is not None
        content_column, content = context
        self.assertEqual(2, content_column)
        self.assertTrue(content.startswith("    ##"))

    def test_nested_tab_padding_uses_outer_visual_column(self) -> None:
        heading = "I14 — Contract changes are explicit"
        markdown = f"- -\t  ## {heading}"
        self.assertIn(heading, module.markdown_level2_headings(markdown))

    def test_blockquote_fence_stays_active(self) -> None:
        markdown = (
            "> ~~~\n"
            "> ## I14 — Contract changes are explicit\n"
            "> ~~~\n"
        )
        self.assertEqual((), module.markdown_level2_headings(markdown))

    def test_first_line_list_code_not_rendered_prose(self) -> None:
        prose = module.markdown_rendered_prose_text(
            "-     machine-checkable Phase 0 validator"
        )
        self.assertNotIn("machine-checkable Phase 0 validator", prose)

    def test_whitespace_only_reference_label_is_visible(self) -> None:
        prose = module.markdown_rendered_prose_text(
            '[ ]: /url "machine-checkable Phase 0 validator"'
        )
        self.assertIn("machine-checkable Phase 0 validator", prose)

    def test_blockquote_comment_ends_on_container_exit(self) -> None:
        markdown = (
            "> <!--\n"
            "## I14 — Contract changes are explicit\n"
            "-->\n"
        )
        self.assertIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_blockquote_reference_definition_is_hidden(self) -> None:
        prose = module.markdown_rendered_prose_text(
            '> [hidden]: /url "machine-checkable Phase 0 validator"'
        )
        self.assertNotIn("machine-checkable Phase 0 validator", prose)

    def test_inline_link_title_is_not_rendered_prose(self) -> None:
        prose = module.markdown_rendered_prose_text(
            '[visible](/url "machine-checkable Phase 0 validator")'
        )
        self.assertEqual("visible", prose.strip())

    def test_multiline_reference_definition_resets_state(self) -> None:
        markdown = (
            "[hidden]:\n"
            "/url\n"
            "2. ## I14 — Contract changes are explicit\n"
        )
        self.assertIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_raw_html_container_identity_rejects_replacement(self) -> None:
        markdown = (
            "- <div>\n"
            "> ## I14 — Contract changes are explicit\n"
        )
        self.assertIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_unicode_only_list_paragraph_blocks_nested_ordered_two(self) -> None:
        markdown = (
            "- \u00a0\n"
            "  2. ## I14 — Contract changes are explicit\n"
        )
        self.assertNotIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_lazy_dedent_eligibility_updates_after_visible_continuation(self) -> None:
        markdown = (
            "- \u00a0\n"
            "  ordinary paragraph\n"
            "2. ## I14 — Contract changes are explicit\n"
        )
        self.assertNotIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_quoted_list_dedent_uses_container_relative_columns(self) -> None:
        markdown = (
            "> - \u00a0\n"
            ">   2. ## I14 — Contract changes are explicit\n"
        )
        self.assertNotIn(
            "I14 — Contract changes are explicit",
            module.markdown_level2_headings(markdown),
        )

    def test_paragraph_container_transition_matrix(self) -> None:
        heading = "I14 — Contract changes are explicit"
        cases = (
            (
                "fresh-quote-resets-outer-paragraph",
                f"paragraph\n> 2. ## {heading}\n",
                True,
            ),
            (
                "same-list-paragraph-rejects-first-two",
                f"- \u00a0\n  2. ## {heading}\n",
                False,
            ),
            (
                "same-list-paragraph-rejects-repeated-two",
                f"- \u00a0\n  2. ## {heading}\n  2. ## {heading}\n",
                False,
            ),
            (
                "quoted-list-paragraph-rejects-two",
                f"> - \u00a0\n>   2. ## {heading}\n",
                False,
            ),
            (
                "nested-quote-is-fresh-container",
                f"> - item\n> > 2. ## {heading}\n",
                True,
            ),
        )

        for name, markdown, expected_visible in cases:
            with self.subTest(name=name):
                headings = module.markdown_level2_headings(markdown)
                self.assertEqual(expected_visible, heading in headings)

    def test_nested_quote_ends_list_paragraph_before_reference(self) -> None:
        prose = module.markdown_rendered_prose_text(
            '> - item\n> > [hidden]: /url "machine-checkable Phase 0 validator"'
        )
        self.assertNotIn("machine-checkable Phase 0 validator", prose)

    def test_list_reference_tab_overshoot_stays_visible(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- [hidden]:\n"
            "\t  /url\n"
            '  "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))


if __name__ == "__main__":
    unittest.main()
