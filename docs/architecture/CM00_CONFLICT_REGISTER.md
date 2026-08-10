# CM00 CONFLICT REGISTER — Production Authority Conflicts

**Date:** 2026-08-10
**Status:** DRAFT — IN PROGRESS
**Allowed statuses:** OBSERVED | CONFIRMED | RULED OUT | UNKNOWN
**Forbidden:** FIXED | SHOULD | IMPLEMENT

---

## CM00-CONFLICT-001 — VoiceWorkspace as Shadow Conversation

```
Status:       CONFIRMED

Observed:
  VoiceWorkspace (voice-workspace.js) maintains completed semantic turns
  (user_content + assistant_content + turn_id + status) that are NOT
  yet present in Core canonical (julia_ai_assistant/data/conversations.json).
  Between FINAL STT and flush, VoiceWorkspace IS the only source of these
  turns. A rapid mode switch or crash during this window loses them.

Competing authorities:
  VoiceWorkspace (runtime, client-side) vs ConversationRuntime (canonical)

Contracts touched:
  C-02 Conversation Authority (sole transcript truth)
  C-03 Context OS (sole model-visible gateway)
  C-10 Gateway/Client (client projection only)
  CM-I06 (completed turns not client-side only)
  CM-I10 (S2S/provider not authority)

Production consequence:
  Rapid Voice→Text→Voice switch loses recent semantic turns.
  Confirmed by Tony in production testing: "Julia完全看不到前面的话题内容."

Root mechanism:
  VoiceWorkspace holds D/E/F while Core has A/B/C.
  New voice session bootstraps from Core → sees A/B/C only.

Severity:     P0

Disposition:  UNRESOLVED
Target:       CM-Core Contract — durable user accept before ACK (CM-I05)
              eliminates this gap.
```

---

## CM00-CONFLICT-002 — S2S Chat as Provider-Owned Cognitive History

```
Status:       CONFIRMED

Observed:
  S2S speech-to-speech library maintains a Chat with full conversation
  history (audio placeholders, STT transcripts, assistant responses).
  This Chat is sent to Brain as messages[] in every /v1/chat/completions
  request. Currently IGNORED by Brain when conversation_id present
  (native_stream path). But the data is IN the request.

Competing authorities:
  S2S Chat (provider-owned) vs Context OS (Core-owned)

Contracts touched:
  C-03 Context OS (sole model-visible gateway)
  C-11 Voice/Media (voice is body, not cognition)
  CM-I10 (S2S non-authority)
  CM-I11 (client history ≠ context)

Production consequence:
  If Brain path changes (external_history accepted), S2S Chat becomes
  de-facto LLM context authority. Currently dormant but the bypass
  exists in production code (openai_compat.py legacy path, lines 95-108).

Severity:     P1 (dormant P0)

Disposition:  UNRESOLVED
Target:       CM-Core Contract — C1B-L-I7: S2S is media transport only.
              Brain external_history rejection becomes invariant.
```

---

## CM00-CONFLICT-003 — Dual Session Metadata Stores

```
Status:       CONFIRMED

Observed:
  Two separate JSON files store session metadata:
  - SessionRepository (julia_ai_assistant/data/conversations.json, 38 sessions)
  - SessionStore (~/.julia/sessions.json, 31 sessions)
  
  SessionStore.message_count ≠ SessionRepository message count.
  SessionStore stores truncated message snippets (last 20).
  SessionStore has stale session IDs not in SessionRepository (e3-gate, etc.)

Competing authorities:
  SessionRepository (canonical) vs SessionStore (legacy metadata)

Contracts touched:
  C-02 Conversation Authority
  CM-I01 (sole conversation authority)

Production consequence:
  Two session lists exist. Title generation works from SessionStore
  snippets, not canonical transcript. Session listing could show
  stale data or wrong counts.

Severity:     P2

Disposition:  UNRESOLVED
Target:       CM-Core — SessionStore retired or reconciled.
```

---

## CM00-CONFLICT-004 — Electron Conversation Created Before Core Durable

```
Status:       CONFIRMED

Observed:
  Electron createConversation() generates a local conversation_id and
  writes to julia-conversations-v1.json BEFORE Core creates the artifact.
  Core creation happens later via ensureConversationMessages().
  If Core is unreachable, Electron has a conversation_id with no
  durable Core backing.

Competing authorities:
  Electron local cache vs Core SessionRepository

Contracts touched:
  C-02 Conversation Authority
  CM-I04 (new conversation → durable Core artifact)

Production consequence:
  Conversation ID exists in Electron but not in Core. Reopen on
  another device or after Electron cache clear → conversation lost.

Severity:     P1

Disposition:  UNRESOLVED
Target:       CM-Core — Core creates conversation_id, Electron receives it.
```

---

## CM00-CONFLICT-005 — Brain external_history Legacy Path Active

```
Status:       OBSERVED

Observed:
  openai_compat.py contains a legacy path (lines 95-108) that passes
  caller-owned external_history to prepare_voice_turn() when 
  conversation_id is absent. Currently blocked by the conversation_id
  presence check at line 58. But the path EXISTS in production code.

Competing authorities:
  Caller-owned history vs Core-owned context

Contracts touched:
  C-03 Context OS (sole model-visible gateway)
  CM-I11 (client history ≠ context)

Production consequence:
  Dormant. Could activate if conversation_id is not sent by S2S.

Severity:     P2 (dormant)

Disposition:  UNRESOLVED
Target:       CM-Core — legacy path removed. S2S always sends conversation_id.
```

---

## CM00-CONFLICT-006 — Context History Assembly Boundary UNKNOWN

```
Status:       UNKNOWN

Observed:
  _stream_turn calls js.process_stream(user_text, ctx.history, ...).
  ctx.history is produced by ConversationRuntime.begin_turn_streaming().
  The exact bounds of ctx.history are UNKNOWN without runtime trace:
  - Does it include all canonical messages?
  - Is there a get_history(max_messages=N) cap?
  - Is ActiveTail applied here or downstream?

Competing authorities:
  UNKNOWN until traced

Contracts touched:
  C-03 Context OS
  CM-I12 (Context OS alone selects visible context)
  CM-CMP-I3 (no fixed last-N policy)

Production consequence:
  UNKNOWN — could silently truncate context for long conversations.

Severity:     P1 (needs runtime trace)

Disposition:  UNRESOLVED
Target:       CM00-F (Context/Compact audit)
```

---

## CM00-CONFLICT-007 — Electron liveVoiceProjections Not Yet Canonical

```
Status:       OBSERVED

Observed:
  upsertVoiceProjection() renders voice turns with authority: "non_canonical"
  into Electron text timeline. These projections are reconciled (deleted)
  when canonical sync returns matching turn_ids. Between upsert and reconcile,
  the Electron timeline shows content not yet in Core.

Competing authorities:
  Electron projection (UI) vs Core canonical (truth)

Contracts touched:
  C-10 Gateway/Client (client projection only)
  CM-I09 (Electron disposal)

Production consequence:
  Electron shows correct content faster (good). But if Core sync fails,
  projections could persist without canonical backing. LOW risk given
  self-declared non-canonical + class-based styling.

Severity:     P3

Disposition:  UNRESOLVED
Note:         This is a working-as-designed projection, not a bug.
              The conflict is architectural, not operational.
```

---

*CM00 CONFLICT REGISTER — CONTINUES WITH CM00-E/F*
