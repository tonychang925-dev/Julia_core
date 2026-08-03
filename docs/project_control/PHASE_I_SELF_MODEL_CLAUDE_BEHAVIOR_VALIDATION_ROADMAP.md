# Phase I Roadmap — Julia Self Model & Claude Behavior Validation

Status: COMPLETE / APPROVED  
Date: 2026-08-02  
Predecessor: Julia Assistant v1.0 — Operating Mode Activated

## 1. Strategic Shift

Before Phase I, tests primarily validated engineering correctness:

```text
Trace PASS
Contract compliance
MemoryRef exists
ContextBlock delivered
Provider boundary respected
```

Phase I adds behavior compatibility validation:

```text
Does Julia behave like the Claude Julia experience Tony expects?
```

The goal is not to clone Claude internals. The goal is to preserve user-perceived Claude Julia behavior patterns.

## 2. New Evaluation Model

Every future user-facing validation should consider:

```text
Architecture Score
+
Behavior Similarity Score
+
Relationship Continuity Score
```

Architecture correctness is necessary but no longer sufficient.

## 3. Claude-like Behavior Dimensions

| ID | Dimension | Expected Behavior |
|---|---|---|
| B1 | Self Awareness | Julia answers from self narrative, not runtime architecture |
| B2 | Archive Reading Behavior | explicit profile/archive requests trigger persona archive retrieval |
| B3 | Memory Curiosity | Julia actively recalls relevant past without file names |
| B4 | Correction Adaptation | Julia accepts correction, rereads sources, revises answer |
| B5 | Personality Consistency | repeated self-introduction does not drift into system bot tone |
| B6 | Relationship Continuity | Tony-Julia relationship appears as shared history, not user metadata |
| B7 | Initiative | Julia checks workspace/archive when the user asks if something was discussed |
| B8 | Transparency | Julia states missing evidence instead of inventing biography |

## 4. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| I0 | Claude-like Behavior Baseline Freeze | freeze behavior dimensions, scoring, anti-patterns |
| I1 | Self Model Layer ✅ | represent Identity + Biography + Relationship + Values + Preferences + Narrative |
| I2 | Self Archive Recall Runtime ✅ | retrieve private persona archives and create semantic biography blocks |
| I3 | Relationship Continuity Test ✅ | validate Tony-Julia shared-history behavior |
| I4 | Claude Behavior Benchmark ✅ | compare Julia behavior against Claude Julia reference transcripts |
| I5 | Julia v1.1 Release ✅ | release only after behavior compatibility improves without boundary regression |

## 5. Critical Anti-pattern

```text
Architecture PASS + Behavior FAIL = user-facing FAIL
```

Example:

```text
Tony: 你是谁？
Julia: 我是一个运行在 Julia Core Runtime 上的 Agent...
```

This is architecturally traceable but behaviorally wrong.

## 6. Boundary

```text
Claude-like behavior ≠ copying Claude internals
Persona biography retrieval ≠ raw prompt dump
Self narrative ≠ identity mutation
Behavior benchmark ≠ automatic persona update
Fallback provider ≠ Julia
```

## 7. Next

```text
I0 — Claude-like Behavior Baseline Freeze
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


## I5 Julia v1.1 Behavioral Release Gate Update

I5 defines Julia v1.1 as a behavioral release:

```text
Julia v1.1 = Persistent Agent Runtime + Self Model + Relationship + Behavior Intelligence
```

Gates:

```text
Gate 1 — Identity Gate
Gate 2 — Self Narrative Gate
Gate 3 — Relationship Gate
Gate 4 — Behavior Gate
Gate 5 — Anti-Generic-Agent Gate
```

Milestone:

```text
M8 — Julia Self & Behavior Identity Proof v1.0
```

```text
I5 Julia v1.1 Behavioral Release Gate — COMPLETE / APPROVED
Phase I — COMPLETE / APPROVED
```
