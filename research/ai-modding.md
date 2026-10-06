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
Predeclare one or more implementation-cost measures before outcome inspection. Candidate measures include active human implementation time, wall-clock implementation time, tool/agent steps, reliable token or compute cost, and cost per accepted executable prototype.

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

Run conventional-implementation and AI-implementation-assistance conditions under the same total effort budget. Measure predeclared implementation cost, accepted executable prototypes, cost per accepted prototype, integration defects, retained mechanics, and behavioural verification.

Primary H5 analysis compares the measured implementation-cost difference with the executable recombination-rate difference. A cost reduction without increased recombination, or increased recombination without the predicted cost reduction, weakens the stated mechanism.

### M3 — Design-only mechanism control
Where resources permit, add a condition in which AI may alter or propose the mashup design but implementation remains conventional.

If this condition increases recombination while implementation cost is unchanged, report that as evidence for an ideation/design mechanism rather than the H5 implementation-cost mechanism.

### M4 — Mutation diversity
Run repeated solutions to the same broad design goal and measure behavioural diversity among successful outputs. Report diversity separately from H5 unless the implementation-cost mechanism is also identified.

## Important distinction
A higher mutation or recombination rate can coexist with lower average quality. Throughput, quality, diversity, and implementation cost are separate outcomes and should not be collapsed without a predeclared aggregation rule.

## Phase 0 position
The “Second Modding Revolution” is a named hypothesis frame, not a conclusion.
