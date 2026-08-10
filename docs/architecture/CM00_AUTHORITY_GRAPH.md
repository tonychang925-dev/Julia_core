# CM00 AUTHORITY GRAPH — Production Conversation Authority Assignment

**Date:** 2026-08-10
**Status:** DRAFT — IN PROGRESS
**Classifications:** CANONICAL | RUNTIME | DERIVED | PROJECTION | CACHE | LEGACY | BYPASS | UNKNOWN

---

## Authority Assignments

### ConversationRuntime
```
Classification: CANONICAL
Evidence:       conversation_runtime.py — sole process_turn() owner
                All text turns route through process_turn()
                begin_turn_streaming / commit_streaming_turn
Storage:        SessionRepository (atomic JSON)
```

### ConversationMessage
```
Classification: CANONICAL
Evidence:       conversation_state/models.py — durable transcript schema
                Written by SessionRepository.add_message()
                Read by ConversationRuntime for context assembly
```

### SessionRepository
```
Classification: CANONICAL (storage layer)
Evidence:       repository.py — atomic temp→fsync→os.replace
                All append/read operations through RLock
File:           julia_ai_assistant/data/conversations.json
```

### SessionStore (~/.julia/sessions.json)
```
Classification: LEGACY
Evidence:       session_store.py — parallel metadata store
                NOT synced with SessionRepository message_count
                Stores truncated message snippets (last 20)
Risk:           Duplicate session metadata authority
```

### ContextExecutionRuntime / JuliaSession.process_stream()
```
Classification: CANONICAL (cognition gateway)
Evidence:       conversation_routes.py _stream_turn()
                Calls js.process_stream(user_text, ctx.history, ...)
                ctx.history sourced from ConversationRuntime.begin_turn_streaming()
```

### Context OS / ConversationFrame
```
Classification: DERIVED
Evidence:       context_os/ assembles from canonical sources
                UNKNOWN — need to trace how ctx.history is assembled
                in begin_turn_streaming to verify it doesn't clip at N
```

### ActiveTail / StructuredCompact
```
Classification: DERIVED
Evidence:       context_os/compact/ and context_os/budget/
                STATIC_ONLY — need runtime trace to confirm production usage
```

### Electron conversation-store (julia-conversations-v1.json)
```
Classification: PROJECTION
Evidence:       self-declared "disposable_projection", "authority: non_canonical"
                Reconciled from Core via syncConversationMessages
                Deleting cache does not delete conversation
```

### Electron activeConversationId
```
Classification: RUNTIME (client state)
Evidence:       In-memory variable in Electron renderer
                Points to current conversation, not an authority
```

### Electron liveVoiceProjections (via upsertVoiceProjection)
```
Classification: PROJECTION
Evidence:       authority: "non_canonical"
                Replaced by canonical on sync
                Turn-keyed dedup (conv::vws::turnId::role)
```

### VoiceWorkspace (voice-workspace.js)
```
Classification: BYPASS
Evidence:       Contains completed semantic turns (user_content, assistant_content)
                NOT yet in Core canonical between FINAL STT and flush
                Acts as multi-turn cognitive history source during voice session
                exportDelta() supplies turns to commitExternalTurns
Risk:           Shadow conversation authority during live voice sessions
Contracts:      Violates C-02 (sole transcript authority), CM-I06 (completed
                turns not client-side only)
```

### S2S Chat (speech-to-speech library)
```
Classification: BYPASS
Evidence:       Sent to Brain as messages[] in /v1/chat/completions
                Currently IGNORED by Brain when conversation_id present
                If that changes, becomes de-facto LLM context authority
Risk:           Provider-owned cognitive history
Contracts:      Violates C-03 (Context OS sole gateway), CM-I10 (S2S non-authority)
                CM-I11 (client history ≠ context)
```

### Brain openai_compat external_history path
```
Classification: BYPASS (active in legacy path)
Evidence:       openai_compat.py lines 95-108 — legacy path uses
                prepare_voice_turn(user_text, external_history=...)
                Only active when conversation_id absent
Risk:           LOW — currently blocked by conversation_id presence check
                But still present in production code
```

### Brain openai_compat native_stream path
```
Classification: CANONICAL (correct path)
Evidence:       conversation_id present → routes through Core
                external_history IGNORED
                This is the CORRECT behavior under C1B-L
```

### Memory OS (memory/*.jsonl)
```
Classification: CANONICAL (for Memory domain, NOT for transcript)
Evidence:       C-05 Memory OS Contract
                Separate from Conversation authority
                Read by startup_memory for persona bootstrap
```

### Legacy Diary / Session Summarizer
```
Classification: LEGACY
Evidence:       Not found in running production processes
                STATIC_ONLY — code paths in legacy servers
```

---

## Authority Gap Summary

| Object | Classification | Problem |
|--------|---------------|---------|
| VoiceWorkspace | BYPASS | Shadow transcript during live voice |
| S2S Chat | BYPASS | Provider-owned cognitive history |
| SessionStore | LEGACY | Duplicate metadata authority |
| external_history (legacy path) | BYPASS | Dormant but present |
| Context history assembly | UNKNOWN | Need to trace ctx.history bounds |
| ActiveTail/Compact in production | UNKNOWN | STATIC_ONLY |

---

*CM00 AUTHORITY GRAPH — CONTINUES AS CM00-E/F complete*
