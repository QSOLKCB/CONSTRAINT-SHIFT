from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_phase0.py"

spec = importlib.util.spec_from_file_location("validate_phase0", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def contract_texts() -> dict[str, str]:
    return {relative: module.read_text(relative) for relative in module.REQUIRED_FILES}


class Phase0ContractTests(unittest.TestCase):
    def test_repository_contract_passes(self) -> None:
        self.assertEqual([], module.validate_repo())

    def test_markdown_hypotheses_exactly_match_contract(self) -> None:
        headings = module.hypothesis_headings(module.read_text("HYPOTHESES.md"))
        self.assertEqual(module.HYPOTHESES, headings)

    def test_duplicate_hypothesis_heading_is_rejected(self) -> None:
        texts = contract_texts()
        texts["HYPOTHESES.md"] += "\n## H1 — Specification Primacy\n"
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("hypothesis headings must exactly match" in error for error in errors),
            errors,
        )

    def test_missing_required_terminology_is_rejected(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = texts["TERMINOLOGY.md"].replace(
            "## Machine Verifiability",
            "### Machine Verifiability",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertIn(
            "missing terminology definition: Machine Verifiability",
            errors,
        )

    def test_fenced_level2_heading_is_ignored(self) -> None:
        texts = contract_texts()
        fence = chr(96) * 3
        texts["TERMINOLOGY.md"] += (
            f"\n{fence}markdown\n"
            "## Example subsection\n"
            "This is example content, not a contract heading.\n"
            f"{fence}\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_invalid_suffixed_fence_marker_does_not_close(self) -> None:
        texts = contract_texts()
        fence = chr(96) * 3
        texts["TERMINOLOGY.md"] += (
            f"\n{fence}markdown\n"
            f"{fence}not-a-close\n"
            "## Example subsection\n"
            f"{fence}\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_tilde_fenced_level2_heading_is_ignored(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] += (
            "\n~~~markdown\n"
            "## Another example\n"
            "~~~\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_indented_level2_heading_is_accepted(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = texts["TERMINOLOGY.md"].replace(
            "## Machine Verifiability",
            "  ## Machine Verifiability",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_invariant_headings_exactly_match_contract(self) -> None:
        headings = module.invariant_headings(module.read_text("INVARIANTS.md"))
        self.assertEqual(module.INVARIANTS, headings)

    def test_invariant_identifier_in_comment_does_not_satisfy_contract(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += "\n<!-- Former label: I14 — -->\n"
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_multiline_html_comment_cannot_hide_invariant_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n<!--\n"
            "## I14 — Contract changes are explicit\n"
            "-->\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_raw_html_pre_block_cannot_hide_invariant_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n<pre>\n"
            "## I14 — Contract changes are explicit\n"
            "</pre>\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_raw_html_div_block_ignores_level2_heading(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] += (
            "\n<div>\n"
            "## Example subsection\n"
            "</div>\n"
            "\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_tab_delimited_pre_block_cannot_hide_invariant_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n<pre\tclass=\"x\">\n"
            "## I14 — Contract changes are explicit\n"
            "</pre>\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_generic_html_tag_does_not_interrupt_paragraph(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = texts["TERMINOLOGY.md"].replace(
            "\n\n## Machine Verifiability",
            "\n<span>\n## Machine Verifiability",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_comment_marker_inside_code_span_is_literal(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = (
            "Use the literal marker `<!--` here.\n\n"
            + texts["TERMINOLOGY.md"]
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_multiline_code_span_masks_comment_marker(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = (
            "Use ``code\n"
            "and <!-- marker\n"
            "continues`` here.\n\n"
            + texts["TERMINOLOGY.md"]
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_thematic_break_does_not_open_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n---\n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n"
            "\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_list_item_fence_hides_nested_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        fence = chr(96) * 3
        texts["INVARIANTS.md"] += (
            f"\n- {fence}markdown\n"
            "  ## I14 — Contract changes are explicit\n"
            f"  {fence}\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_type1_html_requires_exact_closer(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n<pre>\n"
            "</pre >\n"
            "## I14 — Contract changes are explicit\n"
            "</pre>\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_unclosed_code_span_cannot_cross_blank_line(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] = (
            "`unclosed\n\n"
            + texts["TERMINOLOGY.md"]
            + "\nclosing `"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_asterisk_thematic_break_does_not_open_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n***\n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_ordered_list_fence_hides_nested_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        fence = chr(96) * 3
        texts["INVARIANTS.md"] += (
            f"\n1. {fence}markdown\n"
            "   ## I14 — Contract changes are explicit\n"
            f"   {fence}\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_indented_paragraph_continuation_keeps_paragraph_open(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\nparagraph\n"
            "    continuation\n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_escaped_backticks_do_not_form_code_span(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n\\`<!--\\`\n"
            "## I14 — Contract changes are explicit\n"
            "-->\n"
        )
        # This is a visible ATX heading in the pinned CommonMark dialect.
        self.assertEqual([], module.validate_texts(texts))

    def test_nested_fence_dedent_reprocesses_top_level_opener(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        fence = chr(96) * 3
        texts["INVARIANTS.md"] += (
            f"\n- {fence}markdown\n"
            "  sample\n"
            f"{fence}\n"
            "## I14 — Contract changes are explicit\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_ordered_list_start_two_does_not_interrupt_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\nparagraph\n"
            "2. ~~~markdown\n"
            "   ## I14 — Contract changes are explicit\n"
            "   ~~~\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_tab_expanded_list_fence_uses_visual_columns(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n1.\t~~~markdown\n"
            "   ## I14 — Contract changes are explicit\n"
            "   ~~~\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_link_reference_metadata_does_not_satisfy_prose_checks(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: / "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

        texts = contract_texts()
        texts["README.md"] = texts["README.md"].replace(
            "The thesis is **not treated as established fact**",
            "The thesis remains a research proposition",
            1,
        )
        texts["README.md"] += (
            '\n[hidden]: / "The thesis is **not treated as established fact**"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn(
            "README must explicitly separate thesis from established fact",
            errors,
        )

    def test_multiline_reference_destination_is_hidden_metadata(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]:\n"
            '  /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_reference_looking_line_inside_paragraph_remains_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '[note]: / "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_filtered_fence_preserves_reference_block_boundary(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        fence = chr(96) * 3
        texts["ROADMAP.md"] += (
            "\nordinary paragraph\n"
            f"{fence}\n"
            "code\n"
            f"{fence}\n"
            '[hidden]: /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_balanced_parenthesis_reference_destination_is_hidden(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: (url) "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_multiline_reference_destination_stops_at_block_start(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]:\n"
            "# machine-checkable Phase 0 validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_reference_label_uses_first_unescaped_closing_bracket(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[foo\\]:<bar]: /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_escaped_reference_title_closer_remains_visible_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]:\n"
            "  /url\n"
            '"machine-checkable Phase 0 validator\\\"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_backslash_space_does_not_escape_reference_destination(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: /foo\\ bar "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_unescaped_opening_bracket_invalidates_reference_label(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[foo[bar]: /url "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_inline_reference_title_requires_whitespace_after_destination(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: <url>"machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_multiline_reference_title_is_hidden_metadata(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]: /url\n"
            '"machine-checkable Phase 0 validator\n'
            'continued"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_ordered_list_stops_multiline_reference_destination(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]:\n"
            '1. "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_type7_angle_tag_can_be_multiline_reference_destination(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[hidden]:\n"
            "<url>\n"
            '"machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_inline_multiline_reference_title_is_hidden(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: /url "machine-checkable Phase 0 validator\n'
            'continued"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_first_unescaped_closing_bracket_invalidates_reference_label(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[foo]bar]: /url "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_blank_ordered_list_item_does_not_interrupt_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\nparagraph\n"
            "1. \n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_indented_code_does_not_satisfy_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n    machine-checkable Phase 0 validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_generic_closing_tag_with_attributes_is_not_raw_html(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n</span foo>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_standalone_equals_marker_starts_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n=\n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_generic_html_tag_allows_gt_inside_quoted_attribute(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            '\n<span title=">">\n'
            "## I14 — Contract changes are explicit\n\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_indented_list_continuation_counts_as_rendered_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- item\n"
            "    machine-checkable Phase 0 validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_nbsp_is_list_item_content_not_blank_whitespace(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\nparagraph\n"
            "1. \u00a0\n"
            "<span>\n"
            "## I14 — Contract changes are explicit\n\n"
        )
        # This is a visible ATX heading in the pinned CommonMark dialect.
        self.assertEqual([], module.validate_texts(texts))

    def test_nbsp_after_multiline_reference_title_invalidates_definition(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[hidden]: /url "machine-checkable Phase 0 validator\n'
            'continued"\u00a0\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_nested_list_indented_code_does_not_count_as_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- # item\n"
            "      machine-checkable Phase 0 validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_newline_padding_does_not_satisfy_artifact_size(self) -> None:
        texts = contract_texts()
        texts["METHODOLOGY.md"] = "x" + "\n" * 79
        errors = module.validate_texts(texts)
        self.assertIn(
            "required artifact is suspiciously small: METHODOLOGY.md",
            errors,
        )

    def test_nbsp_preserves_list_continuation_state(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- item\n"
            "  \u00a0\n"
            "    machine-checkable Phase 0 validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_nested_list_paragraph_continuation_uses_innermost_column(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- - item\n"
            "      machine-checkable Phase 0 validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_list_reference_definition_does_not_open_paragraph(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- [foo]: /foo\n"
            '[hidden]: /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_multiline_reference_definition_inside_list_is_hidden(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- [hidden]:\n"
            '  /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_dedented_lazy_continuation_preserves_list_paragraph(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- item\n"
            '[hidden]: /url "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_thematic_break_is_not_nested_list_chain(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- - -\n"
            "        machine-checkable Phase 0 validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_nested_ordered_list_cannot_interrupt_open_list_paragraph(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- paragraph\n"
            "  2. # heading\n"
            "         machine-checkable Phase 0 validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_raw_html_block_inside_list_hides_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n- <div>\n"
            "  ## I14 — Contract changes are explicit\n"
            "  </div>\n\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_fenced_code_nested_through_multiple_list_markers_is_hidden(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n- - ~~~\n"
            "    machine-checkable Phase 0 validator\n"
            "    ~~~\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_level2_heading_inside_list_satisfies_contract(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_soft_line_break_is_normalized_in_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "machine-checkable Phase 0\nvalidator",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_heading_extraction_preserves_paragraph_state(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "paragraph\n2. ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_five_space_list_padding_leaves_code_indent(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "-     ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_list_reference_tab_padding_resolves_definition(self) -> None:
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
        self.assertIn("roadmap does not require Phase 0 validator",
                      module.validate_texts(texts))

    def test_list_generic_html_resets_outer_paragraph_state(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\nparagraph\n"
            "- <span>\n"
            "  ## I14 — Contract changes are explicit\n\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_dedent_ends_list_scoped_raw_html(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n- <div>\n"
            "## I14 — Contract changes are explicit\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_tab_marker_padding_keeps_heading_as_code(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "-\t  ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_blockquote_raw_html_hides_nested_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n> <div>\n"
            "> ## I14 — Contract changes are explicit\n"
            ">\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_reference_definition_does_not_open_heading_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "[hidden]: /url\n2. ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_nested_tab_padding_keeps_inner_heading_visible(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- -\t  ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_blockquote_fence_hides_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n> ~~~\n"
            "> ## I14 — Contract changes are explicit\n"
            "> ~~~\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_first_line_list_code_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += "\n-     machine-checkable Phase 0 validator\n"
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_whitespace_only_reference_label_is_not_hidden(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[ ]: /url "machine-checkable Phase 0 validator"\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_blockquote_comment_ends_on_dedent(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n> <!--\n"
            "## I14 — Contract changes are explicit\n"
            "-->\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_blockquote_reference_definition_is_hidden_metadata(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n> [hidden]: /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_inline_link_title_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[visible](/url "machine-checkable Phase 0 validator")\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_multiline_reference_definition_resets_heading_state(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "[hidden]:\n/url\n2. ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_raw_html_container_replacement_exposes_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n- <div>\n"
            "> ## I14 — Contract changes are explicit\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_unicode_only_list_paragraph_blocks_nested_ordered_two(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- \u00a0\n  2. ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_lazy_dedent_updates_after_visible_list_continuation(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- \u00a0\n  ordinary paragraph\n2. ## I14 — Contract changes are explicit",
            1,
        )
        # This is a visible ATX heading in the pinned CommonMark dialect.
        self.assertEqual([], module.validate_texts(texts))

    def test_quoted_list_dedent_is_measured_inside_quote(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "> - \u00a0\n>   2. ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_fresh_blockquote_resets_outer_paragraph_for_ordered_two(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "paragraph\n> 2. ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_repeated_ordered_two_cannot_interrupt_open_list_paragraph(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- \u00a0\n"
            "  2. ## I14 — Contract changes are explicit\n"
            "  2. ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_nested_quote_ends_list_paragraph_before_reference_definition(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n> - item\n'
            '> > [hidden]: /url "machine-checkable Phase 0 validator"\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_lazy_quoted_list_dedent_retains_quote_owner(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "> - item\n> 2. ## I14 — Contract changes are explicit",
            1,
        )
        # This is a visible ATX heading in the pinned CommonMark dialect.
        self.assertEqual([], module.validate_texts(texts))

    def test_mixed_quote_list_fence_hides_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "## Contract changes are explicit",
            1,
        )
        texts["INVARIANTS.md"] += (
            "\n> - ~~~\n"
            ">   ## I14 — Contract changes are explicit\n"
            ">   ~~~\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_quoted_soft_break_satisfies_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> machine-checkable Phase 0\n"
            "> validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_unresolved_reference_syntax_remains_visible_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[visible][machine-checkable Phase 0 validator]\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_quoted_indented_code_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n>     machine-checkable Phase 0 validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_inline_html_attribute_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\nvisible <span title="machine-checkable Phase 0 validator">'
            'text</span>\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_sibling_list_item_ends_nested_fence(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "- - ~~~\n-   ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_reference_definition_after_fence_resolves_inline_reference(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[visible][machine-checkable Phase 0 validator]\n\n"
            "```\ncode\n```\n"
            "[machine-checkable Phase 0 validator]: /url\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_lazy_blockquote_soft_break_satisfies_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> machine-checkable Phase 0\n"
            "validator\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_escaped_inline_html_remains_visible_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n\\<span title="machine-checkable Phase 0 validator">\n'
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_list_interrupt_keeps_required_words_in_separate_blocks(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\nmachine-checkable Phase 0\n"
            "- validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_resolved_reference_with_escaped_bracket_hides_label_metadata(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[visible][machine-checkable Phase 0 validator\\]]\n\n"
            "[machine-checkable Phase 0 validator\\]]: /url\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_quoted_indented_code_after_paragraph_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\nordinary paragraph\n"
            ">     machine-checkable Phase 0 validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_unquoted_blank_ends_quote_scoped_fence_for_reference_definition(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[visible][machine-checkable Phase 0 validator]\n\n"
            "> ```\n"
            "\n"
            "> [machine-checkable Phase 0 validator]: /url\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_lazy_quote_ordered_two_keeps_marker_literal(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> machine-checkable Phase 0\n"
            "2. validator\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_unquoted_blank_ends_quote_scoped_raw_html(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "> <pre>\n\n"
            "> ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_unquoted_blank_ends_quote_scoped_html_comment(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "> <!--\n\n"
            "> ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_markdown_escape_decodes_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "machine\\-checkable Phase 0 validator",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_quoted_multiline_code_span_cannot_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> `machine-checkable Phase 0\n"
            "> validator`\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_oversized_reference_label_remains_visible_prose(self) -> None:
        required = "machine-checkable Phase 0 validator"
        label = ("a" * 1000) + required
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            required,
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            f"\n[visible][{label}]\n\n"
            f"[{label}]: /url\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_multiline_inline_link_title_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            '\n[visible](/url "machine-checkable Phase 0\n'
            'validator")\n'
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_unicode_line_separator_cannot_create_invariant_heading(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "ordinary\u0085## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_quote_tab_padding_keeps_heading_as_code(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            ">\t  ## I14 — Contract changes are explicit",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_nested_quote_marker_after_tab_keeps_heading_visible(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] = texts["INVARIANTS.md"].replace(
            "## I14 — Contract changes are explicit",
            "> \t> ## I14 — Contract changes are explicit",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_oversized_reference_use_remains_visible(self) -> None:
        required = "machine-checkable Phase 0 validator"
        oversized = (" " * 1000) + required
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            required,
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            f"\n[visible][{oversized}]\n\n"
            f"[{required}]: /url\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_link_text_escape_satisfies_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[machine\\-checkable Phase 0 validator](/url)\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_invalid_multiline_link_remains_visible_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n[visible](/url machine-checkable Phase 0\n"
            "validator)\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_lazy_quoted_multiline_code_span_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> prefix\n"
            "`machine-checkable Phase 0\n"
            "> validator`\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_lazy_quoted_inline_comment_does_not_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "Phase 0 validator",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n> visible <!--\n"
            "machine-checkable Phase 0 validator -->\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_reference_after_pre_closer_resolves(self) -> None:
        required = "machine-checkable Phase 0 validator"
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            required,
            f"[visible][{required}]",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n<pre>\nstuff\n</pre>\n"
            f"[{required}]: /url\n"
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_same_shape_sibling_duplicate_invariant_is_rejected(self) -> None:
        texts = contract_texts()
        texts["INVARIANTS.md"] += (
            "\n- ~~~\n"
            "- ## I14 — Contract changes are explicit\n"
        )
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

    def test_backslash_before_code_closer_cannot_satisfy_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "`machine-checkable Phase 0 validator\\`",
            1,
        )
        errors = module.validate_texts(texts)
        self.assertIn("roadmap does not require Phase 0 validator", errors)

    def test_malformed_link_literal_can_satisfy_required_prose(self) -> None:
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            "machine-checkable Phase 0 validator",
            "[visible](machine-checkable Phase 0 validator)",
            1,
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_equivalent_emphasis_and_entity_prose_is_accepted(self) -> None:
        required = "machine-checkable Phase 0 validator"

        entity_texts = contract_texts()
        entity_texts["ROADMAP.md"] = entity_texts["ROADMAP.md"].replace(
            required,
            "machine&#45;checkable Phase 0 validator",
            1,
        )
        self.assertEqual([], module.validate_texts(entity_texts))

        emphasis_texts = contract_texts()
        emphasis_texts["ROADMAP.md"] = emphasis_texts["ROADMAP.md"].replace(
            required,
            "**machine-checkable** Phase 0 validator",
            1,
        )
        self.assertEqual([], module.validate_texts(emphasis_texts))

        readme_texts = contract_texts()
        readme_texts["README.md"] = readme_texts["README.md"].replace(
            "**not treated as established fact**",
            "__not treated as established fact__",
            1,
        )
        self.assertEqual([], module.validate_texts(readme_texts))

    def test_hidden_pre_reference_definition_does_not_resolve(self) -> None:
        required = "machine-checkable Phase 0 validator"
        texts = contract_texts()
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            required,
            f"[visible][{required}]",
            1,
        )
        texts["ROADMAP.md"] += (
            "\n<pre>\n\n"
            f"[{required}]: /url\n"
            "</pre>\n"
        )
        self.assertEqual([], module.validate_texts(texts))

    def test_roadmap_heading_in_fence_does_not_satisfy_contract(self) -> None:
        texts = contract_texts()
        required = "## Phase 0 — Foundational Research Contract"
        texts["ROADMAP.md"] = texts["ROADMAP.md"].replace(
            required,
            "## Phase Zero",
            1,
        )
        fence = chr(96) * 3
        texts["ROADMAP.md"] += f"\n{fence}markdown\n{required}\n{fence}\n"
        errors = module.validate_texts(texts)
        self.assertIn(
            "roadmap does not define exactly one Phase 0 foundational contract",
            errors,
        )

    def test_all_documented_terminology_headings_are_required(self) -> None:
        terminology = module.read_text("TERMINOLOGY.md")
        self.assertEqual(module.TERMS, module.terminology_headings(terminology))

    def test_required_files_are_repo_relative(self) -> None:
        for relative in module.REQUIRED_FILES:
            path = Path(relative)
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)


if __name__ == "__main__":
    unittest.main()
