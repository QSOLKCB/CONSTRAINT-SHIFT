#!/usr/bin/env python3
"""Validate the Phase 0 research contract using one CommonMark parse per file."""

from __future__ import annotations

from pathlib import Path
import re
import logging
import sys
from typing import NamedTuple

try:
    from markdown_it import MarkdownIt
    from markdown_it.token import Token
    from markdown_it.common.utils import charCodeAt, isSpace, isStrSpace, normalizeReference
    from markdown_it.rules_block import StateBlock
    from markdown_it.rules_inline import StateInline
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Phase 0 validator dependencies are missing; run "
        "python3 -m pip install --require-hashes -r requirements.txt"
    ) from exc

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


class Heading(NamedTuple):
    title: str
    line: int


class ProseBlock(NamedTuple):
    text: str
    line: int


class Document(NamedTuple):
    headings: tuple[Heading, ...]
    prose: tuple[ProseBlock, ...]


# The four rules below are adapted from markdown-it-py 4.2.0 (MIT).
# See THIRD_PARTY_NOTICES.md. They run in the same parser state, not as
# independent scans. Changes: raw reference-label length <=999, and trim
# only CommonMark whitespace from paragraphs. All other parsing is upstream.
LOGGER = logging.getLogger(__name__)

def reference(state: StateBlock, startLine: int, _endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering reference: %s, %s, %s, %s", state, startLine, _endLine, silent
    )

    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]
    nextLine = startLine + 1

    if state.is_code_block(startLine):
        return False

    if state.src[pos] != "[":
        return False

    string = state.src[pos : maximum + 1]

    # string = state.getLines(startLine, nextLine, state.blkIndent, False).strip()
    maximum = len(string)

    labelEnd = None
    pos = 1
    while pos < maximum:
        ch = charCodeAt(string, pos)
        if ch == 0x5B:  # /* [ */
            return False
        elif ch == 0x5D:  # /* ] */
            labelEnd = pos
            break
        elif ch == 0x0A:  # /* \n */
            if (lineContent := getNextLine(state, nextLine)) is not None:
                string += lineContent
                maximum = len(string)
                nextLine += 1
        elif ch == 0x5C:  # /* \ */
            pos += 1
            if (
                pos < maximum
                and charCodeAt(string, pos) == 0x0A
                and (lineContent := getNextLine(state, nextLine)) is not None
            ):
                string += lineContent
                maximum = len(string)
                nextLine += 1
        pos += 1

    if (
        labelEnd is None or labelEnd < 0 or charCodeAt(string, labelEnd + 1) != 0x3A
    ):  # /* : */
        return False

    # [label]:   destination   'title'
    #         ^^^ skip optional whitespace here
    pos = labelEnd + 2
    while pos < maximum:
        ch = charCodeAt(string, pos)
        if ch == 0x0A:
            if (lineContent := getNextLine(state, nextLine)) is not None:
                string += lineContent
                maximum = len(string)
                nextLine += 1
        elif isSpace(ch):
            pass
        else:
            break
        pos += 1

    # [label]:   destination   'title'
    #            ^^^^^^^^^^^ parse this
    destRes = state.md.helpers.parseLinkDestination(string, pos, maximum)
    if not destRes.ok:
        return False

    href = state.md.normalizeLink(destRes.str)
    if not state.md.validateLink(href):
        return False

    pos = destRes.pos

    # save cursor state, we could require to rollback later
    destEndPos = pos
    destEndLineNo = nextLine

    # [label]:   destination   'title'
    #                       ^^^ skipping those spaces
    start = pos
    while pos < maximum:
        ch = charCodeAt(string, pos)
        if ch == 0x0A:
            if (lineContent := getNextLine(state, nextLine)) is not None:
                string += lineContent
                maximum = len(string)
                nextLine += 1
        elif isSpace(ch):
            pass
        else:
            break
        pos += 1

    # [label]:   destination   'title'
    #                          ^^^^^^^ parse this
    titleRes = state.md.helpers.parseLinkTitle(string, pos, maximum, None)
    while titleRes.can_continue:
        if (lineContent := getNextLine(state, nextLine)) is None:
            break
        string += lineContent
        pos = maximum
        maximum = len(string)
        nextLine += 1
        titleRes = state.md.helpers.parseLinkTitle(string, pos, maximum, titleRes)

    if pos < maximum and start != pos and titleRes.ok:
        title = titleRes.str
        pos = titleRes.pos
    else:
        title = ""
        pos = destEndPos
        nextLine = destEndLineNo

    # skip trailing spaces until the rest of the line
    while pos < maximum:
        ch = charCodeAt(string, pos)
        if not isSpace(ch):
            break
        pos += 1

    if pos < maximum and charCodeAt(string, pos) != 0x0A and title:
        # garbage at the end of the line after title,
        # but it could still be a valid reference if we roll back
        title = ""
        pos = destEndPos
        nextLine = destEndLineNo
        while pos < maximum:
            ch = charCodeAt(string, pos)
            if not isSpace(ch):
                break
            pos += 1

    if pos < maximum and charCodeAt(string, pos) != 0x0A:
        # garbage at the end of the line
        return False

    # Compatibility correction: length is checked before label normalization.
    if labelEnd - 1 > 999:
        return False
    label = normalizeReference(string[1:labelEnd])
    if not label:
        # CommonMark 0.20 disallows empty labels
        return False

    # Reference can not terminate anything. This check is for safety only.
    if silent:
        return True

    if "references" not in state.env:
        state.env["references"] = {}

    state.line = nextLine

    # note, this is not part of markdown-it JS, but is useful for renderers
    if state.md.options.get("inline_definitions", False):
        token = state.push("definition", "", 0)
        token.meta = {
            "id": label,
            "title": title,
            "url": href,
            "label": string[1:labelEnd],
        }
        token.map = [startLine, state.line]

    if label not in state.env["references"]:
        state.env["references"][label] = {
            "title": title,
            "href": href,
            "map": [startLine, state.line],
        }
    else:
        state.env.setdefault("duplicate_refs", []).append(
            {
                "title": title,
                "href": href,
                "label": label,
                "map": [startLine, state.line],
            }
        )

    return True


def getNextLine(state: StateBlock, nextLine: int) -> None | str:
    endLine = state.lineMax

    if nextLine >= endLine or state.isEmpty(nextLine):
        # empty line or end of input
        return None

    isContinuation = False

    # this would be a code block normally, but after paragraph
    # it's considered a lazy continuation regardless of what's there
    if state.is_code_block(nextLine):
        isContinuation = True

    # quirk for blockquotes, this line should already be checked by that rule
    if state.sCount[nextLine] < 0:
        isContinuation = True

    if not isContinuation:
        terminatorRules = state.md.block.ruler.getRules("reference")
        oldParentType = state.parentType
        state.parentType = "reference"

        # Some tags can terminate paragraph without empty line.
        terminate = False
        for terminatorRule in terminatorRules:
            if terminatorRule(state, nextLine, endLine, True):
                terminate = True
                break

        state.parentType = oldParentType

        if terminate:
            # terminated by another block
            return None

    pos = state.bMarks[nextLine] + state.tShift[nextLine]
    maximum = state.eMarks[nextLine]

    # max + 1 explicitly includes the newline
    return state.src[pos : maximum + 1]


def link(state: StateInline, silent: bool) -> bool:
    href = ""
    title = ""
    label = None
    oldPos = state.pos
    maximum = state.posMax
    start = state.pos
    parseReference = True

    if state.src[state.pos] != "[":
        return False

    labelStart = state.pos + 1
    labelEnd = state.md.helpers.parseLinkLabel(state, state.pos, True)

    # parser failed to find ']', so it's not a valid link
    if labelEnd < 0:
        return False

    pos = labelEnd + 1

    if pos < maximum and state.src[pos] == "(":
        #
        # Inline link
        #

        # might have found a valid shortcut link, disable reference parsing
        parseReference = False

        # [link](  <href>  "title"  )
        #        ^^ skipping these spaces
        pos += 1
        while pos < maximum:
            ch = state.src[pos]
            if not isStrSpace(ch) and ch != "\n":
                break
            pos += 1

        if pos >= maximum:
            return False

        # [link](  <href>  "title"  )
        #          ^^^^^^ parsing link destination
        start = pos
        res = state.md.helpers.parseLinkDestination(state.src, pos, state.posMax)
        if res.ok:
            href = state.md.normalizeLink(res.str)
            if state.md.validateLink(href):
                pos = res.pos
            else:
                href = ""

            # [link](  <href>  "title"  )
            #                ^^ skipping these spaces
            start = pos
            while pos < maximum:
                ch = state.src[pos]
                if not isStrSpace(ch) and ch != "\n":
                    break
                pos += 1

            # [link](  <href>  "title"  )
            #                  ^^^^^^^ parsing link title
            res = state.md.helpers.parseLinkTitle(state.src, pos, state.posMax)
            if pos < maximum and start != pos and res.ok:
                title = res.str
                pos = res.pos

                # [link](  <href>  "title"  )
                #                         ^^ skipping these spaces
                while pos < maximum:
                    ch = state.src[pos]
                    if not isStrSpace(ch) and ch != "\n":
                        break
                    pos += 1

        if pos >= maximum or state.src[pos] != ")":
            # parsing a valid shortcut link failed, fallback to reference
            parseReference = True

        pos += 1

    if parseReference:
        #
        # Link reference
        #
        if "references" not in state.env:
            return False

        if pos < maximum and state.src[pos] == "[":
            start = pos + 1
            pos = state.md.helpers.parseLinkLabel(state, pos)
            if pos >= 0:
                label = state.src[start:pos]
                pos += 1
            else:
                pos = labelEnd + 1

        else:
            pos = labelEnd + 1

        # covers label == '' and label == undefined
        # (collapsed reference link and shortcut reference link respectively)
        if not label:
            label = state.src[labelStart:labelEnd]

        # Compatibility correction: explicit, collapsed and shortcut labels.
        if len(label) > 999:
            state.pos = oldPos
            return False
        label = normalizeReference(label)

        ref = state.env["references"].get(label, None)
        if not ref:
            state.pos = oldPos
            return False

        href = ref["href"]
        title = ref["title"]

    #
    # We found the end of the link, and know for a fact it's a valid link
    # so all that's left to do is to call tokenizer.
    #
    if not silent:
        state.pos = labelStart
        state.posMax = labelEnd

        token = state.push("link_open", "a", 1)
        token.attrs = {"href": href}

        if title:
            token.attrSet("title", title)

        # note, this is not part of markdown-it JS, but is useful for renderers
        if label and state.md.options.get("store_labels", False):
            token.meta["label"] = label

        state.linkLevel += 1
        state.md.inline.tokenize(state)
        state.linkLevel -= 1

        token = state.push("link_close", "a", -1)

    state.pos = pos
    state.posMax = maximum
    return True


def image(state: StateInline, silent: bool) -> bool:
    label = None
    href = ""
    oldPos = state.pos
    max = state.posMax

    if state.src[state.pos] != "!":
        return False

    if state.pos + 1 < state.posMax and state.src[state.pos + 1] != "[":
        return False

    labelStart = state.pos + 2
    labelEnd = state.md.helpers.parseLinkLabel(state, state.pos + 1, False)

    # parser failed to find ']', so it's not a valid link
    if labelEnd < 0:
        return False

    pos = labelEnd + 1

    if pos < max and state.src[pos] == "(":
        #
        # Inline link
        #

        # [link](  <href>  "title"  )
        #        ^^ skipping these spaces
        pos += 1
        while pos < max:
            ch = state.src[pos]
            if not isStrSpace(ch) and ch != "\n":
                break
            pos += 1

        if pos >= max:
            return False

        # [link](  <href>  "title"  )
        #          ^^^^^^ parsing link destination
        start = pos
        res = state.md.helpers.parseLinkDestination(state.src, pos, state.posMax)
        if res.ok:
            href = state.md.normalizeLink(res.str)
            if state.md.validateLink(href):
                pos = res.pos
            else:
                href = ""

        # [link](  <href>  "title"  )
        #                ^^ skipping these spaces
        start = pos
        while pos < max:
            ch = state.src[pos]
            if not isStrSpace(ch) and ch != "\n":
                break
            pos += 1

        # [link](  <href>  "title"  )
        #                  ^^^^^^^ parsing link title
        res = state.md.helpers.parseLinkTitle(state.src, pos, state.posMax, None)
        if pos < max and start != pos and res.ok:
            title = res.str
            pos = res.pos

            # [link](  <href>  "title"  )
            #                         ^^ skipping these spaces
            while pos < max:
                ch = state.src[pos]
                if not isStrSpace(ch) and ch != "\n":
                    break
                pos += 1
        else:
            title = ""

        if pos >= max or state.src[pos] != ")":
            state.pos = oldPos
            return False

        pos += 1

    else:
        #
        # Link reference
        #
        if "references" not in state.env:
            return False

        # /* [ */
        if pos < max and state.src[pos] == "[":
            start = pos + 1
            pos = state.md.helpers.parseLinkLabel(state, pos)
            if pos >= 0:
                label = state.src[start:pos]
                pos += 1
            else:
                pos = labelEnd + 1
        else:
            pos = labelEnd + 1

        # covers label == '' and label == undefined
        # (collapsed reference link and shortcut reference link respectively)
        if not label:
            label = state.src[labelStart:labelEnd]

        # Compatibility correction: explicit, collapsed and shortcut labels.
        if len(label) > 999:
            state.pos = oldPos
            return False
        label = normalizeReference(label)

        ref = state.env["references"].get(label, None)
        if not ref:
            state.pos = oldPos
            return False

        href = ref["href"]
        title = ref["title"]

    #
    # We found the end of the link, and know for a fact it's a valid link
    # so all that's left to do is to call tokenizer.
    #
    if not silent:
        content = state.src[labelStart:labelEnd]

        tokens: list[Token] = []
        state.md.inline.parse(content, state.md, state.env, tokens)

        token = state.push("image", "img", 0)
        token.attrs = {"src": href, "alt": ""}
        token.children = tokens or None
        token.content = content

        if title:
            token.attrSet("title", title)

        # note, this is not part of markdown-it JS, but is useful for renderers
        if label and state.md.options.get("store_labels", False):
            token.meta["label"] = label

    state.pos = pos
    state.posMax = max
    return True


def paragraph(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    LOGGER.debug(
        "entering paragraph: %s, %s, %s, %s", state, startLine, endLine, silent
    )

    nextLine = startLine + 1
    ruler = state.md.block.ruler
    terminatorRules = ruler.getRules("paragraph")
    endLine = state.lineMax

    oldParentType = state.parentType
    state.parentType = "paragraph"

    # jump line-by-line until empty one or EOF
    while nextLine < endLine:
        if state.isEmpty(nextLine):
            break
        # this would be a code block normally, but after paragraph
        # it's considered a lazy continuation regardless of what's there
        if state.sCount[nextLine] - state.blkIndent > 3:
            nextLine += 1
            continue

        # quirk for blockquotes, this line should already be checked by that rule
        if state.sCount[nextLine] < 0:
            nextLine += 1
            continue

        # Some tags can terminate paragraph without empty line.
        terminate = False
        for terminatorRule in terminatorRules:
            if terminatorRule(state, nextLine, endLine, True):
                terminate = True
                break

        if terminate:
            break

        nextLine += 1

    content = state.getLines(startLine, nextLine, state.blkIndent, False).strip(" \t\r\n")

    state.line = nextLine

    token = state.push("paragraph_open", "p", 1)
    token.map = [startLine, state.line]

    token = state.push("inline", "", 0)
    token.content = content
    token.map = [startLine, state.line]
    token.children = []

    token = state.push("paragraph_close", "p", -1)

    state.parentType = oldParentType

    return True


# HTML must be parsed so block ownership and hidden references are understood.
# No GFM plugins: task-list markers remain ordinary paragraph text.
PARSER = MarkdownIt("commonmark", {"html": True})
PARSER.block.ruler.at("reference", reference)
PARSER.block.ruler.at("paragraph", paragraph)
PARSER.inline.ruler.at("link", link)
PARSER.inline.ruler.at("image", image)


def read_text(relative: str) -> str:
    path = ROOT / relative
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AssertionError(f"missing required file: {relative}") from exc
    except (UnicodeDecodeError, OSError) as exc:
        raise AssertionError(f"cannot read required file: {relative}: {exc}") from exc
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


def inline_prose(children: list[Token]) -> tuple[str, ...]:
    """Project decoded text, preserving boundaries around excluded inline nodes.

    The parser owns escapes, entities, emphasis eligibility and resolved links.
    Code, images (including alt text), HTML and unknown nodes split the text;
    they cannot disappear in a way that manufactures a required phrase.
    """
    parts: list[str] = []
    blocks: list[str] = []

    def flush() -> None:
        text = re.sub(r"[ \t\r\n]+", " ", "".join(parts)).strip(" \t")
        if text:
            blocks.append(text)
        parts.clear()

    for child in children:
        if child.type == "text":
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append(" ")
        elif child.type in {
            "em_open", "em_close", "strong_open", "strong_close",
            "link_open", "link_close",
        }:
            continue
        else:
            flush()
    flush()
    return tuple(blocks)


def parse_document(text: str) -> Document:
    """One parse provides block ownership, references, headings and prose.

    Only level-2 ATX headings count toward inventories; Setext headings are
    intentionally ineligible. ATX headings at any level can supply prose.
    Separate leaf blocks and excluded inline nodes never join into a phrase.
    """
    tokens = PARSER.parse(text)
    headings: list[Heading] = []
    prose: list[ProseBlock] = []
    for index, token in enumerate(tokens):
        if token.type != "inline":
            continue
        owner = tokens[index - 1]
        atx = owner.type == "heading_open" and owner.markup.startswith("#")
        if owner.type != "paragraph_open" and not atx:
            continue
        line = (token.map or owner.map or [0])[0] + 1
        segments = inline_prose(token.children or [])
        prose.extend(ProseBlock(segment, line) for segment in segments)
        if atx and owner.tag == "h2" and segments:
            headings.append(Heading("\n".join(segments), line))
    return Document(tuple(headings), tuple(prose))



def markdown_level2_headings(text: str) -> tuple[str, ...]:
    return tuple(heading.title for heading in parse_document(text).headings)


def hypothesis_headings(text: str) -> tuple[str, ...]:
    return tuple(h for h in markdown_level2_headings(text)
                 if HYPOTHESIS_HEADING_RE.fullmatch(h))


def terminology_headings(text: str) -> tuple[str, ...]:
    return markdown_level2_headings(text)


def invariant_headings(text: str) -> tuple[str, ...]:
    return tuple(h for h in markdown_level2_headings(text)
                 if INVARIANT_HEADING_RE.fullmatch(h))


def markdown_rendered_prose_text(text: str) -> str:
    return "\n".join(block.text for block in parse_document(text).prose)


def validate_texts(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []

    missing = [relative for relative in REQUIRED_FILES if relative not in texts]
    if missing:
        errors.extend(f"missing required file: {relative}" for relative in missing)
        return errors

    documents = {name: parse_document(texts[name]) for name in REQUIRED_FILES}
    observed_hypotheses = tuple(
        heading.title for heading in documents["HYPOTHESES.md"].headings
        if HYPOTHESIS_HEADING_RE.fullmatch(heading.title)
    )
    if observed_hypotheses != HYPOTHESES:
        errors.append(
            "hypothesis headings must exactly match the Phase 0 contract "
            f"(expected {HYPOTHESES!r}, observed {observed_hypotheses!r})"
            f"; HYPOTHESES.md headings at lines "
            + ", ".join(str(h.line) for h in documents["HYPOTHESES.md"].headings)
        )

    observed_terms = tuple(h.title for h in documents["TERMINOLOGY.md"].headings)
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

    observed_invariants = tuple(
        heading.title for heading in documents["INVARIANTS.md"].headings
        if INVARIANT_HEADING_RE.fullmatch(heading.title)
    )
    if observed_invariants != INVARIANTS:
        errors.append(
            "invariant headings must exactly match the Phase 0 contract "
            f"(expected {INVARIANTS!r}, observed {observed_invariants!r})"
            f"; INVARIANTS.md headings at lines "
            + ", ".join(str(h.line) for h in documents["INVARIANTS.md"].headings)
        )

    roadmap_headings = tuple(h.title for h in documents["ROADMAP.md"].headings)
    phase0_heading = "Phase 0 — Foundational Research Contract"
    if roadmap_headings.count(phase0_heading) != 1:
        errors.append("roadmap does not define exactly one Phase 0 foundational contract")

    if not any(
        "machine-checkable Phase 0 validator" in block.text
        for block in documents["ROADMAP.md"].prose
    ):
        errors.append("roadmap does not require Phase 0 validator")

    if not any(
        "The thesis is not treated as established fact" in prose.text
        for prose in documents["README.md"].prose
    ):
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
