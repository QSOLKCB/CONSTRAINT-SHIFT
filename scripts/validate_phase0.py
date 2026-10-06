#!/usr/bin/env python3
"""Validate the Phase 0 CONSTRAINT-SHIFT research contract."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "HYPOTHESES.md",
    "INVARIANTS.md",
    "METHODOLOGY.md",
    "ROADMAP.md",
    "TERMINOLOGY.md",
    "research/specification-primacy.md",
    "research/language-selection.md",
    "research/legacy-preservation.md",
    "research/ai-modding.md",
    "research/tool-legitimacy-gap.md",
)

HYPOTHESES = (
    "H1 — Specification Primacy",
    "H2 — Verification Selection",
    "H3 — Legacy Preservation Paradox",
    "H4 — Modding Mutation",
    "H5 — Recombination Acceleration",
    "H6 — Tool Legitimacy Gap",
)

TERMS = (
    "Constraint Shift",
    "Implementation Fungibility",
    "AI Language Fitness",
    "Legacy Preservation Paradox",
    "Second Modding Revolution",
    "Tool Legitimacy Gap",
    "AI Disclosure Penalty",
)

INVARIANT_PREFIXES = tuple(f"I{i} —" for i in range(1, 15))


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing required file: {relative}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise AssertionError(f"required file is empty: {relative}")
    return text


def validate_repo() -> list[str]:
    errors: list[str] = []
    texts: dict[str, str] = {}

    for relative in REQUIRED_FILES:
        try:
            texts[relative] = read_text(relative)
        except AssertionError as exc:
            errors.append(str(exc))

    if errors:
        return errors

    for identifier in HYPOTHESES:
        if identifier not in texts["HYPOTHESES.md"]:
            errors.append(f"missing hypothesis contract: {identifier}")

    for term in TERMS:
        if f"## {term}" not in texts["TERMINOLOGY.md"]:
            errors.append(f"missing terminology definition: {term}")

    for prefix in INVARIANT_PREFIXES:
        if prefix not in texts["INVARIANTS.md"]:
            errors.append(f"missing research invariant: {prefix}")

    if "## Phase 0 — Foundational Research Contract" not in texts["ROADMAP.md"]:
        errors.append("roadmap does not define Phase 0 foundational contract")

    if "machine-checkable Phase 0 validator" not in texts["ROADMAP.md"]:
        errors.append("roadmap does not require Phase 0 validator")

    if "The thesis is **not treated as established fact**" not in texts["README.md"]:
        errors.append("README must explicitly separate thesis from established fact")

    for path, text in texts.items():
        if len(text.strip()) < 80:
            errors.append(f"required artifact is suspiciously small: {path}")

    return errors


def main() -> int:
    errors = validate_repo()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Phase 0 research contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
