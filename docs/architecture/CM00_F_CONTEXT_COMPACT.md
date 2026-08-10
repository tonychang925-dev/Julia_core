# CM00-F — Context / Compact / Model-Visible History Reality

**Date:** 2026-08-10
**Status:** DRAFT
**Code changes:** 0

---

## F-01: Complete Context Chain

```
User input (Text or Voice STT final)
        │
        ▼
ConversationRuntime.begin_turn_streaming()
        │
        ├── get_history(conversation_id, max_messages=40)
        │       │
        │       ├── session.messages[-40:]          ← HARD CAP
        │       ├── filter: status == "completed"   ← EXCLUDES pending
        │       └── return [{role, content}, ...]
        │
        ├── ctx.history = get_history result
        │
        ▼
Brain _stream_turn:
  js.process_stream(user_text, ctx.history, ...)
        │
        ▼
JuliaSession._prepare_turn():
  context_os.prepare(history=ctx.history, ...)
        │
        ├── _compute_active_tail(history, max_turns=20)
        │       │
        │       ├── budget_tokens = 4000 (soft cap)
        │       ├── iterate history in reverse
        │       ├── break when token_count + estimated > budget_tokens
        │       │   AND len(tail) >= 4
        │       └── hard cap: max_turns * 2 = 40 messages
        │
        ├── to_messages(tail, user_text)
        │       │
        │       ├── IdentityFrame → system text
        │       ├── ExperienceFrame → system text
        │       ├── EvidenceFrame → system text
        │       ├── CapabilityFrame → system text
        │       ├── SituationFrame → system text
        │       ├── ContinuityFrame → system text
        │       └── history messages (user/assistant pairs)
        │
        ▼
  provider.chat(messages, cognitive_mode="private_voice_continuity")
        │
        ▼
  DeepSeek (via LLM provider)
```

---

## F-02: Each Step Classified

### F02-01: get_history(max_messages=40)

```
File:       conversation_runtime.py:178-189
Type:       CANONICAL SOURCE (with cap)
Input:      SessionRepository.messages (full canonical)
Output:     Last 40 completed messages as [{role, content}]
Filter:     role in (user, assistant) AND status == "completed"

HARD CAP:   40 messages (NOT configurable by caller)
PENDING:    Invisible (status != "completed")
INTERRUPTED: Invisible (status != "completed")

Classification: CANONICAL SOURCE
Risk:          Conversations longer than 40 messages silently truncate
```

### F02-02: _compute_active_tail(max_turns=20)

```
File:       context_execution_runtime.py:221-237
Type:       DERIVED CONTEXT
Input:      ctx.history (from get_history, already capped at 40)
Output:     Token-budgeted tail, max 40 messages (max_turns * 2)

Soft cap:   4000 tokens (budget_tokens)
Hard cap:   40 messages (max_turns * 2 = sanity bound)
Min keep:   4 messages (len(tail) >= 4 before break)

Classification: DERIVED CONTEXT
Note:          Dual cap with get_history — get_history caps at 40,
               then ActiveTail further caps at 4000 tokens.
               Result: Julia sees at most min(40, ~4000 tokens).
```

### F02-03: to_messages(tail, user_text)

```
File:       context_execution_runtime.py:41-60
Type:       DERIVED CONTEXT (rendering)
Input:      ActiveTail history + user_text
Output:     Flat messages list: [system, ...history, user_text]

System text: IdentityFrame + ExperienceFrame + EvidenceFrame +
             CapabilityFrame + SituationFrame + ContinuityFrame
History:     Only the ActiveTail subset of get_history result

Classification: DERIVED CONTEXT
Note:          "Transitional — will be replaced by structured Alignment
               projection (C-09) in P6" (code comment at line 42)
```

### F02-04: Voice Path — Same Chain

```
Voice turn context assembly uses the IDENTICAL chain:
  openai_compat.py → native_stream → begin_turn_streaming
  → get_history(40) → ctx.history → process_stream → ActiveTail

VoiceWorkspace and S2S Chat are NOT in the context chain.
external_history is IGNORED by Brain (native_stream path).

Classification: CANONICAL SOURCE (same as Text)
```

### F02-05: Context OS prepare()

```
File:       context_execution_runtime.py:prepare()
Type:       DERIVED CONTEXT
Frames:     IdentityFrame, ConversationFrame, ExperienceFrame,
            SituationFrame, EvidenceFrame, CapabilityFrame,
            ContinuityFrame

ConversationFrame content: { active_turn_count, active_tail_topic }
  ← does NOT include message content in the frame itself.
  The actual conversation content is in the history list
  passed separately to to_messages().

Classification: DERIVED CONTEXT
```

---

## F-03: Context Source Map

```
┌─────────────────────────────┬──────────────────┬──────────────────────┐
│ Source                      │ Type             │ Production Status    │
├─────────────────────────────┼──────────────────┼──────────────────────┤
│ get_history(max_messages=40)│ CANONICAL SOURCE │ PRODUCTION           │
│ _compute_active_tail(20)    │ DERIVED CONTEXT  │ PRODUCTION           │
│ to_messages()               │ DERIVED CONTEXT  │ PRODUCTION           │
│ ConversationFrame            │ DERIVED CONTEXT  │ PRODUCTION           │
│ IdentityFrame                │ CANONICAL SOURCE │ PRODUCTION           │
│ ExperienceFrame              │ CANONICAL SOURCE │ PRODUCTION           │
│ EvidenceFrame                │ DERIVED CONTEXT  │ PRODUCTION (market) │
│ SituationFrame               │ DERIVED CONTEXT  │ PRODUCTION           │
│ CapabilityFrame              │ DERIVED CONTEXT  │ PRODUCTION           │
│ ContinuityFrame              │ DERIVED CONTEXT  │ PRODUCTION           │
├─────────────────────────────┼──────────────────┼──────────────────────┤
│ VoiceWorkspace               │ BYPASS           │ NOT IN CONTEXT CHAIN │
│ S2S Chat                     │ BYPASS           │ NOT IN CONTEXT CHAIN │
│ external_history (legacy)    │ BYPASS           │ DORMANT              │
│ Electron history             │ PROJECTION       │ NOT IN CONTEXT CHAIN │
│ Startup memory transcripts   │ CANONICAL SOURCE │ PERSONA BOOTSTRAP    │
│ Memory OS experiences        │ CANONICAL SOURCE │ PERSONA BOOTSTRAP    │
│ get_messages(max_messages=100)│ API ENDPOINT   │ NOT IN CONTEXT CHAIN │
└─────────────────────────────┴──────────────────┴──────────────────────┘
```

---

## F-04: Legacy / Non-Production Checks

```
get_history(max_messages=40):           PRODUCTION ✅  (begin_turn_streaming line 257)
history[-N]:                             NOT FOUND ❌   (replaced by ActiveTail)
ActiveTail (budget-driven):              PRODUCTION ✅  (_compute_active_tail line 286)
StructuredCompact (separate compact):    NOT IN CONTEXT CHAIN ❌ (compact/ exists but used for long-conversation offline)
ctx.history boundary:                    get_history(40) → ActiveTail(4000 tokens)
Voice/S2S extra messages[]:              NOT IN PRODUCTION ❌ (Brain ignores external_history)
Brain external_history reachability:     DORMANT (only when conversation_id absent)
get_messages(max_messages=100):          API ENDPOINT ONLY (NOT context — used by Electron sync)
```

---

## F-05: Key Findings

### F05-01: Dual Context Cap

```
Julia's model-visible conversation history goes through TWO caps:

1. get_history(max_messages=40):    Hard last-40 slice from canonical
2. _compute_active_tail(4000 tokens): Budget-driven, max 40 messages

Combined: Julia sees at most min(40 completed messages, 4000 tokens)
          of conversation history.

Long conversations (>40 messages) are silently truncated at the
40-message boundary from canonical storage.

CM-CMP-I3 ("No fixed last-N") is NOT currently satisfied.
```

### F05-02: VoiceWorkspace NOT in Context Chain

```
Voice turn context comes from Core get_history(), same as Text.
VoiceWorkspace and S2S Chat are BYPASS objects — they exist but
are NOT in the model-visible context path.

The continuity problem is NOT that Julia sees S2S Chat instead of Core.
The problem is that Core doesn't have the latest turns yet.

This means: CM00-CONFLICT-001 (VoiceWorkspace shadow) affects
PERSISTENCE timing, not CONTEXT selection.
```

### F05-03: Pending Messages Invisible

```
get_history filters status == "completed".
Messages with status == "pending" are durable in conversations.json
but invisible to context assembly.

Impact: if a turn crashes after add_message(user, pending) but before
commit_streaming_turn, the user message exists in the file but
Julia can never see it in context (filtered out).

This is the exact CM-I05 gap identified in E5.
```

### F05-04: external_history Dormant But Present

```
openai_compat.py legacy path (lines 95-108):
  When conversation_id is absent → external_history used.
  Currently conversation_id is always present for Julia-bound S2S.
  Classification: DORMANT BYPASS (not active, but reachable if S2S
  config changes).
```

---

*End CM00-F*
