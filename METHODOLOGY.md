# Methodology

## Purpose
CONSTRAINT-SHIFT is designed as an empirical research repository, not a collection of AI-development predictions. Each experiment should connect a falsifiable hypothesis to an operational definition, controlled procedure, retained evidence, and bounded conclusion.

## Common experiment lifecycle

1. **Select hypothesis.** Identify the exact hypothesis and sub-claim under test.
2. **Freeze task contract.** Define inputs, outputs, acceptance conditions, resource limits, and stopping rules before comparison.
3. **Declare factors.** Record independent variables such as language, compiler, agent, disclosure condition, or assistance mode.
4. **Declare controls.** Identify variables held constant and unavoidable differences.
5. **Run trials.** Preserve successful and failed trials.
6. **Verify independently.** Use compilers, tests, static checks, formal tools, or blinded evaluation appropriate to the claim.
7. **Retain evidence.** Store machine-readable results plus enough provenance to reproduce interpretation.
8. **Analyze.** Report distributions and uncertainty rather than only best-case examples.
9. **Bound the conclusion.** State what was tested and what was not.
10. **Attempt replication.** Prefer conclusions that survive reruns, alternative tasks, and changed models/toolchains.

## Experimental unit
The experimental unit must be explicit: one generation attempt, repair trajectory, task-language pair, legacy-maintenance task, modding task, participant evaluation, or another declared unit.

Repeated attempts from the same underlying task are not automatically independent observations.

## Comparability
Cross-language experiments must distinguish same specification from same implementation strategy, language-required boilerplate from task logic, ecosystem effects from core language/toolchain effects, model familiarity from language semantics, and compile-time failure from behavioural failure.

## AI execution metadata
Where available and permitted, record model/provider identifier, date, agent/tool version, relevant instructions, iteration count, compiler/tool cycles, reliable token/cost measures, human intervention, and termination reason.

If exact parameters are unavailable, record that limitation rather than inventing them.

## Toolchain metadata
Record language version, compiler/interpreter version, build flags, dependency lock state, analysis tools, operating system/architecture, test command, and materially relevant hardware.

## Evidence classes

### E0 — Motivation
Anecdote, historical example, external observation, or qualitative rationale. Useful for choosing a question; not confirmation.

### E1 — Single controlled trial
A reproducible result under one task/environment condition.

### E2 — Replicated controlled evidence
Repeated results under the same contract with retained failures and stable analysis.

### E3 — Cross-condition evidence
Results reproduced across materially different tasks, models, toolchains, systems, or participant samples.

## Metrics
Metrics are hypothesis-specific. Phase 0 approves categories, not fixed weights: success/failure, compile attempts, repair iterations, test-pass rate, static/formal outcomes, wall-clock duration, reliable token/cost data, human interventions, behavioural divergence, modification throughput, recombination completion, and controlled perception ratings.

Any composite score must publish its formula, normalization, weights, missing-data policy, and sensitivity to alternative weights.

## Statistical reporting
When sample size permits, report sample count, distributions, uncertainty, exploratory versus confirmatory status, exclusions, invalid trials, and dependence between repeated attempts.

## Human evaluation
Human-participant studies should randomize or counterbalance where appropriate, hold the artifact constant when testing disclosure, predefine primary outcomes, and document consent, privacy, data handling, and applicable ethics requirements.

## Legacy-code safety
Legacy experiments should use public, synthetic, redistributable, or otherwise authorized code. Toy experiments cannot establish safety for production banking, trading, medical, industrial, or other critical systems.

## Reproducibility target
A retained experiment should make it possible for an independent operator to answer:

> What was attempted, under which contract, with which tools, what happened, and how was the result judged?

If those questions cannot be answered, the experiment is incomplete.
