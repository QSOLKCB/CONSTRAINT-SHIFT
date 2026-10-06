# CONSTRAINT-SHIFT

**Research and experiments on how AI shifts software development from code authorship toward specification, constraints, verification, and machine-generated implementation.**

CONSTRAINT-SHIFT treats a simple observation as a research problem: when implementation becomes cheap to generate, the scarce work may move upward into defining intent, constraining admissible solutions, verifying outcomes, and selecting among candidate implementations.

## Central thesis

> AI does not merely automate programming. It can change the unit of software authorship from implementation production toward specification, constraint design, verification, and selection among machine-generated implementations.

This is a hypothesis-driven repository. The thesis is **not treated as established fact**. Claims must earn support through reproducible experiments and retained evidence.

## Research tracks

- [Specification primacy](research/specification-primacy.md)
- [Programming-language selection](research/language-selection.md)
- [Legacy preservation](research/legacy-preservation.md)
- [AI-assisted modding](research/ai-modding.md)
- [Tool legitimacy gap](research/tool-legitimacy-gap.md)

## Foundation

Phase 0 defines the research contract:

- [Hypotheses](HYPOTHESES.md) — six falsifiable hypotheses.
- [Terminology](TERMINOLOGY.md) — stable definitions for project terms.
- [Methodology](METHODOLOGY.md) — common experiment and evidence rules.
- [Invariants](INVARIANTS.md) — non-negotiable research constraints.
- [Roadmap](ROADMAP.md) — implementation sequence from foundation to archival record.

The repository intentionally separates **motivation**, **hypothesis**, **measurement**, **evidence**, and **conclusion**.

## Phase 0 validation

The foundational contract is mechanically checked with the Python standard library only:

```bash
python3 scripts/validate_phase0.py
python3 -m unittest discover -s tests -v
```

The validator checks that required research artifacts exist, the six hypothesis identifiers are present, key terms are defined, and the roadmap records the Phase 0 contract.

## Planned experimental flow

```text
human intent
    |
    v
specification
    |
    v
constraints / contracts
    |
    v
machine-generated candidate implementation
    |
    v
compiler + tests + static / formal checks
    |
    v
retained evidence
    |
    v
supported, weakened, or falsified claim
```

## Current status

**Phase 0 — Foundational Research Contract**

No language ranking, legacy-survival claim, modding claim, or social-perception claim is considered established merely because it appears in project motivation. Empirical phases begin after the research contract is merged.

## Scope

The project is interested in:

- spec-driven and contract-driven AI development;
- compiler and toolchain feedback as machine guidance;
- machine-verifiable programming-language properties;
- legacy-language maintenance and preservation;
- implementation fungibility across languages and toolchains;
- AI-assisted game modification and mechanic recombination;
- disclosure effects on perceptions of AI-assisted work.

The project is **not** a leaderboard for preferred programming languages and is not designed to prove that AI-generated software is inherently better or worse than human-authored software.

## License

See [LICENSE](LICENSE).
