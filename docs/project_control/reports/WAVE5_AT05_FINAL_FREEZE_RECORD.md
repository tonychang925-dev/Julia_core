# Wave5 AT-05 Final Freeze Record — Retry Idempotency

Status: FROZEN
Date: 2026-08-22
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Freeze commit candidate: `aa4eb43`
Scope: AT-05 — Retry idempotency

## 1. Freeze Decision

```text
AT-05 Retry Idempotency: FROZEN
```

AT-05 is frozen because the full lineage is complete:

```text
Audit
  ↓
R0 Contract
  ↓
R1 Permanent Acceptance Evidence
  ↓
Integration Acceptance
  ↓
Final Freeze Evidence
  ↓
Final Freeze Record
```

No implementation remediation was required before R1 because the Audit found no new P0 blocker.

## 2. Commit Lineage

```text
a9d36cc  feat: STORAGE-DIA-7-R2-R0/R1 context admission contract + bridge
  ↓
9791651  test(wave5): freeze AT-03 text voice text evidence
  ↓
a59d625  docs(wave5): freeze AT-04 reconnect UUID R0 contract
  ↓
e966375  fix(wave5): remediate AT-04 turn identity boundaries
  ↓
30eb91e  test(wave5): add AT-04 reconnect sabotage evidence
  ↓
072e7f8  test(wave5): add AT-04 integration acceptance evidence
  ↓
e86dc56  docs(wave5): freeze AT-04 reconnect identity evidence
  ↓
ed37e96  docs(wave5): freeze AT-05 retry idempotency R0 contract
  ↓
fa0d51c  test(wave5): add AT-05 retry idempotency evidence
  ↓
aa4eb43  test(wave5): add AT-05 integration acceptance evidence
```

## 3. Frozen Artifacts

```text
docs/project_control/reports/WAVE5_AT05_RETRY_IDEMPOTENCY_AUDIT.md
docs/authority/WAVE5_AT05_R0_RETRY_IDEMPOTENCY_CONTRACT.md
docs/project_control/reports/WAVE5_AT05_R1_PERMANENT_ACCEPTANCE_EVIDENCE.md
docs/project_control/reports/WAVE5_AT05_IA_FINAL_FREEZE_EVIDENCE.md
docs/project_control/reports/WAVE5_AT05_FINAL_FREEZE_RECORD.md
tests/wave5/test_at05_retry_idempotency.py
tests/wave5/test_at05_integration_acceptance.py
```

## 4. Frozen Boundary

AT-05 freezes this boundary:

```text
retry signal / request replay / transport repeat
  ≠
new canonical history authority
```

Primary rule:

```text
Retry may repeat execution, but may not repeat canonical history.

Same canonical turn identity retry must produce exactly one canonical effect.
```

Confirmed rules:

1. Same `(conversation_id, turn_id)` with identical canonical content is an idempotent retry.
2. Retry creates neither duplicate user message nor duplicate assistant message.
3. Idempotency survives fresh runtime / Brain restart over the same canonical repository.
4. Same turn identity with different content is conflict, not retry.
5. Retry metadata, request ids, and transport/session ids are not canonical retry authority.
6. Raw `repository.add_message(...)` is not the acceptance-level retry authority surface.
7. Partial execution retry may recover existing effects but may not synthesize false completion.
8. Idempotency is scoped by `conversation_id`; canonical retry identity is `(conversation_id, turn_id)`, not bare `turn_id`.

## 5. Verification Evidence

### AT-05 R1 Permanent Acceptance

```text
tests/wave5/test_at05_retry_idempotency.py
9 passed
```

### AT-05 Focused Existing + Permanent Bundle

```text
tests/wave5/test_at05_retry_idempotency.py
tests/test_conversation_authority.py::TestIdempotency
tests/test_conversation_authority.py::TestP1ConversationConvergence::test_retry_idempotency_no_duplicate
tests/test_voice_turn_reconciliation.py::test_retry_identical_batch_is_idempotent
tests/test_voice_turn_reconciliation.py::test_same_turn_id_different_content_conflicts
tests/rt2_r3/test_core_acceptance.py::test_r3_at04_retry_exactly_once
tests/rt2_r2/test_cutover.py::test_d_at06_idempotent_on_v2
tests/rt2_r2/test_storage_v2_repository.py::test_b_at05_idempotent_turn
tests/wave5/test_at04_voice_reconnect_uuid_identity.py::test_tc_at04_r1_002_same_turn_same_content_idempotent_no_duplicate
tests/wave5/test_at04_integration_acceptance.py::test_tc_at04_ia_002_real_retry_path_idempotent_no_duplicate

20 passed
```

### AT-05 Integration Acceptance

```text
tests/wave5/test_at05_integration_acceptance.py
5 passed
```

### AT-05 R1 + IA Bundle

```text
tests/wave5/test_at05_retry_idempotency.py
tests/wave5/test_at05_integration_acceptance.py

14 passed
```

### Wave5 AT-03/04/05 + Authority Focused Bundle

```text
tests/wave5/test_at03_text_voice_text.py
tests/wave5/test_at03_integration_acceptance.py
tests/wave5/test_at04_voice_reconnect_uuid_identity.py
tests/wave5/test_at04_integration_acceptance.py
tests/wave5/test_at05_retry_idempotency.py
tests/wave5/test_at05_integration_acceptance.py
tests/test_voice_turn_reconciliation.py
tests/test_conversation_authority.py

75 passed
```

### Compile Check

```text
/opt/miniconda3/bin/python -m compileall -q julia_core tests/wave5/test_at05_integration_acceptance.py
compileall_exit=0
```

## 6. Integration Path Confirmed

AT-05 IA proved the real governed path:

```text
ConversationManagementService create/read
  ↓
ConversationRuntime governed turn path
  ↓
canonical idempotency gate
  ↓
StorageV2 repository persistence
  ↓
fresh runtime / repository recovery
  ↓
exactly-one canonical effect
```

This confirms that retry idempotency is not merely an isolated unit behavior. It holds across product management surface, runtime authority, repository persistence, and recovery.

## 7. Explicit Non-Scope

AT-05 freeze does not include:

```text
AT-06 Cross-conversation sabotage
AT-07 segment rotation
AT-08 pagination
AT-20 full system restart recovery beyond retry idempotency evidence
AT-04 reconnect UUID generation or stale conversation rejection
network retry UX
provider retry strategy
S2S/TTS/media reconnect quality
voice architecture redesign
conversation creation idempotency key semantics
```

## 8. Acceptance Matrix Update

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry Idempotency               FROZEN
```

## 9. Canonical-History Defense Chain

AT-03 through AT-05 now form this frozen canonical-history defense chain:

```text
AT-03: modality change does not split history
AT-04: reconnect / transport retry does not own identity authority
AT-05: execution retry does not duplicate canonical history
```

## 10. Next Gate

Next allowed Wave5 item:

```text
AT-06 Cross-conversation sabotage Audit
```

Do not start AT-06 implementation before AT-06 audit/contract confirms scope.
Do not start AT-07 segment rotation.
