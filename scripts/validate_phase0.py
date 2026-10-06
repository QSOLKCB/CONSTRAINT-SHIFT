#!/usr/bin/env python3
"""Validate the Phase 0 CONSTRAINT-SHIFT research contract."""

from __future__ import annotations

from pathlib import Path
import re
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
    "Specification Primacy",
    "Implementation Fungibility",
    "AI Language Fitness",
    "Machine Verifiability",
    "Diagnostic Feedback Quality",
    "Legacy Preservation Paradox",
    "Second Modding Revolution",
    "Modding Mutation Rate",
    "Recombination Acceleration",
    "Tool Legitimacy Gap",
    "AI Disclosure Penalty",
    "Research Contract",
)

INVARIANT_PREFIXES = tuple(f"I{i} —" for i in range(1, 15))
HYPOTHESIS_HEADING_RE = re.compile(r"^H\d+ — .+$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing required file: {relative}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise AssertionError(f"required file is empty: {relative}")
    return text


def load_contract_texts() -> tuple[dict[str, str], list[str]]:
    texts: dict[str, str] = {}
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        try:
            texts[relative] = read_text(relative)
        except AssertionError as exc:
            errors.append(str(exc))

    return texts, errors


def markdown_level2_headings(text: str) -> tuple[str, ...]:
    """Return level-2 ATX headings outside fenced code blocks."""
    headings: list[str] = []
    fence_char: str | None = None
    fence_len = 0

    for line in text.splitlines():
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            marker_char = marker[0]
            marker_len = len(marker)

            if fence_char is None:
                fence_char = marker_char
                fence_len = marker_len
                continue

            if marker_char == fence_char and marker_len >= fence_len:
                fence_char = None
                fence_len = 0
                continue

        if fence_char is not None:
            continue

        if line.startswith("## ") and not line.startswith("### "):
            heading = line[3:].strip()
            if heading:
                headings.append(heading)

    return tuple(headings)


def hypothesis_headings(text: str) -> tuple[str, ...]:
    return tuple(
        heading
        for heading in markdown_level2_headings(text)
        if HYPOTHESIS_HEADING_RE.fullmatch(heading)
    )


def terminology_headings(text: str) -> tuple[str, ...]:
    return markdown_level2_headings(text)


def validate_texts(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []

    missing = [relative for relative in REQUIRED_FILES if relative not in texts]
    if missing:
        errors.extend(f"missing required file: {relative}" for relative in missing)
        return errors

    observed_hypotheses = hypothesis_headings(texts["HYPOTHESES.md"])
    if observed_hypotheses != HYPOTHESES:
        errors.append(
            "hypothesis headings must exactly match the Phase 0 contract "
            f"(expected {HYPOTHESES!r}, observed {observed_hypotheses!r})"
        )

    observed_terms = terminology_headings(texts["TERMINOLOGY.md"])
    if observed_terms != TERMS:
        for term in TERMS:
            if term not in observed_terms:
                errors.append(f"missing terminology definition: {term}")
        duplicates = tuple(
            term for term in observed_terms if observed_terms.count(term) > 1
        )
        if duplicates:
            errors.append(
                "duplicate terminology definitions: "
                + ", ".join(dict.fromkeys(duplicates))
            )
        unexpected = tuple(term for term in observed_terms if term not in TERMS)
        if unexpected:
            errors.append(
                "unexpected terminology definitions: "
                + ", ".join(unexpected)
            )
        if not any(
            error.startswith(
                (
                    "missing terminology definition:",
                    "duplicate terminology definitions:",
                    "unexpected terminology definitions:",
                )
            )
            for error in errors
        ):
            errors.append(
                "terminology headings must exactly match the Phase 0 contract "
                f"(expected {TERMS!r}, observed {observed_terms!r})"
            )

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


def validate_repo() -> list[str]:
    texts, errors = load_contract_texts()
    if errors:
        return errors
    return validate_texts(texts)


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
