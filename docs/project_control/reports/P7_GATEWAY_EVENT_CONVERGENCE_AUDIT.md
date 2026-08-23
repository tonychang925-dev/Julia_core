# P7_GATEWAY_EVENT_CONVERGENCE_AUDIT

Status: P7 AUDIT (convergence direction pending approval)
Date: 2026-08-23
Repository: julia_ai_assistant_rmd3g_prod `voice_api/`
Source: B0_GATEWAY_BOUNDARY_EVIDENCE_REPORT_v1.0 §6 (Event Plane gap)
Mode: READ-ONLY audit (no patch)

---

## 1. Current Event Plane (Brain :18089 `_stream_turn`)

Per-delta SSE payload:

```json
{"id": "chatcmpl-<uuid>", "object": "chat.completion.chunk",
 "created": <ts>, "model": "julia-brain",
 "choices": [{"index": 0, "delta": {"content": "<text>"}}]}
```

Termination:

```text
data: [DONE]
```

## 2. C-10 CoreEvent Requirement (§3)

```text
CoreEvent {event_id, event_type, conversation_id, turn_id,
           generation_id, sequence, canonical_ref}
```

Distinguish: execution event / canonical conversation event / presentation
event. Only `assistant.completed` with `canonical_ref` signals canonical
finalization.

## 3. Gap Analysis

| CoreEvent field | Current SSE | Gap |
|---|---|---|
| `event_id` | chunk_id only (`chatcmpl-*`) | no per-event id for dedup (§11) |
| `event_type` | OpenAI object only | no `turn.accepted` / `assistant.completed` / `assistant.interrupted` |
| `conversation_id` | **absent** | client cannot correlate events to conversation |
| `turn_id` | **absent** (server knows it) | client cannot correlate events to turn |
| `generation_id` | **absent** | no generation identity (C-11 barge-in needs it) |
| `sequence` | **absent** | no ordering guarantee per turn (§10) |
| `canonical_ref` | **absent** (`[DONE]` only) | client cannot distinguish canonical completed vs transport end (§3) |

Also missing: `assistant.interrupted` event (C-10 §13: canonical interrupted
must remain visible); `turn.accepted` (command acceptance).

## 4. Convergence Direction (options)

### Option A — SSE dual-track (recommended)

Keep OpenAI-compatible `data:` deltas (Electron/S2S existing parsers work),
ADD CoreEvent-carrying events at lifecycle points:

```text
data: {"event_id":"e1","event_type":"turn.accepted", conversation_id, turn_id, generation_id, sequence}
data: {chat.completion.chunk ...}          ← existing, unchanged
data: {"event_id":"eN","event_type":"assistant.completed", conversation_id, turn_id, generation_id, sequence, canonical_ref}
data: [DONE]
```

- Backward compatible; adds canonical-finalization + correlation.
- Client can dedup (event_id/sequence), reconcile (canonical_ref), and
  render interrupted state.

### Option B — Extend OpenAI payload

Add CoreEvent fields to each chunk top level (conversation_id/turn_id/
sequence/generation_id) + a final canonical_ref event before [DONE].

- Less protocol change; fields ride on existing chunks.
- No `event_type` taxonomy; weaker than C-10 §3 distinction.

### Option C — Full CoreEvent stream (largest change)

Replace OpenAI delta framing with CoreEvent stream (text/event-stream typed
events). Requires Electron + S2S parsers to change.

## 5. Impact Surface

| Consumer | Current | Option A impact |
|---|---|---|
| Electron `text-client.js` | parses OpenAI SSE deltas | backward compatible; add handlers for new events |
| S2S `/v1/chat/completions` | single-turn STT, reads reply text | unaffected (extra events ignored) |
| Brain `_stream_turn` | producer | add CoreEvent emission at lifecycle points |

## 6. Recommendation

**Option A** — dual-track SSE: preserves compatibility, satisfies C-10 §3
(canonical_ref completion signal), §10 (sequence), §11 (event_id dedup),
§13 (interrupted visibility), and C-11 (generation_id for barge-in).

This is the remaining production boundary convergence item. Implementation
pending approval (touches production Brain streaming protocol).

## 7. Acceptance

```text
[ ] CoreEvent fields present at lifecycle points (turn.accepted /
    assistant.completed / assistant.interrupted)
[ ] canonical_ref on completion (C-10 §3)
[ ] sequence per turn (C-10 §10)
[ ] event_id dedup (C-10 §11)
[ ] OpenAI deltas preserved (compat)
[ ] S2S + Electron regression pass
```
