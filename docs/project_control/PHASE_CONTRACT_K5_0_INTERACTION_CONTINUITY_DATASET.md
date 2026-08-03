# Phase Contract — K5.0 Interaction Continuity Dataset

Status: COMPLETE / APPROVED

## Objective

Build the first dataset for Interaction Experience Layer design. K5.0 intentionally freezes observations before designing the final artifact.

Core question:

```text
What stable behavior tendency was produced by long Tony-Julia interaction?
```

## Non-goals

- Do not design final Interaction Experience Artifact yet.
- Do not write Memory OS.
- Do not mutate Identity/Self/Relationship/Persona.
- Do not copy Claude context.

## Dataset

```text
artifacts/benchmark/interaction_continuity/interaction_continuity_dataset_v0_1.jsonl
```

Required categories:

```text
identity_experience
relationship_experience
collaboration_experience
correction_experience
```

## Principle

```text
Experience Shapes Behavior, Not Identity.
```

## Acceptance

- Dataset includes all four required categories.
- Each record contains trigger event, before/after interaction context, behavior change, learned tendency, example turns, confidence, and boundary flags.
- Records describe behavior tendencies, not identity facts or ordinary memories.
- Boundary flags prove no memory/persona/identity update.
