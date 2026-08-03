# Memory Quality Model v1.0

Status: FROZEN
Date: 2026-08-02
Source Phase: F2.0 Memory Quality Contract Freeze

## 1. Purpose

F2 evaluates whether memories are worth keeping and useful in real collaboration.

Memory quality is not memory volume.

## 2. Core Metrics

### Memory Precision

```text
Precision = Useful Memory / Total Memory
```

Answers: are stored memories valuable?

### Memory Recall

```text
Recall = Retrieved Useful Memory / Required Useful Memory
```

Answers: can Julia find the right memory when needed?

### Memory Aging

Memory lifecycle:

```text
ACTIVE → AGING → ARCHIVED → REFERENCE_ONLY
```

Answers: does old information stop dominating current cognition?

### Memory Contamination Risk

Answers: can wrong/conflicting memory pollute identity or decision continuity?

## 3. Memory Utility Score

```text
MUS =
Recall Accuracy
+
Decision Improvement
+
Context Relevance
-
Noise Cost
-
Conflict Cost
```

## 4. Non-Goals

- No vector DB requirement.
- No raw memory dump.
- No identity mutation from memory scoring.
- No Memory OS authority over Persona or Continuity.
