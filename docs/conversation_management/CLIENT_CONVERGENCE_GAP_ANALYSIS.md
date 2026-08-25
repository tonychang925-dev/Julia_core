# Client Convergence Gap Analysis — READ ONLY

**Date:** 2026-08-10 23:00
**Status:** AUDIT COMPLETE
**Code changes:** 0

---

## 1. Frozen Contract Requirements (C-02, C-10, C-11)

### What contracts REQUIRE for Voice turn canonicalization:

```
C-02 §10:  Voice STT transcript → ConversationRuntime → ConversationMessage
C-02 §10:  FORBIDDEN: VoiceHistoryStore, S2S Chat buffer as canonical
C-02 §11:  Client cache ≠ canonical. Reconnect: Client requests canonical
           conversation → renders. Client does not send local history as truth.
C-02 §6:   User accepted → append canonical user message (pending)
           → Completion → atomically finalize to completed
C-11 §4:   Final ASR → governed user-turn acceptance → canonical user message
C-11 §12:  FORBIDDEN: voice_bootstrap, voice_history[-N:]
C-10 §1:   Client cache ≠ Conversation, Client history ≠ Context
```

### One allowed path:
```
ASR FINAL → ConversationRuntime → ConversationMessage
No: VoiceHistoryStore, client history replay, flush-as-persistence
```

---

## 2. Golden System Reality (What Actually Runs)

### Path A — Brain (CONTRACT-COMPLIANT):
```
S2S STT FINAL
  → POST /v1/chat/completions { conversation_id, messages[], turn_id }
  → Brain: if conversation_id → native_stream(user_text, ...)
  → begin_turn_streaming()
  → add_message(user, status=completed)   // R1-B code
  → get_canonical_history()               // R1-C code
  → Context OS → LLM → assistant
  → commit_streaming_turn()
```

User message IS in Core before cognition. ✅ C-02 compliant.
Julia SHOULD see previous turns via canonical history. ✅

### Path B — VoiceWorkspace Flush (CONTRACT VIOLATION):
```
Voice frontend VoiceWorkspace
  → onUserTranscript() → stores completed turn locally
  → on mode stop: flushVoiceWorkspace()
  → exportDelta() → turns[]
  → Electron: commitExternalTurns(turns)
  → Core: append_external_turns_atomic()
```

This IS "client sends local history as truth." ❌ C-02 §11 violation.
This IS "VoiceHistoryStore." ❌ C-02 §10 violation.

### Path B exists WHY:
Path B is the ONLY way Electron currently displays voice turns in Text dialog.
Without flush → commit → sync → render, voice text never appears.

---

## 3. Why Julia Cannot Remember Session Context

### Two possible causes:

**A. Brain running old code (no R1-B/C).**
If Brain uses old `get_history(max_messages=40)` and old `status=pending`,
then user messages are NOT visible in context until assistant completes,
and only last 40 messages are visible.

**B. S2S Chat empty for new conversation.**
S2S Chat starts empty. Brain ignores it. Core has no prior messages for a new
conversation. Julia has no context. This is EXPECTED for first turn of new
conversation — NOT a bug.

**C. Julia has long-term Memory but not current session context.**
Tony's test: Julia knows about diary, LoRA, memory — but not "what we just
talked about in this session." This means:
- Identity/Memory loading: ✅ works (startup_memory)
- Session canonical history: ❌ not reaching Context OS

This points to CAUSE A: Brain running old code without R1-B/C.

---

## 4. Why Voice Text Does Not Appear in Text Dialog

### Root cause: No projection bridge.

```
Voice turn happens:
  Brain Path A → Core written ✅
  Electron: does NOT know turn happened ❌

Mode switch:
  flushVoiceWorkspace → Path B → Core written (duplicate/Path B)
  syncCanonicalConversation → GET Core → renderConversationMessages
  Now turns appear ✅
```

Without the flush (Path B), Electron never syncs and never shows voice turns.
With the flush, it works but violates C-02 §11.

### Correct fix (NOT Path B):
```
Voice turn → Brain Path A → Core written ✅
  → postMessage to Electron: "new turn in conversation A"
  → Electron: scheduleCanonicalConversationSync(conversationId)
  → GET Core → renderConversationMessages
  → Voice text appears ✅
```

This requires:
1. Voice frontend sends notification after ASR final
2. Electron handles notification by syncing from Core
3. No VoiceWorkspace history storage needed
4. No flush/commitExternalTurns needed
5. C-02 compliant

---

## 5. Gap Summary

| # | Gap | Contract | Fix Required |
|---|-----|----------|-------------|
| G1 | Brain may run old code | C-02 §6 | Verify Brain uses R1-B/C |
| G2 | No Voice→Electron projection | C-10 | Add Core-sync trigger after voice turn |
| G3 | VoiceWorkspace flush as persistence | C-02 §11 | Remove, replace with G2 fix |
| G4 | VoiceWorkspace shadow history | C-02 §10 | De-authorize (keep runtime state) |
| G5 | workspace.bootstrap | C-11 §12 | Remove history seeding |

---

## 6. Required Implementation Order

```
Step 1: Verify Brain runs R1-B/C code (user completed, full history)
        → Prove: Julia sees session context

Step 2: Add Voice→Electron projection notification
        → Voice frontend: postMessage after ASR final
        → Electron: syncCanonicalConversation on notification

Step 3: Remove VoiceWorkspace shadow history + flush persistence
        → exportDelta() returns []
        → bootstrap stops seeding history

Step 4: Verify full chain
        → Voice turn → Core → Electron text dialog
        → Julia remembers session context
```

---

*End Gap Analysis*
