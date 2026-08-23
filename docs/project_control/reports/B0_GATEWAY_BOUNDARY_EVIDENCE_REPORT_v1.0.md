# B0_GATEWAY_BOUNDARY_EVIDENCE_REPORT_v1.0

Status: EVIDENCE REPORT v1.0
Date: 2026-08-23
Repository scope: julia_core / julia_ai_assistant(+rmd3g_prod) / Julia-Voice-S2S / julia_electron_v2
Mode: READ-ONLY audit evidence (no patch)

---

## 1. Gateway Responsibility Migration Evidence

Historical architecture (retired):

```text
Electron → :8100 Gateway → JuliaSession (js.chat)          ← historical, ADR-022 E0.8
```

Current frozen architecture (verified):

```text
Julia Core (ConversationRuntime)
    ↓
Brain :18089  ← CURRENT Gateway Boundary (transport surface)
    ↓
Julia_client (Electron)        Voice S2S (Audio Body)
```

- ADR-022 (DESIGN FREEZE): Runtime Gateway = Command API + Event Stream between
  Brain and Bodies.
- C-10 (FROZEN): Gateway = transport boundary; Client = body.
- Electron default endpoint = `127.0.0.1:18089` (not 8100).
- Brain launchd `com.julia.brain.18089` → `start-brain-18089` →
  `voice_api/server.py --port 18089` (RP-1 gated).

**Verdict: Gateway responsibility MIGRATED to Brain :18089 API surface.**

## 2. :8100 Legacy Classification

| Check | Result |
|---|---|
| launch config | NONE (no plist/launchd/script; manual `--port 8100`) |
| Electron endpoint | ZERO reference |
| Brain / Assistant config | ZERO reference |
| Voice / S2S config | ZERO reference |
| Production process | NOT running |
| Production import | ZERO (non-test) |

Classification:

```text
Legacy Gateway
Compatibility only
No cognitive authority
No production topology
```

Note: `gateway_server.py` (v1.1) and `gateway.py` (v1.0) both default to
:8100 — two historical implementations, both outside production topology.

## 3. Brain :18089 Authority Chain Proof

```text
ClientCommand {conversation_id, turn_id, modality, input}
    ↓
ConversationRuntime (process_turn / begin_turn_streaming / commit_streaming_turn)
    ↓
JuliaSession.process / process_stream
    ↓
ContextExecutionRuntime (Context OS)   ← julia_session.py:108,260
    ↓
provider
```

- `ConversationTurnRequest{turn_id, modality, input, stream}` — ClientCommand
  semantics; no history/persona/memory override.
- `external_history` (messages[]) **IGNORED** when conversation_id present
  (CC-2) — C-10 §8: client cannot select cognitive history.
- ConversationRuntime = sole transcript authority (no second writer).

**PASS** — authority chain correct; single conversation authority.

## 4. Client Boundary Proof

Electron (`julia_electron_v2`):

- `buildTurnBody` sends only turn_id/modality/input/stream (C-10 compliant).
- Reconnect = canonical reconciliation (C-10 §7); local history disposable
  projection, never uploaded as truth.
- No direct canonical store access (C-10 §21).
- Zero `:8100` reference.

Assistant runtime layer:

- `assistant_runtime.py`: Runtime owns short-term session lifecycle only;
  non-goals = no Memory OS retrieval / no Context OS planner-resolver / no
  long-term memory writes.
- `ReadOnlyMemoryBindingAdapter`: retrieval-only; no memory/persona/ranking
  mutation authority.

**PASS** — Electron = body; runtime holds no mutation authority.

## 5. Voice Same-Turn Proof

```text
mic → :7860 → WS :8765 (S2S)
  → HTTP :8089(tunnel) → :18089 /v1/chat/completions
  → conversation_id present → Core authority path (native_stream / process_turn)
  → messages[] discarded; Core owns history
```

- S2S: zero :8100/gateway references; turn_id = uuid4 (RP-2).
- AutoDL production (SOP v1.1): no gateway component.
- Voice and text share the same logical turn path (C-10 §15 / C-11 §2).

**PASS** — voice is a body; no second voice-brain authority.

## 6. Remaining Gap — P7 Event Plane Convergence (OPEN)

Current streaming response:

```json
{"id": "chatcmpl-...", "object": "chat.completion.chunk",
 "choices": [{"index": 0, "delta": {"content": "..."}}]}
```

OpenAI-compatible delta ≠ C-10 CoreEvent:

```text
CoreEvent {event_id, event_type, conversation_id, turn_id,
           generation_id, sequence, canonical_ref}
```

Why it matters: future events (voice chunk, emotion state, presence, action,
artifact) cannot be expressed as text delta. This is a **P7 Gateway/Event
Convergence** work item, NOT a B0 defect.

## 7. B0 Acceptance

| Item | Status |
|---|---|
| Gateway Boundary exists | PASS |
| Current Gateway owner | Brain :18089 |
| Electron role | Body / Client |
| Voice role | Body / Media |
| Client authority leakage | NONE |
| Conversation authority | PASS (single) |
| External history injection | PASS (ignored) |
| :8100 | LEGACY (compatibility, no production topology) |
| CoreEvent Event Plane | OPEN GAP → P7 |

```text
B0 Gateway Boundary
    ACCEPTED (no patch — legacy classification + migration evidence)
    → NEXT: P7 Gateway/Event Convergence
```
