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

    def test_tilde_fenced_level2_heading_is_ignored(self) -> None:
        texts = contract_texts()
        texts["TERMINOLOGY.md"] += (
            "\n~~~markdown\n"
            "## Another example\n"
            "~~~\n"
        )
        self.assertEqual([], module.validate_texts(texts))

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
