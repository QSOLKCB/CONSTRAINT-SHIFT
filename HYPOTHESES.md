# Hypotheses

CONSTRAINT-SHIFT begins with six falsifiable hypotheses. A hypothesis may be supported, weakened, rejected, split, or replaced by evidence. It must not be silently reworded to fit results.

## H1 — Specification Primacy

**Claim:** As independently measured AI implementation capability increases, the relative benefit of persistent specifications and machine-checkable contracts over transient prompt-only workflows increases for preserving, regenerating, and changing intended software behaviour.

**Candidate measurements:** predeclared AI capability strata measured independently of H1 outcomes; regeneration success against a fixed acceptance suite; change-propagation success; human implementation editing after regeneration; behavioural divergence across repeated implementations; and the interaction between capability level and workflow condition.

**Falsification pressure:** H1 is weakened if the persistent-specification advantage is flat, decreases, or disappears as independently measured implementation capability increases under matched tasks and resource budgets. A benefit observed at only one capability level supports specification utility under that condition but does not by itself support H1's directional claim.

## H2 — Verification Selection

**Claim:** AI-assisted development disproportionately benefits languages and toolchains that provide precise, machine-actionable diagnostics and enforceable constraints.

**Candidate measurements:** attempts to first successful compile; repair iterations; diagnostic-to-fix conversion; human interventions; static-analysis defects; token and wall-clock cost.

**Falsification pressure:** H2 is weakened if stronger machine-checkable constraints and diagnostics provide no reproducible improvement after controlling for model familiarity, ecosystem maturity, and task suitability.

## H3 — Legacy Preservation Paradox

**Claim:** AI assistance can extend the operational lifetime of legacy languages and systems by reducing maintenance cost associated with scarce human expertise.

**Candidate measurements:** predeclared expertise/scarcity strata measured independently of H3 outcomes; matched AI-assisted versus unassisted conventional-maintenance outcomes within each stratum; scarce-expert consultation hours consumed; defect-localization and repair success; active human effort; verification burden; behavioural regressions; and a predeclared maintenance-viability horizon or equivalent lifecycle proxy under a fixed cumulative maintenance budget.

**Falsification pressure:** H3 is weakened if AI assistance does not reduce maintenance burden relative to the matched unassisted baseline under scarce-expertise conditions, if the benefit does not persist or increase as expert access becomes scarcer, if the predeclared maintenance-viability horizon is not extended, or if apparent gains are offset by verification burden or behavioural risk. Short experiments may support only the declared lifecycle proxy, not literal calendar-year lifetime claims.

## H4 — Modding Mutation

**Claim:** AI-assisted development reduces the technical barrier to software modification and increases the number and diversity of executable modification attempts under a fixed effort budget.

**Candidate measurements:** executable modifications per unit time; human technical actions; distinct completed changes; failure rate; behavioural diversity.

**Falsification pressure:** H4 is weakened if AI-assisted workflows do not increase executable modification throughput or diversity once setup, debugging, and correction costs are included.

## H5 — Recombination Acceleration

**Claim:** When implementation cost is reduced while design intent and quality criteria are held fixed, the rate at which mechanics, systems, genres, and implementation patterns are recombined into executable prototypes increases under a fixed total effort budget.

**Candidate measurements:** a predeclared outcome-independent implementation-input measure recorded per attempt, such as active human time, wall-clock time, tool/agent steps, or reliable compute/token expenditure; successful executable recombinations per fixed total effort budget; retained source concepts; integration defects; and behavioural verification. Derived efficiency metrics such as cost per accepted prototype may be secondary outcomes but cannot establish the H5 mechanism.

**Falsification pressure:** H5 is weakened if an implementation-focused intervention fails to reduce the predeclared implementation-cost measure, if measured cost reduction does not increase executable recombination rate under the fixed total budget, or if recombination increases only when design ideation changes while implementation cost remains unchanged.

## H6 — Tool Legitimacy Gap

**Claim:** For otherwise equivalent software artifacts, disclosure of AI participation can alter perceived legitimacy independently of demonstrated artifact quality.

**Candidate measurements:** perceived quality, creativity, originality, authenticity, technical competence, trust, and willingness to use or recommend.

**Falsification pressure:** H6 is weakened if disclosure produces no reproducible difference, or if observed differences are explained by uncontrolled artifact, wording, sampling, or expectancy effects.

## Status language

Results should use restrained labels:

- **untested**
- **inconclusive**
- **supported under tested conditions**
- **weakened**
- **falsified under tested conditions**

“Proven” is not the default label for an empirical result.
