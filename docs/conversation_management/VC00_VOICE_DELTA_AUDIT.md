# VC-00 — Voice Delta Audit

**Date:** 2026-08-10
**Status:** COMPLETE
**Baseline:** Core Conversation v2 (CLOSED) + Electron Convergence (CLOSED)
**Voice baseline:** `Julia-Voice-S2S` @ `feature/voice-c1b-workspace-reconcile`

---

## VC-00 Check 1: Final ASR → Core Path

### Finding: GAP P0 — ASR final goes to VoiceWorkspace, not Core accept_user_turn

```
Current:
  S2S WebSocket transcript event
  → main.js onTranscript handler
  → voiceWorkspace.onUserTranscript(d)  ← stores user_content locally
  → chat.onTranscript(d)                ← renders in voice iframe DOM
  → postToElectron (our EC addition)    ← sends to Electron (non-canonical)

  Core accept_user_turn() is NEVER called from voice path.
  Voice turn persistence happens only on flush → commitExternalTurns.

Target:
  ASR FINAL
  → ConversationRuntime.accept_user_turn()
  → canonical user durable
  → ACK
  → cognition
```

**Evidence:** `frontend/main.js:1376-1395` (transcript handler), `voice-workspace.js`
**Contract gap:** CM-I05 (durable before ACK), CM-I06 (completed turns not client-only)
**Severity:** P0
**Disposition:** VC-01: route ASR final through Core accept_user_turn().

---

## VC-00 Check 2: VoiceWorkspace as Shadow Conversation

### Finding: GAP P0 — VoiceWorkspace holds completed semantic turns

```
VoiceWorkspace stores:
  - user_content (final STT transcript)
  - assistant_content (response text)
  - turn_id, modality, status, timestamps
  - exportDelta() exports these as "turns" for flush

  These are COMPLETED semantic facts held outside Core canonical.
  Between ASR final and flush, VoiceWorkspace IS the only source.

Target:
  VoiceWorkspace = media/runtime state (VAD, partial ASR, playback, barge-in)
  VoiceWorkspace ≠ conversation history
  Completed turns live in Core ConversationMessage only
```

**Evidence:** `frontend/voice-workspace.js:40-158`
**Contract gap:** CM-I02 (sole transcript truth), CM-I06 (completed turns not client-only)
**Severity:** P0
**Disposition:** VC-03: de-authorize VoiceWorkspace. Remove turn storage from workspace.

---

## VC-00 Check 3: S2S Chat History

### Finding: LEGACY / DORMANT — S2S Chat exists but NOT in cognitive path

```
CM-00 already confirmed: S2S Chat is NOT in Julia cognitive context.
Brain native_stream path ignores external_history.
S2S Chat = provider transport state, not conversation authority.

But: S2S Chat is STILL being sent to Brain in every request.
If Brain path changes, it becomes active cognition source.
```

**Evidence:** CM00-D (Voice Turn Reality), CM00-F (Context/Compact)
**Contract gap:** CM-I10 (S2S non-authority), CM-I11 (client history ≠ context)
**Severity:** P1 (dormant)
**Disposition:** VC-04: neutralize S2S history path. S2S sends only current turn.

---

## VC-00 Check 4: external_history / Bootstrap

### Finding: DORMANT BYPASS — bootstrap seeds S2S Chat from Core history

```
Current:
  Electron bootstrapVoiceWorkspace
  → syncConversationMessages → Core GET
  → selectBootstrapWindow(canonical messages)
  → S2S seedConversationHistory(bootstrapMessages)

  This is the OPPOSITE of what we want:
  Electron reads Core history → seeds S2S Chat → S2S sends to Brain
  → Brain ignores it (correct) → but the round-trip is wasted

Target:
  S2S does NOT receive or carry conversation history.
  Context comes from Core Context OS via Brain native_stream.
  S2S only sends: { conversation_id, turn_id, transcript }
```

**Evidence:** `app.js:bootstrapVoiceWorkspace`, `main.js:seedConversationHistory`
**Contract gap:** CM-I11 (client history ≠ context), C-03 (Context OS sole gateway)
**Severity:** P1
**Disposition:** VC-04: remove bootstrap/seeding. S2S sends current turn only.

---

## VC-00 Check 5: Text ↔ Voice Mode Switch

### Finding: GAP P1 — mode switch requires flush/bootstrap cycle

```
Current:
  Voice → Text:
    flushVoiceWorkspace() → commitExternalTurns → syncCanonicalConversation

  Text → Voice:
    bootstrapVoiceWorkspace() → syncConversationMessages → seed S2S Chat

  This is a "history transfer" between clients.
  With Core v2, the history already lives in Core. Mode switch should
  be zero-transfer: just attach/detach modality.

Target:
  Voice → Text: stop mic, show text, GET Core view (no flush needed)
  Text → Voice: bind conversation_id, start mic (no bootstrap needed)
```

**Evidence:** `app.js:flushVoiceWorkspace`, `app.js:bootstrapVoiceWorkspace`
**Contract gap:** CM-I08 (mode switch no client history transfer)
**Severity:** P1
**Disposition:** VC-02: mode switch becomes conversation_id attach only.

---

## VC-00 Check 6: Restart / Crash Recovery

### Finding: PARTIAL — Core canonical survives, Voice state lost

```
Current:
  - Kill Electron: VoiceWorkspace turns lost (P0 gap from CM-00)
  - Kill S2S: S2S Chat lost, VoiceWorkspace lost
  - Core restart: canonical conversations survive

  After VC-01 fix (ASR → Core accept_user_turn):
  - Accepted user messages survive all Voice crashes
  - Assistant responses may still be lost if S2S dies mid-generation

Target:
  - All ACKed user messages survive any crash
  - Assistant canonicalization handles interrupted/incomplete responses
```

**Evidence:** CM00-E4/E5/E6
**Contract gap:** CM-I18 (restart recovery)
**Severity:** P1 (improves to P2 after VC-01)
**Disposition:** VC-05: verify restart after VC-01/02/03/04 fixes.

---

## VC-00 Delta Summary

| Check | Status | Severity | Owner |
|-------|--------|----------|-------|
| 1. ASR → Core path | GAP | P0 | VC-01 |
| 2. VoiceWorkspace shadow | GAP | P0 | VC-03 |
| 3. S2S Chat history | LEGACY | P1 | VC-04 |
| 4. Bootstrap/seeding | DORMANT | P1 | VC-04 |
| 5. Mode switch flush | GAP | P1 | VC-02 |
| 6. Restart recovery | PARTIAL | P1→P2 | VC-05 |

### VC Program Plan

```
VC-00 Delta Audit                      ✅ COMPLETE
VC-01 ASR → Core canonical             🟢 GO  (P0 fix)
VC-02 Mode/Conversation Attach         ⏳     (P1 fix)
VC-03 VoiceWorkspace de-authorize      ⏳     (P0 fix)
VC-04 S2S history neutralization       ⏳     (P1 fix)
VC-05 Restart/Interruption Acceptance  ⏳
```

### Required Voice changes only (no Core, no Electron, no Storage)

```
VC-01: route ASR final through Core accept_user_turn() in main.js
VC-02: simplify mode switch to conversation_id attach only in app.js
VC-03: remove turn storage/semantic history from VoiceWorkspace
VC-04: remove bootstrap/seeding from S2S path
```

---

*End VC-00*
