# B0_FINAL_BOUNDARY_AUDIT

Status: FINAL BOUNDARY AUDIT
Date: 2026-08-23
Repository scope: julia_core / julia_ai_assistant(+rmd3g_prod) / Julia-Voice-S2S / julia_electron_v2
Mode: READ-ONLY (no patch)

---

## 0. Audit Questions

```text
Q1  Is there a SECOND conversation authority?
Q2  Does Gateway participate in cognitive decision?
Q3  What is the final :8100 role? (launch config / Electron endpoint /
    Assistant runtime config / voice route config)
```

## 1. Production Path

| Entry | Path | Gateway :8100? |
|---|---|---|
| Electron text | `→ HTTP :18089 /internal/v1/conversations/{id}/turns → Brain → CRT.process_turn` | NO |
| Electron voice | `→ :7860 → WS :8765 (S2S) → HTTP :8089(tunnel)→:18089 /v1/chat/completions → CRT` | NO |
| Brain | `launchd com.julia.brain.18089 → start-brain-18089 → voice_api/server.py --port 18089` | NO |

**PASS** — all production entries route through Brain :18089 → ConversationRuntime.

## 2. Conversation Authority — Q1 Answer

**NO second authority exists.**

Evidence:
- `conversation_runtime.py:103` is the ONLY runtime instantiation of the
  canonical repository (`data/conversations.json`); all writes flow through
  the `_repository` protocol (process_turn / streaming / append / import).
- `js.chat()` chain (`julia_session.py:226 → _chat_impl:289`) calls NO
  ConversationRuntime API; transcript lives only in an ephemeral in-memory
  TurnContext and is dropped at turn end. EventStore writes are event traces,
  not transcript.
- Gateway `store.touch()` writes only derived catalog metadata
  (message_count/topics), never message content (CM-R1 retired).
- Assistant side: zero direct transcript writes (server_v2_1 history.append
  is in-memory legacy; startup_memory transcripts.jsonl is memory layer).

Conclusion: gateway path is **zero-transcript-persistence**, NOT a second
authority.

**PASS** — single authority = ConversationRuntime.

## 3. Voice Path

Data flow (verified in code):

```text
mic → Electron postMessage → :7860 frontend → WS :8765 (S2S)
  → HTTP POST /v1/chat/completions → 127.0.0.1:8089 (SSH tunnel)
  → :18089 Brain → ConversationRuntime
```

- S2S: zero `8100`/`gateway` references (BRAIN_BASE_URL=http://127.0.0.1:8089/v1).
- AutoDL production (SOP v1.1 `JULIA_VOICE_MANUAL_DEPLOYMENT_SOP_v1.1.md`,
  `RMD3G_PRODUCTION_RUNBOOK` SUPERSEDED): no gateway component.
- turn_id = uuid4 (RP-2 compliant).

**PASS** — voice routes through ConversationRuntime; no gateway dependency.

## 4. Electron Path

- `text-client.js` `buildTurnBody` sends only turn_id/modality/input/stream
  (C-10 compliant).
- Reconnect = canonical reconciliation; local history is disposable
  projection (C-10 §7 compliant).
- No direct storage access (C-10 §21 compliant).
- Zero `:8100` reference.

**PASS** — Electron is client/body, Brain is the only endpoint.

## 5. Gateway Decision — Q3 Answer

Four-point confirmation:

| Check | Result |
|---|---|
| launch config | NONE — no plist/launchd/script; manual `python --port 8100` |
| Electron endpoint | ZERO reference to :8100 |
| Assistant runtime config | ZERO reference (js.chat() zero hits in rmd3g_prod) |
| voice route config | ZERO reference (S2S → 8089 tunnel, no gateway) |

Also: `gateway_server.py` (v1.1) and `gateway.py` (v1.0 legacy) **both default
to :8100** — two implementations contending for one port. Docs already mark
":8100 direct js.chat()" as REGISTERED-LEGACY / Non-ConversationRuntime path.

**Gateway Decision: COMPATIBILITY** — freeze :8100 as a legacy compatibility
transport layer, remove all cognitive state access (14 read points), per
C-10 §9 transport-only.

## 6. Final Audit Verdict

```text
Production Path:        PASS
Conversation Authority: PASS  (single authority = ConversationRuntime)
Voice Path:             PASS
Electron Path:          PASS
Gateway Decision:       COMPATIBILITY  (legacy compatibility transport)
```

## 7. Operational Note (separate from B0)

Brain launchd is currently gated: HEAD 44cea89 != approved bbd90af → RP-1
fail-closed (exit 4). This is the provenance gate working as designed against
an unapproved HEAD. Recovery = re-approve HEAD or rollback — a separate
governance decision, NOT part of B0.
