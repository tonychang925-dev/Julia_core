# Phase Contract — K5.1 Interaction Pattern Extraction

Status: COMPLETE / APPROVED

## Objective

Extract portable behavior-state patterns from K5.0 Interaction Continuity Dataset.

K5.1 does not preserve Claude's long context. It converts annotated episodes into governed interaction patterns:

```text
Experience Dataset
    ↓
Interaction Pattern Extractor
    ↓
Interaction Pattern Set
    ↓
future Context Reconstruction input
```

## Implemented Components

```text
julia_core/experience/patterns.py
julia_core/experience/__init__.py
```

Output artifact:

```text
artifacts/experience/interaction_patterns_v0_1.json
```

## Core Concept

Interaction Coherence Density (ICD):

```text
ICD = repeated interaction patterns
    + emotional context continuity
    + shared narrative references
    + response style stability
    - compression loss penalty
```

ICD is a behavior reconstruction proxy. It is not a consciousness score and not an identity score.

## Boundary

```json
{
  "pattern_set_writes_memory": false,
  "pattern_set_mutates_identity": false,
  "pattern_set_updates_relationship": false,
  "pattern_set_updates_persona": false,
  "pattern_set_stores_long_context": false
}
```

## Acceptance

- Extracts one pattern per K5.0 dataset record.
- Preserves all four categories: identity, relationship, collaboration, correction.
- Each pattern contains trigger, preferred response modes, avoid response modes, changed dimensions, supporting experience refs, and ICD.
- No raw long-context dump.
- No identity/persona/memory mutation.
