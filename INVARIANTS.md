# Research Invariants

These rules constrain every experimental phase unless a later change explicitly amends the research contract and documents compatibility with prior evidence.

## I1 — No conclusion by model assertion
An LLM output, prediction, ranking, or explanation is not evidence for a project hypothesis by itself.

## I2 — Equivalent-task comparisons
Cross-language, cross-tool, and cross-agent comparisons must begin from an equivalent task contract. Language-specific accommodations must be declared rather than hidden.

## I3 — Preserve failures
Failed generations, compiler failures, abandoned repair paths, timeouts, and invalid outputs are part of the evidence and must not be silently discarded.

## I4 — Record intervention
Human intervention must be recorded at a useful granularity. Manual fixes may not be attributed to an agent.

## I5 — Record environment
Experiments must retain enough environment information to interpret the result, including model/tool identity, toolchain versions, task/specification identity, and execution platform where relevant.

## I6 — Separate generation from verification
A system that generates an implementation must not be treated as independent verification merely because it also says the implementation is correct.

## I7 — Observable contracts before equivalence claims
Implementation fungibility or behavioural equivalence claims require an explicit observable contract and a declared comparison procedure.

## I8 — No predetermined language winner
The project must not choose metric weights or task suites solely to produce a preferred language ranking.

## I9 — Negative results are publishable results
A result that contradicts the central thesis remains valid project output if the method and evidence are sound.

## I10 — Social experiments control the artifact
Tool-legitimacy experiments must hold the evaluated artifact constant across disclosure conditions unless artifact variation is itself the declared independent variable.

## I11 — Human-subject safeguards
Experiments involving human participants must document consent, privacy, data handling, and applicable ethics or institutional requirements before public claims are made from participant data.

## I12 — Motivation is not evidence
Historical analogies, anecdotes, popularity trends, and project origin stories may motivate a hypothesis but do not count as experimental confirmation.

## I13 — Reproducible validators
Machine-derived claims should be accompanied by reproducible validators or analysis code where practical.

## I14 — Contract changes are explicit
Changes to hypotheses, terminology, methodology, or invariants that affect interpretation of existing results must be versioned and explained.
