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

Phase 1 defines how experimental work is retained:

- [Experiment schema](docs/EXPERIMENT_SCHEMA.md) — versioning, field semantics, evidence references, failure retention, and validation policy.
- [`experiment-record.schema.json`](schema/experiment-record.schema.json) — JSON Schema Draft 2020-12 structural contract.
- [Schema examples](schema/examples/) — successful and explicitly failed trials.

The repository intentionally separates **motivation**, **hypothesis**, **measurement**, **evidence**, and **conclusion**.

## Validation

The foundational contract uses Python 3.12 or 3.14 and a pinned CommonMark parser.
Install the hashed Phase 0 dependencies before running the full validation suite:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --require-hashes -r requirements.txt
python3 scripts/validate_phase0.py
python3 scripts/validate_phase1.py
python3 -m unittest discover -s tests -v
```

The Phase 0 validator checks required files, exact ordered hypothesis/invariant/terminology
heading inventories, two required prose statements, the Phase 0 roadmap heading,
and a non-whitespace source-size heuristic. It does not assess the completeness
of section bodies or establish empirical support for any hypothesis.

The Phase 1 validator checks the versioned experiment-record schema, retained examples,
strict declared fields, evidence references, intervention ordering, time ordering,
duplicate JSON keys, non-JSON numeric constants, and repository-relative evidence paths.
A failed trial remains a valid record when it accurately records the failure.

[Phase 0 validation policy](docs/VALIDATION.md) defines eligible headings, decoded prose,
excluded metadata, parser compatibility corrections, and regression coverage.
[Phase 1 schema policy](docs/EXPERIMENT_SCHEMA.md) defines record semantics and versioning.

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

**Phase 1 — Experiment Schema**

The repository now has a versioned machine-readable record for tasks, agents, languages, toolchains, environments, trials, interventions, verification outcomes, and retained evidence. No language ranking, legacy-survival claim, modding claim, or social-perception claim is considered established by the schema itself.

Phase 2 will build the first equivalent-task language harness on top of this record contract.

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
