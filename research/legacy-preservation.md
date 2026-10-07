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

## Scarcity and lifecycle operationalization

H3 specifically concerns **scarce human expertise** and **operational lifetime**, so neither may be inferred from one short repair task with plentiful experts.

Before inspecting H3 outcomes, predeclare at least two expertise/scarcity strata. Suitable designs include:

- maintainers stratified by independently established language-specific expertise;
- conditions with high versus constrained access to qualified expert consultation under a fixed expert-hour budget;
- a combination of maintainer expertise and expert-access limits.

Scarcity strata must be defined independently of the AI-assisted outcomes. Age, language popularity, or anecdotal claims about a shrinking workforce are not substitutes for a measured experimental scarcity condition.

Also predeclare a **maintenance-viability horizon** or equivalent lifecycle proxy. One suitable proxy is the number of sequential maintenance tasks that can be completed while preserving the behavioural contract before a fixed cumulative maintenance budget, scarce-expert-hour budget, or stopping threshold is exhausted.

This horizon is a laboratory proxy for retention pressure, not a direct estimate of calendar years of production lifetime. Any extrapolation from the proxy to real system retirement must be reported separately and cannot be treated as established by these experiments.

Primary H3 analysis should compare AI-assisted and unassisted maintenance **within each scarcity stratum** and test whether AI reduces scarce-expert consumption and/or extends the predeclared maintenance-viability horizon as expert access becomes more constrained.

## Candidate experiments

### L1 — Explain and localize across scarcity strata
Provide matched AI-assisted and unassisted maintainers with an unfamiliar legacy codebase plus the same failing behavioural test in each predeclared expertise/scarcity stratum.

Measure defect-localization accuracy, time or effort to a correct localization, scarce-expert consultation consumed, unsupported assumptions, and failure rate under the same stopping rule.

### L2 — Constrained repair across scarcity strata
Require a minimal repair preserving a fixed behavioural contract in both assistance conditions and repeat across the predeclared expertise/scarcity strata.

Measure successful repair rate, behavioural regressions, compiler/test cycles, active human effort, scarce-expert consultation consumed, elapsed time, verification burden, and unsupported assumptions introduced during the repair.

### L3 — Repair versus rewrite
Use a factorial comparison where practical:

- assistance: AI-assisted versus unassisted;
- strategy: constrained repair versus rewrite into a declared modern target.

All cells use the same observable behavioural contract and declared non-functional requirements. This distinguishes the effect of AI assistance from the separate repair-versus-rewrite decision.

### L4 — Maintenance-viability horizon
Run a predeclared sequence of representative maintenance tasks under a fixed cumulative maintenance budget and scarce-expert-hour budget.

Compare AI-assisted and unassisted conditions on:

- number of tasks completed while preserving the behavioural contract;
- cumulative scarce-expert consultation consumed;
- cumulative verification effort;
- the task or threshold at which the maintenance budget is exhausted.

This experiment supplies the lifecycle proxy required by H3. It does not by itself establish a real-world calendar lifetime.

## Interpretation

Evidence for H3 requires an improvement relative to the matched unassisted baseline **under predeclared scarce-expertise conditions** and evidence on the declared maintenance-viability horizon or equivalent lifecycle proxy. An AI-assisted success rate reported without those comparisons is descriptive evidence about AI performance, not evidence for the full Legacy Preservation Paradox.

Any apparent time, expert-access, or effort savings must be reported alongside verification cost and behavioural regressions. A faster patch that requires enough additional verification to erase the savings does not support the maintenance-cost mechanism. A short benchmark must not be described as directly proving extra calendar years of operational life.

## Safety boundary
Toy or public experiments cannot establish that autonomous maintenance is safe for production banking, trading, medical, industrial, defence, or other mission-critical systems.

Human-participant maintenance studies are also subject to I11 and the human-evaluation safeguards in METHODOLOGY.md.

## Falsification pressure
The paradox is weakened if AI-assisted conditions do not reduce burden relative to unassisted conventional maintenance under scarce-expertise strata, if AI does not reduce scarce-expert consumption as access tightens, if the predeclared maintenance-viability horizon is not extended, or if apparent gains are offset by verification burden or behavioural risk.

## Phase 0 position
Untested.
