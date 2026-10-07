# Roadmap

The roadmap deliberately separates the research contract from empirical work.

## Phase 0 — Foundational Research Contract

**Status: implemented by the foundational PR**

Deliverables:

- [x] central thesis and scope;
- [x] six falsifiable hypotheses;
- [x] stable initial terminology;
- [x] methodology;
- [x] research invariants;
- [x] five research-track briefs;
- [x] machine-checkable Phase 0 validator;
- [x] standard-library `unittest` runner with pinned CommonMark parsing;
- [x] CI validation.

Exit criterion: the Phase 0 validator and test suite pass on the merged default branch.

## Phase 1 — Experiment Schema

**Status: implemented by the Phase 1 PR**

Deliverables:

- [x] versioned JSON Schema record;
- [x] task, agent, language, toolchain, environment, and trial metadata;
- [x] predeclared trial-handling and analysis rules;
- [x] intervention and verification-outcome records;
- [x] retained evidence manifest with SHA-256 identities;
- [x] successful and failed-trial examples;
- [x] dependency-free structural and semantic validator;
- [x] regression tests and CI validation.

Exit criterion: the Phase 1 validator accepts the retained examples, the failed-trial example remains a valid explicit failure, and the repository test suite passes.

## Phase 2 — Language Harness

**Status: implemented by the Phase 2 PR**

Deliverables:

- [x] one frozen bounded-integer task with eight shared acceptance cases;
- [x] C, C++, Rust, Go, and Python reference adapters;
- [x] isolated working directories, process-group deadlines, and bounded output capture;
- [x] source/contract snapshots, observed toolchain identity, and retained raw execution evidence;
- [x] schema `2.0.0` records for successful, failed, timed-out, and invalid/unavailable trials;
- [x] physical evidence verification, regression tests, and all-five-adapter CI artifacts.

Exit criterion: the five reference adapters satisfy the same frozen acceptance suite in CI, emitted records and physical evidence verify, and repository tests pass. No hypothesis support is inferred from smoke coverage.

TypeScript, Java, Ada, Fortran, and COBOL remain candidate additions where reproducible toolchains are practical. See [Language harness](docs/LANGUAGE_HARNESS.md) for the implemented scope and replay limits.

## Phase 3 — Compiler Feedback Experiment
Test H2 by measuring whether diagnostic and constraint feedback changes agent repair performance.

## Phase 4 — Legacy Preservation
Test H3 using authorized legacy or legacy-style code with constrained maintenance tasks.

## Phase 5 — Implementation Fungibility
Test how far implementations can be regenerated or translated while preserving observable behaviour.

## Phase 6 — AI Modding and Recombination
Test H4 and H5 using controlled modification and mechanic-recombination tasks.

## Phase 7 — Tool Legitimacy Gap
Design and, where appropriate, run a controlled disclosure study for H6.

## Phase 8 — AI Language Fitness Model
Derive a multidimensional language/toolchain comparison from accumulated measurements. Do not assign a universal scalar ranking unless data justify a declared aggregation method.

## Phase 9 — Replication and Sensitivity
Repeat key experiments across alternative tasks, models, versions, toolchains, and analysis choices.

## Phase 10 — Technical Record and Archival Release
Produce a bounded technical synthesis, release artifacts, machine-readable evidence, reproducibility instructions, and archival metadata suitable for long-term citation.
