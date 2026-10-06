# Programming-Language Selection Under AI

## Question
Does AI-assisted development change which properties make a programming language and toolchain attractive for a workload?

## Hypothesis link
Primary: **H2 — Verification Selection**

## Working model
Traditional language choice includes ecosystem, performance, interoperability, deployment constraints, maintainability, and human ergonomics.

CONSTRAINT-SHIFT adds AI-relevant dimensions without assuming they dominate: machine verifiability, diagnostic feedback quality, generation success, repairability, tool automation, model familiarity, and ecosystem accessibility to agents.

## AI Language Fitness is a vector first
Phase 0 rejects a premature universal score. A language/toolchain observation should initially preserve separate measured dimensions. Definitions and measurement procedures must precede aggregation.

## Experimental design

H2 contains a causal idea — that machine-actionable diagnostics and enforceable constraints improve AI-assisted development — so the project must not infer that cause from a raw cross-language ranking alone.

### A — Cross-language outcome study

Give a fixed model/agent an equivalent task contract across several languages and toolchains.

Record first-generation validity, compile attempts, diagnostic cycles, test failures, repair iterations, human interventions, completion outcome, static/formal check outcomes, and time/token/cost data where reliable.

This study is **descriptive and associational**. It can show that language/toolchain outcomes differ under the tested conditions, but by itself it cannot establish that diagnostic quality or constraint strength caused the difference.

### B — Diagnostic-feedback ablation

Test diagnostic feedback within the same language, compiler/toolchain, task, model, dependency set, resource budget, and acceptance criteria.

Where technically practical, randomize otherwise matched trials between predeclared feedback conditions such as:

- full native compiler diagnostics;
- normalized diagnostics with nonessential explanatory detail removed;
- location/error-class information without full diagnostic prose;
- compile success/failure status with diagnostic text withheld.

The compiler's acceptance decision and task contract remain unchanged; only the diagnostic information exposed to the agent is manipulated.

Measure repair success, repair iterations, invalid edits, human intervention, time, and token/cost data where reliable.

A reproducible gradient across these conditions can support a causal claim about **diagnostic feedback** more directly than cross-language comparison.

### C — Constraint ablation

Constraint effects require a separate controlled design. Where a language/toolchain exposes a check that can be enabled or disabled without changing the task specification, compare matched trials with that check enforced versus withheld and verify both final outputs against the same external behavioural contract.

Examples may include optional static-analysis, lint, contract, or type-checking modes where the manipulation is well-defined. The exact check and semantic consequences must be documented.

If constraint strength cannot be varied cleanly within a toolchain, the project must report cross-language results as association rather than causal evidence for H2.

## Confound control

For controlled H2 experiments, hold constant where practical:

- model and model version;
- agent/tool version and system instructions;
- task specification and acceptance suite;
- dependency versions and allowed libraries;
- hardware/OS execution environment;
- resource and stopping budgets;
- initial context, aside from the declared feedback manipulation.

Randomize or counterbalance trial order, use fresh contexts where carry-over could occur, repeat across multiple tasks, and retain all failed trials.

Training-corpus familiarity and ecosystem maturity may remain residual confounds in cross-language studies. They should be measured or discussed rather than silently attributed to diagnostics.

## Important confounds
- training-corpus imbalance;
- package/library availability;
- task-language suitability;
- compiler maturity;
- agent-specific tool integration;
- differing safety guarantees;
- version skew.

## Legacy languages
COBOL, Fortran, Ada, C, and older C++ should not be evaluated solely by greenfield popularity. Installed-base value and maintenance constraints belong to the legacy-preservation track.

## Phase 0 position
No language is declared an AI-era winner or loser.
