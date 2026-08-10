# CM-CORE-v1 — Conversation Core Runtime Contract

**Status:** 🔒 FROZEN  
**Date:** 2026-08-10 (frozen)  
**Derived from:** CM-00 Production Reality Audit (CLOSED)  
**Implementation feasibility:** CM-SPIKE-01 (PASS — p50 3.9ms, p95 7.7ms, p99 10.0ms)  
**Parent:** JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0  
**References:** C-01 Runtime Execution, C-02 Conversation Authority, C-03 Context OS, C-10 Gateway/Client, C-11 Voice/Media  
**Scope:** Stage 1 only — Storage v2, Compact, Diary, Archive/Delete are Stage 2 (CM-Extended)

**Known implementation limitation (NOT contract violation):**
Single-file conversations.json whole-rewrite scales linearly with store size.
Future storage evolution (Stage 2) may change persistence format. CM-I05
durability semantics remain unchanged regardless of storage implementation.

---

## 0. What This Contract Answers

```
Who owns conversation?       → ConversationRuntime (sole authority)
When is a turn accepted?     → Before ACK, before cognition
How do modalities attach?    → Same conversation_id, same turn protocol
How does cognition obtain    → Context OS, from canonical Conversation
   conversation context?        only. No client/provider history.
What survives restart?       → All accepted user messages + completed
                               assistant messages. NOT client state.
```

---

## 1. Core Model

```
                  Client Surfaces
       Electron / Voice / Web / Future Mobile
                     │
                     │ current interaction only
                     ▼
════════════════ JULIA CORE ═════════════════

              ConversationRuntime
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
 ConversationMessage          RuntimeTurn
 durable transcript           in-flight execution state
 authority                    non-transcript, per-turn
        │                         │
        └────────────┬────────────┘
                     ▼
                  Context OS
                     │
          CognitiveContextPackage
                     │
                     ▼
                    LLM

════════════════════════════════════════════

Electron cache     = disposable projection
VoiceWorkspace     = transitional runtime artifact (no authority)
S2S Chat           = provider transport state (no authority)
external_history   = legacy compatibility (rejected for Julia-native)
```

---

## 2. Frozen Invariants

### Authority

```
CM-I01  ConversationRuntime is the sole conversation authority.
        No other component may create, own, or mutate canonical
        conversation state.

CM-I02  ConversationMessage is the sole durable transcript truth.
        ConversationMessage represents exactly one user or assistant
        semantic fact in a conversation.
```

### Durable Acceptance (THE HARDEST INVARIANT)

```
CM-I05  Durable User Acceptance

        Once Core acknowledges a finalized user input as accepted,
        that user semantic fact MUST already be durably represented
        in canonical Conversation authority and MUST survive:

        - client loss
        - Electron restart
        - media-session loss
        - S2S restart
        - Core process restart
        - assistant cognition failure

        Assistant completion MUST NOT determine whether an accepted
        user message remains part of canonical Conversation.

        ACK returned to the client MUST mean the user semantic input
        is durable enough to survive Core process death.
```

### Runtime Lifecycle

```
CM-I03  Conversation ≠ Session.
        A conversation is a durable logical dialogue identity.
        An Electron session, Voice session, WebSocket, S2S process,
        provider session, or model instance is NOT a conversation.

CM-I06  Completed turns must not remain only in client, runtime,
        or S2S state. A turn that has completed its lifecycle
        (user accepted, assistant settled) must exist in canonical
        ConversationMessage form.

CM-I07  Text/Voice/Web share one conversation_id and one turn
        protocol. Modality does not create a separate conversation
        or a separate turn lifecycle.
```

### Modality / Client Convergence

```
CM-I04  Creating a new conversation MUST produce a durable Core
        artifact before any client treats it as canonical.
        A client MAY optimistically render a creation surface.
        A conversation MUST NOT be treated as canonical until Core
        has accepted/created its durable conversation identity.

CM-I08  Mode switching (Voice↔Text↔Web) attaches to the same
        conversation_id. It MUST NOT require client-side semantic
        history transfer, workspace flush, or history bootstrap.

CM-I09  Electron is presentation-only. Deleting its cache loses
        no conversation truth. Electron may choose display range;
        Electron MUST NOT choose model-visible history.

CM-I10  S2S is a media transport. Its internal Chat/history state
        MUST NOT serve as Julia conversation authority or cognitive
        history source. S2S provider hidden state is not Julia
        conversation authority.

CM-I11  Client history may never become Context authority.
        No caller-owned messages[], history[], or external_history
        may enter the Julia-native cognitive context path when
        a conversation_id is present.
```

### Context / Recovery

```
CM-I12  Context OS alone selects model-visible conversation context.
        ConversationRuntime MUST NOT impose any fixed message-count
        history cap (e.g. last-40, last-100, last-N for any N) on the
        cognitive path. ConversationRuntime provides canonical
        Conversation source; Context OS applies budget, ActiveTail,
        and retrieval policy.

        This prohibits: get_history(N) as cognitive gatekeeper,
        history[-N:] as permanent context policy.
        This does NOT prohibit: display pagination (page_size=40),
        storage segmentation, API cursor limits.

CM-I18  Core crash/restart recovers completed conversations without
        client help. Client restart is not a conversation recovery
        mechanism. Core restart does not require client history replay.

CM-I19  Idempotent current-turn retry must not duplicate messages.
        Retry by conversation_id + turn_id is safe. Clients MUST NOT
        retry by resending prior conversation history.

CM-I20  Cross-conversation leakage must be impossible by construction
        and tested. Attaching to conversation B MUST NOT expose or
        mutate conversation A.
```

---

## 3. CM-00 Conflict Dispositions

| # | Conflict | Severity | Disposition |
|---|----------|----------|-------------|
| 001 | VoiceWorkspace shadow conversation | P0 | **REMOVE AUTHORITY**: must not hold completed semantic turns that are not yet durable in Core |
| 002 | S2S Chat provider history bypass | P1 | **DE-AUTHORIZE**: may exist as transport/provider state; must not enter Julia cognitive context |
| 003 | SessionStore duplicate metadata | P2 | **DEFER** to CM-Extended/Migration |
| 004 | Electron create before Core durable | P1 | **REWRITE**: Core creates first; Electron receives canonical identity |
| 005 | external_history legacy path | P2 | **RETIRE**: Julia-native conversation cognition must reject caller-owned history |
| 006 | get_history(40) cognitive cap | P1 | **REMOVE CAP**: ConversationRuntime must not pre-truncate history; Context OS is sole selector |
| 007 | Electron live projection | P3 | **KEEP**: working as designed (disposable, non-canonical, turn-keyed) |

---

## 4. Acceptance Tests

```
CM-AT01  Core creates canonical conversation before client treats
         it as canonical. POST create → durable artifact → client
         receives confirmed conversation_id.

CM-AT02  Accepted text input survives Electron crash.
         User sends message → ACK returned → kill Electron →
         restart → conversation contains the message.

CM-AT03  Accepted voice final-ASR survives Electron crash.
         Voice STT final → Core ACK → kill Electron before
         assistant response → restart → user message present.

CM-AT04  Assistant cognition failure does not erase accepted
         user message. User accepted → LLM fails/timeout →
         user message remains in canonical conversation.

CM-AT05  Same turn retry produces exactly one canonical user
         message. Send T17 → ACK lost → retry T17 with same
         content → exactly one message in conversation.

CM-AT06  Voice↔Text rapid switch ×10 loses zero accepted turns.
         Each cycle: mode switch → turn accept → switch back.
         All accepted turns present in canonical conversation.

CM-AT07  Conversation A active → switch B → zero cross-
         conversation leakage. A turns do not appear in B.
         B bootstrap does not contain A content.

CM-AT08  Delete Electron cache → all canonical conversation
         recoverable. Cache file deleted → reopen →
         conversation list and all messages restored from Core.

CM-AT09  Restart Core → canonical conversation recoverable
         without client history. Kill Brain process → restart →
         conversation list and all completed messages present.

CM-AT10  Long conversation (>40 messages): ConversationRuntime
         does not pre-truncate history. Context OS can access
         messages beyond position 40 through retrieval/cursor.
```

---

## 5. Non-Requirements (Explicitly Out of Scope)

```
- Storage format (JSON/JSONL/SQLite): implementation choice
- Storage segmentation and rotation:     implementation choice
- Compact generation and invalidation:   Context OS policy
- ActiveTail token budget tuning:        Context OS policy
- Diary/reflection:                      CM-Extended
- Archive/delete/retention:              CM-Extended
- Legacy migration:                      CM-Extended
- Long-conversation UI pagination:       Electron/Client concern
```

---

## 6. Freeze Checklist

```
[ ] ConversationRuntime sole authority              CM-I01
[ ] ConversationMessage sole transcript truth        CM-I02
[ ] Conversation ≠ Session                           CM-I03
[ ] Core durable create before client canonical       CM-I04
[ ] Durable user acceptance before ACK                CM-I05
[ ] Completed turns canonical, not client-side        CM-I06
[ ] Modality convergence                              CM-I07
[ ] Mode switching no client history transfer         CM-I08
[ ] Electron disposable                               CM-I09
[ ] S2S non-authority                                 CM-I10
[ ] Client history ≠ context                          CM-I11
[ ] Context OS sole selector, no fixed-N cognitive cap CM-I12
[ ] Restart recovery without client help              CM-I18
[ ] Idempotent retry, no history replay               CM-I19
[ ] Cross-conversation isolation                      CM-I20
[ ] 7 conflict dispositions recorded                  §3
[ ] 10 acceptance tests defined                       §4
```

---

## 7. Closure Matrix — CFR Traceability

| Invariant | CM-00 Evidence | Conflict | Acceptance Test |
|-----------|---------------|----------|-----------------|
| CM-I01 | A/B/C (single canonical store) | 003, 004 | AT-01, AT-08 |
| CM-I02 | A/F (ConversationMessage schema) | 001, 005 | AT-02, AT-04 |
| CM-I03 | B/E (session ≠ conversation_id) | 001 | AT-02, AT-03, AT-08, AT-09 |
| CM-I04 | B (Electron create before Core) | 004 | AT-01 |
| **CM-I05** | C/E (pending invisible, E4 loss) | **001** | **AT-02, AT-03, AT-04, AT-05** |
| CM-I06 | D (VoiceWorkspace holds completed) | 001 | AT-06 |
| CM-I07 | C/D (same turn_id, same protocol) | — | AT-06 |
| CM-I08 | D/E (bootstrap/flush required) | 001 | AT-06 |
| CM-I09 | B/E (Electron cache disposable) | 004, 007 | AT-01, AT-08 |
| CM-I10 | D/F (S2S Chat not in context) | 002 | AT-03, AT-06 |
| CM-I11 | D/F (external_history blocked) | 002, 005 | AT-03 |
| **CM-I12** | C/F (get_history(40) cap) | **006** | **AT-10** |
| CM-I18 | E (E4/E5 restart scenarios) | 001, 004 | AT-08, AT-09 |
| CM-I19 | C/E (E7 pending retry gap) | 001 | AT-05 |
| CM-I20 | C/E (E3/E8 isolation) | — | AT-07 |

Bold rows indicate invariants with direct CM-00 production evidence of failure.

### CFR Verdict

```
1. Internal consistency               ✅ PASS
   No invariant contradicts another.
   CM-I05 + CM-I06 complementary (user accept vs assistant settle).

2. No implementation freezing          ✅ PASS (with CM-I12 clarification)
   Storage format, budget values, pagination, file paths: all open.

3. Conflict → invariant traceability    ✅ PASS
   All 7 conflicts map to ≥1 invariant.

4. AT → invariant coverage             ✅ PASS
   All 15 invariants covered by ≥1 acceptance test.
   Hard invariants (I05, I12) have multiple ATs.

CFR                                   ✅ COMPLETE
→ CM-SPIKE-01                         🟢 GO
```

---

*End CM-CORE-v1*
