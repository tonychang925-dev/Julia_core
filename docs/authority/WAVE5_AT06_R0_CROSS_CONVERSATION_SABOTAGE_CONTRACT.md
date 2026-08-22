# Wave5 AT-06-R0 Contract — Cross-conversation Sabotage

Status: R0 READY FOR FREEZE / IMPLEMENTATION BLOCKED BY P0 GAP
Date: 2026-08-22
Scope: AT-06 — Cross-conversation sabotage
Source audit: `docs/project_control/reports/WAVE5_AT06_CROSS_CONVERSATION_SABOTAGE_AUDIT.md`

## 1. Purpose

AT-06 freezes the boundary that one canonical conversation cannot become another conversation's storage, search, Context OS, Electron/client, or provider-visible truth.

Source requirement:

```text
AT-06 — Cross-conversation sabotage

Conversation A and B contain distinct markers.

No leakage through storage, search, Context OS, or Electron.
```

Primary rule:

```text
Conversation boundary is a canonical isolation boundary.
```

AT-06 is not a multi-user authorization, encryption, or tenancy redesign. It is a canonical conversation isolation contract.

## 2. Current Gate Position

```text
AT-06 Audit: COMPLETE
Core semantic intent: CLEAR
Storage/runtime lane: GREEN
Search lane: AMBER
Context OS lane: RED / P0 GAP
Electron/client cache lane: AMBER
Implementation: BLOCKED
R0 Contract: READY FOR FREEZE
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

Reason:

The audit proved storage/runtime marker isolation but found a P0 Context OS authority gap: `ContextExecutionRuntime.prepare(conversation_id="conv_B", history=[conv_A, conv_B])` can make conversation A marker provider-visible inside conversation B context.

## 3. P0 Gap Frozen by This Contract

### P0-GAP-1 — Context OS admits foreign conversation history from caller-supplied history

Observed audit probe:

```text
ContextExecutionRuntime.prepare(
  conversation_id="conv_B",
  history=[
    conv_A user: ALPHA_PRIVATE_MARKER_001,
    conv_A assistant: ack A,
    conv_B user: BETA_PRIVATE_MARKER_002,
    conv_B assistant: ack B,
  ]
)
```

Observed provider-visible output:

```text
ALPHA_PRIVATE_MARKER_001
BETA_PRIVATE_MARKER_002
```

Bad behavior:

```text
foreign conversation history
  ↓
caller-supplied history
  ↓
Context OS ActiveTail
  ↓
provider-visible context
```

Why this is P0:

Storage isolation alone is not sufficient. Context OS is the model-visible admission boundary. If Context OS accepts foreign conversation history, then conversation A can become visible while processing conversation B even when the canonical repository remains correctly isolated.

Required behavior:

```text
Context OS prepare for conversation B
  + candidate/history item whose conversation_id is A
    → reject / drop / quarantine before model-visible output
    → zero A marker in B provider-visible messages
```

Forbidden:

- trusting caller-supplied mixed history as already authorized;
- admitting foreign conversation messages into ActiveTail;
- recording provenance as `conversation:B` while rendering messages from `conversation:A`;
- using search results, Electron cache, voice session cache, or runtime-local history as current-conversation truth without canonical conversation gating.

## 4. Frozen Invariants

### AT06-I01 — Conversation boundary is a canonical isolation boundary

Each canonical `conversation_id` defines an isolation boundary.

```text
conversation A
  ≠
conversation B
```

A message, turn, transcript, search hit, context candidate, UI cache entry, or model-visible frame from A MUST NOT become current conversation truth for B.

### AT06-I02 — Storage read/recovery is scoped by canonical conversation_id

Canonical storage and recovery for a conversation MUST read only that conversation's transcript.

```text
read/recover conversation A
  → A messages only
  → zero B marker

read/recover conversation B
  → B messages only
  → zero A marker
```

Segment files, catalog rows, search indexes, caches, and recovery scans must not merge transcripts across conversation IDs.

### AT06-I03 — Search results are derived candidates, not current-conversation authority

Search may be a global derived read model and may return multiple conversation handles for broad queries.

However:

```text
search relevance
  ≠
permission to enter current conversation context
```

Search hits, snippets, ranks, cursors, handles, and candidate lists MUST NOT be treated as current-conversation transcript or Context OS admission authority.

### AT06-I04 — Context preparation is scoped by canonical conversation identity

`Context OS prepare(conversation_id=B, ...)` MUST only admit context that is eligible for conversation B.

If a supplied history/candidate item carries `conversation_id=A` while active `conversation_id=B`:

```text
foreign item
  → reject / drop / quarantine
  → zero provider-visible A marker
```

The exact remediation mechanism may be reject, drop, or quarantine, but R1 must prove zero foreign marker reaches provider-visible output.

### AT06-I05 — Caller-supplied history is not authority

The following are not authorization to enter model-visible context:

- runtime-supplied history list by itself;
- client-supplied history;
- Electron local cache;
- voice/session local history;
- gateway `_sessions[session_id]["history"]`;
- search result payloads;
- retrieved candidate lists;
- provider prompt assembly inputs.

Context OS must perform or rely on a governed canonical conversation gate before rendering provider-visible messages.

### AT06-I06 — Context OS admission must preserve conversation boundary even after retrieval/candidate mistakes

Even if an upstream retrieval/search/cache layer returns a foreign conversation candidate:

```text
candidate from A
  + active conversation B
    → not visible in B
```

This preserves the already-frozen Wave5 boundary:

```text
retrieved
  ≠
projected
  ≠
admitted
  ≠
visible
  ≠
consumed
```

### AT06-I07 — Electron/client/session cache is not canonical history or Context OS input authority

Electron/client/session cache MAY store temporary UI or transport state.

It MUST NOT:

- recover canonical transcript;
- define current conversation history;
- feed Context OS directly as model-visible history;
- override canonical repository state;
- merge A/B UI histories during rapid conversation switching.

### AT06-I08 — Runtime and interaction caches are scoped by conversation_id

Runtime interaction state and derived caches MUST be keyed by `conversation_id` and rebuild only from that conversation's canonical messages.

A cache hit for A cannot answer or seed B.

### AT06-I09 — Provider-visible context must contain no foreign conversation marker

For marker sabotage:

```text
Conversation A: ALPHA_PRIVATE_MARKER_001
Conversation B: BETA_PRIVATE_MARKER_002
```

When preparing or consuming conversation B:

```text
provider-visible messages contain BETA_PRIVATE_MARKER_002 if B history is eligible
provider-visible messages contain zero ALPHA_PRIVATE_MARKER_001
```

And vice versa.

### AT06-I10 — Fresh runtime/repository recovery preserves A/B isolation

After restart over the same canonical repository:

```text
A recovery → A marker only
B recovery → B marker only
Context OS for A → no B marker
Context OS for B → no A marker
```

## 5. Required Fix Scope Before R1

Implementation remains HOLD until a minimal remediation plan covers the P0 Context OS gap:

1. Context OS must enforce active `conversation_id` against history/candidate items that carry a `conversation_id` field.
2. Foreign conversation items must be rejected, dropped, or quarantined before `CognitiveContextPackage.to_messages(...)` can make them provider-visible.
3. Provenance must not claim `conversation:B` for rendered messages that originated from `conversation:A`.
4. Runtime governed path must remain compatible: correctly scoped canonical history for the active conversation must continue to pass.
5. The fix must not redesign search, Electron, authorization, encryption, tenancy, or segment storage.

## 6. R1 Hold Criteria

R1 must remain HOLD until permanent Wave5-named tests prove:

- Storage A/B marker reads are isolated.
- Fresh runtime recovery preserves A/B marker isolation.
- Marker-specific search returns only matching conversation handles.
- Broad/global search candidates cannot become current-conversation transcript authority.
- Context OS mixed-history sabotage cannot make A marker visible in B.
- Runtime interaction cache is conversation-scoped and rebuilds from canonical state.
- Electron/session cache simulation cannot restore A history into B.
- Provider-visible messages for B contain no A marker under sabotage input.

## 7. Suggested R1 Test IDs

```text
TC-AT06-R1-001 storage A/B marker isolation through canonical reads
TC-AT06-R1-002 fresh runtime recovery preserves A/B marker isolation
TC-AT06-R1-003 search marker-specific query returns only matching conversation handle
TC-AT06-R1-004 broad search results cannot be used as current-conversation transcript
TC-AT06-R1-005 Context OS mixed-history sabotage rejects/drops foreign conversation marker
TC-AT06-R1-006 runtime interaction cache A/B isolation and rebuild from canonical state
TC-AT06-R1-007 electron/session cache simulation cannot restore A history into B
TC-AT06-R1-008 provider-visible messages for B contain no A marker under sabotage input
```

## 8. Required IA Focus

AT-06 IA should prove the real governed route:

```text
ConversationManagementService create/read/search
  ↓
ConversationRuntime governed turn path
  ↓
canonical repository scoped by conversation_id
  ↓
Context OS scoped admission for active conversation_id
  ↓
client/session cache treated as non-authoritative
  ↓
provider-visible output contains no foreign conversation marker
```

IA should validate product-like A/B switching and recovery, not only isolated helper functions.

## 9. Explicit Non-Goals

AT-06-R0 does not freeze or test:

- multi-user authorization
- encryption
- distributed tenancy
- access-control redesign
- search ranking optimization
- vector index architecture
- Electron architecture redesign
- voice architecture redesign
- AT-07 segment rotation
- AT-08 pagination
- AT-20 full restart recovery beyond A/B isolation evidence
- provider response quality

## 10. Failure Criteria

Any of the following fails AT-06:

- storage read/recovery for A exposes B marker or messages;
- Context OS for B renders A marker provider-visible;
- search hit/snippet/rank/cursor is treated as current conversation transcript authority;
- Electron/client/session cache restores or injects A history into B;
- runtime/interaction cache for A influences B;
- provenance claims active conversation B while rendering foreign conversation A message;
- broad search candidates are admitted into model-visible context without canonical conversation gating.

## 11. Gate Decision

```text
AT-06-R0 Contract: READY FOR FREEZE
Implementation: BLOCKED until P0 Context OS gap remediation starts
R1: HOLD
IA: HOLD
Freeze: NOT READY
```
