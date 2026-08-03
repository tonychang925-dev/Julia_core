# ADR-017: Context Semantic Binding Boundary

Status: Proposed
Date: 2026-08-02
Phase: E2.1.5.4 — Semantic Context Binding

## Context

E2.1.5.2 DeepSeek Alpha failed memory/compact semantic recall while architecture and continuity evidence passed. E2.1.5.3 identified the root cause as a Context semantic reconstruction gap:

```text
MemoryRef exists
Continuity governance exists
Trace exists
Provider-understandable semantic context is missing
```

## Decision

Context OS may transform governed refs into provider-readable semantic ContextBlocks.

Context OS must not:

- store memory;
- decide identity importance;
- modify persona;
- create continuity checkpoints;
- restore old prompts;
- inject raw memory dumps.

## Boundary

| Layer | Question |
|---|---|
| Persona Engine | Who am I? |
| Memory OS | What happened? |
| Continuity OS | What must survive? |
| Context OS | What meaning should be available now? |

Semantic binding is a Context OS capability, not a new OS.

## Required Chain

```text
MemoryRef
  ↓
Memory Governance
  ↓
Continuity Decision
  ↓
Semantic Context Builder
  ↓
ContextBlock
  ↓
Provider
```

## Rejected

```text
memory.md → ContextBlock → LLM
```

Rejected because it reintroduces raw memory prompt injection.
