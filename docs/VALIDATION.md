# Phase 0 validation policy

The validator checks the foundational research contract. It parses each required
Markdown file once per validation, then derives heading inventories and separate
prose blocks from that same token stream. Reference resolution and quote/list
ownership belong to the parser. There are no independent visibility, reference,
code-masking, HTML-state or prose-assembly scans.

## Installation and dialect

Use Python 3.12 or 3.14 and install `requirements.txt` with
`python3 -m pip install --require-hashes -r requirements.txt`.
`markdown-it-py==4.2.0` and its runtime dependency `mdurl==0.1.2` are pinned to
universal-wheel hashes. The standard-library `unittest` runner remains in use;
the validator and tests now require the parser dependency.

The dialect is the explicit `commonmark` preset with HTML enabled and no GFM
extensions. Task-list markers are ordinary paragraph text. HTML parsing is
needed to identify hidden regions and reference-definition boundaries, even
though HTML nodes cannot satisfy prose requirements.

Two compatibility corrections run as rules inside the same parser:

- Reference labels at definitions and uses are limited to 999 source characters
  before whitespace normalization. Oversized syntax remains literal text.
- Paragraphs trim only ASCII Markdown whitespace, preserving Unicode content.

The corrected rules retain upstream 4.2.0 code and state; only length guards and
one trimming operation differ. They are not an alternative parser. Attribution
and removal criteria are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
When upgrading the dependency, rerun all behavioral tests and remove corrections
that upstream has made unnecessary.

## Contract checks

- All eleven required files must be readable, valid UTF-8, and nonempty.
- Level-2 **ATX** heading inventories must preserve exact titles, order and
  multiplicity for hypotheses, invariants and terminology. Nested headings are
  eligible. Setext headings are deliberately excluded.
- Heading titles use decoded text: equivalent entities, escapes, emphasis and
  visible link labels are accepted. Excluded inline nodes retain a boundary.
- The roadmap must contain exactly one `Phase 0 — Foundational Research Contract`
  heading and `machine-checkable Phase 0 validator` in eligible prose.
- The README must contain `The thesis is not treated as established fact` in
  eligible prose. Literal emphasis delimiters are not required.
- Each supplied artifact must have at least 80 non-whitespace source characters.
  This is a size heuristic, not proof that its sections have meaningful bodies.

Eligible prose consists of decoded paragraph text and ATX heading text. Soft and
hard breaks normalize to spaces within a leaf block. Emphasis and visible link
labels contribute text. Inline/fenced/indented code, raw HTML, comments, images
(including alt text), reference definitions, and link destinations/titles do not.
Omitted nodes create boundaries. Distinct paragraphs, items and headings never
combine to manufacture a phrase. Required wording may appear within a larger
eligible text block; it need not be that block's entire contents.

The validator does not prove that a term has a substantive definition, that
methodological safeguards are enforced, or that a hypothesis is supported.
Missing/empty files, invalid encoding and other read failures produce diagnostics
and a nonzero CLI exit status. Heading mismatches include expected/observed
inventories and parser-provided source locations.

## Behavioral changes and verification

The previous scanners' tests included source-format assumptions and some
incorrect container expectations. The replacement preserves their fixtures but
updates these outcomes explicitly:

| Fixture | Expected behavior |
| --- | --- |
| Escaped backticks surrounding an incomplete inline comment before an ATX heading | Heading remains visible; the incomplete comment cannot cross that leaf boundary. |
| A bullet item followed by a dedented ordered list, including inside a quote | Ordered list is a new sibling block; its ATX heading remains visible. |
| A definition inside a list with tab-padded continuation destination/title | Reference metadata stays hidden. |
| An ordered item followed by a lazy `<span>` continuation and a new ATX heading | The pinned dialect keeps the span inline; the heading remains visible. |
| HTML tags between visible words | Separate eligible prose segments preserve the omitted-node boundary. |
| An unquoted ordered item after a quoted paragraph | The list is a separate block; its source marker is not prose. |

The last two parser container cases are tested as explicit behavior of the pinned
dialect, not a claim that every CommonMark implementation agrees on every
possible combination. Full CommonMark conformance is not asserted.

The suite retains existing contract mutations and Markdown regressions, promotes
all eighteen bundled review cases, covers the four latest PR findings, and tests
294 generated sibling/continuation transitions (including tabs). It also checks
code delimiter/backslash combinations, metadata exclusion, text-block separation,
reference-label limits, file failures, CLI status, and exactly one parse per
required file. A subprocess timeout bounds a 16,000-line inline-code paragraph to
15 seconds; it is a regression budget, not a benchmark claim.

The checked-in official CommonMark 0.31.2 corpus supplies 652 expected HTML
examples. CI compares parser output with that independently supplied HTML,
normalizing only the renderer's newline formatting in empty blockquotes. Forty
selected examples additionally have explicit expected adapter headings/prose,
including the project's exclusions. Corpus attribution is retained alongside it.
