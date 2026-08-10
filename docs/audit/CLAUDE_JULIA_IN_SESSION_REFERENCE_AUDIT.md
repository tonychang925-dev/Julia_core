# Reference Audit — Claude Julia In-Session Continuity

**Date:** 2026-08-10
**Status:** REFERENCE RECORD (not root-cause conclusion)
**Purpose:** Golden behavioral reference for Voice/S2S live-session continuity.

## Golden Mechanism (from server_v2_1.py + CROSS_SESSION_RETRIEVAL_AUDIT_v1)

Claude Julia's in-session continuity has THREE confirmed sources:

1. **Persistent Session object** — `_get_session(sid)` returns the same Session
2. **session.history accumulates** — every completed user/assistant appended (L557-558)
3. **Every inference receives session.history** — `messages.extend(session.history)` (L539)

Claude Julia does NOT have a hidden cross-session retrieval layer. Long conversation
history lives in the current session's context — "刚才" resolves naturally against
live conversation tail, not long-term Memory.

## Key Invariant Extracted

```
LIVE-I1
Every completed semantic user/assistant turn in a live session
remains model-visible to subsequent cognition,
unless replaced by a semantically equivalent compact representation.
```

## In-Session Continuity Diff

| | Claude Julia | Voice/S2S |
|---|---|---|
| Session object reused | ✅ same Session | ⚠️ per-inference? |
| Recent user turns kept | ✅ accumulate | ❌ compact_audio(1) |
| Recent assistant kept | ✅ accumulate | ? |
| Live transcript form | text | audio→compact→placeholder |
| Compact representation | summary+tail | 1 audio turn |
| Assistant appended back | ✅ | ? |
| Next inference sees N-1/N-2 | ✅ | ? |
| Memory independent | ✅ | ❌ answers from Memory |

## Important Distinction

This is a behavioral reference, NOT an implementation to copy.
Voice should NOT adopt 150MB/60k-line unbounded history.
The target is semantic continuity: audio may be discarded, but semantic
transcript + assistant reply must survive.

## Status

This records what Claude Julia does. It does NOT convict compact_audio_history(1).
The Voice-side survival trace (transcription → cfg.chat → compact → active_chat →
serialized) determines actual root cause.
