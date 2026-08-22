# Wave5 AT-04 Voice Reconnect UUID Identity Audit

Status: AUDIT COMPLETE / R0 FROZEN / MINIMAL REMEDIATION GREEN / R1 GREEN / IA GREEN / FROZEN
Date: 2026-08-22
Scope: AT-04 — Voice reconnect UUID identity
Branch: `wave4/integration-base`
Core lane: `/Users/admin/julia_core_wave4_integration`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN
AT-03 Text → Voice → Text             FROZEN
AT-04 Voice reconnect UUID identity   AUDIT START
```

## 2. AT-04 Source Requirement

From `JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-04 — Voice reconnect UUID identity
Reconnect repeatedly.
No reused canonical turn_id.
```

AT-04 shifts focus from AT-03's modality continuity to canonical turn identity across voice reconnect / transport retry.

## 3. Non-Goals

AT-04 does not test:

- voice clone consistency
- TTS quality
- speaker identity
- emotion/prosody
- multimodal UX
- AT-03 mixed modality sequence, already covered
- general retry idempotency for same logical turn, covered by AT-05

## 4. Authority Baseline

Relevant frozen rules:

- `C-02_CONVERSATION_AUTHORITY_CONTRACT.md`
  - one conversation may span many voice connections;
  - session lifecycle does not mutate `conversation_id`;
  - `turn_id` is logical turn grouping;
  - client reconnect must not modify completed messages.

- `C-10_GATEWAY_CLIENT_CONTRACT.md`
  - `turn_id` origin is Runtime/Core or client candidate accepted by Core;
  - reconnect reconciles from Core canonical truth;
  - reconnect must not send local `history[]` as truth;
  - network timeout retry must not create duplicate turns.

- `GAP8_UNKNOWN_CONVERSATION_RESOLUTION_v1.0.md`
  - stale voice reconnect with unknown `conversation_id` must be rejected;
  - no ghost canonical truth may be manufactured.

- `JULIA_FOUR_REPO_AUTHORITY_MANIFEST.md`
  - Voice/S2S deployed source authority includes RP-2B turn_id UUID fix;
  - live runtime currently recorded as unverified.

## 5. Audit Questions

AT-04 must answer:

1. Does each new voice turn after reconnect get a fresh canonical `turn_id`?
2. If a reconnect accidentally reuses a previous `turn_id` for different content, is it rejected rather than silently skipped/overwritten?
3. If reconnect uses a stale/unknown `conversation_id`, is it rejected rather than auto-created?
4. Are `voice_session_id`, websocket id, RTC session id, or reconnect count prevented from becoming canonical `turn_id` authority?
5. Does recovered canonical history show collision-free turn IDs after repeated reconnect events?

## 6. Evidence Commands

### Existing voice/conversation focused tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Prior AT-03 run result:

```text
39 passed in 0.40s
```

These tests prove baseline append/idempotency behavior for legacy repository and conversation authority, but do not fully prove AT-04 reconnect UUID identity.

## 7. Audit Probe Findings

### P0-F1 — StorageV2 silently skips reused `turn_id` with different content

Probe:

```text
append voice turn_id="reused-turn" content="first after connect"
append voice turn_id="reused-turn" content="second after reconnect"
```

Observed:

```text
legacy     → CONFLICT ✅
storage_v2 → NO_CONFLICT; skipped_turn_ids=["reused-turn"] ❌
```

Raw observed result:

```text
legacy {'status': 'CONFLICT', 'error': 'Turn reused-turn: content differs from persisted'}
storage_v2 {'status': 'NO_CONFLICT', 'result': {'appended_turn_ids': [], 'skipped_turn_ids': ['reused-turn'], 'message_count': 2}, 'history': [('reused-turn', 'first after connect'), ('reused-turn', 'ack1')]}
```

Impact:

A reconnect bug that reuses a previous canonical `turn_id` for a new voice utterance would be silently dropped under StorageV2. That violates AT-04's intent because the system does not prove collision-free UUID identity; it masks collision as idempotent success.

Expected behavior:

- same `(conversation_id, turn_id)` + same content → idempotent skip/return existing;
- same `(conversation_id, turn_id)` + different content → conflict / fail closed;
- new voice utterance after reconnect → fresh canonical `turn_id`.

### P0-F2 — Direct `process_turn/accept_user_turn` auto-creates unknown conversation_id

Probe:

```text
before: get_conversation("stale-voice-reconnect-cid") == None
process_turn(conversation_id="stale-voice-reconnect-cid", turn_id="stale-turn-1", modality="voice")
after: conversation exists
```

Observed:

```text
{'before': None, 'result_status': 'completed', 'after_exists': True, 'after_id': 'stale-voice-reconnect-cid', 'message_count': 2}
```

Impact:

If a voice reconnect path calls `ConversationRuntime.process_turn` directly with stale/typo `conversation_id`, Core currently manufactures a ghost canonical conversation. This conflicts with `GAP8-I01` unless product ingress performs a mandatory existence check before runtime turn processing.

Expected behavior for AT-04 product/IA lane:

- reconnect with stale/unknown `conversation_id` → `CONVERSATION_NOT_FOUND`;
- no canonical conversation created;
- caller must explicitly create/select/recover.

### P1-F3 — Core lane has no turn_id allocator for voice turns

Search result:

- `ConversationRuntime.allocate_conversation_id()` exists.
- No equivalent canonical `allocate_turn_id()` was found in Core lane.
- Voice/product tests often use timestamp or caller-supplied `turn_id`.

Impact:

AT-04 can freeze acceptance behavior, but final Product IA must identify the active production turn_id allocator in the Voice/S2S/Brain path and prove it uses collision-resistant UUID identity after reconnect.

### P1-F4 — Legacy gateway/session paths remain non-authoritative risk surfaces

Existing AT-03 audit already identified:

- `gateway_server.py::_process_speech_reply` invokes `JuliaSession.chat(text)` with `session_id` rather than canonical `conversation_id` / `turn_id`.
- `event_gateway.py::_handle_speech_final` keeps `_sessions[session_id]["history"]`.

For AT-04, these are additionally risky because reconnect/session identity might become de facto turn/session authority if used as active ingress.

## 8. Current Coverage Assessment

GREEN:

- Legacy repository detects same `turn_id` with different content.
- Existing `ConversationRuntime.append_external_turns` voice tests cover basic idempotency/conflict behavior on the legacy-backed test fixture.
- AT-03 proves transport/session metadata cannot become conversation identity in the mixed-modality lane.

AMBER/RED:

- StorageV2 does not compare existing turn content before skipping reused `turn_id`.
- Direct runtime turn path can auto-create unknown conversations.
- No dedicated AT-04 permanent test exists.
- Product/source authority for deployed Voice/S2S UUID generator is documented but not locally verified in this Core lane.

## 9. Audit Decision

```text
AT-04 Audit: COMPLETE
Core semantic intent: CLEAR
Implementation readiness: BLOCKED
R0 Contract: MAY PROCEED only if it records the two P0 fail-closed requirements
R1 tests: MUST be red/green for StorageV2 turn collision and stale reconnect ghost creation
```

## 10. Required AT-04-R0 Invariants

Recommended R0 invariants:

- AT04-I01 — Every new voice logical turn after reconnect must have a fresh canonical `turn_id`.
- AT04-I02 — Same `conversation_id + turn_id + same content` is idempotent retry, not a new turn.
- AT04-I03 — Same `conversation_id + turn_id + different content` is identity conflict and must fail closed.
- AT04-I04 — Unknown/stale `conversation_id` on reconnect must not auto-create canonical truth.
- AT04-I05 — Transport/session ids are not canonical `turn_id` authority.
- AT04-I06 — Recovered canonical transcript after repeated reconnect contains no duplicate/reused logical `turn_id` for distinct user utterances.

## 11. Suggested AT-04-R1 Tests

Suggested file:

```text
tests/wave5/test_at04_voice_reconnect_uuid_identity.py
```

Minimum tests:

1. `TC-AT04-R1-001` repeated reconnect simulation appends distinct voice turns with distinct UUID-like `turn_id` values.
2. `TC-AT04-R1-002` reused `turn_id` + same content is idempotent and creates no duplicate.
3. `TC-AT04-R1-003` reused `turn_id` + different content conflicts on StorageV2 and legacy repository.
4. `TC-AT04-R1-004` stale reconnect `conversation_id` through governed ingress rejects and creates no ghost.
5. `TC-AT04-R1-005` transport IDs (`voice_session_id`, reconnect count, websocket id) cannot be used as canonical turn allocator evidence.

## 12. Next Step

Proceed to AT-04-R0 Contract with P0 gaps explicitly frozen as fail-closed requirements.

Do not mark AT-04 R1 or IA green until StorageV2 collision behavior and stale reconnect ghost-creation behavior are covered by permanent tests.

---

## R0 Contract Transition — 2026-08-22

AT-04-R0 Contract artifact created:

```text
docs/authority/WAVE5_AT04_R0_VOICE_RECONNECT_UUID_IDENTITY_CONTRACT.md
```

R0 freezes two P0 fail-closed gaps:

- P0-GAP-1 — StorageV2 turn_id conflict must fail closed.
- P0-GAP-2 — Unknown/stale reconnect conversation_id must not auto-create canonical truth.

R0 also freezes six invariants:

- AT04-I01 — Reconnect creates fresh logical turn identity for new utterances.
- AT04-I02 — Same turn_id + same content is idempotent retry.
- AT04-I03 — Same turn_id + different content is identity conflict.
- AT04-I04 — Unknown/stale conversation_id on reconnect must not auto-create truth.
- AT04-I05 — Transport/session identifiers are not canonical turn_id authority.
- AT04-I06 — Recovery must show no reused turn_id for distinct utterances.

Current state:

```text
AT-04 Audit: COMPLETE
AT-04-R0 Contract: FROZEN
Implementation: HOLD / BLOCKED BY P0 GAPS
R1: GREEN
IA: GREEN
Freeze: FROZEN
```


---

## Minimal Remediation Evidence — 2026-08-22

Artifact:

```text
docs/project_control/reports/WAVE5_AT04_MINIMAL_REMEDIATION_EVIDENCE.md
```

Result:

```text
AT-04 Minimal Remediation: GREEN
R1: GREEN
IA: GREEN
Freeze: FROZEN
```


---

## R1 Sabotage Evidence — 2026-08-22

Artifact:

```text
docs/project_control/reports/WAVE5_AT04_R1_SABOTAGE_EVIDENCE.md
```

Result:

```text
AT-04-R1 sabotage evidence: GREEN
IA: GREEN
Freeze: FROZEN
```


---

## IA / Final Freeze Evidence — 2026-08-22

Artifact:

```text
docs/project_control/reports/WAVE5_AT04_IA_FINAL_FREEZE_EVIDENCE.md
```

Result:

```text
AT-04 Integration Acceptance: GREEN
AT-04 Final Freeze Evidence: FROZEN
```


---

## Final Freeze Record — 2026-08-22

Artifact:

```text
docs/project_control/reports/WAVE5_AT04_FINAL_FREEZE_RECORD.md
```

Result:

```text
AT-04 Voice reconnect UUID identity: FROZEN
```
