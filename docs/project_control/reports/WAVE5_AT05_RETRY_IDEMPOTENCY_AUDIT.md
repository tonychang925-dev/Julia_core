# Wave5 AT-05 Retry Idempotency Audit

Status: AUDIT COMPLETE / R0 READY
Date: 2026-08-22
Scope: AT-05 — Retry idempotency
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Observed HEAD: `e86dc56`
Core lane: `/Users/admin/julia_core_wave4_integration`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry idempotency               AUDIT START
```

## 2. AT-05 Source Requirement

From `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-05 — Retry idempotency

Same `(conversation_id, turn_id)` retry:

- no duplicate user message
- no duplicate assistant message
```

AT-05 validates exactly-once canonical persistence for a retried logical turn. It is related to AT-04 but has a narrower focus: retry of the same logical turn must converge to one canonical user message and one canonical assistant message, rather than creating duplicate history.

## 3. Non-Goals

AT-05 does not test:

- voice reconnect UUID generation, already frozen by AT-04
- unknown/stale `conversation_id` rejection, already frozen by AT-04 / GAP8
- general voice architecture, S2S, TTS, latency, or reconnect UX
- conversation creation idempotency keys, which belong to management create semantics rather than turn retry
- re-running assistant cognition after an already-persisted turn, unless R0 explicitly defines a retry policy for incomplete/failed assistant state

## 4. Authority Baseline

Relevant existing authority rules:

- `STO_D0_DECISION_REGISTER_v1.0.md`
  - retry must inspect canonical store by `conversation_id + turn_id`;
  - content-identical user message is idempotent recovery of the same logical turn;
  - same `turn_id` with different content is conflict / fail closed;
  - retry must not append a duplicate canonical message.

- `ConversationRuntime.accept_user_turn(...)`
  - user message is durable canonical fact before cognition;
  - same `turn_id + same content` returns existing result;
  - same `turn_id + different content` raises `TurnConflictError`.

- `ConversationRuntime.process_turn(...)`
  - if `_accept_user_turn_locked(...)` marks the turn as `_idempotent_replay`, processing returns the existing canonical result and does not append another assistant message.

- `StorageV2ConversationRepository.append_external_turns_atomic(...)`
  - same external `turn_id` with matching user/modality/assistant fields is skipped as idempotent;
  - same external `turn_id` with different content now raises `TurnConflictError` after AT-04 remediation.

## 5. Audit Questions

AT-05 must answer:

1. Does same `(conversation_id, turn_id)` + same user content retry return/reconcile the existing canonical turn?
2. Does retry avoid appending a duplicate user message?
3. Does retry avoid appending a duplicate assistant message?
4. Is idempotency based on canonical repository state rather than session-local cache or transport-local history?
5. Does same `(conversation_id, turn_id)` + different content fail closed as identity conflict?
6. Does retry after runtime restart still converge through canonical store?
7. Is idempotency scoped by `conversation_id`, so identical `turn_id` values in different conversations remain isolated?

## 6. Evidence Commands

### Focused existing retry/idempotency evidence

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
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
11 passed in 0.38s
```

## 7. Code Path Findings

### F1 — Text `process_turn` has a canonical idempotency gate

Evidence:

- `julia_core/runtime/conversation_runtime.py::_accept_user_turn_locked`
  - calls `_find_turn_in_store(conversation_id, turn_id)` before any append;
  - content-identical replay returns existing `TurnResult` with `_idempotent_replay=True`;
  - content mismatch raises `TurnConflictError`.

- `julia_core/runtime/conversation_runtime.py::_process_turn_locked`
  - returns immediately when `_idempotent_replay=True`;
  - therefore does not append a second assistant message for the same completed logical turn.

Assessment: GREEN for Core text runtime lane.

### F2 — External voice turn retry is idempotent through repository reconciliation

Evidence:

- `ConversationRuntime.append_external_turns(...)` delegates to `repository.append_external_turns_atomic(...)` under canonical write lock.
- `StorageV2ConversationRepository.append_external_turns_atomic(...)` checks `find_turn(session_id, tid)` and skips only when `_turn_equals(...)` confirms same canonical user/modality/assistant content.
- Existing `tests/test_voice_turn_reconciliation.py::test_retry_identical_batch_is_idempotent` proves duplicate voice batch retry appends zero new turns.

Assessment: GREEN for Core external-turn lane after AT-04 remediation.

### F3 — Conflict boundary already exists and should be referenced, not reimplemented

Evidence:

- Same `conversation_id + turn_id + different content` raises `TurnConflictError` in runtime and external-turn paths.
- AT-04 has already frozen this as identity conflict / fail closed.

Disposition: AT-05 R0 should reference this boundary because it protects idempotency from false-positive replay, but AT-05 should not duplicate AT-04 reconnect scope.

### F4 — StorageV2 low-level `add_message(...)` is not itself an idempotency authority

Evidence:

- `tests/rt2_r2/test_storage_v2_repository.py::test_b_at05_idempotent_turn` explicitly notes: storage layer may allow duplicate user records through direct `add_message`; Runtime handles idempotency.

Impact:

Direct repository writes are a sharp edge. For AT-05, the acceptance boundary should state that canonical turn ingestion must go through governed runtime/external-turn APIs. Raw `add_message(...)` is storage plumbing and must not be treated as a retry surface.

Assessment: AMBER documentation/contract risk, not an implementation blocker if R0 freezes runtime/external-turn as the authority surface.

### F5 — Restart recovery is partially covered but lacks AT-05-named permanent evidence

Evidence:

- Existing runtime idempotency tests verify no duplicate user/assistant in live runtime.
- Existing restart tests verify canonical recovery generally.
- AT-04 IA includes fresh runtime recovery preserving turn identity.

Gap:

No dedicated Wave5 AT-05 test currently proves: completed turn persisted, runtime restarted, same `(conversation_id, turn_id, content)` retried, and canonical transcript remains exactly one user + one assistant.

Assessment: AMBER coverage gap for R1, not a P0 implementation gap.

### F6 — Assistant failure retry semantics must remain narrow

Evidence:

- AT-02 freezes that accepted user fact survives cognition failure.
- Current runtime behavior treats same `turn_id + same user content` as idempotent replay once the user message exists, returning existing turn state rather than blindly appending another assistant.

Audit disposition:

AT-05 must freeze no-duplicate behavior. It should not silently redefine product policy for re-running assistant cognition after a failed assistant message. If R0 includes failure retry, it should say: no duplicate user and no duplicate assistant; any completion retry policy must be explicit and governed, not implicit duplicate append.

## 8. Current Coverage Assessment

GREEN:

- Same text `process_turn` retry returns existing canonical message IDs.
- Concurrent same `turn_id` calls converge to one canonical turn.
- Voice/external identical batch retry appends zero new turns.
- Same `turn_id` with different content conflicts.
- Focused existing idempotency bundle passes: `11 passed`.

AMBER:

- No dedicated `tests/wave5/test_at05_retry_idempotency.py` permanent acceptance artifact yet.
- Restart-after-completed-turn retry needs AT-05-named evidence.
- Low-level repository `add_message(...)` is not an idempotency surface; R0 must explicitly keep retry authority at Runtime / governed external-turn ingestion.
- Assistant-failure same-turn retry semantics require a narrow contract statement to avoid accidental duplicate assistant append or accidental policy expansion.

RED/P0:

- No new AT-05 P0 implementation blocker found during Audit.
- The previous P0 conflict/ghost-conversation gaps were AT-04 issues and are already remediated/frozen.

## 9. Audit Decision

```text
AT-05 Audit: COMPLETE
Core semantic intent: CLEAR
Implementation readiness: NOT BLOCKED by new P0
R0 Contract: READY
R1 tests: REQUIRED before freeze because Wave5-named permanent AT-05 evidence is missing
IA: HOLD until R1
Freeze: NOT READY
```

## 10. Recommended AT-05-R0 Invariants

- AT05-I01 — Same `(conversation_id, turn_id)` with identical user content is one logical turn retry.
- AT05-I02 — Retry MUST NOT append a duplicate canonical user message.
- AT05-I03 — Retry MUST NOT append a duplicate canonical assistant message.
- AT05-I04 — Retry reconciliation MUST read canonical repository state, not session-local or transport-local history.
- AT05-I05 — Same `(conversation_id, turn_id)` with different user content is identity conflict and must fail closed, referencing AT-04.
- AT05-I06 — Idempotency is scoped by `conversation_id`; same `turn_id` in different conversations must not collide.
- AT05-I07 — Fresh runtime recovery must preserve retry idempotency for completed turns.
- AT05-I08 — Retry after partial/failed assistant state must not duplicate the durable user fact or create competing assistant messages; any re-completion behavior must be explicit and governed.

## 11. Suggested AT-05-R1 Tests

Suggested file:

```text
tests/wave5/test_at05_retry_idempotency.py
```

Suggested cases:

- `TC-AT05-R1-001` same text turn retry returns same user and assistant message IDs.
- `TC-AT05-R1-002` same text turn retry leaves exactly one user and one assistant message.
- `TC-AT05-R1-003` concurrent same turn retry converges to one canonical turn.
- `TC-AT05-R1-004` external/voice identical turn batch retry skips without duplicate user/assistant.
- `TC-AT05-R1-005` same turn_id with different content conflicts and leaves transcript unchanged.
- `TC-AT05-R1-006` fresh runtime retry after completed turn recovery remains exactly-once.
- `TC-AT05-R1-007` same `turn_id` in different conversations is isolated.
- `TC-AT05-R1-008` failed/partial assistant retry does not duplicate user or create competing assistant messages.

## 12. Next Gate

Proceed to:

```text
AT-05-R0 Contract
```

Hold:

```text
AT-05 R1
AT-05 IA
AT-05 Freeze
```

No implementation is required before R0 unless R0 chooses to harden the low-level repository API, which is currently outside the minimal AT-05 scope.
