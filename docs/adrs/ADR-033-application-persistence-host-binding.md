# ADR-033 — Application Persistence Host Binding

**Date:** 2026-08-13
**Status:** FROZEN / ACCEPTED
**Supersedes:** none (fills a gap not previously resolved)

## Context

VOICE-C1 remediation (2026-08-12) closed three root causes (runtime drift, authority cutover, turn identity). The next program — Conversation Storage + Julia Diary — requires a durable physical storage substrate. The frozen unified architecture defines semantic ownership and a recommended filesystem layout, but does not explicitly name which repository owns physical application persistence.

This gap previously caused ambiguity: Julia_core is the "OS / semantic kernel", but the actual Julia product's user data must live somewhere concrete without polluting the Git working tree (RP-1 clean-worktree gate forbids that).

## Decision

Physical persistence ownership is assigned as follows, and this assignment does NOT transfer semantic authority.

```text
Julia_core
  = semantic authority
  = ConversationRuntime / Context OS / Memory OS / Continuity OS
  = owns semantic contracts and invariants
  ≠ application-specific physical data host

Julia-AI-Assistant
  = application host / Brain / composition root
  = owns physical application persistence
  = binds Core repository/storage ports to <PRIVATE_JULIA_DATA>

Julia_client / julia_electron_v2
  = desktop shell / projection
  = may cache display state
  ≠ canonical transcript authority

Julia-Voice-S2S
  = media / transport adapter
  ≠ conversation / memory / diary authority
```

## Abstract Root

```text
JULIA_PRIVATE_DATA_ROOT = <PRIVATE_JULIA_DATA>
```

The exact OS-specific default path is an implementation decision (STO-D0-01), not part of this ADR.

## Consequences

### Positive

- Core remains application-agnostic; it can be reused by any Julia product.
- The Assistant can host durable data outside the Git working tree, preserving RP-1 provenance gates.
- No repository silently becomes a second semantic authority.

### Negative / Constraints

- The Assistant MUST NOT bypass Core semantic contracts when writing conversation transcript or diary/memory artifacts.
- Electron and S2S MUST NOT read/write `<PRIVATE_JULIA_DATA>` directly for canonical truth.
- Any future storage backend (SQLite, vector store, etc.) is derived infrastructure unless a later ADR explicitly re-scopes this binding.

## Non-Goals (deferred to STO-D0 / later waves)

- Exact `<PRIVATE_JULIA_DATA>` default path
- Diary physical format (single day file vs. date directory)
- accepted-user fsync/durability policy
- segment rotation thresholds
- archive/delete semantics
- search index technology
- backup retention
- Claude Julia legacy migration taxonomy

## References

- `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_FINAL_FREEZE_CANDIDATE.md` (Physical Storage Location ≠ Semantic Authority)
- `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`
- `docs/authority/STORAGE_PROGRAM_BASELINE_20260813.md`
