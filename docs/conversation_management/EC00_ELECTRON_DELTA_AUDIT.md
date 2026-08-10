# EC-00 — Electron Reality Delta Audit

**Date:** 2026-08-10
**Status:** COMPLETE
**Core baseline:** Core Conversation Layer v2 (CLOSED)
**Electron baseline:** `julia_electron_v2` @ branch `codex/bugfix/electron-c10-c11-projection`

---

## EC-00 Check 1: New Conversation ID Ownership

### Finding: GAP — Electron generates ID before Core creates

```
Current:
  conversation-store.js:139 → createId('conv') → local timestamp-based ID
  app.js:1060 → textClient.createConversation('New Conversation')
  → Electron writes to local cache FIRST
  → Core creates lazily via ensureConversationMessages (GET → 404 → POST)

Target:
  Electron → POST create to Core
  → Core durable create → returns canonical conversation_id
  → Electron binds to returned ID
```

**Evidence:** `conversation-store.js:135-151`
**Contract gap:** CM-I04 (Core durable create before client bind)
**Severity:** P1
**Disposition:** EC-01 must add Core-first create path.

---

## EC-00 Check 2: Conversation List Authority

### Finding: PARTIAL — list from Core, but Electron owns display

```
Current:
  listConversations() → reads julia-conversations-v1.json (local cache)
  refreshConversationList() → syncs from Core via textClient.listConversations()
  → renders grouped by date

Target:
  list = Core catalog only
  local cache = disposable projection
  (Already mostly correct — cache self-declares non-canonical)
```

**Evidence:** `conversation-store.js:7-9` (self-declared non-canonical)
**Contract gap:** CM-I09 (disposable projection). Already largely compliant.
**Severity:** P3
**Disposition:** EC-02 to ensure Core catalog is sole list authority.

---

## EC-00 Check 3: Open/Reopen Authority

### Finding: OK — already Core-driven

```
Current:
  openConversation() → textClient.openConversation(id)
  → syncConversationMessages() → GET Core → reconcile local cache
  → renderConversationMessages()

  Conversation history loads from Core GET.
```

**Evidence:** `app.js:1013-1031`
**Contract gap:** None. Already Core-authoritative.
**Severity:** PASS
**Disposition:** KEEP. Verify in EC-02.

---

## EC-00 Check 4: Display History as Disposable Projection

### Finding: OK with live voice projection note

```
Current:
  renderConversationMessages() → renders from Core canonical
  liveVoiceProjections → upsertVoiceProjection() for voice turns
  → non-canonical, reconciled on Core sync

  Cache deletion → conversation list and messages reload from Core.
```

**Evidence:** `conversation-store.js:7-9`, `app.js:upsertVoiceProjection`
**Contract gap:** EC-03 live projections properly reconciled.
**Severity:** PASS (with EC-03 verification)
**Disposition:** KEEP. EC-03 to verify cache deletion recovery.

---

## EC-00 Check 5: Switch A→B Stale Event Isolation

### Finding: GAP — no conversation_id guard on streaming events

```
Current:
  textClient.onTextStreamEvent → activeTextStreams Map
  voice transcript events → scheduleCanonicalConversationSync
  Neither checks: event.conversation_id == activeConversationId

  Rapid switch A→B during streaming in A:
  A's late delta → could render into B's thread
```

**Evidence:** `app.js:1129-1160` (text stream handler), `app.js:189-207` (message listener)
**Contract gap:** CM-I20 (cross-conversation isolation)
**Severity:** P1
**Disposition:** EC-04 must add conversation_id guard on all async events.

---

## EC-00 Check 6: Restart Recovery

### Finding: PARTIAL — Core recoverable, Electron cache disposable

```
Current:
  Core restart → conversations.json persists → recoverable ✅
  Delete Electron cache → reopen → sync from Core → recoverable ✅
  BUT: active voice turns in VoiceWorkspace → LOST ❌ (known Voice issue)

  For Electron-only (no Voice): restart recovery works.
```

**Evidence:** CM00-E4 (Electron restart), CM00-E5 (Core restart)
**Contract gap:** CM-I18 (restart recovery). Core layer satisfied.
**Severity:** P2 (Electron-only: OK. Voice gap is Voice bug, not Electron.)
**Disposition:** EC-05 to verify. Voice convergence will close the VoiceWorkspace gap.

---

## EC-00 Delta Summary

| Check | Status | Severity | Owner |
|-------|--------|----------|-------|
| 1. New Conversation ID | GAP | P1 | EC-01 |
| 2. Conversation List | PARTIAL | P3 | EC-02 |
| 3. Open/Reopen | PASS | — | EC-02 verify |
| 4. Display Projection | PASS | — | EC-03 verify |
| 5. Switch Isolation | GAP | P1 | EC-04 |
| 6. Restart Recovery | PARTIAL | P2 | EC-05 |

### EC Program Plan

```
EC-00 Delta Audit                   ✅ COMPLETE
EC-01 Core-first Create             🟢 GO  (fix CM-I04 gap)
EC-02 Core List/Open authority      ⏳
EC-03 Projection/Restart            ⏳
EC-04 Switching isolation           ⏳
EC-05 Acceptance                    ⏳
```

### Required Electron changes only (no Core, no Voice)

```
EC-01: conversation creation path (conversation-store.js, app.js)
EC-02: list from Core catalog only (if gap found)
EC-04: conversation_id guard on async events (app.js)
```

---

*End EC-00*
