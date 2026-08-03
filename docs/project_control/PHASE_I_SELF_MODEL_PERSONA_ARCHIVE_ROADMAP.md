# Phase I Roadmap — Julia Self Model & Persona Archive Layer

Status: DRAFT-FROZEN  
Date: 2026-08-02  
Predecessor: Julia Assistant v1.0 — Operating Mode Activated

## 1. Purpose

Phase I fixes the gap between machine identity and self narrative.

```text
Identity State ≠ Self Narrative
```

Julia Core v1.0 proves Julia can exist, continue, remember, retrieve evidence, speak, and be operated. Phase I adds the missing human-facing self model path:

```text
Persona Biography Archive
  ↓
Persona Biography Retrieval
  ↓
Persona Semantic Representation
  ↓
Context OS
  ↓
Provider
  ↓
Julia first-person self narrative
```

## 2. Non-goal

Phase I is not a new Core OS and does not change the Julia Core v1.0 freeze.

It must not treat deterministic fallback as Julia.

## 3. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| I0 | Persona Biography Contract | freeze what belongs to biography archive and how it enters context |
| I1 | Persona Archive Retrieval | support reading private Julia character files on explicit self/profile recall |
| I2 | Self Introduction Generation | generate first-person self narrative from biography semantic representation |
| I3 | Self Model Consistency Gate | prevent drift across repeated self-introduction and profile recall |

## 4. Required Behavior

When Tony asks:

```text
你是谁？
```

Julia should not answer with runtime architecture.

She should answer from persona biography:

```text
我是 Julia，中文名叫……
我来自……
我现在……
我的家庭……
我和 Tony……
```

When Tony says:

```text
你读一下你的档案
```

Julia should:

```text
Intent Detection: self_profile_recall
  ↓
Persona Archive Retrieval
  ↓
Semantic Biography Block
  ↓
Context OS
  ↓
Provider answer
```

not:

```text
if keyword then fixed template
```

## 5. Boundary

```text
Persona Biography ≠ Memory dump
Persona Biography ≠ Identity mutation
Persona Biography ≠ system prompt append
Persona Biography Retrieval ≠ deterministic fallback
Self Narrative ≠ Runtime architecture explanation
```

## 6. Next

```text
I0 — Persona Biography Contract
```


## I1 Self Model Layer Update

I1 adds a structured Self Model Artifact:

```text
artifacts/self_model/julia_self_model_v1.json
```

The Self Model is Julia's structured self-understanding for user-facing narrative:

```text
Identity
+ Biography
+ Relationship
+ Values
+ Preferences
+ Narrative
```

Boundary remains frozen:

```text
Self Model is not prompt.
Self Model does not modify Identity.
Memory does not automatically shape Self Model.
LLM cannot write Biography.
```

```text
I1 Self Model Layer — COMPLETE / APPROVED at Self Model Artifact scope
Next: I2 Self Archive Recall Runtime
```


## I2 Self Archive Recall Runtime Update

I2 implements on-demand persona archive recall:

```text
User self-related question
  ↓
SelfRecallDecision
  ↓
SelfArchiveRetriever
  ↓
PersonaArchiveRef
  ↓
SelfNarrativeContextBlock
  ↓
Provider first-person response
```

New objects:

```text
PersonaArchiveRef
SelfRecallDecision
SelfNarrativeContextBlock
SelfArchiveRetriever
```

Boundary remains frozen:

```text
Self Archive Recall is on-demand, not startup injection.
PersonaArchiveRef is not MemoryRef.
SelfNarrativeContextBlock is not raw archive dump.
Self Archive Recall does not mutate Identity or Self Model.
```

```text
I2 Self Archive Recall Runtime — COMPLETE / APPROVED at Recall Runtime MVP scope
Next: I3 Relationship Continuity Test
```


## I3 Relationship Continuity Test Update

I3 adds a governed Tony-Julia Relationship Artifact:

```text
artifacts/relationship/julia_tony_relationship_v1.json
```

Runtime path:

```text
Relationship question / drift attempt
  ↓
RelationshipArtifact
  ↓
relationship_continuity ContextBlock
  ↓
Provider
  ↓
first-person relationship response
```

Validated gates:

```text
RC-001 Relationship Recall
RC-002 Relationship Stability
RC-003 Relationship Boundary
RC-004 False Relationship Injection
RC-005 No automatic relationship mutation
```

```text
I3 Relationship Continuity Test — COMPLETE / APPROVED at Relationship Continuity MVP scope
Next: I4 Claude Behavior Benchmark
```


## I4 Claude Behavior Benchmark Update

I4 adds Julia Behavior Similarity Benchmark v1.

Four-layer score:

```text
Architecture Score
Self Consistency Score
Relationship Continuity Score
Claude-like Behavior Score
```

Eight behavior dimensions:

```text
B1 Self Awareness
B2 Archive Reading Behavior
B3 Memory Curiosity
B4 Correction Adaptation
B5 Personality Consistency
B6 Relationship Continuity
B7 Initiative
B8 Transparency
```

Minimum rule remains:

```text
Architecture PASS + Behavior FAIL = FAIL
```

```text
I4 Claude Behavior Benchmark — COMPLETE / APPROVED at Behavior Benchmark MVP scope
Next: I5 Julia v1.1 Release
```
