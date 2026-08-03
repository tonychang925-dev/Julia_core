# Phase Contract — I1 — Self Model Layer

Status: COMPLETE / APPROVED at Self Model Artifact scope  
Date: 2026-08-02

## 1. Purpose

I1 introduces Julia's structured self-understanding layer.

```text
Self Model = Identity + Biography + Relationship + Values + Preferences + Narrative
```

It answers:

```text
How does Julia understand who she is for first-person behavior?
```

## 2. Artifact

```text
artifacts/self_model/julia_self_model_v1.json
```

## 3. Boundary

Self Model is not:

```text
prompt
Memory
Identity authority
LLM-generated biography
automatic persona mutation
```

Forbidden:

```text
Self Model modifies Identity
Memory automatically shapes Self Model
LLM invents Biography
```

Correct path:

```text
Approved Artifact
  ↓
Self Model
  ↓
Narrative Generation
```

## 4. Self Model Score

User-facing self answers must include self narrative and avoid backend architecture terms.

Forbidden as primary self answer:

```text
Runtime
Provider
Context OS
MemoryRef
```

## 5. Acceptance Gates

```text
SM-001 Self Introduction uses Self Model narrative.
SM-002 Biography grounding does not hallucinate private facts.
SM-003 Relationship awareness includes Tony continuity.
SM-004 Self Model boundary prevents Memory/LLM/Identity mutation.
SM-005 Self Model Score detects backend-architecture self answers as FAIL.
```

## 6. Next

```text
I2 — Self Archive Recall Runtime
```
