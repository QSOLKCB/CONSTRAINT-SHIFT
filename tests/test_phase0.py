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
