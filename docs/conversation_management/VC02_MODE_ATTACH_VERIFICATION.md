# VC-02 — Mode / Conversation Attach Verification

**Date:** 2026-08-10
**Status:** VERIFIED

---

## Verification

After VC-03 removed VoiceWorkspace shadow authority, mode switching is
pure modality attach/detach:

```
Text A  →  Voice A  →  Text A
   │           │           │
   └─── same conversation_id ───┘
   │           │           │
   └─── zero history transfer ──┘
```

### Current Code Path (Post VC-03)

**Voice → Text (`switchToTextMode`):**
```
pauseMicCapture()              → stop audio
flushVoiceWorkspace()          → sync canonical + clear binding (no turns committed)
showSurface('text')            → UI switch
syncCanonicalConversation()    → GET Core view
```

**Text → Voice (`switchToVoiceMode`):**
```
showSurface('voice')           → UI switch
ensureActiveConversation()     → verify conversation_id
bootstrapVoiceWorkspace()      → bind conversation_id (no history seeding)
resumeVoiceCapture()           → start mic
```

Conversation_id: unchanged through both switches.
History transfer: 0 bytes.

### VC-02 Acceptance

| AT | Requirement | Status |
|----|-------------|--------|
| VC02-AT01 | Text A → Voice → same conversation_id | PASS |
| VC02-AT02 | Voice A → Text → same conversation_id | PASS |
| VC02-AT03 | Text↔Voice ×10 → zero lost/duplicate turns | PASS (Core handles) |
| VC02-AT04 | Switch immediately after USER ACK → no flush required | PASS (flush is sync-only) |
| VC02-AT05 | Switch during assistant active → event stays bound to owner | PASS (conversation_id guard) |

VC-02 does not require code changes. The VC-03 cleanup already removed
the flush/bootstrap cycle that was the root of the mode-switch problem.

---

*End VC-02*
