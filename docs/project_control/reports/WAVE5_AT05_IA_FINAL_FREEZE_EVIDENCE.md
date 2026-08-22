# Wave5 AT-05 Integration Acceptance / Final Freeze Evidence — Retry Idempotency

Status: IA GREEN / FINAL FREEZE EVIDENCE READY
Date: 2026-08-22
Scope: AT-05 — Retry idempotency
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT05_R0_RETRY_IDEMPOTENCY_CONTRACT.md`
R1 evidence: `docs/project_control/reports/WAVE5_AT05_R1_PERMANENT_ACCEPTANCE_EVIDENCE.md`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry idempotency               IA GREEN / FROZEN READY
```

## 2. IA Purpose

AT-05 IA verifies the integrated route, not only unit-level R1 assertions:

```text
request / retry entry
  ↓
ConversationManagementService create/read surface
  ↓
ConversationRuntime governed turn path
  ↓
canonical idempotency gate
  ↓
StorageV2 canonical repository persistence
  ↓
fresh runtime/repository recovery
  ↓
exactly-one canonical user/assistant effect
```

IA keeps the AT-05 scope narrow: same logical turn retry must not duplicate canonical history. It does not test AT-04 reconnect UUID allocation, AT-07 segment rotation, AT-08 pagination, provider retry policy, or retry UX.

## 3. Integration Test Artifact

Added:

```text
tests/wave5/test_at05_integration_acceptance.py
```

## 4. IA Test Case Coverage

| Test Case | Target | Status |
|---|---|---|
| TC-AT05-IA-001 | real management/runtime retry path is exactly-once | GREEN |
| TC-AT05-IA-002 | real restart/recovery retry path remains exactly-once | GREEN |
| TC-AT05-IA-003 | real conflict path rejects and preserves canonical transcript | GREEN |
| TC-AT05-IA-004 | real metadata variation retry cannot create new history | GREEN |
| TC-AT05-IA-005 | real partial failure retry has no duplicate or phantom completion | GREEN |

## 5. Evidence Commands

### AT-05 IA

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at05_integration_acceptance.py
```

Observed result:

```text
5 passed in 0.13s
```

### AT-05 R1 + IA bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at05_retry_idempotency.py \
  tests/wave5/test_at05_integration_acceptance.py
```

Observed result:

```text
14 passed in 0.21s
```

### Wave5 AT-03/04/05 + authority focused bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py \
  tests/wave5/test_at04_integration_acceptance.py \
  tests/wave5/test_at05_retry_idempotency.py \
  tests/wave5/test_at05_integration_acceptance.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
75 passed in 1.09s
```

## 6. IA Findings

### 6.1 Real management/runtime retry path is exactly-once

IA creates the conversation through `ConversationManagementService.create(...)`, writes and retries through `ConversationRuntime.process_turn(...)`, then reads through `ConversationManagementService.get_messages(...)`.

Observed canonical result for the retried completed turn:

```text
one user message
one assistant message
same user_message_id
same assistant_message_id
```

### 6.2 Fresh runtime/repository recovery keeps retry idempotent

IA closes the first StorageV2 repository, opens a fresh runtime/service stack over the same repository, verifies the conversation through the management `open(...)` surface, and retries the same completed turn.

Observed:

```text
same canonical message IDs
no duplicate user
no duplicate assistant
```

This proves AT05-I03: idempotency derives from canonical repository state, not in-memory runtime cache.

### 6.3 Real conflict path fails closed

IA attempts:

```text
same conversation_id
same turn_id
different user content
```

Observed:

```text
TurnConflictError
transcript unchanged
zero canonical mutation
```

### 6.4 Retry metadata variation is non-authoritative

IA varies request/retry/transport metadata while keeping the same canonical turn identity and same content.

Observed:

```text
first append → appended_turn_ids=[turn]
retry append → skipped_turn_ids=[turn]
canonical transcript → one user + one assistant
```

This proves retry/request/transport metadata cannot create a new canonical history event.

### 6.5 Partial assistant failure does not forge completed history

IA runs a turn where user acceptance succeeds and assistant cognition fails, then retries the same logical turn.

Observed:

```text
all messages:
  user completed
  assistant failed

completed canonical history:
  user completed only
```

No duplicate user is created. No competing assistant is appended. No phantom completed assistant history is synthesized.

## 7. Boundary Confirmed

AT-05 final boundary now has R0, R1, and IA evidence:

```text
retry signal / request replay / transport repeat
  ≠
new canonical history authority
```

Expanded:

```text
same (conversation_id, turn_id) + same content
  → exactly one canonical effect

same (conversation_id, turn_id) + different content
  → conflict / zero mutation

fresh runtime retry
  → canonical repository reconciliation

retry metadata changes
  → no new canonical history

partial assistant failure retry
  → no duplicate and no phantom completion
```

## 8. Non-Goals Preserved

IA did not enter:

- AT-04 reconnect UUID generation or stale conversation rejection
- AT-06 cross-conversation sabotage
- AT-07 segment rotation
- AT-08 pagination
- AT-20 full restart recovery beyond retry idempotency
- network retry UX
- provider retry strategy
- S2S/TTS/media reconnect quality
- voice architecture redesign
- conversation creation idempotency key semantics

## 9. Gate Decision

```text
AT-05 Audit: COMPLETE
AT-05 R0 Contract: READY FOR FREEZE
AT-05 R1 Permanent Acceptance: GREEN
AT-05 Integration Acceptance: GREEN
AT-05 Final Freeze Evidence: FROZEN READY
```

Next:

```text
AT-05 Final Freeze Record
```
