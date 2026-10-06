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
        errors = module.validate_texts(texts)
        self.assertTrue(
            any("invariant headings must exactly match" in error for error in errors),
            errors,
        )

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
