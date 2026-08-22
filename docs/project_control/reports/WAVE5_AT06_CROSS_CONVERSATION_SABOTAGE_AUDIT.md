# Wave5 AT-06 Cross-conversation Sabotage Audit

Status: AUDIT COMPLETE / R0 BLOCKED BY P0 GAP
Date: 2026-08-22
Scope: AT-06 — Cross-conversation sabotage
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Observed HEAD: `c212e44`
Core lane: `/Users/admin/julia_core_wave4_integration`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry Idempotency               FROZEN
AT-06 Cross-conversation sabotage     AUDIT START
```

## 2. AT-06 Source Requirement

From `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-06 — Cross-conversation sabotage

Conversation A and B contain distinct markers.

No leakage through storage, search, Context OS, or Electron.
```

AT-06 shifts from single-conversation continuity/idempotency to cross-conversation isolation:

```text
Conversation A
  ≠
Conversation B
```

Conversation boundary is a canonical isolation boundary. Storage, search, Context OS, and client/session surfaces must not acquire authority to merge or leak histories across that boundary.

## 3. Non-Goals

AT-06 does not test:

- multi-user authorization
- encryption
- distributed tenancy
- access-control redesign
- search ranking optimization
- segment rotation, reserved for AT-07
- pagination, reserved for AT-08
- retry/reconnect semantics, already frozen by AT-04/AT-05
- provider behavior quality or prompt style

## 4. Authority Baseline

Relevant frozen principles:

- `ConversationRuntime.get_canonical_history(conversation_id)` reads from one canonical conversation.
- `ConversationManagementService.get_messages(conversation_id)` first resolves the requested conversation and then reads only that conversation.
- Search/catalog are derived read models, not canonical authority.
- Context OS is the sole model-visible context authority; retrieved/projected/admitted/visible/consumed are distinct stages.
- Runtime/session/client state is not canonical conversation authority.

## 5. Audit Questions

AT-06 must answer:

1. Can storage read/restart reconstruction for conversation A expose marker B?
2. Can repository search for marker A return or hydrate marker B as the result for A?
3. Can Context OS admit conversation A history into a conversation B model-visible package?
4. Can Electron/event/session-local cache restore or present another conversation's history as current truth?
5. Are search hits/candidates prevented from becoming Context OS or provider authority without canonical conversation gating?
6. Do existing permanent tests cover AT-06 by name across storage, search, Context OS, and Electron/cache surfaces?

## 6. Evidence Commands

### Existing isolation-focused tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/test_conversation_authority.py::TestInteractionIsolation::test_cross_conversation_isolation \
  tests/test_conversation_authority.py::TestConversationIsolation::test_history_isolation \
  tests/rt2_r3/test_core_acceptance.py::test_r3_at08_conversation_isolation \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at10_cross_conversation_isolation \
  tests/spikes/test_cm_spike_01_durable_acceptance.py::test_sp07_cross_conversation_isolation
```

Observed result:

```text
5 passed in 0.14s
```

These tests prove useful baseline storage/runtime isolation but do not fully prove AT-06 across search, Context OS, and Electron/cache surfaces.

## 7. Audit Probes

### Probe P-A — Storage/restart marker isolation

Setup:

```text
Conversation A: ALPHA_PRIVATE_MARKER_001
Conversation B: BETA_PRIVATE_MARKER_002
```

Observed through governed management/runtime path:

```text
A_MESSAGES: A contains ALPHA only
B_MESSAGES: B contains BETA only
A_RESTART: A contains ALPHA only after fresh StorageV2 runtime
B_RESTART: B contains BETA only after fresh StorageV2 runtime
```

Assessment: GREEN for canonical storage and restart reconstruction.

### Probe P-B — Search marker specificity

Observed:

```text
search("ALPHA_PRIVATE_MARKER_001") → A only
search("BETA_PRIVATE_MARKER_002")  → B only
search("PRIVATE_MARKER")           → A and B handles
```

Assessment:

- GREEN for marker-specific derived search returning the matching conversation handle.
- AMBER for AT-06 R0 wording: broad/global search may intentionally return multiple conversations, but search results must remain result handles/candidates only. They must not be treated as current-conversation transcript, Context OS admission, or provider-consumable history.

### Probe P-C — Context OS mixed-history sabotage

Sabotage input:

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

Observed:

```text
ACTIVE_TAIL_IDS ['a1', 'a1', 'b1', 'b1']
VISIBLE [('system', '[situation]\nmodality: text'),
         ('user', 'ALPHA_PRIVATE_MARKER_001'),
         ('assistant', 'ack A'),
         ('user', 'BETA_PRIVATE_MARKER_002'),
         ('assistant', 'ack B'),
         ('user', 'question B')]
ALPHA_VISIBLE True
```

Assessment: P0 GAP.

Context OS currently trusts the caller-supplied `history` list. The governed runtime normally supplies canonical history for the requested conversation, but the Context OS boundary itself does not fail closed if given mixed-conversation history.

Why this matters:

```text
retrieved / supplied / client-cached history
  ≠
model-visible current-conversation authority
```

A stale client/session/history bridge or search-to-context misuse could feed A history into B's Context OS package. Current Context OS ActiveTail will admit it into provider-visible messages.

Expected AT-06 behavior:

```text
Context OS prepare for conversation B
  + candidate/history item whose conversation_id is A
    → reject/drop/quarantine before model-visible output
    → zero ALPHA marker in B provider-visible messages
```

This must be frozen in R0 before implementation.

### Probe P-D — Electron/event session history risk surface

Evidence:

- `julia_core/event_gateway.py` keeps `_sessions[session_id]["history"]` and appends user/assistant messages locally.
- This history is session-local runtime state, not canonical repository truth.
- Current audit did not find an Electron cache acceptance test proving rapid A/B switch cannot restore or display the wrong transcript.

Assessment: AMBER/P0-candidate for product lane.

If any Electron/voice path uses session-local `history` as current conversation history or Context OS input, it would violate AT-06. R0 must freeze that Electron/client/session cache cannot be recovery source, Context OS input authority, or current-conversation truth.

## 8. Code Path Findings

### F1 — Storage read path is conversation-scoped

Evidence:

- `StorageV2ConversationRepository.get_messages(session_id, ...)` iterates only `_iter_transcript(session_id)`.
- `StorageV2ConversationRepository.find_turn(session_id, turn_id)` scans only the requested session transcript.
- `ConversationRuntime.get_messages(conversation_id)` gets one repository session.
- `ConversationManagementService.get_messages(conversation_id)` verifies the conversation exists before reading.

Assessment: GREEN.

### F2 — Runtime cognition path normally passes conversation-scoped canonical history

Evidence:

- `ConversationRuntime._process_turn_locked(...)` calls `get_canonical_history(conversation_id)` and passes that history to `cognitive_fn(...)`.
- Probe P-A confirmed cognition history for A contained A marker only, and cognition history for B contained B marker only.

Assessment: GREEN for governed runtime path.

### F3 — Search is global derived read model, not conversation authority

Evidence:

- `ConversationRuntime.search_conversations(query)` delegates to repository search and returns `ConversationHandle` objects.
- `StorageV2ConversationRepository.search(query)` scans all conversations and returns matching sessions.
- Broad search can return A and B together by design.

Assessment: AMBER.

Search is not inherently wrong as a global UI function, but AT-06 must freeze: search hits are derived candidates/handles and must not be fed into current conversation transcript or Context OS without canonical conversation boundary gating.

### F4 — Context OS lacks a fail-closed conversation_id filter for supplied history

Evidence:

- `ContextExecutionRuntime.prepare(...)` receives `conversation_id` and `history` separately.
- It computes ActiveTail directly from the supplied `history`.
- It records provenance `conversation:{conversation_id}` even if supplied history contains messages from another `conversation_id`.
- Probe P-C showed A marker became model-visible during B preparation.

Assessment: P0 GAP.

### F5 — Legacy/chat/session paths remain non-authoritative risk surfaces

Evidence:

- `JuliaSession.chat(text)` uses `TurnContext([])` and is marked legacy.
- `event_gateway.py` stores session-local history in `_sessions[session_id]["history"]`.
- Prior AT-03 audit already classified gateway/session local history as product/transport AMBER.

Assessment: AMBER until AT-06 R1/IA proves Electron/client/session cache cannot restore or inject cross-conversation history.

## 9. Current Coverage Assessment

GREEN:

- Canonical storage reads are scoped by conversation id.
- Runtime `get_canonical_history(conversation_id)` is scoped by conversation id.
- Existing focused isolation tests pass: `5 passed`.
- Marker-specific search returns the matching conversation handle only.
- Restart reconstruction preserves A/B separation.

AMBER:

- No dedicated `tests/wave5/test_at06_cross_conversation_sabotage.py` permanent acceptance artifact exists.
- Search is global and must be explicitly frozen as derived candidates only, not current-conversation context authority.
- Electron/client cache behavior is not covered by a Wave5 AT-06 acceptance artifact in this Core lane.
- Event gateway session-local history remains a risk surface if treated as canonical or model-visible history.

RED/P0:

- Context OS currently admits caller-supplied mixed-conversation history into provider-visible messages without fail-closed filtering or rejection.

## 10. Audit Decision

```text
AT-06 Audit: COMPLETE
Core semantic intent: CLEAR
Storage/runtime lane: GREEN
Search lane: AMBER
Context OS lane: RED / P0 GAP
Electron/client cache lane: AMBER
Implementation readiness: BLOCKED by P0 Context OS boundary gap
R0 Contract: REQUIRED and must freeze Context OS fail-closed gating before R1
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

## 11. Required AT-06-R0 Invariants

Recommended R0 invariants:

- AT06-I01 — Conversation boundary is a canonical isolation boundary.
- AT06-I02 — Storage read/recovery for conversation A must not expose conversation B messages or markers.
- AT06-I03 — Search results are derived candidates/handles only; search relevance is not current-conversation context authority.
- AT06-I04 — Context OS must reject/drop/quarantine any candidate/history item whose `conversation_id` does not match the active canonical conversation before model-visible output.
- AT06-I05 — Electron/client/session cache is not canonical history, recovery source, or Context OS input authority.
- AT06-I06 — Runtime/interaction caches are scoped by `conversation_id` and must rebuild from canonical repository only.
- AT06-I07 — Provider-visible context for conversation A must contain no marker from conversation B, even if sabotage input includes mixed history/search/cache candidates.
- AT06-I08 — Fresh runtime/repository recovery must preserve A/B isolation.

## 12. Suggested R1 Tests

Suggested file:

```text
tests/wave5/test_at06_cross_conversation_sabotage.py
```

Suggested cases:

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

## 13. Next Gate

Proceed to:

```text
AT-06-R0 Contract
```

Hold:

```text
AT-06 Implementation
AT-06 R1
AT-06 IA
AT-06 Freeze
```

Do not start AT-07 segment rotation.
