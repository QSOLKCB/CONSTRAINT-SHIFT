# TASK-FOLD-001 — Bounded integer fold, version 1.0.0

Input is ASCII text: an integer count `n`, then exactly `n` signed integer values,
separated by ASCII whitespace. Integer tokens may have an optional `+`/`-` sign
and leading zeros; they are always decimal, so `+008` is eight and `-0` is zero.
`0 <= n <= 64` and every value is in `[-1000, 1000]`.
Each invocation receives one valid input and then EOF. Invalid-input behaviour is
outside this first task contract.

Output is exactly `n sum sum_of_squares\n` in ASCII decimal, with one space between
fields and one LF at the end. No extra stdout, no stderr, and exit status zero.
For an empty input list the output is `0 0 0\n`. The largest sum of squares is
64,000,000, so the task does not require overflow-prone arithmetic in any adapter.

The acceptance suite is frozen in `cases.json`. Implementations use the same
observable contract; parsing and language-required boilerplate may differ.
The fixtures are reference implementations, not AI generation or repair trials.
Passing these finite cases establishes only harness smoke coverage, not universal
equivalence, language fitness, or support for H2.
