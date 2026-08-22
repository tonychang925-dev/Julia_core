# Wave5 AT-03-R0 Contract — Text → Voice → Text Canonical Sequence

Status: R0 READY / R1 GREEN / IA GREEN / FROZEN READY
Date: 2026-08-22
Scope: AT-03 Text → Voice → Text
Source audit: `docs/project_control/reports/WAVE5_AT03_TEXT_VOICE_TEXT_AUDIT.md`

## 1. Purpose

AT-03 freezes the boundary that voice is a conversation modality, not a conversation authority.

The required acceptance sequence is:

```text
Text T1
  ↓
Voice T2
  ↓
Text T3
```

The canonical result MUST be one ordered conversation sequence:

```text
Conversation(conversation_id)
  ├─ Turn T1 modality=text
  ├─ Turn T2 modality=voice
  └─ Turn T3 modality=text
```

It MUST NOT become:

```text
text_history + voice_history + text_history
```

## 2. Frozen Invariants

### AT03-I01 — Conversation continuity is modality-independent

A conversation continues across text and voice input modes using the same canonical `conversation_id`.

Changing modality from text to voice or voice to text MUST NOT allocate a new canonical conversation unless the caller explicitly creates or selects a different conversation through the conversation management authority.

### AT03-I02 — Text and voice share canonical conversation authority

Text turns and voice turns MUST enter the same canonical conversation authority:

```text
ConversationRuntime
  ↓
canonical ConversationRepository
  ↓
ConversationMessage transcript
```

A voice turn is valid for AT-03 only if it is represented as canonical messages with:

- `conversation_id`
- `turn_id`
- `role`
- `modality="voice"`
- `content`
- `status`
- ordering metadata / append order

### AT03-I03 — Voice transport/session state cannot establish conversation authority

The following values are transport metadata only:

- `voice_session_id`
- `voice_trace_id`
- `participant_id`
- websocket id
- RTC room/session id
- S2S connection id
- TTS speech id
- ASR segment id

They MAY be recorded as provenance or runtime diagnostics.

They MUST NOT:

- allocate canonical `conversation_id`
- fork an existing canonical conversation
- become the durable transcript key
- become recovery authority
- become Context OS history source

### AT03-I04 — Modality metadata cannot create a separate history lineage

`modality` classifies a canonical turn/message.

It MUST NOT create an independent semantic history, such as:

- `voice_history`
- `voice_conversation`
- `voice_workspace` completed-turn authority
- session-local conversation memory
- S2S-owned transcript authority

Any voice-local buffer is runtime/transport state only and MUST be disposable after its canonical commit or reconciliation point.

### AT03-I05 — Voice reconnect or transport identity does not define conversation identity

AT-03 does not test reconnect UUID behavior; that belongs to AT-04.

However, AT-03 freezes this boundary:

A reconnect, transport rebinding, or voice session replacement MUST NOT by itself define a new canonical conversation identity.

The canonical conversation remains determined by the explicit `conversation_id` supplied through the conversation authority boundary.

## 3. Accepted AT-03 Ingress Paths

An AT-03-compliant voice turn MUST reach canonical storage through one of these authority-preserving paths:

```text
Voice/Text product ingress
  → ConversationRuntime.process_turn(..., modality="voice" | "text", conversation_id=cid, turn_id=tid)
```

or:

```text
External voice reconciliation
  → ConversationRuntime.append_external_turns(conversation_id=cid, turns=[{turn_id, modality="voice", ...}])
```

Both paths must write/read through the same canonical repository for the same `conversation_id`.

## 4. Non-Authoritative / Legacy Paths

The following are not accepted as AT-03 proof unless explicitly wrapped by one of the accepted ingress paths above:

- `JuliaSession.chat(text)` invoked directly from voice transport code
- session-local `_sessions[session_id]["history"]`
- VoiceWorkspace completed semantic turn storage
- S2S-local chat history
- Electron presentation cache
- websocket/session id keyed transcript

These paths may exist only as disposable runtime state, projection cache, or legacy compatibility, not as conversation authority.

## 5. Required R1 Test Shape

A permanent AT-03 R1 test MUST prove:

```text
Given: one canonical conversation_id
When:  T1 is written as text
And:   T2 is written as voice
And:   T3 is written as text
Then:  canonical user turn order is [T1, T2, T3]
And:   modality order is [text, voice, text]
And:   all messages are under the same conversation_id
And:   no voice/session id creates or selects a separate conversation
```

Suggested test ID:

```text
TC-AT03-R1-001
```

Suggested file:

```text
tests/wave5/test_at03_text_voice_text.py
```

## 6. Explicit Non-Goals

AT-03-R0 does not freeze or test:

- voice UUID continuity across reconnect, reserved for AT-04
- voice clone consistency
- TTS quality
- speaker identity
- emotion/prosody
- S2S continuity semantics
- realtime latency
- transport optimization
- multimodal UI behavior

## 7. Gate Decision

AT-03-R0 Contract: READY FOR FREEZE

AT-03-R1 Permanent Acceptance: GREEN

AT-03 IA / Final Freeze Evidence: GREEN

R1 evidence is recorded in `docs/project_control/reports/WAVE5_AT03_TEXT_VOICE_TEXT_AUDIT.md` and implemented in `tests/wave5/test_at03_text_voice_text.py`.
