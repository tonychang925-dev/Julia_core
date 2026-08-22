# Wave5 AT-05-R1 Permanent Acceptance Evidence — Retry Idempotency

Status: R1 GREEN
Date: 2026-08-22
Scope: AT-05 — Retry idempotency
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT05_R0_RETRY_IDEMPOTENCY_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT05_RETRY_IDEMPOTENCY_AUDIT.md`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry idempotency               R1 GREEN
```

## 2. R1 Purpose

AT-05-R1 converts the R0 retry idempotency contract into permanent Wave5 acceptance tests.

Frozen rule:

```text
Retry may repeat execution, but may not repeat canonical history.

Same canonical turn identity retry must produce exactly one canonical effect.
```

The R1 evidence is limited to same logical turn retry semantics. It does not test reconnect UUID generation, segment rotation, pagination, provider retry strategy, or retry UX.

## 3. Permanent Test Artifact

Added:

```text
tests/wave5/test_at05_retry_idempotency.py
```

## 4. Test Case Coverage

| Test Case | Target | Status |
|---|---|---|
| TC-AT05-R1-001 | same text turn retry returns same user and assistant message IDs | GREEN |
| TC-AT05-R1-002 | completed text retry leaves exactly one user and one assistant message | GREEN |
| TC-AT05-R1-003 | concurrent same turn retry converges to one canonical turn | GREEN |
| TC-AT05-R1-004 | external/voice identical turn batch retry skips without duplicate user/assistant | GREEN |
| TC-AT05-R1-005 | same turn_id with different content conflicts and leaves transcript unchanged | GREEN |
| TC-AT05-R1-006 | fresh runtime retry after completed turn recovery remains exactly-once | GREEN |
| TC-AT05-R1-007 | same turn_id in different conversations is isolated | GREEN |
| TC-AT05-R1-008 | partial/failed assistant retry does not duplicate canonical effects | GREEN |
| TC-AT05-R1-009 | retry metadata changes cannot create new canonical history | GREEN |

## 5. Evidence Commands

### AT-05 R1 permanent test

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at05_retry_idempotency.py
```

Observed result:

```text
9 passed in 0.16s
```

### AT-05 focused existing + permanent bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at05_retry_idempotency.py \
  tests/test_conversation_authority.py::TestIdempotency \
  tests/test_conversation_authority.py::TestP1ConversationConvergence::test_retry_idempotency_no_duplicate \
  tests/test_voice_turn_reconciliation.py::test_retry_identical_batch_is_idempotent \
  tests/test_voice_turn_reconciliation.py::test_same_turn_id_different_content_conflicts \
  tests/rt2_r3/test_core_acceptance.py::test_r3_at04_retry_exactly_once \
  tests/rt2_r2/test_cutover.py::test_d_at06_idempotent_on_v2 \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at05_idempotent_turn \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py::test_tc_at04_r1_002_same_turn_same_content_idempotent_no_duplicate \
  tests/wave5/test_at04_integration_acceptance.py::test_tc_at04_ia_002_real_retry_path_idempotent_no_duplicate
```

Observed result:

```text
20 passed in 0.28s
```

## 6. R0 Invariant Mapping

| R0 Invariant | R1 Evidence |
|---|---|
| AT05-I01 same canonical identity + same content is idempotent retry | TC-AT05-R1-001, TC-AT05-R1-002, TC-AT05-R1-004 |
| AT05-I02 retry must not duplicate user or assistant messages | TC-AT05-R1-002, TC-AT05-R1-003, TC-AT05-R1-004 |
| AT05-I03 idempotency survives fresh runtime / Brain restart | TC-AT05-R1-006 |
| AT05-I04 same turn identity + different content is conflict, not retry | TC-AT05-R1-005 |
| AT05-I05 retry metadata is not canonical retry authority | TC-AT05-R1-009 |
| AT05-I06 raw repository add_message is not the acceptance-level retry surface | R1 tests exercise governed `ConversationRuntime.process_turn(...)` and `append_external_turns(...)` paths |
| AT05-I07 partial execution retry may recover existing effects but cannot synthesize false completion | TC-AT05-R1-008 |
| AT05-I08 idempotency is scoped by conversation_id | TC-AT05-R1-007 |

## 7. Key Findings Proven by R1

### 7.1 Same logical turn retry is exactly-once

A repeated call with the same `(conversation_id, turn_id)` and identical content returns the same canonical user and assistant message IDs. Canonical storage contains one user message and one assistant message for the completed turn.

### 7.2 Concurrent retry converges to one canonical turn

Concurrent same-turn submissions through the governed runtime path converge to a single canonical turn. R1 uses the legacy runtime path for this concurrency proof because StorageV2's sqlite connection is not a cross-thread test fixture surface.

### 7.3 Voice/external retry is reconciled, not duplicated

Identical external voice turn retry returns `skipped_turn_ids` and does not append a second user or assistant message.

### 7.4 Conflict is not retry

Same `conversation_id + turn_id` with different content raises `TurnConflictError` and leaves the transcript unchanged. This preserves the AT-04 identity conflict boundary while proving the AT-05 false-idempotency guard.

### 7.5 Fresh runtime retry remains exactly-once

After closing the first runtime/repository and opening a fresh runtime over the same repository, retrying the same completed turn resolves to the existing canonical turn and creates no duplicate messages.

### 7.6 Idempotency is scoped by conversation_id

The same `turn_id` string can exist independently in two different conversations. AT-05 idempotency identity is `(conversation_id, turn_id)`, not bare `turn_id`.

### 7.7 Partial/failed assistant retry does not invent success history

After assistant failure, retrying the same logical turn does not duplicate the accepted user message and does not create a competing assistant message. Completed canonical history contains only the completed user fact and does not synthesize a completed assistant entry.

### 7.8 Retry metadata cannot create new history

Changing request/retry/transport metadata on an otherwise identical external turn does not create a new canonical history event. Canonical retry truth remains governed by the runtime/reconciliation path over repository state.

## 8. Non-Goals Preserved

R1 did not enter:

- AT-04 reconnect UUID generation
- AT-06 cross-conversation sabotage
- AT-07 segment rotation
- AT-08 pagination
- AT-20 full restart recovery beyond retry idempotency
- retry UX
- provider retry strategy
- S2S/TTS/media reconnect quality
- voice architecture redesign

## 9. Gate Decision

```text
AT-05 Audit: COMPLETE
AT-05 R0 Contract: READY FOR FREEZE
AT-05 R1 Permanent Acceptance: GREEN
AT-05 IA: HOLD
AT-05 Freeze: NOT READY
```

Next:

```text
AT-05 Integration Acceptance
```
