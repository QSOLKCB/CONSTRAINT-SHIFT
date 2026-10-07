# Phase 2 — Language Harness

The first harness executes one frozen task contract across C, C++, Rust, Go, and
Python. It uses the Python standard library and emits Phase 1 schema `2.0.0`
records with physical SHA-256-bound evidence. Harness version and task version
are each `1.0.0`; they are separate from the record schema version.

## Run

From the repository root, with Python 3.12 or newer on a POSIX host:

```bash
python3 scripts/language_harness.py list
python3 scripts/language_harness.py run --languages c cpp python --output evidence/my-run
python3 scripts/language_harness.py verify evidence/my-run
```

To run every implemented adapter, omit `--languages`. Every selected language
is retained, including unavailable toolchains. Use a new output directory for
each invocation; existing output is rejected without overwriting it. Output
must resolve inside this repository because schema evidence paths are relative
to its root. Explicit source/output arguments resolve from the caller's working
directory, so invocation from an external directory is supported.

To execute alternative implementations of the same task:

```bash
python3 scripts/language_harness.py run --languages python --sources /path/to/candidates --timeout 5 --output-limit 1048576 --output evidence/candidate-run
```

`--sources` must contain the same language subdirectories and filenames as the
reference fixtures. This phase executes supplied code; it does not call an LLM,
attempt repair, or infer its author's identity. The acting agent in each record
is the scripted harness. Authoring provenance belongs to a later generation
protocol rather than an invented model/provider label.

Exit codes: `0` means every selected trial succeeded (or integrity verification
passed), `1` means at least one retained trial did not succeed (or verification
found a mismatch), and `2` means a command/configuration/I/O error. An unavailable
compiler is an invalid retained trial, not a silent omission or a passing skip.

## Equivalent task

[TASK-FOLD-001](../harness/tasks/bounded-integer-fold/TASK.md) accepts a count and
up to 64 integers bounded to `[-1000, 1000]`. It returns the count, sum, and sum of
squares. These bounds avoid language-specific overflow requirements.

Eight frozen cases cover empty input, positive and negative values, zeros,
numeric bounds, mixed values, maximum count, and balanced maximum count. The
harness checks the case file against a separate integer oracle before execution.
Acceptance requires exact ASCII stdout bytes, empty stderr, and exit status zero.
Invalid-input behaviour is deliberately outside this task's domain.

| Adapter | Tool | Source | Declared accommodation |
| --- | --- | --- | --- |
| `c` | GCC | `c/main.c` | C11, `-O0`, warning diagnostics as errors |
| `cpp` | G++ | `cpp/main.cpp` | C++17, `-O0`, warning diagnostics as errors |
| `rust` | rustc | `rust/main.rs` | Edition 2021, optimization level zero |
| `go` | Go | `go/main.go` | Standard library only, modules/workspaces/CGO disabled |
| `python` | Harness interpreter | `python/main.py` | Isolated mode; syntax compile without writing bytecode |

There are no third-party candidate dependencies. The compilers' standard
libraries and runtimes are external toolchain dependencies and are recorded as
such. TypeScript, Java, Ada, Fortran, and COBOL remain candidates for later
adapters; they are not reported as implemented or silently substituted.

## Frozen procedure and outcomes

The task, cases, harness, record validator, schema, all selected sources, and analysis rules are
copied before any subprocess executes. One version probe and one build are
attempted per selected language. Cases run in declared order and stop at the
first failure; remaining case IDs are retained as `cases_not_run`. There are no
retries or post-outcome exclusions.

The default process deadline is 30 seconds, with a shared 1 MiB stdout/stderr
capture limit per process. A process group is terminated on timeout or output
overflow, including descendants that keep output pipes open. Output overflow
is a failure with explicitly truncated retained output. A deadline is a timeout;
missing tools/sources, unusable version identity, or process-start errors are
invalid; compiler diagnostics, nonzero exits, stderr, and output mismatches are
failures. No failed result is deleted merely because later languages succeed.

The harness uses controlled locale, timezone, and Go settings. It retains the
exact execution environment it supplies, including the inherited tool search
path and home directory. Fresh temporary Go caches are removed after the run.
OS/kernel/architecture and full observed tool version output are retained.
Process bounds are not a sandbox: supplied programs execute with the operator's
permissions. Use an isolated host/container when candidates require isolation.

## Evidence and verification

Each bundle contains `contract/` snapshots, one directory per selected language,
and `summary.json`. Language directories retain source, available compiled
binary, version/build/case argv and exit codes, monotonic process durations,
inputs, expected bytes, actual stdout/stderr bytes, result decisions, and
`record.json`. Every selected trial has explicit tool identity, build, and
behavioural verification outcomes, including evidence-backed `not_run` entries.

`verify` checks record schemas, selected-language retention, summary agreement,
and every listed evidence file's SHA-256 and byte count. Evidence must resolve
within the bundle. Integrity verification can succeed for a correctly retained
failed trial. It does not rerun acceptance or authenticate the producer; custody
and signatures are outside Phase 2. Keep the records and their evidence together
at the recorded repository-relative location.

The acceptance procedure is external to the candidate program; the records
conservatively set `independent_from_generator` to false because independent
fixture-author/verifier provenance has not been established.

## CI and reproducibility limits

The Phase 2 workflow runs all five adapters on Ubuntu 24.04 with GCC 13 tools,
Python 3.12.14, Rust 1.85.0, and Go 1.24.0. Python/Rust/Go release selections are
fixed; GCC package revision and runner image can change and their observed
identities are retained. This is source/contract replay support, not a claim of
bit-identical builds or identical timings on mutable hosted runners. The full
version logs, flags, platform, and inputs identify the tested conditions.

CI verifies the emitted records and retains the bundle as an Actions artifact
for 30 days even when execution fails. Download artifacts before that expires
when a run is intended for longer retention.

```bash
python3 -m unittest discover -s tests -p test_phase2.py -v
python3 -m unittest discover -s tests -v
```

Reference smoke tests exercise adapters available on the current host; the
dedicated CI invocation explicitly selects all five and fails when any cannot
run successfully. The suite also tests missing tools/sources, compilation and
runtime failures, resource limits, descendant cleanup, corrupted evidence,
output preservation, and caller-relative invocation.

Passing these cases demonstrates the harness under the retained conditions.
It is not a universal equivalence proof, AI performance experiment, language
ranking, or empirical support for H2. Phase 3 adds the generation/diagnostic
feedback experiment under a separate frozen protocol.
