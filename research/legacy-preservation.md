# Legacy Preservation

## Question
Can AI reduce the maintenance burden created by declining human expertise in legacy languages and systems?

## Hypothesis link
Primary: **H3 — Legacy Preservation Paradox**

## Motivation
A language can lose new adopters while remaining operationally important because valuable systems, numerical models, embedded software, or institutional workflows already depend on it.

The question is whether AI changes the economics and risk of maintaining software whose expert population is scarce.

## Candidate languages
Depending on reproducible toolchain availability and suitable corpora: COBOL, Fortran, Ada, C, older C++, and other historically important languages with maintained compilers or interpreters.

## Candidate experiments

### L1 — Explain and localize
Provide an unfamiliar legacy codebase plus a failing behavioural test. Measure defect-localization accuracy before any patch is accepted.

### L2 — Constrained repair
Require a minimal repair preserving a fixed behavioural contract. Measure success, regression, compiler/test cycles, intervention, and unsupported assumptions.

### L3 — Repair versus rewrite
Compare constrained repair against a rewrite into a modern language. Both are evaluated against the same observable contract plus declared non-functional requirements.

## Safety boundary
Toy or public experiments cannot establish that autonomous maintenance is safe for production banking, trading, medical, industrial, defence, or other mission-critical systems.

## Falsification pressure
The paradox is weakened if AI fails to improve maintenance outcomes, substantially increases verification burden, or produces behaviourally unsafe changes at a rate that negates maintenance savings.

## Phase 0 position
Untested.
