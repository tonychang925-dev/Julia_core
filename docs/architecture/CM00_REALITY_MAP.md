# CM00 REALITY MAP — Production Conversation Paths

**Date:** 2026-08-10
**Status:** DRAFT — IN PROGRESS
**Method:** Static source audit + runtime file/process verification
**Code changes:** 0

---

## CM00-A — STORAGE REALITY

### A-01: SessionRepository (PRODUCTION, CANONICAL)

```
Path:     julia_ai_assistant/data/conversations.json
Schema:   JSON array of ConversationSession objects
Writer:   SessionRepository (atomic: temp → fsync → os.replace)
Reader:   ConversationRuntime, voice_api conversation management
Sessions: 38 (production), including conv_msmyary5/conv_msmsz5cg etc.
Evidence: file exists, 38 sessions, last message 2026-08-10T09:16
```

**Schema (per session):**
```json
{
  "id": "conv_xxx",
  "title": "...",
  "topic": "",
  "messages": [
    {
      "message_id": "msg_xxx",
      "conversation_id": "conv_xxx",
      "turn_id": "turn_xxx",
      "role": "user|assistant",
      "modality": "text|voice",
      "content": "...",
      "status": "completed|interrupted|pending",
      "created_at": "ISO-8601"
    }
  ],
  "tags": [],
  "created_at": "...",
  "updated_at": "...",
  "message_count": 0
}
```

### A-02: SessionStore (LEGACY METADATA, NON-CANONICAL)

```
Path:     ~/.julia/sessions.json
Schema:   { "sessions": { "id": { metadata } } }
Sessions: 31
Purpose:  Metadata cache (title, message_count snapshot, last 20 msg snippets)
          NOT canonical transcript. message_count ≠ actual message count.
Evidence: file exists, 31 sessions including stale IDs (e3-gate, default)
Risk:     Parallel metadata store not synced with canonical repository.
```

### A-03: Electron Local Cache (PROJECTION, DISPOSABLE)

```
Path:     ~/Library/Application Support/julia-electron-v2/julia-conversations-v1.json
Schema:   version 2, conversations array with messages[], projection metadata
Sessions: 4 active, reconcialed from Core
Authority: self-declared "disposable_projection", "non_canonical"
Evidence: file at path, 4 conversations, all stale=False
Risk:     LOW — correctly self-identifies as non-authority
```

### A-04: VoiceWorkspace (RUNTIME ONLY, NON-PERSISTENT)

```
Location: In-memory, Julia-Voice-S2S frontend
Schema:   VoiceWorkspace class (voice-workspace.js)
Content:  Active session turns (user_content, assistant_content, turn_id, status)
Lifetime: Voice session only. Exported as delta on flush.
Risk:     HIGH — contains completed semantic turns not in Core until flush
```

### A-05: S2S Chat (PROVIDER STATE, NON-PERSISTENT)

```
Location: In-memory, speech-to-speech library (PyPI 0.2.12)
Content:  Realtime conversation items (audio, transcripts, responses)
Lifetime: S2S process only
Risk:     MEDIUM — used as context source for LLM (via external_history)
```

### A-06: Legacy Transcripts (HISTORICAL, READ-ONLY)

```
Path:     julia_ai_assistant/memory/conversations/transcripts.jsonl
Purpose:  Startup memory loader reads recent turns for Julia persona bootstrap
Evidence: adapters/startup_memory.py line 80
Risk:     LOW — read-only for persona context, not canonical authority
```

### A-07: julia_core/data/conversations.json (TEST/LEGACY)

```
Path:     julia_core/data/conversations.json
Sessions: 2 (test data)
Purpose:  Used when ConversationRuntime is instantiated from julia_core working dir
Risk:     LOW — not the production path
```

### A-08: Legacy servers (HISTORICAL)

```
Files:    server_j0_11.py, server_v2_1.py, server_voice.py, server_cognitive.py
Purpose:  Predecessor implementations, not currently running
Risk:     LOW — not in production process list
```

---

## CM00-B — CREATE / LIST / OPEN REALITY

### B-01: Electron "New Conversation" Flow

```
STEP CM00-B-01: createConversation (Electron)

Caller:   app.js createNewConversation()
          → textClient.createConversation('New Conversation')
          → ipcMain 'julia:conversation:create'
          → conversation-store.js createConversation()

Object:   Local JavaScript object with generated conversation_id
Format:   conv_<timestamp_base36>_<random_hex>

Persistence:
  1. writes to julia-conversations-v1.json (Electron local cache)  ← FIRST
  2. Core artifact created later via ensureConversationMessages()   ← SECOND

ACCEPTED before Core durable?  YES — Electron creates local ID first
Core ACK required?             NO — createConversation is local-only
Durable before return?         NO — Core artifact may not exist yet

Evidence: main.js line 51-52 (createConversationStore), 
          conversation-store.js lines 135-151 (createConversation)
```

### B-02: Conversation List

```
STEP CM00-B-02: listConversations

Two sources exist:
  A. Electron local cache (conversation-store.js listConversations)
     → reads from julia-conversations-v1.json
     → primary display source for Electron sidebar

  B. Core catalog (GET /internal/v1/conversations)
     → Brain conversation_management.py serves from SessionRepository
     → used by refresh/sync path

Rendered by: app.js renderConversationList(), grouped by date
Authority:  Core catalog, Electron cache is projection
```

### B-03: Conversation Open

```
STEP CM00-B-03: openConversation

Caller:   app.js openConversation(conversationId)
          1. If active voice session → flush workspace for old conversation
          2. conversation-store.js setCurrentConversation()
          3. textClient.openConversation() → Core GET
          4. syncConversationMessages() → reconcile local cache
          5. renderConversationMessages() → display

Evidence: app.js lines 1013-1031
```

---

## CM00-C — TEXT TURN REALITY

### C-01: User Input

```
STEP CM00-TEXT-01: sendComposerMessage

Caller:   app.js composerForm submit handler
          → ensureActiveConversation()
          → appendMessage('user', text) to DOM (optimistic)
          → textClient.addConversationMessage() → local cache
          → executeTextTurn()

Evidence: app.js lines 1322-1401
```

### C-02: Core Turn Processing

```
STEP CM00-TEXT-02: Text Turn → Core

HTTP:     POST /internal/v1/conversations/{id}/turns
          { turn_id, modality: "text", input: "user text", stream: true }
          
Handler:  voice_api/conversation_routes.py conversation_turn()
          → ConversationRuntime.process_turn()
          
Evidence: conversation_routes.py lines 47-96, text-client.js line 59
```

### C-03: User Message Persistence

```
STEP CM00-TEXT-03: persist user message

Owner:    ConversationRuntime.process_turn()
          → SessionRepository.add_message()
          
Action:   append ConversationMessage to session.messages
          → _save() → atomic write to conversations.json

Durable before cognition?  YES (add_message calls _save before returning)
Evidence: conversation_runtime.py, repository.py line 114-140
```

### C-04: Cognition Context

```
STEP CM00-TEXT-04: assemble cognitive context

Owner:    ContextExecutionRuntime 
          → JuliaSession.process_stream(user_text, ctx.history, ...)
          
ctx.history comes from: ConversationRuntime.begin_turn_streaming()
          → loads canonical messages from SessionRepository

Evidence: conversation_routes.py lines 99-164 (_stream_turn)
Risk:     UNKNOWN — need to verify ctx.history includes full canonical
          or is limited by get_history(max_messages=N)
```

### C-05: Assistant Commit

```
STEP CM00-TEXT-05: commit assistant response

Owner:    ConversationRuntime.commit_streaming_turn()
          → SessionRepository.add_message() for assistant

Durable on return?  YES
Evidence: conversation_routes.py line 149
```

---

## CM00-D — VOICE TURN REALITY

### D-01: ASR Final → S2S → Brain

```
STEP CM00-VOICE-01: Voice turn delivery

S2S       speech-to-speech → HTTP POST /v1/chat/completions
          { conversation_id, messages: [full S2S Chat history], 
            turn_id, modality: "voice", stream: true }

Brain     openai_compat.py chat_completions()
          → extracts user_text from last message
          → IF conversation_id present: 
              → native_stream(user_text, conversation_id, turn_id, modality)
              → external_history IGNORED
          → ELSE:
              → legacy path: prepare_voice_turn() with external_history

Evidence: openai_compat.py lines 38-93
Risk:     voice_api/conversation_routes.py native_stream assembles context
          from Core canonical. Live workspace turns not yet in Core are
          invisible to LLM.
```

### D-02: VoiceWorkspace Dual Authority

```
STEP CM00-VOICE-02: VoiceWorkspace as shadow history

Location: Julia-Voice-S2S/frontend/voice-workspace.js
Role:     Tracks completed voice turns:
          - user_content (final STT)
          - assistant_content (response transcript)
          - turn_id, modality, status, timestamps

When does it hold completed turns NOT in Core?
          From FINAL STT → until flush completes.
          In rapid switching, this window is human-perceptible.

Evidence: voice-workspace.js onUserTranscript, onResponseFinished,
          exportDelta, markCommitted
```

### D-03: S2S Chat as Cognitive History Source

```
STEP CM00-VOICE-03: S2S Chat role

Location: speech-to-speech library (PyPI 0.2.12), Chat class
Content:  Multi-turn semantic history including:
          - input_audio placeholders (after compact_audio_history)
          - STT transcripts
          - assistant response text
          - system instructions

Sent to Brain as: messages[] in /v1/chat/completions request
Brain treatment:  IGNORED when conversation_id present (C1B-V path)
                  USED when conversation_id absent (legacy path)

Risk:     If Brain path changes, S2S Chat could become de-facto
          cognitive history authority for voice turns.
```

### D-04: Voice Bootstrap / Flush Cycle

```
STEP CM00-VOICE-04: Bootstrap from Core

When:     Electron enters Voice mode
          → bootstrapVoiceWorkspace()
          → syncConversationMessages() → Core GET
          → selectBootstrapWindow(canonical messages)
          → sendVoiceWorkspaceRequest('julia.voice.workspace.bootstrap')
          → voice frontend doStart() with bootstrapMessages
          → S2S seedConversationHistory(bootstrapMessages)

Evidence: app.js lines 343-361, main.js handleHostMessage

STEP CM00-VOICE-05: Flush to Core

When:     Electron exits Voice mode
          → flushVoiceWorkspace()
          → sendVoiceWorkspaceRequest('julia.voice.workspace.flush')
          → voiceWorkspace.exportDelta()
          → textClient.commitExternalTurns()
          → SessionRepository.append_external_turns_atomic()
          → syncCanonicalConversation()

Evidence: app.js lines 363-398
```

---

## QUICK REFERENCE — Container Reality

```
REPOSITORY               PATH                                               SESSIONS   AUTHORITY
──────────────────────────────────────────────────────────────────────────────────────────────
SessionRepository        julia_ai_assistant/data/conversations.json         38         CANONICAL
SessionStore             ~/.julia/sessions.json                            31         LEGACY METADATA  
Electron cache           .../julia-conversations-v1.json                   4          PROJECTION
VoiceWorkspace           in-memory (voice iframe)                          N/A        RUNTIME (shadow)
S2S Chat                 in-memory (speech-to-speech lib)                  N/A        PROVIDER STATE
Core test data           julia_core/data/conversations.json                2          TEST/LEGACY
Startup transcripts      memory/conversations/transcripts.jsonl            N/A        READ-ONLY BOOTSTRAP
```

---

*CM00 REALITY MAP — CONTINUES IN CM00-E (Switch/Restart) and CM00-F (Context/Compact)*
