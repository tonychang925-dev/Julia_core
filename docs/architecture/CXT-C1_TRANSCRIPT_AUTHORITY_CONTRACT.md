# CXT-C1 — Transcript Authority Contract

**Status**: DRAFT — NO IMPLEMENTATION
**Depends on**: CXT-C0 (ADR-020)
**Scope**: julia_core architecture only

## Five Core Objects

### 1. ConversationMessage

Canonical fact. Already partially implemented.

```
message_id       — unique, non-empty
conversation_id  — owning conversation
turn_id          — logical turn grouping
role             — user | assistant
modality         — text | voice
content          — message body
status           — pending | completed | interrupted | failed
created_at       — ISO-8601, authoritative timestamp
```

Owned by: ConversationRuntime / SessionRepository.
Never owned by: Context OS, Continuity OS, Memory OS, Electron.

### 2. ContextTurn

Context OS projection metadata for a canonical turn. NOT a copy of ConversationMessage.

```
turn_id          — references canonical turn
state            — ACTIVE | SUMMARIZED | ARCHIVED | RETRIEVED | DROPPED
token_estimate   — approximate token count for this turn's messages
topic_refs       — extracted topic references
continuity_hints — L0 | L1 | L2 hints for Continuity OS
```

Owned by: Context OS.
Derived from: ConversationMessage (canonical).
Lifecycle: computed per context assembly, not persisted permanently.

### 3. ContextBoundary

Marks where raw active window ends and structured context begins.

```
boundary_id      — unique
type             — compact | session_restore | manual_checkpoint | budget_pressure
conversation_id  — which conversation
position         — turn_id marking the boundary
created_at       — when boundary was established
```

Owned by: Context OS.
Purpose: tells Context OS that turns before this point must use StructuredCompact, not raw message window.

### 4. StructuredCompact

Derived context artifact for turns beyond a ContextBoundary.

```
compact_id       — unique
boundary_id      — which boundary this compact belongs to
conversation_id  — owning conversation
summary          — compressed representation
key_entities     — extracted entities, decisions, open loops
token_estimate   — compressed size
created_at       — when compact was generated
```

Owned by: Context OS.
NOT: Memory (not governed long-term), NOT: conversation authority (derived, not canonical).

### 5. ActiveTail

The most recent N turns that remain in raw message form.

```
conversation_id  — owning conversation
start_turn_id    — first turn in tail
end_turn_id      — last turn in tail
turn_count       — number of turns
token_total      — total tokens in tail
computed_at      — when tail was last computed
```

Owned by: Context OS.
Computed from: budget constraints + turn completeness.
Replaces: hardcoded `history[-20:]`.

## Relationships

```
ConversationRuntime
  │
  ├── ConversationMessage[] (canonical facts)
  │
  └── feeds →
       │
       Context OS
         │
         ├── ContextTurn[] (projection metadata)
         ├── ContextBoundary (where raw window ends)
         ├── StructuredCompact[] (compressed older turns)
         └── ActiveTail (recent raw turns)
              │
              └── model-visible context
```

## Contract Rules

1. ContextTurn must not duplicate ConversationMessage content.
2. StructuredCompact is derived, not authoritative — deletion is loss of convenience, not loss of fact.
3. ContextBoundary is established by policy (compact, restart, budget), not by client request.
4. ActiveTail size is determined by Context OS budget, not by hardcoded constant.
5. ConversationRuntime never reads ContextTurn/StructuredCompact — it only writes/reads ConversationMessage.
6. Continuity OS checkpoint stores refs to ContextBoundary + StructuredCompact IDs, not the artifacts themselves.
