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

INVARIANTS = (
    "I1 — No conclusion by model assertion",
    "I2 — Equivalent-task comparisons",
    "I3 — Preserve failures",
    "I4 — Record intervention",
    "I5 — Record environment",
    "I6 — Separate generation from verification",
    "I7 — Observable contracts before equivalence claims",
    "I8 — No predetermined language winner",
    "I9 — Negative results are publishable results",
    "I10 — Social experiments control the artifact",
    "I11 — Human-subject safeguards",
    "I12 — Motivation is not evidence",
    "I13 — Reproducible validators",
    "I14 — Contract changes are explicit",
)

HYPOTHESIS_HEADING_RE = re.compile(r"^H\d+ — .+$")
INVARIANT_HEADING_RE = re.compile(r"^I\d+ — .+$")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
RAW_HTML_TYPE1_OPEN_RE = re.compile(
    r"^ {0,3}<(?P<tag>script|pre|style|textarea)(?:[ \\t>]|$)",
    re.IGNORECASE,
)
RAW_HTML_BLOCK_TAGS = (
    "address", "article", "aside", "base", "basefont", "blockquote", "body",
    "caption", "center", "col", "colgroup", "dd", "details", "dialog", "dir",
    "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "header", "hr", "html", "iframe", "legend", "li", "link", "main", "menu",
    "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
    "search", "section", "summary", "table", "tbody", "td", "tfoot", "th",
    "thead", "title", "tr", "track", "ul",
)
RAW_HTML_BLOCK_TAG_RE = re.compile(
    r"^ {0,3}</?(?:" + "|".join(RAW_HTML_BLOCK_TAGS) + r")(?:[ \\t/>]|$)",
    re.IGNORECASE,
)
RAW_HTML_GENERIC_TAG_RE = re.compile(
    r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(?:[ \\t]+[^<>]*?)?/?>[ \\t]*$"
)


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


def _valid_fence_open(line: str) -> str | None:
    match = FENCE_OPEN_RE.match(line)
    if not match:
        return None

    marker = match.group(1)
    info = match.group(2)
    if marker[0] == "`" and "`" in info:
        return None
    return marker


def _mask_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Mask HTML comments with spaces while preserving source columns."""
    chars = list(line)
    cursor = 0

    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end == -1:
                for index in range(cursor, len(chars)):
                    chars[index] = " "
                return "".join(chars), True

            for index in range(cursor, end + 3):
                chars[index] = " "
            cursor = end + 3
            in_comment = False
            continue

        start = line.find("<!--", cursor)
        if start == -1:
            break

        end = line.find("-->", start + 4)
        if end == -1:
            for index in range(start, len(chars)):
                chars[index] = " "
            return "".join(chars), True

        for index in range(start, end + 3):
            chars[index] = " "
        cursor = end + 3

    return "".join(chars), in_comment


def _raw_html_block_start(line: str) -> tuple[str, str | None] | None:
    """Return the raw-HTML block mode and terminator, if one starts here."""
    type1 = RAW_HTML_TYPE1_OPEN_RE.match(line)
    if type1:
        return "tag", type1.group("tag").lower()

    if re.match(r"^ {0,3}<\\?", line):
        return "marker", "?>"

    if re.match(r"^ {0,3}<!\\[CDATA\\[", line):
        return "marker", "]]>"

    if re.match(r"^ {0,3}<![A-Z]", line):
        return "marker", ">"

    if RAW_HTML_BLOCK_TAG_RE.match(line):
        return "blank", None

    if RAW_HTML_GENERIC_TAG_RE.match(line):
        return "blank", None

    return None


def _raw_html_block_ends(line: str, mode: str, terminator: str | None) -> bool:
    if mode == "blank":
        return not line.strip()

    if mode == "marker":
        assert terminator is not None
        return terminator in line

    if mode == "tag":
        assert terminator is not None
        return re.search(
            rf"</{re.escape(terminator)}[ \\t]*>",
            line,
            re.IGNORECASE,
        ) is not None

    raise AssertionError(f"unknown raw HTML block mode: {mode}")


def markdown_visible_lines(text: str) -> tuple[str, ...]:
    """Return Markdown lines visible outside code, comments, and raw HTML."""
    visible_lines: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    in_html_comment = False
    raw_html_mode: str | None = None
    raw_html_terminator: str | None = None

    for raw_line in text.splitlines():
        if fence_char is not None:
            close_match = FENCE_CLOSE_RE.match(raw_line)
            if close_match:
                marker = close_match.group(1)
                if marker[0] == fence_char and len(marker) >= fence_len:
                    fence_char = None
                    fence_len = 0
            continue

        if raw_html_mode is not None:
            if _raw_html_block_ends(
                raw_line, raw_html_mode, raw_html_terminator
            ):
                if raw_html_mode == "blank":
                    visible_lines.append("")
                raw_html_mode = None
                raw_html_terminator = None
            continue

        if not in_html_comment:
            marker = _valid_fence_open(raw_line)
            if marker is not None:
                fence_char = marker[0]
                fence_len = len(marker)
                continue

        visible_line, in_html_comment = _mask_html_comments(
            raw_line, in_html_comment
        )
        if in_html_comment:
            visible_lines.append(visible_line)
            continue

        marker = _valid_fence_open(visible_line)
        if marker is not None:
            fence_char = marker[0]
            fence_len = len(marker)
            continue

        raw_html = _raw_html_block_start(visible_line)
        if raw_html is not None:
            mode, terminator = raw_html
            if not _raw_html_block_ends(visible_line, mode, terminator):
                raw_html_mode = mode
                raw_html_terminator = terminator
            continue

        visible_lines.append(visible_line)

    return tuple(visible_lines)

def markdown_visible_text(text: str) -> str:
    return "\n".join(markdown_visible_lines(text))


def markdown_level2_headings(text: str) -> tuple[str, ...]:
    """Return rendered level-2 ATX headings from visible Markdown."""
    headings: list[str] = []

    for line in markdown_visible_lines(text):
        heading_match = ATX_HEADING_RE.match(line)
        if not heading_match or len(heading_match.group(1)) != 2:
            continue

        heading = (heading_match.group(2) or "").strip()
        heading = re.sub(r"[ \t]+#+[ \t]*$", "", heading).rstrip()
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


def invariant_headings(text: str) -> tuple[str, ...]:
    return tuple(
        heading
        for heading in markdown_level2_headings(text)
        if INVARIANT_HEADING_RE.fullmatch(heading)
    )


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

    observed_invariants = invariant_headings(texts["INVARIANTS.md"])
    if observed_invariants != INVARIANTS:
        errors.append(
            "invariant headings must exactly match the Phase 0 contract "
            f"(expected {INVARIANTS!r}, observed {observed_invariants!r})"
        )

    roadmap_headings = markdown_level2_headings(texts["ROADMAP.md"])
    phase0_heading = "Phase 0 — Foundational Research Contract"
    if roadmap_headings.count(phase0_heading) != 1:
        errors.append("roadmap does not define exactly one Phase 0 foundational contract")

    roadmap_visible = markdown_visible_text(texts["ROADMAP.md"])
    if "machine-checkable Phase 0 validator" not in roadmap_visible:
        errors.append("roadmap does not require Phase 0 validator")

    readme_visible = markdown_visible_text(texts["README.md"])
    if "The thesis is **not treated as established fact**" not in readme_visible:
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
