# AI-Assisted Modding and Recombination

## Question
Does AI-assisted development reduce the technical barrier to modifying games and other interactive software, and does measured implementation-cost reduction increase executable experimentation and mechanic recombination?

## Hypothesis link
Primary: **H4 — Modding Mutation**

Primary: **H5 — Recombination Acceleration**

## Historical frame
The early modding scenes around engines such as Quake motivate this track because improved access to scripting, editors, and engine internals enabled users to treat a finished game as a platform for mutation.

CONSTRAINT-SHIFT uses this as an analogy, not as proof.

## Proposed measurable quantities

### Modification barrier
Observe programming actions, setup actions, asset work, debugging cycles, integration failures, and elapsed effort. No universal scalar barrier is assumed in Phase 0.

### Modding mutation rate
Count distinct executable modification attempts completed under a fixed effort budget. Throughput must be reported separately from quality.

### Implementation cost
Predeclare at least one **outcome-independent implementation-input measure** as the primary H5 mechanism measure before outcome inspection. It must be measured per attempt regardless of whether that attempt succeeds. Suitable primary measures include active human implementation time per attempt, wall-clock implementation time per attempt, tool/agent steps per attempt, or reliable token/compute expenditure per attempt.

Metrics derived from the number of successful outputs — including cost per accepted executable prototype — may be reported as secondary efficiency outcomes, but they cannot serve as the primary mechanism measure because they are algebraically coupled to recombination success under a fixed budget.

Do not collapse unlike cost measures into a single score unless the aggregation rule and weights are declared in advance.

### Recombination
A mashup task specifies mechanics or systems drawn from multiple design sources. Completion requires behavioural checks showing requested components are actually present.

## H5 mechanism isolation

H5 attributes recombination acceleration specifically to reduced **implementation cost**, so design quality must not be allowed to change silently with the implementation condition.

Use mashup specifications frozen before condition assignment and compare, at minimum:

- **Conventional implementation:** implement the fixed mashup specification without generative AI.
- **AI implementation assistance:** use AI for implementation while the design specification, mechanics, quality criteria, and acceptance tests remain fixed.

An optional **AI design-only control** may allow AI to improve or propose the design while implementation remains conventional. This helps distinguish a better-ideas mechanism from an implementation-cost mechanism.

Use the same total effort budget and acceptance criteria across the primary implementation conditions. H5 receives mechanism-consistent support only if the implementation-focused intervention reduces the predeclared implementation-cost measure and the lower-cost condition produces more accepted executable recombinations per fixed total budget, or an equivalent predeclared analysis links the measured cost reduction to increased recombination rate.

If AI produces better mashups without reducing implementation cost, that may support a separate design-assistance claim but does not support H5's stated cost mechanism.

## Candidate experiments

### M1 — Matched mod task
Compare the same modification goal under conventional tooling and AI-assisted tooling. Measure the modification barrier, successful executable changes, failures, and retained behavioural quality.

M1 primarily informs H4 unless its design also satisfies the H5 mechanism-isolation requirements.

### M2 — Mechanic mashup cost experiment
Freeze a structured specification combining independent mechanics before condition assignment.

Run conventional-implementation and AI-implementation-assistance conditions under the same total effort budget. Measure the predeclared outcome-independent implementation input **for every attempt**, accepted executable prototypes, integration defects, retained mechanics, and behavioural verification. Cost per accepted prototype may be reported only as a secondary efficiency statistic.

Primary H5 analysis requires an independently measured reduction in implementation input per attempt and compares that reduction with the executable recombination-rate difference. A throughput increase without an independent per-attempt input reduction does not support H5's implementation-cost mechanism. Likewise, a measured input reduction without increased recombination weakens the stated mechanism.

### M3 — Design-only mechanism control
Where resources permit, add a condition in which AI may alter or propose the mashup design but implementation remains conventional.

If this condition increases recombination while implementation cost is unchanged, report that as evidence for an ideation/design mechanism rather than the H5 implementation-cost mechanism.

### M4 — Matched mutation diversity
Freeze the same broad design goal, acceptance criteria, repetition count, diversity metric, and total effort budget before condition assignment.

Run matched repeated attempts under at least:

- **Conventional condition:** conventional tooling without generative AI.
- **AI-assisted condition:** the same task and budget with the predeclared AI assistance available.

Use the same diversity measure in both conditions and retain failed attempts in the trial record. Compare behavioural diversity among accepted executable outputs while also reporting completion rate and the number of accepted outputs, so a condition cannot appear more diverse merely because it produced a smaller selectively successful subset.

This comparison tests the diversity component of H4. Report it separately from H5 unless the implementation-cost mechanism is also identified.

## Important distinction
A higher mutation or recombination rate can coexist with lower average quality. Throughput, quality, diversity, and implementation cost are separate outcomes and should not be collapsed without a predeclared aggregation rule.

## Phase 0 position
The “Second Modding Revolution” is a named hypothesis frame, not a conclusion.
