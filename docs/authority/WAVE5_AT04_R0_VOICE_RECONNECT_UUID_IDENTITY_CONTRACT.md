# Wave5 AT-04-R0 Contract — Voice Reconnect UUID Identity

Status: R0 FROZEN / MINIMAL REMEDIATION GREEN / R1 GREEN / IA HOLD
Date: 2026-08-22
Scope: AT-04 — Voice reconnect UUID identity
Source audit: `docs/project_control/reports/WAVE5_AT04_VOICE_RECONNECT_UUID_IDENTITY_AUDIT.md`

## 1. Purpose

AT-04 freezes the boundary that voice reconnect / transport retry cannot acquire canonical turn authority.

Source requirement:

```text
Reconnect repeatedly.
No reused canonical turn_id.
```

This is not a test of UUID formatting alone. It is a test of semantic turn identity authority across reconnect.

## 2. Current Gate Position

```text
AT-04 Audit: COMPLETE
Core semantic intent: CLEAR
Implementation readiness: MINIMAL REMEDIATION GREEN
Implementation: COMPLETED FOR P0-GAP-1/P0-GAP-2
R1: GREEN
```

Reason:

The audit found two P0 authority gaps. They are frozen as fail-closed requirements and now have minimal remediation evidence; R1 evidence remains on HOLD until the remediation commit is reviewed/accepted.

## 3. P0 Gaps Frozen by This Contract

### P0-GAP-1 — StorageV2 turn_id conflict does not fail closed

Observed audit probe:

```text
legacy     → CONFLICT
storage_v2 → NO_CONFLICT / skipped_turn_ids=["reused-turn"]
```

Bad behavior:

```text
same conversation_id
same turn_id
new/different voice content
  ↓
silently skipped as if idempotent
```

Why this is P0:

A reconnect collision can make a new user utterance disappear while the system reports success. This corrupts canonical history integrity.

Required behavior:

```text
same conversation_id + same turn_id + same content
  → idempotent retry / no duplicate

same conversation_id + same turn_id + different content
  → identity conflict / fail closed
```

Forbidden:

- silent skip
- overwrite
- merge
- append under same `turn_id`
- treating different content as successful idempotency

### P0-GAP-2 — Unknown conversation_id may auto-create ghost canonical truth

Observed audit probe:

```text
before get_conversation("stale-voice-reconnect-cid") → None
process_turn(conversation_id="stale-voice-reconnect-cid", modality="voice")
after get_conversation("stale-voice-reconnect-cid") → exists
```

Bad behavior:

```text
stale / typo / reconnect-provided conversation_id
  ↓
automatic canonical conversation creation
```

Why this is P0:

Reconnect reference is not conversation creation authority. A stale or malformed reconnect can manufacture ghost conversation truth.

Required behavior:

```text
unknown/stale conversation_id on reconnect
  → CONVERSATION_NOT_FOUND / fail closed
  → zero canonical conversation created
  → caller must explicitly create, recover, or select an existing conversation
```

Forbidden:

- auto-create on append/open/resume/reconnect
- ghost conversation creation from transport id
- treating stale reconnect id as explicit create intent

## 4. Frozen Invariants

### AT04-I01 — Reconnect creates fresh logical turn identity for new utterances

A new voice utterance after reconnect MUST use a fresh canonical `turn_id`.

Reconnect does not mean “continue using the previous logical turn.”

### AT04-I02 — Same turn_id + same content is idempotent retry

For the same `conversation_id`:

```text
same turn_id + same user content + same modality
  → idempotent retry
  → no duplicate user message
  → no duplicate assistant message
```

This is allowed for network retry / at-least-once delivery of the same logical turn.

### AT04-I03 — Same turn_id + different content is identity conflict

For the same `conversation_id`:

```text
same turn_id + different user content
  → identity conflict
  → fail closed
```

This is mandatory across all canonical repository backends, including StorageV2.

### AT04-I04 — Unknown/stale conversation_id on reconnect must not auto-create truth

Reconnect may reference an existing canonical `conversation_id`.

If the referenced `conversation_id` is unknown:

```text
CONVERSATION_NOT_FOUND
zero canonical mutation
```

Creation requires an explicit governed create operation.

### AT04-I05 — Transport/session identifiers are not canonical turn_id authority

The following are not canonical turn identity authorities:

- `voice_session_id`
- reconnect id
- websocket id
- RTC room/session id
- S2S connection id
- participant id
- trace id
- speech id
- reconnect count

They MAY be recorded as provenance/diagnostics.

They MUST NOT be used as proof of unique canonical `turn_id` generation.

### AT04-I06 — Recovery must show no reused turn_id for distinct utterances

After reconnect and fresh runtime/repository recovery, the canonical transcript MUST NOT contain a reused `turn_id` for distinct user utterances.

Expected property:

```text
distinct user utterance
  → distinct canonical turn_id
```

Unless it is the same logical turn retry with identical content.

## 5. Required Fix Scope Before R1

Implementation remains HOLD until the fix plan covers both P0s:

1. StorageV2 `append_external_turns_atomic` must compare existing turn content/modality/status before idempotent skip.
2. Governed voice/product reconnect ingress must reject unknown `conversation_id` before calling any runtime path that can auto-create.
3. If direct `ConversationRuntime.process_turn` remains auto-create capable for legacy reasons, AT-04 IA must prove the active reconnect ingress does not expose that behavior.
4. If Core policy changes to reject unknown `conversation_id` in turn paths, compatibility impact must be recorded separately.

## 6. R1 Hold Criteria

R1 must remain HOLD until tests can prove:

- StorageV2 conflict behavior is fail-closed.
- stale reconnect `conversation_id` cannot create ghost truth through governed ingress.
- repeated reconnect simulation produces fresh canonical turn IDs for distinct utterances.
- same logical turn retry remains idempotent.

## 7. Suggested R1 Test IDs

```text
TC-AT04-R1-001 repeated reconnect → distinct voice utterances have distinct canonical turn_id
TC-AT04-R1-002 same turn_id + same content → idempotent retry / no duplicate
TC-AT04-R1-003 same turn_id + different content → conflict on every repository backend
TC-AT04-R1-004 stale reconnect conversation_id → rejected / no ghost conversation
TC-AT04-R1-005 transport ids cannot be treated as canonical turn_id authority
TC-AT04-R1-006 fresh runtime recovery preserves collision-free turn identity
```

## 8. Explicit Non-Goals

AT-04-R0 does not freeze or test:

- TTS quality
- voice clone consistency
- speaker identity
- emotion/prosody
- realtime latency
- S2S media continuity quality
- AT-03 mixed modality sequence
- AT-05 retry idempotency beyond turn identity boundary

## 9. Gate Decision

```text
AT-04-R0 Contract: FROZEN
Implementation: MINIMAL REMEDIATION GREEN
R1: GREEN
IA: HOLD
Freeze: NOT READY
```
