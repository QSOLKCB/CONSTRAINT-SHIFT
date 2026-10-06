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


def _column_at(
    text: str, index: int, initial_column: int = 0
) -> int:
    column = initial_column
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


def _list_marker_content(
    line: str,
    paragraph_open: bool = False,
    initial_column: int = 0,
) -> tuple[int, str] | None:
    """Return absolute visual content column and content after one list marker."""
    match = _list_match(line)
    if match is None:
        return None

    if paragraph_open and not _list_can_interrupt_paragraph(line):
        return None

    spacing_start = match.start("spacing")
    spacing_end = match.end("spacing")
    marker_end_column = _column_at(
        line, spacing_start, initial_column=initial_column
    )
    spacing_end_column = _column_at(
        line, spacing_end, initial_column=initial_column
    )
    padding_columns = spacing_end_column - marker_end_column

    if padding_columns <= 4:
        return spacing_end_column, line[spacing_end:]

    # Five or more visual columns: consume exactly one visual column as
    # list padding and preserve any residual tab expansion as indentation.
    content_column = marker_end_column + 1
    content = _strip_columns_prefix(
        line[spacing_start:],
        1,
        initial_column=marker_end_column,
    )
    if content is None:
        return None

    return content_column, content

def _list_item_context_details(
    line: str, paragraph_open: bool = False
) -> tuple[int, str, tuple[str, ...]] | None:
    """Return innermost column/content plus explicit list-container identity."""
    segment = line
    base_column = 0
    context: tuple[int, str, tuple[str, ...]] | None = None
    signature: list[str] = []
    first_marker = True

    while True:
        if THEMATIC_BREAK_RE.match(segment):
            return context

        marker_content = _list_marker_content(
            segment,
            paragraph_open=paragraph_open if first_marker else False,
            initial_column=base_column,
        )
        if marker_content is None:
            return context

        content_column, content = marker_content
        if not content.strip(" \t"):
            return context

        signature.append("list")
        base_column = content_column
        context = (base_column, content, tuple(signature))
        segment = content
        first_marker = False


def _list_item_context(
    line: str, paragraph_open: bool = False
) -> tuple[int, str] | None:
    details = _list_item_context_details(
        line, paragraph_open=paragraph_open
    )
    if details is None:
        return None
    column, content, _signature = details
    return column, content

def _list_content_column(
    line: str, paragraph_open: bool = False
) -> int | None:
    context = _list_item_context(line, paragraph_open=paragraph_open)
    if context is None:
        return None
    return context[0]


def _strip_columns_prefix(
    line: str, columns: int, initial_column: int = 0
) -> str | None:
    column = initial_column
    target_column = initial_column + columns
    index = 0

    while index < len(line) and column < target_column:
        char = line[index]
        if char == " ":
            column += 1
            index += 1
            continue

        if char == "\t":
            next_column = column + 4 - (column % 4)
            if next_column > target_column:
                overshoot = next_column - target_column
                return (" " * overshoot) + line[index + 1 :]
            column = next_column
            index += 1
            continue

        return None

    if column < target_column:
        return None

    return line[index:]

def _strip_quote_prefixes(
    line: str, count: int | None = None
) -> tuple[int, str] | None:
    content = line
    stripped_count = 0

    while count is None or stripped_count < count:
        quote = re.match(r"^ {0,3}>[ \t]?", content)
        if quote is None:
            break
        content = content[quote.end() :]
        stripped_count += 1

    if count is not None and stripped_count != count:
        return None

    return stripped_count, content


def _container_content_identity(
    line: str, paragraph_open: bool = False
) -> tuple[int, str, bool, tuple[str, ...]]:
    """Return prefix width, content, inner paragraph state, and identity."""
    content = line
    base_column = 0
    inner_paragraph_open = paragraph_open
    signature: list[str] = []

    while True:
        quote = re.match(r"^ {0,3}>[ \t]?", content)
        if quote is not None:
            base_column = _column_at(
                content, quote.end(), initial_column=base_column
            )
            content = content[quote.end() :]
            signature.append("quote")
            inner_paragraph_open = False
            continue

        details = _list_item_context_details(
            content, paragraph_open=inner_paragraph_open
        )
        if details is not None:
            column, nested, list_signature = details
            # list context columns are absolute from the current base.
            if base_column:
                column += base_column
            base_column = column
            content = nested
            signature.extend(list_signature)
            inner_paragraph_open = False
            continue

        return (
            base_column,
            content,
            inner_paragraph_open,
            tuple(signature),
        )


def _container_content_state(
    line: str, paragraph_open: bool = False
) -> tuple[int, str, bool]:
    column, content, inner_paragraph_open, _signature = (
        _container_content_identity(
            line, paragraph_open=paragraph_open
        )
    )
    return column, content, inner_paragraph_open


def _container_content(
    line: str, paragraph_open: bool = False
) -> tuple[int, str]:
    column, content, _paragraph_open, _signature = (
        _container_content_identity(
            line, paragraph_open=paragraph_open
        )
    )
    return column, content


def _container_scoped_content(
    line: str,
    container_column: int,
    container_signature: tuple[str, ...],
) -> str | None:
    """Return content only when the opener's Markdown container continues."""
    if not container_signature and container_column <= 0:
        return line

    (
        structural_column,
        structural_content,
        _paragraph_open,
        structural_signature,
    ) = _container_content_identity(line, paragraph_open=False)

    if structural_signature:
        if structural_signature == container_signature:
            return structural_content

        # A mixed container may repeat its explicit quote prefix while
        # continuing an inner list purely by indentation.
        prefix_length = len(structural_signature)
        if (
            container_signature[:prefix_length]
            == structural_signature
            and structural_signature
            and all(
                marker == "quote"
                for marker in structural_signature
            )
            and all(
                marker == "list"
                for marker in container_signature[prefix_length:]
            )
        ):
            remaining_columns = (
                container_column - structural_column
            )
            if (
                remaining_columns >= 0
                and _leading_columns(structural_content)
                >= remaining_columns
            ):
                return _strip_columns_prefix(
                    structural_content,
                    remaining_columns,
                    initial_column=structural_column,
                )
        return None

    # List continuations commonly omit the list marker and continue by
    # indentation. Quotes, by contrast, require their explicit marker.
    if container_signature and all(
        marker == "list" for marker in container_signature
    ):
        if _leading_columns(line) >= container_column:
            return _strip_columns_prefix(line, container_column)

    return None

def _container_reference_definition_end(
    lines: tuple[str, ...],
    start: int,
    paragraph_open: bool = False,
) -> int | None:
    (
        container_column,
        first_content,
        inner_paragraph_open,
        container_signature,
    ) = _container_content_identity(
        lines[start], paragraph_open=paragraph_open
    )
    if inner_paragraph_open:
        return None

    virtual_lines = [first_content]
    cursor = start + 1

    while cursor < len(lines):
        line = lines[cursor]
        if not line.strip(" \t"):
            virtual_lines.append("")
            break

        scoped = _container_scoped_content(
            line, container_column, container_signature
        )
        if scoped is None:
            break

        virtual_lines.append(scoped)
        cursor += 1

    definition_end = _reference_definition_end(
        tuple(virtual_lines), 0
    )
    if definition_end is None:
        return None

    return start + definition_end


def _list_reference_definition_end(
    lines: tuple[str, ...], start: int
) -> int | None:
    context = _list_item_context(lines[start])
    if context is None:
        return None

    content_column, content = context
    virtual_lines = [content]
    cursor = start + 1

    while cursor < len(lines):
        line = lines[cursor]
        if not line.strip(" \t"):
            virtual_lines.append("")
            break

        stripped = _strip_columns_prefix(line, content_column)
        if stripped is None:
            break

        virtual_lines.append(stripped)
        cursor += 1

    definition_end = _reference_definition_end(tuple(virtual_lines), 0)
    if definition_end is None:
        return None

    return start + definition_end


def _list_item_is_reference_definition(line: str) -> bool:
    context = _list_item_context(line)
    if context is None:
        return False

    _column, content = context
    return _reference_definition_end((content,), 0) == 1


def _list_item_starts_paragraph(line: str) -> bool:
    context = _list_item_context(line)
    if context is None:
        return False

    _column, content = context
    if _reference_definition_end((content,), 0) is not None:
        return False

    return _line_starts_paragraph_block(content)

def _fence_open_details(
    line: str, paragraph_open: bool = False
) -> tuple[str, int, tuple[str, ...]] | None:
    """Return marker, container column, and container identity."""
    match = FENCE_OPEN_RE.match(line)
    if match:
        marker = match.group(1)
        info = match.group(2)
        if marker[0] == "`" and "`" in info:
            return None
        return marker, 0, ()

    (
        container_column,
        content,
        _inner_paragraph_open,
        signature,
    ) = _container_content_identity(
        line, paragraph_open=paragraph_open
    )
    if container_column == 0:
        return None

    match = FENCE_OPEN_RE.match(content)
    if match is None:
        return None

    marker = match.group(1)
    info = match.group(2)
    if marker[0] == "`" and "`" in info:
        return None

    return marker, container_column, signature


def _fence_open(
    line: str, paragraph_open: bool = False
) -> tuple[str, int] | None:
    details = _fence_open_details(
        line, paragraph_open=paragraph_open
    )
    if details is None:
        return None
    marker, container_column, _signature = details
    return marker, container_column

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


def _raw_html_container_content(
    line: str,
    container_column: int,
    container_signature: tuple[str, ...],
) -> str | None:
    """Return content while the exact raw-HTML container remains active."""
    return _container_scoped_content(
        line, container_column, container_signature
    )

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

def _markdown_visible_records(
    text: str,
) -> tuple[tuple[str, bool, int], ...]:
    """Return visible lines with paragraph state and owning quote depth."""
    raw_lines = tuple(text.splitlines())
    code_safe_lines = _mask_code_spans(text)
    if len(code_safe_lines) != len(raw_lines):
        raise AssertionError("code-span masking changed line structure")

    records: list[tuple[str, bool, int]] = []
    fence_char: str | None = None
    fence_len = 0
    fence_container_column = 0
    fence_container_signature: tuple[str, ...] = ()
    in_html_comment = False
    comment_container_column = 0
    comment_container_signature: tuple[str, ...] = ()
    raw_html_mode: str | None = None
    raw_html_terminator: str | None = None
    raw_html_container_column = 0
    raw_html_container_signature: tuple[str, ...] = ()
    paragraph_open = False
    paragraph_quote_depth = 0
    list_paragraph_column: int | None = None
    list_paragraph_quote_depth = 0
    list_paragraph_allows_lazy_dedent = False
    index = 0

    while index < len(raw_lines):
        raw_line = raw_lines[index]
        code_safe_line = code_safe_lines[index]

        if list_paragraph_column is not None:
            scoped_quote = _strip_quote_prefixes(
                raw_line, list_paragraph_quote_depth
            )
            if scoped_quote is None:
                if not list_paragraph_allows_lazy_dedent:
                    paragraph_open = False
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
            else:
                _quote_depth, list_line = scoped_quote
                if not list_line.strip(" \t"):
                    paragraph_open = False
                    list_paragraph_column = None
                    list_paragraph_quote_depth = 0
                    list_paragraph_allows_lazy_dedent = False
                elif _leading_columns(list_line) < list_paragraph_column:
                    if (
                        _line_interrupts_inline_block(list_line)
                        or not list_paragraph_allows_lazy_dedent
                    ):
                        paragraph_open = False
                        paragraph_quote_depth = 0
                    else:
                        # The list container ended, but the paragraph
                        # continues lazily in the same outer quote.
                        paragraph_quote_depth = (
                            list_paragraph_quote_depth
                        )
                    list_paragraph_column = None
                    list_paragraph_quote_depth = 0
                    list_paragraph_allows_lazy_dedent = False
                elif list_line.strip():
                    list_paragraph_allows_lazy_dedent = True

        if fence_char is not None:
            block_line = _container_scoped_content(
                raw_line,
                fence_container_column,
                fence_container_signature,
            )
            if (
                fence_container_signature
                and block_line is None
                and (
                    raw_line.strip(" \t")
                    or "quote" in fence_container_signature
                )
            ):
                fence_char = None
                fence_len = 0
                fence_container_column = 0
                fence_container_signature = ()
                paragraph_open = False
            else:
                if block_line is None:
                    block_line = raw_line
                if _fence_close(
                    block_line, fence_char, fence_len, 0
                ):
                    fence_char = None
                    fence_len = 0
                    fence_container_column = 0
                    fence_container_signature = ()
                index += 1
                continue

        if raw_html_mode is not None:
            block_line = _raw_html_container_content(
                code_safe_line,
                raw_html_container_column,
                raw_html_container_signature,
            )
            if (
                raw_html_container_signature
                and raw_line.strip(" \t")
                and block_line is None
            ):
                raw_html_mode = None
                raw_html_terminator = None
                raw_html_container_column = 0
                raw_html_container_signature = ()
                paragraph_open = False
            else:
                if block_line is None:
                    block_line = code_safe_line

                if _raw_html_block_ends(
                    block_line, raw_html_mode, raw_html_terminator
                ):
                    if raw_html_mode == "blank":
                        records.append(("", False, 0))
                    raw_html_mode = None
                    raw_html_terminator = None
                    raw_html_container_column = 0
                    raw_html_container_signature = ()
                    paragraph_open = False
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
                index += 1
                continue

        if in_html_comment and comment_container_signature:
            scoped = _container_scoped_content(
                code_safe_line,
                comment_container_column,
                comment_container_signature,
            )
            if raw_line.strip(" \t") and scoped is None:
                in_html_comment = False
                comment_container_column = 0
                comment_container_signature = ()
                paragraph_open = False

        if not in_html_comment:
            fence = _fence_open_details(
                raw_line, paragraph_open=paragraph_open
            )
            if fence is not None:
                marker, container_column, signature = fence
                fence_char = marker[0]
                fence_len = len(marker)
                fence_container_column = container_column
                fence_container_signature = signature
                records.append(("", False, 0))
                paragraph_open = False
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
                index += 1
                continue

        was_in_html_comment = in_html_comment
        visible_line, in_html_comment = _mask_html_comments(
            code_safe_line, in_html_comment
        )
        if in_html_comment and not was_in_html_comment:
            (
                comment_container_column,
                _comment_content,
                _comment_paragraph,
                comment_container_signature,
            ) = _container_content_identity(
                raw_line, paragraph_open=paragraph_open
            )

        if in_html_comment:
            records.append(
                (
                    visible_line,
                    paragraph_open,
                    (
                        paragraph_quote_depth
                        if paragraph_open
                        else 0
                    ),
                )
            )
            if not visible_line.strip(" \t"):
                paragraph_open = False
            index += 1
            continue

        if was_in_html_comment and not in_html_comment:
            comment_container_column = 0
            comment_container_signature = ()

        if not paragraph_open:
            definition_end = _container_reference_definition_end(
                code_safe_lines, index, paragraph_open=False
            )
            if definition_end is not None:
                paragraph_open = False
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
                index = definition_end
                continue

        (
            container_column,
            block_content,
            inner_paragraph_open,
            container_signature,
        ) = _container_content_identity(
            visible_line, paragraph_open=paragraph_open
        )
        raw_html = _raw_html_block_start(
            block_content, allow_generic=not inner_paragraph_open
        )
        if raw_html is not None:
            mode, terminator = raw_html
            if not _raw_html_block_ends(block_content, mode, terminator):
                raw_html_mode = mode
                raw_html_terminator = terminator
                raw_html_container_column = container_column
                raw_html_container_signature = container_signature
            records.append(("", False, 0))
            paragraph_open = False
            index += 1
            continue

        records.append(
                (
                    visible_line,
                    paragraph_open,
                    (
                        paragraph_quote_depth
                        if paragraph_open
                        else 0
                    ),
                )
            )
        quote_state = _strip_quote_prefixes(visible_line)
        assert quote_state is not None
        quote_depth, list_source = quote_state

        same_list_container = (
            list_paragraph_column is not None
            and quote_depth == list_paragraph_quote_depth
        )
        effective_paragraph_open = (
            paragraph_open
            if quote_depth == 0 or same_list_container
            else False
        )

        list_content_column = _list_content_column(
            list_source, paragraph_open=effective_paragraph_open
        )
        if list_content_column is not None:
            context = _list_item_context(
                list_source,
                paragraph_open=effective_paragraph_open,
            )
            paragraph_open = _list_item_starts_paragraph(
                list_source
            )
            if paragraph_open and context is not None:
                paragraph_quote_depth = quote_depth
                list_paragraph_column = context[0]
                list_paragraph_quote_depth = quote_depth
                list_paragraph_allows_lazy_dedent = bool(
                    context[1].strip()
                )
            else:
                paragraph_quote_depth = 0
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
        else:
            paragraph_open = _paragraph_state_after(
                visible_line, effective_paragraph_open
            )
            paragraph_quote_depth = (
                quote_depth if paragraph_open else 0
            )
        index += 1

    return tuple(records)

def markdown_visible_lines(text: str) -> tuple[str, ...]:
    return tuple(
        line
        for line, _paragraph_open, _paragraph_quote_depth
        in _markdown_visible_records(text)
    )

def markdown_visible_text(text: str) -> str:
    return "\n".join(markdown_visible_lines(text))


def markdown_level2_headings(text: str) -> tuple[str, ...]:
    """Return rendered level-2 ATX headings from visible Markdown."""
    headings: list[str] = []

    for (
        line,
        paragraph_open,
        paragraph_quote_depth,
    ) in _markdown_visible_records(text):
        quote_state = _strip_quote_prefixes(line)
        assert quote_state is not None
        quote_depth, paragraph_line = quote_state

        paragraph_applies_here = (
            paragraph_open
            and quote_depth == paragraph_quote_depth
        )
        if paragraph_applies_here:
            if (
                _list_match(paragraph_line) is not None
                and not _list_can_interrupt_paragraph(paragraph_line)
            ):
                continue

        _container_column, heading_line, _inner_paragraph = (
            _container_content_state(
                line,
                paragraph_open=paragraph_applies_here,
            )
        )
        heading_match = ATX_HEADING_RE.match(heading_line)
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
            label = stripped[1:cursor]
            if not label.strip():
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
    paragraph_quote_depth = 0
    list_content_column: int | None = None
    index = 0

    while index < len(lines):
        line = lines[index]

        if not line.strip(" \t"):
            rendered.append(line)
            paragraph_open = False
            list_content_column = None
            index += 1
            continue

        quote_state = _strip_quote_prefixes(line)
        assert quote_state is not None
        quote_depth, indentation_line = quote_state

        if quote_depth > paragraph_quote_depth:
            paragraph_open = False
            list_content_column = None
        elif (
            quote_depth < paragraph_quote_depth
            and _line_interrupts_inline_block(indentation_line)
        ):
            paragraph_open = False
            list_content_column = None

        leading_columns = _leading_columns(indentation_line)

        if (
            list_content_column is not None
            and leading_columns >= list_content_column
        ):
            nested_context = _list_item_context(
                line, paragraph_open=paragraph_open
            )
            if (
                nested_context is not None
                and nested_context[0] > list_content_column
            ):
                reference_end = _list_reference_definition_end(lines, index)
                if reference_end is not None:
                    index = reference_end
                    list_content_column = nested_context[0]
                    paragraph_open = False
                    continue

                rendered.append(line)
                list_content_column = nested_context[0]
                paragraph_open = _list_item_starts_paragraph(line)
                index += 1
                continue

            relative_indent = leading_columns - list_content_column
            if not paragraph_open and relative_indent >= 4:
                index += 1
                continue

            rendered.append(line)
            if not paragraph_open:
                paragraph_open = _line_starts_paragraph_block(
                    indentation_line.lstrip(" \t")
                )
            if paragraph_open:
                paragraph_quote_depth = quote_depth
            index += 1
            continue

        if list_content_column is not None and leading_columns < list_content_column:
            list_content_column = None
            # Preserve an open paragraph: a dedented line may be a lazy
            # continuation and reference definitions cannot interrupt it.

        if not paragraph_open and leading_columns >= 4:
            index += 1
            while index < len(lines):
                continuation = lines[index]
                continuation_quote = _strip_quote_prefixes(
                    continuation
                )
                assert continuation_quote is not None
                _continuation_depth, continuation_line = (
                    continuation_quote
                )
                if not continuation_line.strip(" \t"):
                    index += 1
                    continue
                if _leading_columns(continuation_line) >= 4:
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

        content_column = _list_content_column(
            line, paragraph_open=paragraph_open
        )
        if content_column is not None:
            reference_end = _list_reference_definition_end(lines, index)
            if reference_end is not None:
                index = reference_end
                list_content_column = content_column
                paragraph_open = False
                continue

            context = _list_item_context(
                line, paragraph_open=paragraph_open
            )
            if (
                context is not None
                and not paragraph_open
                and _leading_columns(context[1]) >= 4
            ):
                list_content_column = content_column
                paragraph_open = False
                list_paragraph_column = None
                list_paragraph_quote_depth = 0
                list_paragraph_allows_lazy_dedent = False
                index += 1
                continue

            rendered.append(line)
            list_content_column = content_column
            paragraph_open = _list_item_starts_paragraph(line)
        else:
            rendered.append(line)
            paragraph_open = _paragraph_state_after(
                indentation_line, paragraph_open
            )
            paragraph_quote_depth = (
                quote_depth if paragraph_open else 0
            )

        index += 1

    return tuple(rendered)

def _matching_inline_link_end(text: str, open_index: int) -> int | None:
    depth = 0
    quote: str | None = None
    cursor = open_index

    while cursor < len(text):
        char = text[cursor]

        if char == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue

        if quote is not None:
            if char == quote:
                quote = None
            cursor += 1
            continue

        if char in ('"', "'"):
            quote = char
            cursor += 1
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return cursor + 1

        cursor += 1

    return None


def _find_unescaped_closing_bracket(
    text: str, start: int
) -> int | None:
    cursor = start
    while cursor < len(text):
        if (
            text[cursor] == "]"
            and not _is_escaped(text, cursor)
        ):
            return cursor
        cursor += 1
    return None


def _normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def _reference_label_key(line: str) -> str | None:
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
            if stripped[cursor + 1] != ":":
                return None
            label = stripped[1:cursor]
            if not label.strip():
                return None
            return _normalize_reference_label(label)
        cursor += 1

    return None


def _defined_reference_labels(text: str) -> set[str]:
    lines = tuple(text.splitlines())
    labels: set[str] = set()
    paragraph_open = False
    fence_char: str | None = None
    fence_len = 0
    fence_column = 0
    fence_signature: tuple[str, ...] = ()
    index = 0

    while index < len(lines):
        line = lines[index]

        if fence_char is not None:
            block_line = _container_scoped_content(
                line, fence_column, fence_signature
            )
            if (
                fence_signature
                and block_line is None
                and (
                    line.strip(" \t")
                    or "quote" in fence_signature
                )
            ):
                fence_char = None
                fence_len = 0
                fence_column = 0
                fence_signature = ()
                paragraph_open = False
            else:
                if block_line is None:
                    block_line = line
                if _fence_close(
                    block_line, fence_char, fence_len, 0
                ):
                    fence_char = None
                    fence_len = 0
                    fence_column = 0
                    fence_signature = ()
                    paragraph_open = False
                index += 1
                continue

        if not line.strip(" \t"):
            paragraph_open = False
            index += 1
            continue

        fence = _fence_open_details(
            line, paragraph_open=paragraph_open
        )
        if fence is not None:
            marker, fence_column, fence_signature = fence
            fence_char = marker[0]
            fence_len = len(marker)
            paragraph_open = False
            index += 1
            continue

        if not paragraph_open:
            definition_end = _container_reference_definition_end(
                lines, index, paragraph_open=False
            )
            if definition_end is not None:
                _column, content = _container_content(line)
                label = _reference_label_key(content)
                if label is not None:
                    labels.add(label)
                index = definition_end
                continue

        paragraph_open = _paragraph_state_after(
            line, paragraph_open
        )
        index += 1

    return labels


def _inline_html_tag_end(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] != "<":
        return None

    quote: str | None = None
    cursor = start + 1

    while cursor < len(text):
        char = text[cursor]
        if quote is not None:
            if char == quote:
                quote = None
            cursor += 1
            continue

        if char in ('"', "'"):
            quote = char
            cursor += 1
            continue

        if char == ">":
            candidate = text[start : cursor + 1]
            if (
                RAW_HTML_GENERIC_OPEN_TAG_RE.fullmatch(candidate)
                or RAW_HTML_GENERIC_CLOSE_TAG_RE.fullmatch(candidate)
            ):
                return cursor + 1
            return None

        cursor += 1

    return None


def _render_inline_prose(
    text: str,
    defined_reference_labels: set[str] | None = None,
) -> str:
    """Approximate rendered inline text, excluding link metadata/titles."""
    rendered: list[str] = []
    cursor = 0
    if defined_reference_labels is None:
        defined_reference_labels = set()

    while cursor < len(text):
        if (
            text[cursor] == "<"
            and not _is_escaped(text, cursor)
        ):
            html_end = _inline_html_tag_end(text, cursor)
            if html_end is not None:
                cursor = html_end
                continue

        label_start = cursor
        image = False
        if text.startswith("![", cursor):
            image = True
            label_start = cursor + 1

        if text[label_start:label_start + 1] == "[":
            close = label_start + 1
            while close < len(text):
                if (
                    text[close] == "]"
                    and not _is_escaped(text, close)
                ):
                    break
                close += 1

            if close < len(text):
                label = text[label_start + 1 : close]
                if close + 1 < len(text) and text[close + 1] == "(":
                    link_end = _matching_inline_link_end(
                        text, close + 1
                    )
                    if link_end is not None:
                        rendered.append(label)
                        cursor = link_end
                        continue

                if close + 1 < len(text) and text[close + 1] == "[":
                    ref_close = _find_unescaped_closing_bracket(
                        text, close + 2
                    )
                    if ref_close is not None:
                        reference_label = text[
                            close + 2 : ref_close
                        ]
                        if not reference_label:
                            reference_label = label
                        if (
                            _normalize_reference_label(
                                reference_label
                            )
                            in defined_reference_labels
                        ):
                            rendered.append(label)
                            cursor = ref_close + 1
                            continue

        rendered.append(text[cursor])
        cursor += 1

    return "".join(rendered)


def markdown_rendered_prose_text(text: str) -> str:
    lines = markdown_rendered_prose_lines(text)
    defined_reference_labels = _defined_reference_labels(text)
    blocks: list[str] = []
    current: list[str] = []
    current_quote_depth: int | None = None

    for line in lines:
        quote_state = _strip_quote_prefixes(line)
        assert quote_state is not None
        quote_depth, quote_content = quote_state

        if not quote_content.strip(" \t"):
            if current:
                blocks.append(" ".join(current))
                current = []
            current_quote_depth = None
            continue

        starts_block = _line_interrupts_inline_block(
            quote_content
        )

        effective_quote_depth = quote_depth
        if (
            current
            and current_quote_depth is not None
            and quote_depth != current_quote_depth
        ):
            lazy_quote_continuation = (
                quote_depth < current_quote_depth
                and not starts_block
            )
            if lazy_quote_continuation:
                effective_quote_depth = current_quote_depth
            else:
                blocks.append(" ".join(current))
                current = []

        paragraph_continuation = bool(current) and not starts_block
        _container_column, content = _container_content(
            quote_content,
            paragraph_open=paragraph_continuation,
        )

        single_line_block = (
            ATX_HEADING_RE.match(content) is not None
            or THEMATIC_BREAK_RE.match(content) is not None
        )

        if starts_block and current:
            blocks.append(" ".join(current))
            current = []

        rendered_content = _render_inline_prose(
            content.strip(" \t"),
            defined_reference_labels,
        )
        if rendered_content:
            current.append(rendered_content)
            current_quote_depth = effective_quote_depth

        if single_line_block and current:
            blocks.append(" ".join(current))
            current = []
            current_quote_depth = None

    if current:
        blocks.append(" ".join(current))

    return "\n".join(blocks)

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
        content_size = sum(1 for char in text if not char.isspace())
        if content_size < 80:
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
