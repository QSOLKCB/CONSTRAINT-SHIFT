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

## Primary assistance contrast

H3 is comparative. Successful AI-assisted maintenance alone cannot establish reduced maintenance burden.

For each primary legacy-maintenance task, compare matched conditions:

- **AI-assisted maintenance:** the maintainer may use the predeclared AI assistant and the conventional tools allowed by the protocol.
- **Unassisted conventional maintenance:** no generative AI is available; the maintainer receives the same code, task contract, behavioural tests, documentation access, and conventional compiler/debugging tools.

Hold the task, acceptance suite, effort or time budget, execution environment, and allowed non-AI tools constant where practical. Match or stratify maintainer expertise. If the same participants experience both conditions, counterbalance tasks and condition order to reduce learning and carry-over effects; otherwise randomize matched participants/tasks where feasible.

Predeclare the primary burden measures, such as active human time, elapsed time, interventions, verification effort, or another justified cost measure. Do not switch to a more favorable burden metric after inspecting results.

## Candidate experiments

### L1 — Explain and localize
Provide matched AI-assisted and unassisted maintainers with an unfamiliar legacy codebase plus the same failing behavioural test.

Measure defect-localization accuracy, time or effort to a correct localization, unsupported assumptions, and failure rate under the same stopping rule.

### L2 — Constrained repair
Require a minimal repair preserving a fixed behavioural contract in both assistance conditions.

Measure successful repair rate, behavioural regressions, compiler/test cycles, active human effort, elapsed time, verification burden, and unsupported assumptions introduced during the repair.

### L3 — Repair versus rewrite
Use a factorial comparison where practical:

- assistance: AI-assisted versus unassisted;
- strategy: constrained repair versus rewrite into a declared modern target.

All cells use the same observable behavioural contract and declared non-functional requirements. This distinguishes the effect of AI assistance from the separate repair-versus-rewrite decision.

## Interpretation

Evidence for H3 requires an improvement relative to the matched unassisted baseline. An AI-assisted success rate reported without that baseline is descriptive evidence about AI performance, not evidence that AI reduced legacy-maintenance burden.

Any apparent time or effort savings must be reported alongside verification cost and behavioural regressions. A faster patch that requires enough additional verification to erase the savings does not support the maintenance-cost mechanism.

## Safety boundary
Toy or public experiments cannot establish that autonomous maintenance is safe for production banking, trading, medical, industrial, defence, or other mission-critical systems.

Human-participant maintenance studies are also subject to I11 and the human-evaluation safeguards in METHODOLOGY.md.

## Falsification pressure
The paradox is weakened if AI-assisted conditions do not improve the predeclared maintenance outcomes or reduce burden relative to unassisted conventional maintenance, or if apparent gains are offset by verification burden or behavioural risk.

## Phase 0 position
Untested.
