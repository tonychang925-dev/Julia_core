# C-02 — Conversation Authority Contract

**Status**: FROZEN
**Date**: 2026-08-09
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §9
**Depends on**: C-00 Cognitive Boundary (07f0ff0), C-01 Runtime Execution (f79db0d)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Sole Canonical Transcript Truth

```
ConversationMessage = canonical durable transcript truth.
ConversationRuntime = sole canonical transcript authority.
```

No other object is conversation authority:

```
RuntimeTurn          ≠ authority
ContextTurn          ≠ authority
ActiveTail           ≠ authority
StructuredCompact    ≠ authority
MemoryObject         ≠ authority
ContinuityCheckpoint ≠ authority
Client history       ≠ authority
Voice bootstrap      ≠ authority
prompt/messages[]    ≠ authority
```

## 2. Conversation ≠ Session

```
Conversation = durable logical dialogue identity
Session      = temporary execution/connection scope
```

One conversation → many runtime sessions → many provider sessions → many Electron reconnects → many voice connections. `conversation_id` is stable across all of them. Session lifecycle does not mutate conversation identity.

## 3. ConversationMessage Schema

```
message_id       — unique, non-empty, durable
conversation_id  — owning conversation
turn_id          — logical turn grouping
role             — user | assistant
modality         — text | voice
content          — message body
status           — pending | completed | interrupted | failed
created_at       — canonical event time (ISO-8601), never import/retrieval/projection time
source           — origin label (native-text, native-voice, legacy-electron, external-import)
provenance       — source trace metadata
```

`created_at` is the canonical event time. It is NEVER the import time, retrieval time, or context projection time. This is critical for historical migration chronology.

## 4. Turn ≠ Message

```
Logical Turn: one user→Julia cognitive exchange
Message: one durable transcript entry
```

A normal turn: `turn_id = T1` → user message M1 + assistant message M2.

A tool-loop turn: `turn_id = T1` → user M1 → model G1 → tool call → model G2 → assistant M2. Still one logical turn, one assistant message. Tool internal state is not automatically canonical transcript unless explicitly declared as conversation artifact.

## 5. Message Status Lifecycle

```
user message:
  pending → completed | failed

assistant message:
  pending → completed | interrupted | failed
```

`interrupted` = transport/media interruption occurred. The assistant message exists in canonical transcript with the content that was actually produced/committed. Transport cancellation does not delete the historical fact that Julia produced partial output.

`failed` = unrecoverable error. No durable assistant content.

Status transitions are final. A `completed` message is immutable except through a governed correction mechanism (not defined here — requires separate governance contract).

## 6. Atomic Canonical Write

Canonical append model. Never overwrite.

```
User accepted → append canonical user message (pending)
Cognition running → pending assistant representation
Completion → atomically finalize to completed
Interruption → atomically finalize to interrupted (content = actually emitted)
Failure → atomically finalize to failed
```

Forbidden:

```
❌ Write temp, delete, rewrite
❌ Context compaction mutates transcript
❌ Memory update repairs transcript
❌ Continuity recovery rewrites transcript
❌ Client reconnect modifies completed messages
```

## 7. Reverse Authority Prohibition

```
ConversationMessage      = canonical truth

ContextTurn              = derived
StructuredCompact        = lossy derived artifact
Prompt / ContextPackage  = projection
Memory summary           = governed interpretation
Continuity signal        = preservation observation
Client history           = presentation cache
```

No derived representation may become transcript authority:

```
❌ StructuredCompact   → overwrite transcript
❌ Memory summary      → repair transcript
❌ Prompt history      → become transcript
❌ Client cache        → become canonical history
❌ Continuity state    → mutate transcript
```

## 8. Historical Transcript Migration

Legacy transcripts (Electron local cache, backups, platform migrations) may be imported into canonical Conversation authority. Migration is a one-time governed import process — not a normal runtime path.

### Migration Rules

```
- Preserve original chronology
- Preserve original timestamps (created_at = original event time, not import time)
- Deterministic message IDs
- Deterministic turn IDs
- Idempotent (same identity + same content → skip; different → conflict)
- Atomic (batch succeeds or fails as a unit)
- Provenance = source label (legacy-electron, backup-restore, platform-migration)
```

### Migration Forbidden Actions

During import, the following MUST NOT execute:

```
❌ LLM invocation
❌ Memory formation
❌ Continuity classification
❌ Context mutation
❌ Semantic rewriting
❌ Conversation summarization
```

Migration imports facts, not interpretations. Post-import governance (Memory formation, Continuity observation) occurs through normal governed pipelines in a separate process.

## 9. Historical ID Strategy

Deterministic message/turn IDs for repeatable migration. Construction based on:

```
legacy_source + legacy_conversation_id + original_timestamp + role + stable_sequence + content_digest
```

Same legacy dataset imported twice → same IDs → no duplicates. Specific hash algorithm deferred to implementation contract, but input semantics are frozen here.

## 10. External / Voice / Imported Turns

All modalities normalize to one authority:

```
Text ASR transcript
Voice STT transcript
Electron imported history
Web input
Future mobile input
External ingestion
        ↓
ConversationRuntime
        ↓
ConversationMessage
```

Forbidden second transcript authorities:

```
❌ VoiceHistoryStore
❌ ElectronHistoryStore
❌ ChatSession.history
❌ S2S Chat buffer as canonical
```

## 11. Client Cache Boundary

Client may cache conversation for UX rendering. Client cache is presentation-only.

```
Client cache ≠ canonical
Client cache ≠ recovery authority
Client cache ≠ continuity authority
Client cache ≠ migration source (once migrated)
```

Reconnect: Client requests canonical conversation → renders. Client does not send its local history as truth.

Historical migration is a one-time governed import. It is not a normal runtime mode where the client regularly submits its local history as canonical.

## 12. Conversation Reopen

```
Open conversation_id → ConversationRuntime → canonical messages → render
```

Conversation owns all history. Context OS (C-03) decides what is visible to the model now.

```
Conversation owns all history.
Context decides what is visible now.
```

Normal reopen does not require a ContinuityCheckpoint. Canonical persistence is sufficient. Continuity OS (C-06) enhances recovery for disruption cases.

## 13. Core Object Relationships

```
                   Conversation
                        │
               conversation_id
                        │
              ConversationRuntime
                        │
               canonical append/read
                        │
                        ▼
            ConversationMessage[]
                  │           │
                  │           │
                  ▼           ▼
            Context OS      Memory OS
             derived         candidate/
            projection       governance
                  │
                  ▼
                LLM
```

Arrows are one-way. No reverse authority:

```
Memory OS     →X Conversation rewrite
Context OS    →X Conversation rewrite
Continuity    →X Conversation rewrite
Client        →X Conversation rewrite
```

## 14. Acceptance Gates

- [x] ConversationMessage = sole canonical transcript truth (§1)
- [x] ConversationRuntime = sole canonical transcript authority (§1)
- [x] Conversation ≠ Session (§2)
- [x] ConversationMessage schema frozen (§3)
- [x] Turn ≠ Message (§4)
- [x] Status lifecycle frozen (§5)
- [x] created_at = canonical event time, not import/retrieval time (§3)
- [x] Atomic append/finalization (§6)
- [x] Completed transcript immutable except governed correction (§6)
- [x] Reverse Authority Prohibition frozen (§7)
- [x] Context projection cannot mutate transcript (§7)
- [x] Memory cannot replace transcript (§7)
- [x] Continuity cannot replace transcript (§7)
- [x] Client cache cannot become authority (§11)
- [x] Text/voice/web/Electron normalize to same authority (§10)
- [x] Historical Transcript Migration contract frozen (§8)
- [x] Migration deterministic + idempotent + atomic (§§8-9)
- [x] Migration preserves chronology and original timestamps (§8)
- [x] Migration performs no LLM/Memory/Continuity/Context side effects (§8)
- [x] Historical ID strategy frozen (§9)
- [x] Normal reopen does not require ContinuityCheckpoint (§12)
- [x] Production changes = 0

## 15. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §9
Depends: C-00 Cognitive Boundary (07f0ff0), C-01 Runtime Execution (f79db0d)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-03 through C-06, C-10, M0

C-02 FREEZE → C-03 Context OS GO
```
