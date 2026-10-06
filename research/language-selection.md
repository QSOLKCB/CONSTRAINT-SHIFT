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

## Candidate experiment
Give one agent/model an equivalent task contract across several languages.

Record first-generation validity, compile attempts, diagnostic cycles, test failures, repair iterations, human interventions, completion outcome, static/formal check outcomes, and time/token/cost data where reliable.

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
