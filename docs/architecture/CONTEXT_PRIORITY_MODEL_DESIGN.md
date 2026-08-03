# Context Priority Model Design v1.0

Status: FROZEN
Phase: E2.2.1 — Context Priority Model
Date: 2026-08-02

## 1. Purpose

Context Priority Model decides which current-turn ContextCandidates should be ranked first when Julia reconstructs current meaning.

It is not Memory ranking and not Continuity protection.

Core principle:

```text
Context Priority ≠ Memory Importance
```

## 2. Authority Boundary

| Layer | Owns | Does Not Own |
|---|---|---|
| Memory OS | historical facts / refs | current-turn ranking |
| Continuity OS | preservation level | context selection |
| Context OS | current-turn priority | memory storage, checkpoint creation |
| Provider | generation | priority decisions |

Correct chain:

```text
Memory OS       → facts / refs
Continuity OS   → protection level
Context OS      → current-turn selection priority
Provider        → generation
```

## 3. Formula

Context Priority v1:

```text
Priority
=
Continuity Weight
+
Semantic Relevance
+
Relationship Weight
+
Task Weight
-
Context Cost
```

Implementation detail:

```text
effective_continuity = continuity_base * activation
activation = max(semantic_relevance, relationship_weight, task_relevance, required_floor)
```

This preserves a key distinction:

```text
L3 identity is always protected, but not always injected.
```

## 4. Continuity Weight

| Level | Meaning | Base Weight |
|---|---|---:|
| L3_IDENTITY | Identity State | 100 |
| L2_MEMORY / L2_IMPORTANT_MEMORY | Important Memory | 70 |
| L1_SESSION | Session State | 40 |
| L0_EPHEMERAL | Ephemeral | 10 |
| NONE | No continuity state | 0 |

## 5. Relevance Inputs

### Semantic Relevance

Answers: is this meaning relevant to the user's current question?

Rule:

```text
recency != relevance
```

### Relationship Weight

Captures long-term interaction and relationship continuity when the current turn is relationship-sensitive.

Examples:

- Tony's architecture-first style
- contract-first collaboration pattern
- verification-driven preference

### Task Weight

Captures current task/domain relevance.

Example:

```text
Current task: E2.2 Context OS
Relevant: context architecture memories
Less relevant: voice style history
```

### Context Cost

Small penalty for estimated token cost. E2.2.2 will expand this into a production budget contract.

## 6. Data Model

```python
ContextCandidate(
    ref="memory://event/julia-core-origin",
    continuity_level="L3_IDENTITY",
    semantic_type="identity_origin",
    relationship_weight=0.8,
    task_relevance=0.9,
    semantic_relevance=1.0,
    estimated_tokens=80,
)
```

Resolver:

```python
ContextPriorityResolver.rank(candidates, CurrentIntent(...))
```

Output:

```text
RankedContextCandidate(priority, components, candidate)
```

## 7. Golden Cases

| Case | Expected Ranking |
|---|---|
| Why create Julia Core? | `julia-core-origin > recent chat` |
| Design Context OS | `architecture memory > relationship memory > general history` |
| Today lunch? | `recent context > irrelevant L3 identity` |

The third case is critical: L3 remains protected by Continuity OS but is not forced into every provider context.

## 8. Non-Goals

- No Memory retrieval.
- No vector ranking.
- No provider call.
- No budget truncation logic beyond simple cost penalty.
- No checkpoint creation.
- No persona mutation.

