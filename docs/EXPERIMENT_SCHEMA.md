# Phase 1 Experiment Schema

Phase 1 defines the machine-readable evidence record used by later CONSTRAINT-SHIFT experiments. It records what was attempted and under which frozen contract; it does not turn a trial into a conclusion.

## Files

- `schema/experiment-record.schema.json` — JSON Schema Draft 2020-12 structural contract.
- `schema/examples/success.json` — valid successful-trial example.
- `schema/examples/failed-trial.json` — valid failed-trial example demonstrating invariant I3.
- `scripts/validate_phase1.py` — dependency-free validator for the schema subset used here plus project semantic checks.
- `tests/test_phase1.py` — regression tests for versioning, strict fields, references, ordering, timestamps, paths, duplicate keys, and non-JSON numeric constants.

## Versioning

Every record declares `schema_version`. Phase 1 begins at `1.0.0`.

- **PATCH**: documentation, fixtures, or validator fixes that do not change valid record meaning.
- **MINOR**: backward-compatible schema additions whose semantics are explicitly documented.
- **MAJOR**: incompatible field, interpretation, or required-data changes.

The validator accepts the exact version it implements. Records are never silently upgraded or reinterpreted.

## Required record domains

A record contains:

1. schema identity and record identity;
2. linked project hypothesis identifiers;
3. the frozen task and equivalence group;
4. the generating or acting agent;
5. language and toolchain metadata;
6. execution environment;
7. the predeclared trial-handling and analysis contract;
8. one trial and its factors/measurements;
9. recorded interventions;
10. verification outcomes; and
11. a retained evidence manifest with SHA-256 identities.

Optional metadata should be omitted when unavailable rather than invented. Required values must describe the observed experiment, not an assumed default.

## Evidence references

`task.specification_ref`, `task.acceptance_ref`, optional agent/toolchain references, intervention references, and verification references resolve to `evidence[].evidence_id`.

The repository validator rejects dangling evidence references and duplicate evidence identifiers. Evidence paths are repository-relative and may not traverse through `..`.

The schema does not assert that a listed path currently has the declared digest. Later execution/archival phases may bind and verify physical evidence files. Phase 1 establishes the record contract and referential integrity.

## Failures are valid records

`trial.status` may be `success`, `failure`, `invalid`, `timeout`, or `aborted`. A failed trial is not schema-invalid merely because its outcome is negative.

The supplied `failed-trial.json` fixture must remain a valid record with status `failure`. This makes I3 — Preserve failures — executable at the schema layer.

## Verification separation

Each verification outcome records `independent_from_generator`. The field records independence; it does not manufacture it. A generator claiming its own output is correct is not independent verification under I6.

Verification evidence must be retained through at least one evidence reference, including for `not_run` outcomes (for example, a retained log explaining why verification could not run).

## Predeclaration

The `predeclared` object carries the experiment rules required by the methodology before outcome inspection: experimental unit, acceptance criteria, resource limits, stopping rule, inclusion/exclusion rules, invalid-trial rule, timeout rule, missing-data rule, and primary denominators.

This keeps later analysis from silently changing the denominator or deleting inconvenient failures after results are known.

## Deliberate exclusions

Phase 1 does **not** define:

- a language leaderboard;
- a universal composite score;
- a Phase 2 execution harness;
- hypothesis-support labels inside raw trial records; or
- automatic empirical conclusions.

Those belong to later phases and must remain separable from the evidence record.

## Validation

```bash
python3 scripts/validate_phase1.py
python3 -m unittest tests.test_phase1 -v
```

The normal repository test discovery also includes the Phase 1 tests:

```bash
python3 -m unittest discover -s tests -v
```
