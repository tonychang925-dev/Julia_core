# B0_GATEWAY_BOUNDARY_ATTRIBUTION

Status: B0 INVENTORY + BOUNDARY CLASSIFICATION (patch direction pending approval)
Date: 2026-08-23
Repository: `/Users/admin/julia_core` / branch `wave5/authority-consolidation`
Source: baseline regression classification — Category B, 8 gateway failures

---

## 1. Failure Shape

```text
AttributeError: 'JuliaSession' object has no attribute 'current_topic'
    julia_core/runtime/gateway_server.py:156/:161/:274/:277/:292/:293/:366/:368/:370
```

8 gateway E2E tests fail through the PRODUCTION `create_app()` path.

## 2. Root Cause — Contract Drift (C1.2)

`JuliaSession` is frozen under **CORE-C1.2: ZERO turn-owned mutable instance
fields**. All turn state (turn_count, current_topic, answered_questions) lives
in `TurnContext`, created per invocation:

```python
# julia_session.py:64-68
class JuliaSession:
    """CORE-C1.2: ZERO turn-owned mutable instance fields.
    All turn state lives in TurnContext, created per invocation."""
```

The production `gateway_server.py` was NOT updated: it reads
`js.current_topic` / `js.turn_count` — attributes that no longer exist on
`JuliaSession` (and never held valid values: `js.chat()` builds an isolated
`TurnContext([])` each call, so turn_count is always 0, topic always
"greeting").

Classification: **B — Real Regression** (production code out of sync with a
frozen runtime contract). Not test drift, not expectation change.

## 3. Entry Path Inventory

| Route | Session path? | Reads stale attrs |
|---|---|---|
| `GET /health` | no | — |
| `GET /livekit/token` | no | — |
| `GET /traces` | no | — |
| `GET /sessions` | catalog | — |
| `POST /sessions` | create | — |
| `GET/DELETE /sessions/{sid}` | catalog | — |
| `POST /chat` | **yes** | `:156 :161 :274 :277 :292 :293` |
| `WS /ws` | **yes** | `:366 :368 :370` |

Problem reading points: **9** (6 in /chat, 3 in /ws).

## 4. Boundary Classification

### Entry Path Integrity

- `/chat` and `/ws` call `get_session() → js.chat(text)` — the **legacy sync
  entry** (`julia_session.py:226` docstring: "New code must use
  ConversationRuntime.process_turn() with JuliaSession.process()").
- The production entry path is therefore NOT aligned with the C1.2/Conversation
  Runtime contract. It still routes through a legacy shim that has no valid
  turn state to expose.

### Authority Forwarding

- Gateway itself only routes / validates / dispatches — it does not define
  identity or mutate continuity. Confirmed.
- `SessionStore.touch` writes **derived catalog metadata only** (message_count,
  topics); its comment states: "CM-R1: shadow transcript retired.
  ConversationRuntime owns sole durable transcript authority." → SessionStore
  is NOT a transcript authority. Consistent with the authority model.
- `store.generate_title(sid, js)` (called when turn_count >= 2) — needs to be
  checked for stale-attribute dependency once the fix direction is chosen.

### Session Boundary

- Gateway `session_id` (runtime session) is separate from canonical
  `conversation_id`. No collision reintroduced (R1 fix in place).
- No identity-authority surface in the gateway layer. ✅

## 5. Expected Authority Path

```text
External request
    ↓
gateway (/chat, /ws)        → route / validate / dispatch
    ↓
ConversationRuntime.process_turn() + JuliaSession.process()   (C1.2 path)
    ↓
TurnContext                  → per-turn state (turn_count, current_topic)
    ↓
reply + derived catalog metadata (SessionStore)
```

Turn/topic must be derived from the per-turn execution (TurnContext / process
result), NOT from `JuliaSession` instance attributes.

## 6. Fix Direction Options (pending approval)

| Option | Change | Impact |
|---|---|---|
| **A — Minimal stop-bleed** | Gateway stops reading `js.current_topic`/`js.turn_count`; derive turn from `store.message_count`, topic from `store.topics` (or omit) | small; topic title-generation degraded |
| **B — Contract alignment** | Gateway migrates `/chat` + `/ws` to `ConversationRuntime.process_turn()` + `JuliaSession.process()`, reading topic/turn from the process result | larger; architecturally correct (sole authority path) |

Recommendation: **B** is the correct direction (aligns the System Entry
Boundary with the frozen C1.2/Conversation Runtime authority path). A may be
acceptable as an interim stop-bleed only.

## 7. Evidence Requirement

After closure, produce:

```text
B0_GATEWAY_BOUNDARY_EVIDENCE_REPORT_v1.0
    Entry Capability ↑
    Authority Surface = constant
    gateway does not define identity / mutate continuity
    /chat + /ws route through the C1.2 authority path
```

## 8. Acceptance

```text
[ ] 8/8 gateway E2E tests pass through production create_app()
[ ] Gateway entry path aligned with ConversationRuntime (or documented interim)
[ ] No identity / continuity authority added to gateway
[ ] AT-17 regression gate 14/14 preserved
```

Patch only after fix direction is approved.
