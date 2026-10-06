# Terminology

Phase 0 fixes the initial vocabulary used by CONSTRAINT-SHIFT. Definitions may be revised only when the change is explicit and the effect on prior experiments is documented.

## Constraint Shift
**Constraint Shift** is the hypothesized movement of software-development effort away from direct implementation authoring and toward specification, constraint design, verification, evidence production, and selection among generated implementations as AI implementation capability increases.

## Specification Primacy
**Specification Primacy** is the condition in which a persistent specification becomes a principal carrier of intended behaviour and can drive implementation, testing, regeneration, or verification.

A repository containing documentation is not sufficient evidence of specification primacy. The specification must materially constrain or generate downstream work.

## Implementation Fungibility
**Implementation Fungibility** is the degree to which one implementation can be replaced, regenerated, translated, or substantially rewritten while preserving externally specified behaviour and required verified properties.

Fungibility is always relative to an explicit contract.

## AI Language Fitness
**AI Language Fitness** is a multidimensional description of how well a programming language and its toolchain support AI-assisted generation, diagnosis, repair, verification, interoperability, and deployment for a defined workload.

Phase 0 deliberately does **not** define a universal scalar score or fixed weights.

## Machine Verifiability
**Machine Verifiability** is the extent to which properties of an implementation can be checked automatically by compilers, type systems, static analyzers, proof systems, tests, model checkers, or other reproducible tools.

## Diagnostic Feedback Quality
**Diagnostic Feedback Quality** is the usefulness of machine-produced feedback for locating and repairing implementation defects.

## Legacy Preservation Paradox
**Legacy Preservation Paradox** is the hypothesis that AI assistance can extend the useful lifetime of legacy systems and languages by reducing maintenance cost associated with scarce human expertise, even when the human programmer population for those languages is declining.

## Second Modding Revolution
**Second Modding Revolution** is the proposed analogy between earlier tool-enabled modding ecosystems and AI-assisted modification, where natural-language direction and agentic tooling may reduce the technical barrier to experimentation and increase the rate of software mutation and recombination.

## Modding Mutation Rate
**Modding Mutation Rate** is the number of distinct, executable modification attempts produced per unit of constrained effort under a defined experimental protocol.

## Recombination Acceleration
**Recombination Acceleration** is an increase in the rate at which previously separate mechanics, systems, genres, interfaces, or implementation patterns are combined into executable prototypes.

## Tool Legitimacy Gap
**Tool Legitimacy Gap** is a difference in evaluation of an otherwise equivalent artifact that is attributable to disclosed production method rather than demonstrated artifact behaviour.

## AI Disclosure Penalty
For an outcome variable R, an **AI Disclosure Penalty** may be represented as:

D_AI = R_undisclosed - R_AI-disclosed

A positive value indicates lower ratings after AI disclosure for that outcome.

## Research Contract
The **Research Contract** is the combination of hypotheses, definitions, methodology, invariants, and validation rules that constrain how CONSTRAINT-SHIFT can turn observations into claims.
