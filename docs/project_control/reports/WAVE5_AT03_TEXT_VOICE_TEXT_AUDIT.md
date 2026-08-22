# Wave5 AT-03 Text → Voice → Text Audit

Status: AUDIT COMPLETE / R0 READY / R1 GREEN / IA GREEN / FROZEN READY
Date: 2026-08-22
Branch: `wave4/integration-base`
Observed HEAD: `a9d36cc`
Workspace: clean at audit start
Core lane: `/Users/admin/julia_core_wave4_integration`

## Checkpoint Context

Frozen inputs carried forward:

- Wave5 Authority Boundary Set: FROZEN
- AT-01 Conversation Create Durability: FROZEN
- AT-02 Accepted User Crash: FROZEN READY

User-provided AT-02 final evidence commit: `9523d7b`.
Audit repository observed commit: `a9d36cc`.

## AT-03 Scope

AT-03 validates only this invariant:

```text
modality input
  ↓
canonical conversation sequence
```

Required sequence:

```text
Text T1
Voice T2
Text T3
=
one canonical conversation sequence
```

Explicit non-goals:

- voice identity continuity
- voice clone consistency
- TTS quality
- speaker identity
- emotion/prosody
- S2S reconnect UUID semantics, reserved for AT-04
- multimodal UX

## Evidence Commands

### Existing Focused Authority + Voice Tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Result:

```text
39 passed in 0.40s
```

### AT-03 Runtime Probe

A temporary repository was configured and the following sequence was executed:

1. `ConversationRuntime.process_turn(conversation_id=cid, turn_id="at03-text-t1", modality="text")`
2. `ConversationRuntime.append_external_turns(cid, [{turn_id:"at03-voice-t2", modality:"voice"}])`
3. `ConversationRuntime.process_turn(conversation_id=cid, turn_id="at03-text-t3", modality="text")`
4. `ConversationRuntime.get_canonical_history(cid)`

Observed canonical user sequence:

```json
[
  ["at03-text-t1", "text", "T1 text"],
  ["at03-voice-t2", "voice", "T2 voice"],
  ["at03-text-t3", "text", "T3 text"]
]
```

Observed canonical messages:

```json
[
  ["user", "at03-text-t1", "text", "T1 text"],
  ["assistant", "at03-text-t1", "text", "ack:text:T1 text"],
  ["user", "at03-voice-t2", "voice", "T2 voice"],
  ["assistant", "at03-voice-t2", "voice", "ack:voice:T2 voice"],
  ["user", "at03-text-t3", "text", "T3 text"],
  ["assistant", "at03-text-t3", "text", "ack:text:T3 text"]
]
```

## Code Path Findings

### F1 — Core canonical model supports AT-03

Evidence:

- `julia_core/runtime/conversation_runtime.py`
  - `process_turn(...)` accepts `conversation_id`, `turn_id`, `modality`.
  - `accept_user_turn(...)` writes durable canonical user message before cognition.
  - `append_external_turns(...)` appends external voice turns into the same repository keyed by `conversation_id`.
  - `get_canonical_history(...)` reads full completed canonical history from the same repository.

### F2 — Repository append is sequence-preserving

Evidence:

- `julia_core/conversation_state/storage_v2_repository.py::append_external_turns_atomic`
  - writes user then assistant messages with monotonic `sequence`.
  - sets `conversation_id = session_id`.
  - stores `turn_id`, `role`, `modality`, `status` in canonical transcript.

- `julia_core/conversation_state/repository.py::append_external_turns_atomic`
  - performs atomic append under one lock.
  - validates turn IDs and user content before save.
  - supports rollback on save failure.

### F3 — Existing tests partially cover voice canonical append

Evidence:

- `tests/test_voice_turn_reconciliation.py`
  - append one completed voice turn.
  - append multiple voice turns preserving order.
  - retry idempotency.
  - conflict on same `turn_id` different content.
  - modality preserved as `voice`.

- `tests/test_conversation_authority.py`
  - text canonical ordering and restart chronology.
  - external voice/interrupted turn remains in canonical conversation.

### F4 — Exact AT-03 T1/T2/T3 contract is not yet a named permanent test

Evidence:

- No dedicated test named AT-03 / Text→Voice→Text was found.
- Existing E2E tests contain broader alternating text/voice checks, but they depend on a running Brain API and are not a minimal Core lane contract.

### F5 — Legacy runtime gateway remains a risk surface, not AT-03 Core proof

Evidence:

- `julia_core/runtime/gateway_server.py::_process_speech_reply` currently calls `JuliaSession.chat(text)` using `session_id`, not an explicit canonical `conversation_id`.
- `julia_core/event_gateway.py::_handle_speech_final` maintains `_sessions[session_id]["history"]`, which is a voice/session-local history shortcut.

Disposition:

- These paths must be classified as legacy/non-authoritative or excluded from AT-03 Core lane.
- If any product path still uses them as the active voice ingress, AT-03 Product lane must fail until routed through `ConversationRuntime` with canonical `conversation_id`.

## Audit Decision

Core lane audit: GREEN

Reason:

- Core `ConversationRuntime` and repository contracts can represent Text T1 → Voice T2 → Text T3 as one canonical sequence.
- Focused existing tests pass.
- Runtime probe confirms exact ordering and modality preservation.

Product/transport lane audit: AMBER

Reason:

- Legacy gateway files still contain session-local voice history / `JuliaSession.chat` shortcuts.
- Need R0 contract to state the only accepted AT-03 ingress path and explicitly exclude or retire legacy shortcuts.

## AT-03-R0 Contract Requirements

R0 should freeze the following:

1. `conversation_id` is the only conversation identity authority across text and voice.
2. `turn_id` is unique per logical turn and is not derived from `voice_session_id`, `voice_trace_id`, or `participant_id` alone.
3. Voice transport metadata may be recorded as provenance but cannot allocate or fork `conversation_id`.
4. Text and voice both write to the same canonical repository/message model.
5. `get_canonical_history(conversation_id)` must return the ordered sequence containing T1/T2/T3.
6. Legacy voice/session-local history paths are non-authoritative and cannot satisfy AT-03.

## AT-03-R1 Test Recommendation

Add a permanent focused Core test with this shape:

```text
TC-AT03-R1-001
Given one canonical conversation_id
When text T1 is processed, voice T2 is appended, and text T3 is processed
Then canonical user turn sequence is [T1 text, T2 voice, T3 text]
And all messages share the same conversation_id
And modality sequence is [text, voice, text]
And no voice/session identifier creates a second conversation
```

Suggested file:

```text
tests/wave5/test_at03_text_voice_text.py
```

## Gate Position

AT-03 may proceed to R0 Contract.

Current state:

```text
AT-03 Text → Voice → Text
  Audit: COMPLETE / CORE GREEN / PRODUCT AMBER
  Next: AT-03-R0 Contract
```

---

## R0 Contract Transition — 2026-08-22

AT-03-R0 Contract artifact created:

```text
docs/authority/WAVE5_AT03_R0_TEXT_VOICE_TEXT_CONTRACT.md
```

R0 freezes five invariants:

- AT03-I01 — Conversation continuity is modality-independent.
- AT03-I02 — Text and voice share canonical conversation authority.
- AT03-I03 — Voice transport/session state cannot establish conversation authority.
- AT03-I04 — Modality metadata cannot create a separate history lineage.
- AT03-I05 — Voice reconnect or transport identity does not define conversation identity.

Next:

```text
AT-03-R1 permanent acceptance test
```

---

## R1 Permanent Acceptance Test — 2026-08-22

Permanent test artifact created:

```text
tests/wave5/test_at03_text_voice_text.py
```

Test IDs:

- TC-AT03-R1-001 — canonical mixed modality sequence
- TC-AT03-R1-002 — voice shortcut/session history cannot create canonical history
- TC-AT03-R1-003 — session-local history cannot recover canonical transcript
- TC-AT03-R1-004 — voice transport metadata cannot fork conversation identity
- TC-AT03-R1-005 — mixed lane remains one canonical repository sequence

### R1 Command

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q tests/wave5/test_at03_text_voice_text.py
```

Result:

```text
5 passed in 0.10s
```

### Focused AT-03 Regression Command

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at03_text_voice_text.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Result:

```text
44 passed in 0.39s
```

## R1 Gate Decision

AT-03-R1 permanent acceptance test: GREEN

AT-03 status after R1:

```text
Audit: COMPLETE
R0 Contract: READY FOR FREEZE
R1 Permanent Acceptance: GREEN
Next: AT-03 IA / final freeze evidence bundle
```

---

## IA / Final Freeze Evidence — 2026-08-22

Final evidence artifact created:

```text
docs/project_control/reports/WAVE5_AT03_IA_FINAL_FREEZE_EVIDENCE.md
```

IA result:

```text
tests/wave5/test_at03_integration_acceptance.py
4 passed in 0.12s
```

Final AT-03 evidence bundle:

```text
tests/wave5/test_at03_text_voice_text.py
tests/wave5/test_at03_integration_acceptance.py
tests/test_voice_turn_reconciliation.py
tests/test_conversation_authority.py

48 passed in 0.45s
```

AT-03 final status:

```text
FROZEN READY
```
