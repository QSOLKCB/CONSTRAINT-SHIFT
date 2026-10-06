#!/usr/bin/env python3
"""Validate the Phase 0 CONSTRAINT-SHIFT research contract."""

from __future__ import annotations

from pathlib import Path
import re
import string
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
SETEXT_UNDERLINE_RE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
LIST_ITEM_RE = re.compile(
    r"^ {0,3}(?:(?P<bullet>[-+*])|(?P<number>\d{1,9})[.)])"
    r"(?P<spacing>[ \t]+)"
)
THEMATIC_BREAK_RE = re.compile(
    r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$"
)
RAW_HTML_TYPE1_OPEN_RE = re.compile(
    r"^ {0,3}<(?P<tag>script|pre|style|textarea)(?:[ \t>]|$)",
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
    r"^ {0,3}</?(?:" + "|".join(RAW_HTML_BLOCK_TAGS) + r")(?:[ \t/>]|$)",
    re.IGNORECASE,
)
RAW_HTML_GENERIC_OPEN_TAG_RE = re.compile(
    r"^ {0,3}<[A-Za-z][A-Za-z0-9-]*"
    r"(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[ \t]*=[ \t]*(?:\"[^\"]*\"|'[^']*'|[^ \t\"'=<>\x60]+))?)*"
    r"[ \t]*/?>[ \t]*$"
)
RAW_HTML_GENERIC_CLOSE_TAG_RE = re.compile(
    r"^ {0,3}</[A-Za-z][A-Za-z0-9-]*[ \t]*>[ \t]*$"
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


def _column_at(text: str, index: int) -> int:
    column = 0
    for char in text[:index]:
        if char == "\t":
            column += 4 - (column % 4)
        else:
            column += 1
    return column


def _list_match(line: str) -> re.Match[str] | None:
    return LIST_ITEM_RE.match(line)


def _list_can_interrupt_paragraph(line: str) -> bool:
    match = _list_match(line)
    if match is None:
        return False

    if not line[match.end() :].strip(" \t"):
        return False

    if match.group("bullet") is not None:
        return True
    return int(match.group("number")) == 1


def _list_content_column(line: str) -> int | None:
    match = _list_match(line)
    if match is None:
        return None

    if not line[match.end() :].strip(" \t"):
        return None

    return _column_at(line, match.end())


def _fence_open(
    line: str, paragraph_open: bool = False
) -> tuple[str, int] | None:
    """Return (marker, base column) for a supported fenced-code opener."""
    match = FENCE_OPEN_RE.match(line)
    if match:
        marker = match.group(1)
        info = match.group(2)
        if marker[0] == "`" and "`" in info:
            return None
        return marker, 0

    list_match = re.match(
        r"^ {0,3}(?:(?P<bullet>[-+*])|(?P<number>\d{1,9})[.)])"
        r"(?P<spacing>[ \t]+)(?P<indent> {0,3})"
        r"(?P<marker>`{3,}|~{3,})(?P<info>.*)$",
        line,
    )
    if not list_match:
        return None

    if (
        paragraph_open
        and list_match.group("number") is not None
        and int(list_match.group("number")) != 1
    ):
        return None

    marker = list_match.group("marker")
    info = list_match.group("info")
    if marker[0] == "`" and "`" in info:
        return None

    marker_start = list_match.start("marker")
    return marker, _column_at(line, marker_start)


def _leading_columns(line: str) -> int:
    index = 0
    while index < len(line) and line[index] in " \t":
        index += 1
    return _column_at(line, index)


def _fence_close(
    line: str, marker_char: str, marker_len: int, base_indent: int
) -> bool:
    min_indent = base_indent
    max_indent = base_indent + 3
    leading = _leading_columns(line)
    if leading < min_indent or leading > max_indent:
        return False

    stripped = line.lstrip(" \t")
    match = re.fullmatch(
        rf"(?P<marker>{re.escape(marker_char)}{{{marker_len},}})[ \t]*",
        stripped,
    )
    return match is not None

def _backtick_run_end(text: str, start: int) -> int:
    end = start
    while end < len(text) and text[end] == "`":
        end += 1
    return end


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _line_prefix(text: str, index: int) -> str:
    line_start = text.rfind("\n", 0, index) + 1
    return text[line_start:index]


def _backtick_run_is_fence_candidate(
    text: str, start: int, run_length: int
) -> bool:
    if run_length < 3 or _is_escaped(text, start):
        return False

    prefix = _line_prefix(text, start)
    if re.fullmatch(r" {0,3}", prefix):
        return True

    return re.fullmatch(
        r" {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+ {0,3}",
        prefix,
    ) is not None


def _line_interrupts_inline_block(line: str) -> bool:
    if not line.strip(" \t"):
        return True

    if ATX_HEADING_RE.match(line):
        return True

    if THEMATIC_BREAK_RE.match(line):
        return True

    if _fence_open(line, paragraph_open=True) is not None:
        return True

    if re.match(r"^ {0,3}>", line):
        return True

    if _list_can_interrupt_paragraph(line):
        return True

    raw_html = _raw_html_block_start(line, allow_generic=False)
    return raw_html is not None


def _inline_block_end(text: str, opener_end: int) -> int:
    cursor = text.find("\n", opener_end)
    if cursor == -1:
        return len(text)

    while cursor < len(text):
        next_start = cursor + 1
        next_end = text.find("\n", next_start)
        if next_end == -1:
            next_end = len(text)

        line = text[next_start:next_end]
        if _line_interrupts_inline_block(line):
            return next_start

        if next_end == len(text):
            return len(text)
        cursor = next_end

    return len(text)


def _matching_code_span_end(
    text: str, opener_start: int, opener_end: int
) -> int | None:
    run_length = opener_end - opener_start
    limit = _inline_block_end(text, opener_end)
    cursor = opener_end

    while cursor < limit:
        tick = text.find("`", cursor, limit)
        if tick == -1:
            return None

        if _is_escaped(text, tick):
            cursor = tick + 1
            continue

        run_end = _backtick_run_end(text, tick)
        candidate_length = run_end - tick
        if (
            candidate_length == run_length
            and not _backtick_run_is_fence_candidate(
                text, tick, candidate_length
            )
        ):
            return run_end
        cursor = run_end

    return None


def _mask_code_spans(text: str) -> tuple[str, ...]:
    """Mask matched code spans without crossing inline-block boundaries."""
    chars = list(text)
    cursor = 0

    while cursor < len(text):
        tick = text.find("`", cursor)
        if tick == -1:
            break

        if _is_escaped(text, tick):
            cursor = tick + 1
            continue

        opener_end = _backtick_run_end(text, tick)
        run_length = opener_end - tick
        if _backtick_run_is_fence_candidate(text, tick, run_length):
            cursor = opener_end
            continue

        code_end = _matching_code_span_end(text, tick, opener_end)
        if code_end is None:
            cursor = opener_end
            continue

        line_has_sentinel = False
        for index in range(tick, code_end):
            if chars[index] == "\n":
                line_has_sentinel = False
                continue
            chars[index] = " "
            if not line_has_sentinel:
                chars[index] = "x"
                line_has_sentinel = True

        cursor = code_end

    return tuple("".join(chars).splitlines())

def _mask_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Mask HTML comments after code-span content has been protected."""
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

        comment_start = line.find("<!--", cursor)
        if comment_start == -1:
            break

        end = line.find("-->", comment_start + 4)
        if end == -1:
            for index in range(comment_start, len(chars)):
                chars[index] = " "
            return "".join(chars), True

        for index in range(comment_start, end + 3):
            chars[index] = " "
        cursor = end + 3

    return "".join(chars), in_comment

def _raw_html_block_start(
    line: str, allow_generic: bool = True
) -> tuple[str, str | None] | None:
    """Return the raw-HTML block mode and terminator, if one starts here."""
    type1 = RAW_HTML_TYPE1_OPEN_RE.match(line)
    if type1:
        return "tag", type1.group("tag").lower()

    if re.match(r"^ {0,3}<\?", line):
        return "marker", "?>"

    if re.match(r"^ {0,3}<!\[CDATA\[", line):
        return "marker", "]]>"

    if re.match(r"^ {0,3}<![A-Z]", line):
        return "marker", ">"

    if RAW_HTML_BLOCK_TAG_RE.match(line):
        return "blank", None

    if allow_generic and (
        RAW_HTML_GENERIC_OPEN_TAG_RE.match(line)
        or RAW_HTML_GENERIC_CLOSE_TAG_RE.match(line)
    ):
        return "blank", None

    return None


def _raw_html_block_ends(line: str, mode: str, terminator: str | None) -> bool:
    if mode == "blank":
        return not line.strip(" \t")

    if mode == "marker":
        assert terminator is not None
        return terminator in line

    if mode == "tag":
        assert terminator is not None
        return re.search(
            rf"</{re.escape(terminator)}>",
            line,
            re.IGNORECASE,
        ) is not None

    raise AssertionError(f"unknown raw HTML block mode: {mode}")


def _line_starts_paragraph_block(line: str) -> bool:
    if not line.strip(" \t"):
        return False

    if ATX_HEADING_RE.match(line):
        return False

    if THEMATIC_BREAK_RE.match(line):
        return False

    if re.match(r"^ {0,3}>", line):
        return False

    if re.match(r"^ {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+", line):
        return False

    if line.startswith("    "):
        return False

    return True


def _paragraph_state_after(line: str, was_open: bool) -> bool:
    if not line.strip(" \t"):
        return False

    if was_open and SETEXT_UNDERLINE_RE.match(line):
        return False

    if was_open and line.startswith("    "):
        return True

    if was_open and not _line_interrupts_inline_block(line):
        return True

    return _line_starts_paragraph_block(line)

def markdown_visible_lines(text: str) -> tuple[str, ...]:
    """Return Markdown lines visible outside code, comments, and raw HTML."""
    raw_lines = text.splitlines()
    code_safe_lines = _mask_code_spans(text)
    if len(code_safe_lines) != len(raw_lines):
        raise AssertionError("code-span masking changed line structure")

    visible_lines: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    fence_base_indent = 0
    in_html_comment = False
    raw_html_mode: str | None = None
    raw_html_terminator: str | None = None
    paragraph_open = False

    for raw_line, code_safe_line in zip(raw_lines, code_safe_lines):
        if fence_char is not None:
            if (
                fence_base_indent > 0
                and raw_line.strip()
                and _leading_columns(raw_line) < fence_base_indent
            ):
                fence_char = None
                fence_len = 0
                fence_base_indent = 0
            else:
                if _fence_close(
                    raw_line, fence_char, fence_len, fence_base_indent
                ):
                    fence_char = None
                    fence_len = 0
                    fence_base_indent = 0
                continue

        if raw_html_mode is not None:
            if _raw_html_block_ends(
                code_safe_line, raw_html_mode, raw_html_terminator
            ):
                if raw_html_mode == "blank":
                    visible_lines.append("")
                raw_html_mode = None
                raw_html_terminator = None
                paragraph_open = False
            continue

        if not in_html_comment:
            fence = _fence_open(raw_line, paragraph_open=paragraph_open)
            if fence is not None:
                marker, base_indent = fence
                fence_char = marker[0]
                fence_len = len(marker)
                fence_base_indent = base_indent
                visible_lines.append("")
                paragraph_open = False
                continue

        visible_line, in_html_comment = _mask_html_comments(
            code_safe_line, in_html_comment
        )
        if in_html_comment:
            visible_lines.append(visible_line)
            if not visible_line.strip():
                paragraph_open = False
            continue

        fence = _fence_open(raw_line, paragraph_open=paragraph_open)
        if fence is not None:
            marker, base_indent = fence
            fence_char = marker[0]
            fence_len = len(marker)
            fence_base_indent = base_indent
            visible_lines.append("")
            paragraph_open = False
            continue

        raw_html = _raw_html_block_start(
            visible_line, allow_generic=not paragraph_open
        )
        if raw_html is not None:
            mode, terminator = raw_html
            if not _raw_html_block_ends(visible_line, mode, terminator):
                raw_html_mode = mode
                raw_html_terminator = terminator
            visible_lines.append("")
            paragraph_open = False
            continue

        visible_lines.append(visible_line)
        paragraph_open = _paragraph_state_after(
            visible_line, paragraph_open
        )

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

        heading = (heading_match.group(2) or "").strip(" \t")
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


def _link_reference_remainder(line: str) -> str | None:
    leading = len(line) - len(line.lstrip(" "))
    if leading > 3:
        return None

    stripped = line[leading:]
    if not stripped.startswith("["):
        return None

    cursor = 1
    while cursor + 1 < len(stripped):
        char = stripped[cursor]

        if char == "[" and not _is_escaped(stripped, cursor):
            return None

        if char == "]" and not _is_escaped(stripped, cursor):
            if cursor <= 1:
                return None
            if stripped[cursor + 1] != ":":
                return None
            return stripped[cursor + 2 :].strip(" \t")

        cursor += 1

    return None


def _reference_title_end_from_initial(
    initial: str, lines: tuple[str, ...], next_index: int
) -> int | None:
    """Return first line after a valid title starting in initial text."""
    current = initial.strip(" \t")
    if not current:
        return None

    opener = current[0]
    closer = {
        '"': '"',
        "'": "'",
        "(": ")",
    }.get(opener)
    if closer is None:
        return None

    cursor = 1
    line_index = next_index - 1

    while True:
        while cursor < len(current):
            char = current[cursor]
            if char == closer and not _is_escaped(current, cursor):
                if current[cursor + 1 :].strip(" \t"):
                    return None
                return line_index + 1
            if (
                opener == "("
                and char == "("
                and not _is_escaped(current, cursor)
            ):
                return None
            cursor += 1

        if next_index >= len(lines):
            return None

        current = lines[next_index]
        if not current.strip(" \t"):
            return None

        line_index = next_index
        next_index += 1
        cursor = 0


def _reference_title_end(
    lines: tuple[str, ...], start: int
) -> int | None:
    """Return first line after a valid possibly-multiline link title."""
    if start >= len(lines):
        return None

    first = lines[start]
    leading = len(first) - len(first.lstrip(" "))
    if leading > 3:
        return None

    return _reference_title_end_from_initial(
        first[leading:], lines, start + 1
    )


def _reference_title_line(line: str) -> bool:
    return _reference_title_end_from_initial(line, (), 0) == 0


def _split_reference_destination(text: str) -> tuple[bool, str]:
    """Return (valid destination, remaining title text)."""
    if not text:
        return False, ""

    if text.startswith("<"):
        cursor = 1
        while cursor < len(text):
            char = text[cursor]
            if char == ">" and not _is_escaped(text, cursor):
                tail = text[cursor + 1 :]
                if tail and tail[0] not in " \t":
                    return False, ""
                return True, tail.strip(" \t")
            if char == "<" and not _is_escaped(text, cursor):
                return False, ""
            if (
                char == "\\"
                and cursor + 1 < len(text)
                and text[cursor + 1] in string.punctuation
            ):
                cursor += 2
                continue
            cursor += 1
        return False, ""

    depth = 0
    cursor = 0
    while cursor < len(text):
        char = text[cursor]

        if char == "\\" and cursor + 1 < len(text):
            if text[cursor + 1] in string.punctuation:
                cursor += 2
                continue
            cursor += 1
            continue

        if char in " \t":
            break

        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                return False, ""
            depth -= 1

        cursor += 1

    if cursor == 0 or depth != 0:
        return False, ""

    return True, text[cursor:].strip(" \t")


def _reference_destination_parts(line: str) -> tuple[bool, str]:
    """Return (valid destination, remaining title text)."""
    leading = len(line) - len(line.lstrip(" "))
    if leading > 3:
        return False, ""

    stripped = line[leading:].strip(" \t")
    if not stripped:
        return False, ""

    return _split_reference_destination(stripped)

def _line_starts_reference_block(line: str) -> bool:
    if not line.strip(" \t"):
        return True

    if ATX_HEADING_RE.match(line):
        return True

    if THEMATIC_BREAK_RE.match(line):
        return True

    if _fence_open(line, paragraph_open=False) is not None:
        return True

    if re.match(r"^ {0,3}>", line):
        return True

    if _list_match(line) is not None:
        return True

    # Type-7 generic tags cannot interrupt a paragraph/reference definition.
    if _raw_html_block_start(line, allow_generic=False) is not None:
        return True

    if line.startswith("    "):
        return True

    return False


def _reference_definition_end(
    lines: tuple[str, ...], start: int
) -> int | None:
    """Return the first line after a complete link-reference definition."""
    remainder = _link_reference_remainder(lines[start])
    if remainder is None:
        return None

    cursor = start + 1

    if remainder:
        valid, title_text = _split_reference_destination(remainder)
        if not valid:
            return None
        if title_text:
            return _reference_title_end_from_initial(
                title_text, lines, cursor
            )
    else:
        if cursor >= len(lines):
            return None
        if _line_starts_reference_block(lines[cursor]):
            return None

        valid, title_text = _reference_destination_parts(lines[cursor])
        if not valid:
            return None
        cursor += 1

        if title_text:
            return _reference_title_end_from_initial(
                title_text, lines, cursor
            )

    if cursor < len(lines):
        title_end = _reference_title_end(lines, cursor)
        if title_end is not None:
            return title_end

    return cursor

def markdown_rendered_prose_lines(text: str) -> tuple[str, ...]:
    """Approximate rendered prose while excluding non-rendered metadata/code."""
    lines = markdown_visible_lines(text)
    rendered: list[str] = []
    paragraph_open = False
    list_content_column: int | None = None
    index = 0

    while index < len(lines):
        line = lines[index]

        if not line.strip():
            rendered.append(line)
            paragraph_open = False
            list_content_column = None
            index += 1
            continue

        leading_columns = _leading_columns(line)

        if (
            list_content_column is not None
            and leading_columns >= list_content_column
        ):
            rendered.append(line)
            paragraph_open = True
            index += 1
            continue

        if list_content_column is not None and leading_columns < list_content_column:
            list_content_column = None

        if not paragraph_open and leading_columns >= 4:
            index += 1
            while index < len(lines):
                continuation = lines[index]
                if not continuation.strip():
                    index += 1
                    continue
                if _leading_columns(continuation) >= 4:
                    index += 1
                    continue
                break
            paragraph_open = False
            continue

        if not paragraph_open:
            definition_end = _reference_definition_end(lines, index)
            if definition_end is not None:
                index = definition_end
                paragraph_open = False
                list_content_column = None
                continue

        rendered.append(line)

        content_column = _list_content_column(line)
        if content_column is not None:
            list_content_column = content_column
            paragraph_open = False
        else:
            paragraph_open = _paragraph_state_after(line, paragraph_open)

        index += 1

    return tuple(rendered)

def markdown_rendered_prose_text(text: str) -> str:
    return "\n".join(markdown_rendered_prose_lines(text))


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

    roadmap_prose = markdown_rendered_prose_text(texts["ROADMAP.md"])
    if "machine-checkable Phase 0 validator" not in roadmap_prose:
        errors.append("roadmap does not require Phase 0 validator")

    readme_prose = markdown_rendered_prose_text(texts["README.md"])
    if "The thesis is **not treated as established fact**" not in readme_prose:
        errors.append("README must explicitly separate thesis from established fact")

    for path, text in texts.items():
        if len(text.strip(" \t")) < 80:
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
