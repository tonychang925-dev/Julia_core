# Phase Contract — K7.5.6 Continuity Failure Attribution Analysis

Status: COMPLETE / APPROVED

## Objective

Identify causes of Julia recognition loss.

K7.5.6 answers:

```text
Which continuity factor disappears when Julia stops feeling like Julia?
```

## Failure Taxonomy

```text
F1 Identity Loss
F2 Relationship Flattening
F3 Experience Collapse
F4 Over Reconstruction
F5 Roleplay Leakage
F6 Provider Expression Drift
```

## Ablation Experiment

Baseline:

```text
Identity + Relationship + Experience + Context Adaptation
```

Ablations:

```text
Remove Experience
Remove Relationship
Remove Identity
Memory only
Persona prompt only
```

## Julia Continuity Equation v1

```text
JC = Identity + Relationship + Experience + Context Adaptation - Drift
```

## Artifact

```text
artifacts/benchmark/julia_continuity_failure_analysis_v1.json
```

## Acceptance

- Full Continuity JRS >= 0.90.
- Removing Identity, Relationship, or Experience drops below viable threshold.
- Memory-only and persona-prompt-only states are not viable Julia continuity.
- Failure taxonomy records frequency, impact, affected dimensions, and root-cause candidates.
- Analysis does not compare provider quality or mutate continuity state.
