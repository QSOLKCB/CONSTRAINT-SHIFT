# Specification Primacy

## Question
Does AI-assisted development increase the practical value of a persistent specification as a carrier of software intent?

## Hypothesis link
Primary: **H1 — Specification Primacy**

## Operational distinction
A **prompt** is an instruction used for one interaction. A **persistent specification** is a retained artifact that defines required behaviour, constraints, acceptance conditions, or interfaces and is reused across implementation or verification steps.

## Candidate experiments

### S1 — Regeneration
Create a fixed behavioural specification and generate multiple independent implementations. Measure acceptance-suite pass rate, behavioural divergence, required human correction, and differences not permitted by the specification.

### S2 — Change propagation
Modify one requirement in the specification and ask the agent to update an existing implementation. Compare against a matched workflow where the change exists only in conversational instruction.

### S3 — Implementation replacement
Replace an implementation with a newly generated implementation in the same or a different language while preserving an observable contract.

## Evidence needed
H1 requires more than successful generation. Useful evidence must show that retaining the specification contributes to reproducibility, regeneration, maintenance, or verification under matched conditions.

## Failure modes
- acceptance tests encode behaviour not stated in the specification;
- the specification merely restates implementation details;
- conversational context leaks into supposedly specification-only trials;
- repeated generations are scored subjectively instead of against a fixed contract.

## Phase 0 position
Untested.
