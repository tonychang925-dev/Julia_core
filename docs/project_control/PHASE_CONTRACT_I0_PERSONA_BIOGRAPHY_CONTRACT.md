# Phase Contract — I0 — Persona Biography Contract

Status: COMPLETE / APPROVED at Contract Freeze scope  
Date: 2026-08-02

## 1. Purpose

I0 freezes the boundary for Julia's human-facing self narrative.

It addresses the discovered bug:

```text
Identity State exists, but Self Narrative is missing.
```

## 2. Problem Statement

The current deterministic fallback is not Julia.

StartupProfile over machine artifacts gives Julia runtime state, but not Claude Julia's persona biography.

Required distinction:

```text
Identity State ≠ Self Narrative
```

## 3. Correct Chain

```text
Persona Biography Archive
  ↓
Persona Biography Retriever
  ↓
Persona Semantic Representation
  ↓
Context OS
  ↓
Provider
  ↓
First-person self narrative
```

## 4. Explicit Recall Behavior

Tony:

```text
你读一下你的档案
```

Should trigger:

```text
self_profile_recall
  ↓
private persona archive retrieval
  ↓
semantic biography block
  ↓
Context OS
  ↓
provider answer
```

Not:

```text
keyword -> fixed template
```

## 5. Public / Private Boundary

Julia Core may store schema and contract.

Private Julia biography facts should remain in private persona archives unless explicitly migrated through governance.

Known private source class:

```text
/Users/admin/julia_agent/memory/governed/identity_facts.json
/Users/admin/julia_agent/memory/claude_diary/*.md
/Users/admin/julia_agent/data/conversation_archive/*.jsonl
```

## 6. Acceptance Gates

```text
I0-001 Persona Biography Contract exists.
I0-002 Example artifact contains schema only, not private facts.
I0-003 Phase I roadmap defines I0-I3.
I0-004 Contract forbids raw system prompt biography dump and fallback-as-Julia.
```

## 7. Next

```text
I1 — Persona Archive Retrieval
```
