# Wave5 AT-05-R0 Contract — Retry Idempotency

Status: R0 READY FOR FREEZE
Date: 2026-08-22
Scope: AT-05 — Retry idempotency
Source audit: `docs/project_control/reports/WAVE5_AT05_RETRY_IDEMPOTENCY_AUDIT.md`

## 1. Purpose

AT-05 freezes the boundary that retry may repeat execution, but may not repeat canonical history.

Source requirement:

```text
AT-05 — Retry idempotency

Same `(conversation_id, turn_id)` retry:

- no duplicate user message
- no duplicate assistant message
```

Primary rule:

```text
Same canonical turn identity retry must produce exactly one canonical effect.
```

AT-05 is not a retry UX or provider retry policy. It is a canonical history exactly-once contract for a retried logical turn.

## 2. Current Gate Position

```text
AT-05 Audit: COMPLETE
Core semantic intent: CLEAR
Implementation readiness: NOT BLOCKED by new P0
R0 Contract: READY FOR FREEZE
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

Reason:

The audit did not find a new P0 implementation blocker. Existing Core paths already contain idempotency behavior for governed runtime turn ingestion and external voice turn reconciliation. However, Wave5 still lacks AT-05-named permanent acceptance evidence, especially restart-over-canonical-repository retry evidence.

## 3. Boundary Statement

AT-05 freezes this authority boundary:

```text
retry signal / request replay / transport repeat
  ≠
new canonical history authority
```

A retry can re-enter runtime/reconciliation paths. It cannot create a second canonical user fact or a second canonical assistant fact for the same logical turn.

## 4. Frozen Invariants

### AT05-I01 — Same canonical identity + same content is idempotent retry

For the same `conversation_id` and same `turn_id`:

```text
same canonical user content
same modality
same logical turn identity
  → idempotent retry
```

The retry resolves to the already persisted canonical turn rather than creating a new turn.

### AT05-I02 — Retry must not duplicate user or assistant messages

For a completed logical turn retry:

```text
same conversation_id + same turn_id + same content
  → exactly one canonical user message
  → exactly one canonical assistant message
```

Forbidden:

- duplicate user message append
- duplicate assistant message append
- second logical turn under the same retry
- treating replay as a new canonical history event

### AT05-I03 — Idempotency survives fresh runtime / Brain restart

Idempotency MUST be derived from canonical repository state, not from in-memory runtime cache.

After a fresh runtime / Brain restart over the same canonical repository:

```text
retry same conversation_id + same turn_id + same content
  → reconcile existing canonical turn
  → zero duplicate user message
  → zero duplicate assistant message
```

This invariant is mandatory for R1 evidence.

### AT05-I04 — Same turn identity + different content is conflict, not retry

For the same `conversation_id` and `turn_id`:

```text
different user content
  → identity conflict
  → fail closed
  → zero canonical mutation
```

This invariant references the AT-04 frozen boundary. AT-05 does not re-open reconnect identity scope; it relies on the same fail-closed rule to prevent false-positive idempotent replay.

### AT05-I05 — Retry metadata is not canonical retry authority

The following may describe a retry attempt but MUST NOT define canonical retry truth:

- client retry counter
- request id
- websocket/session id
- voice/session id
- transport trace id
- provider retry id
- reconnect count
- local session history marker

Canonical retry authority is determined by governed runtime/reconciliation logic over canonical repository state.

### AT05-I06 — Raw repository add_message is not the acceptance-level retry surface

`repository.add_message(...)` is a low-level storage primitive. It is not the Wave5 acceptance-level retry authority surface.

Acceptance-level retry semantics belong to governed ingestion paths such as:

```text
ConversationRuntime.process_turn(...)
ConversationRuntime.accept_user_turn(...)
ConversationRuntime.append_external_turns(...)
repository.append_external_turns_atomic(...)
```

R1 and IA MUST validate retry through governed runtime/reconciliation entry points, not by assuming raw storage writes enforce full semantic idempotency.

### AT05-I07 — Partial execution retry may recover existing effects but cannot synthesize false completion

A retry after partial execution may discover and return existing canonical effects.

It MUST NOT:

- duplicate the durable user fact;
- append competing assistant messages for the same logical turn;
- synthesize a missing assistant history entry merely to appear complete;
- erase or downgrade the accepted user fact frozen by AT-02.

If future behavior re-runs assistant completion for a failed/partial turn, that policy must be explicit, governed, and covered by a later contract. AT-05-R0 freezes no-duplicate canonical effect, not assistant recomputation policy.

### AT05-I08 — Idempotency is scoped by conversation_id

`turn_id` uniqueness is scoped to canonical conversation identity.

```text
conversation A + turn_id T
conversation B + turn_id T
  → independent logical turns
```

Retry detection MUST NOT collide across conversations.

## 5. R1 Hold Criteria

R1 remains HOLD until permanent Wave5-named tests prove:

- same text turn retry returns the same canonical user and assistant message IDs;
- same text turn retry leaves exactly one user and one assistant message;
- concurrent same-turn retry converges to one canonical turn;
- external/voice identical turn batch retry appends no duplicate user or assistant messages;
- same turn identity with different content fails closed and preserves transcript;
- fresh runtime retry over the same canonical repository remains exactly-once;
- same `turn_id` in different conversations is isolated;
- partial/failed assistant retry does not duplicate canonical user or create competing assistant messages.

## 6. Suggested R1 Test IDs

```text
TC-AT05-R1-001 same text turn retry returns same user and assistant message IDs
TC-AT05-R1-002 same text turn retry leaves exactly one user and one assistant message
TC-AT05-R1-003 concurrent same turn retry converges to one canonical turn
TC-AT05-R1-004 external/voice identical turn batch retry skips without duplicate user/assistant
TC-AT05-R1-005 same turn_id with different content conflicts and leaves transcript unchanged
TC-AT05-R1-006 fresh runtime retry after completed turn recovery remains exactly-once
TC-AT05-R1-007 same turn_id in different conversations is isolated
TC-AT05-R1-008 partial/failed assistant retry does not duplicate canonical effects
```

## 7. Required IA Focus

AT-05 IA should prove the real governed route:

```text
retry entry point
  ↓
ConversationRuntime / governed reconciliation
  ↓
canonical repository lookup by conversation_id + turn_id
  ↓
existing canonical turn returned/reconciled
  ↓
no duplicate user or assistant message
  ↓
fresh recovery confirms exactly-once transcript
```

IA must not use transport-local/session-local history as retry truth.

## 8. Explicit Non-Goals

AT-05-R0 does not freeze or test:

- AT-04 reconnect UUID generation or stale conversation rejection
- AT-07 segment rotation
- AT-08 pagination semantics
- AT-20 full system restart recovery beyond retry idempotency evidence
- network retry UX
- provider retry strategy
- S2S/TTS/media reconnect quality
- voice architecture redesign
- conversation creation idempotency keys

## 9. Failure Criteria

Any of the following fails AT-05:

- retry creates more than one canonical user message for the same logical turn;
- retry creates more than one canonical assistant message for the same completed logical turn;
- retry correctness depends only on in-memory cache and fails after fresh runtime over the same repository;
- same `conversation_id + turn_id` with different content is accepted as retry;
- retry metadata or transport/session identity is treated as canonical retry authority;
- raw storage write behavior is presented as acceptance-level retry proof without governed runtime/reconciliation validation;
- partial execution retry manufactures missing canonical history to hide incomplete state.

## 10. Gate Decision

```text
AT-05-R0 Contract: READY FOR FREEZE
Implementation: NOT REQUIRED BEFORE R1 unless R1 exposes a gap
R1: HOLD
IA: HOLD
Freeze: NOT READY
```
