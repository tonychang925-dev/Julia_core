# P7_GENERATION_RUNTIME_DEEP_AUDIT

Status: DEEP AUDIT (Step 18-23)
Date: 2026-08-23
Repository: julia_core `conversation_runtime.py` / `julia_session.py` / `context_execution_runtime.py`
Mode: READ-ONLY

---

## Step 18 — Hidden Generation Runtime?

- NO explicit `GenerationRuntime` class.
- `generation_id` EXISTS but only in `ContextExecutionRuntime` for the tool
  loop (`gen_{uuid4}`, comment: "Same turn_id, new generation_id. ToolResult
  must pass through Context OS" — `context_execution_runtime.py:295`).
- CRT has turn-level begin/commit/cancel streaming; NO generation-level
  lifecycle.

**Conclusion: Generation Boundary NOT formed** (confirms P7 root cause).

KEY asset: generation_id infrastructure already exists in Context OS tool
loop — P7 can elevate it, not start from zero.

## Step 19 — Canonical Commit Location

Confirmed candidate B:

```python
# conversation_runtime.py:300-326
commit_streaming_turn(ctx, assistant_content)
    → self._add_message(role="assistant", status="completed")
```

Called by Brain `_stream_turn` AFTER the stream completes (before [DONE]).

- Canonical commit point: clear and Core-owned.
- Client receives only [DONE] — no `canonical_ref` awareness of commit.

## Step 20 — Memory / Continuity Write Timing

- `process_turn` (CRT): transcript only (`_add_message`); NO memory/continuity
  writes.
- `_chat_impl` (julia_session): provider.chat + event store trace only; NO
  memory/continuity writes.

**Conclusion: NO `provider output → memory.store()` path exists.** Correct
(provider output is not yet Julia experience).

## Step 21 — Interrupt / Cancel Semantics

```python
# conversation_runtime.py:330-341
cancel_streaming_turn(ctx):
    """Cancel/rollback a streaming turn."""
    # user message already durable (completed); assistant cancellation is an
    # independent lifecycle event and must not downgrade/erase user turn.
    pass          # ← effectively NO-OP (only releases lock)
```

- User turn preserved ✅
- **Assistant message after cancel: ABSENT (not interrupted)** ❌
  → violates C-10 §13 (canonical interrupted must remain visible)
  → violates C-02 (interrupted assistant should retain committed/emitted content)

## Step 22 — Retry Semantics

- `begin_turn_streaming` idempotent (existing assistant content →
  already_completed skip).
- **NO generation abstraction** — multiple execution attempts cannot be
  distinguished (audit / streaming / interruption all blind).

Wrong future model avoided so far (idempotency prevents duplicates), but:

```text
3 providers retry = 1 turn, no generation_id records
→ execution identity missing
```

## Step 23 — Persona Host Impact (pre-check)

- Phase8 frozen: artifact != identity.
- P7 scope contract frozen: artifact metadata → Core decides semantic event.
- Generation Runtime must NOT turn artifact metadata into semantic authority.

## Summary Table

| Boundary | Status |
|---|---|
| Generation Identity | ❌ Missing (generation_id infra exists in Context OS tool loop only) |
| Canonical Commit | ✅ Located (`commit_streaming_turn → _add_message`) |
| Memory Commit Boundary | ✅ Correct (no provider→memory path) |
| Interrupt Semantics | ⚠️ Cancel = NO-OP; assistant interrupted message ABSENT (C-10 §13 violation) |
| Retry Semantics | ⚠️ Idempotent but no generation identity |

## P7 Implications

1. Generation Runtime: elevate existing generation_id infrastructure
   (Context OS) into a full provider-generation lifecycle.
2. Interrupt: cancel must produce a canonical `assistant.interrupted`
   message (committed/emitted content preserved) — C-10 §13.
3. Retry: generations recorded under one turn_id (1 turn : N generations).
4. Canonical commit: emit `assistant.completed` + canonical_ref (C-10 §3).
