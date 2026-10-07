# Specification Primacy

## Question
Does the relative value of a persistent specification increase as independently measured AI implementation capability increases?

## Hypothesis link
Primary: **H1 — Specification Primacy**

## Operational distinction
A **prompt** is an instruction used for one interaction. A **persistent specification** is a retained artifact that defines required behaviour, constraints, acceptance conditions, or interfaces and is reused across implementation or verification steps.

H1 is directional. Demonstrating that specifications help one fixed model is not enough. The experiment must vary independently measured implementation capability and test whether the specification advantage changes with it.

## Capability operationalization

Before evaluating H1 outcomes, define at least two and preferably three capability strata.

A capability stratum is a frozen model/agent configuration whose implementation capability is measured on a **held-out capability battery** that is separate from the H1 task set. The battery should use the same broad execution conditions and resource accounting as the H1 study, but its tasks must not be reused as H1 outcomes.

The capability measure and stratum boundaries must be declared before inspecting the specification-versus-transient workflow comparison. Acceptable capability measures may include:

- behavioural task completion against hidden acceptance tests;
- successful repair of independently seeded implementation defects;
- implementation success under a fixed tool and iteration budget.

Model name, release date, parameter count, price, or reputation alone does not establish a capability stratum.

Each stratum must freeze the relevant model version, agent/tool version, system instructions, allowed tools, and resource budget. If these differ for unavoidable reasons, the differences must be declared as limitations.

## Primary experimental design

Use a factorial comparison:

- **Capability condition:** predeclared low / medium / high strata, or another predeclared ordered set with at least two levels.
- **Workflow condition:** persistent specification versus a matched transient prompt-only workflow with no durable specification available after the initial instruction.

Tasks, acceptance suites, resource budgets, starting repositories, and allowed tools should be matched within each capability stratum. Randomize or counterbalance task assignment where practical and use fresh contexts to prevent leakage between workflow conditions.

Define the persistent-specification advantage for a primary outcome before analysis. For a success-rate outcome, for example:

Delta(c) = success_spec(c) - success_transient(c)

H1 predicts that Delta(c) increases with independently measured capability c. Secondary outcomes can include human correction, behavioural divergence, repair iterations, or change-propagation success, but their direction must be predeclared.

The analysis should estimate the **capability × workflow interaction**, not merely compare overall averages.

## Candidate experiments

### S1 — Regeneration across capability strata
Create a fixed behavioural specification and matched transient instruction, then generate multiple independent implementations at each capability stratum.

Measure acceptance-suite pass rate, behavioural divergence, required human correction, and differences not permitted by the specification. Test whether the persistent-specification advantage changes across strata.

### S2 — Change propagation across capability strata
Modify one requirement and compare:

- a workflow where the durable specification is updated and reused;
- a matched workflow where the change exists only in transient conversational instruction.

Repeat at each capability stratum and test the capability × workflow interaction.

### S3 — Implementation replacement across capability strata
Replace an implementation with a newly generated implementation in the same or a different language while preserving an observable contract.

Repeat under the predeclared capability strata. Measure whether higher-capability configurations derive a larger relative benefit from the persistent contract when replacing or regenerating implementation code.

## Evidence needed
A specification advantage at one capability level demonstrates specification utility under that tested condition.

Evidence for H1 specifically requires:

1. capability levels established independently of H1 outcomes;
2. matched persistent-specification and transient workflow conditions at each level;
3. repeated observations with failures retained;
4. an estimated capability × workflow interaction or equivalent predeclared trend test.

If capability and workflow are both changed at the same time, H1 is not identified.

## Failure modes
- capability strata are defined after viewing H1 results;
- model identity or marketing labels are substituted for measured capability;
- capability-battery tasks leak into the H1 task set;
- acceptance tests encode behaviour not stated in the task contract;
- the specification merely restates implementation details;
- conversational context leaks into supposedly transient or specification-only trials;
- higher-capability conditions receive larger budgets or additional tools without those differences being controlled or declared;
- repeated generations are scored subjectively instead of against a fixed contract.

## Phase 0 position
Untested.
