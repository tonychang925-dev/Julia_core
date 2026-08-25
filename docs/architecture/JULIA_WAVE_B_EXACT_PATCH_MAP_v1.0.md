# Julia Wave B — Exact Patch Map v1.0

**Status:** RMD-3A RELEASED / RMD-3B+ HOLD  
**Date:** 2026-08-11  
**Code mutation:** RMD-3A AUTHORIZED BY TONY 2026-08-11; RMD-3B/RMD-3G/RMD-4+ NOT AUTHORIZED  

# 1. RMD-3A — Current Live S2S Session Identity → CRT

## Production objective

```text
Electron active conversation_id
→ current Voice bootstrap
→ VoiceWorkspace.conversationId
→ S2sWsRealtimeClient session metadata
→ deployed S2S ChatCompletions handler
→ Brain /v1/chat/completions JSON conversation_id
→ existing Brain native CRT branch
→ ConversationRuntime
→ Context OS
```

No semantic history transfer. No parallel cognition request.

## Repo: julia_electron

**RMD-3A production mutation:** `0 expected`

Reason: Electron already supplies `conversationId` in the current Voice bootstrap. Keep transitional payload until RMD-4, but semantic `messages[]` / `baseLastMessageId` must have zero cognitive authority.

## Repo: Julia-Voice-S2S — frontend

### File 1
`frontend/main.js`

Authorized function after GO:
`doStart()` only, plus strictly necessary adjacent option typing/wiring.

Change intent:

```text
voiceWorkspace.conversationId
→ S2sWsRealtimeClient option/session identity
```

Do NOT modify ASR/TTS/VAD, transcript persistence, tools, audio, or UI behavior.

### File 2
`frontend/ws/s2s-ws-client.js`

Authorized units after GO:

```text
WsClientOptions identity field/typing
S2sWsRealtimeClient constructor storage if necessary
_sendSessionUpdate()
```

Change intent:

```text
if conversation_id is bound:
  session.metadata = { conversation_id: ... }
```

Do not send history. Do not add a second Brain HTTP request.

## Repo: Julia-Voice-S2S — deployed S2S package ownership

Attested runtime:

```text
speech-to-speech==0.2.12
Python 3.10
handler class: ChatCompletionsApiModelHandler
file: /root/miniconda3/lib/python3.10/site-packages/
      speech_to_speech/LLM/chat_completions_language_model.py
pre-change SHA256:
4aef412253731a83f649bc79895e233faafc0874638e5efc923a44a49d56e90a
```

Authorized deployed-source units after GO:

```text
ChatCompletionsApiModelHandler._generate()
+ strictly necessary request-building helper in same file
```

Change intent:

```text
turn.runtime_config.session.metadata.conversation_id
→ dynamic outbound chat-completions JSON field conversation_id
```

A repo-owned reproducible patch/overlay and SHA verification/rollback script are required. Final state may not depend on an undocumented hand-edited site-packages file.

## Repo: Julia-AI-Assistant

**RMD-3A production mutation:** `0 expected`

Required regression/integration proof only:

```text
/v1/chat/completions + conversation_id
→ native conversation route
→ ConversationRuntime
```

## Repo: Julia_core

**RMD-3A production mutation:** `0 expected`

Regression only: INV-01..08 + native integration invariants.

# 2. RMD-3A cancellation rule

Current deployed S2S source: `MARKS_STALE_ONLY`.

Initial RMD-3A MUST NOT add speculative cancellation redesign.

RMD-3G must prove:

```text
real barge-in
→ S2S stops active generation
→ active Brain HTTP stream terminates
→ Brain async stream gets cancellation
→ CRT.cancel_streaming_turn(ctx)
→ accepted user stays completed
```

If the HTTP stream remains active, STOP and open a separate `RMD-3A-CANCEL` amendment.

# 3. RMD-3B — Brain Legacy Voice HTTP → CRT

**Repo:** Julia-AI-Assistant

Primary unit previously mapped by Codex:

```text
JuliaCoreAdapter.stream_response()
current: prepare_voice_turn() + direct provider + legacy session.history
target: ConversationRuntime begin/commit/cancel lifecycle
```

Disposition:

```text
prepare_voice_turn ownership on legacy Voice route    SUPERSEDE
direct provider cognition on legacy Voice route      RETIRE FROM ROUTE
legacy session.history semantic authority             RETIRE FROM ROUTE
route/SSE external compatibility                      KEEP initially
```

Before mutation: re-attest exact Brain branch/HEAD/worktree and authorized file path.

# 4. Release order

```text
Tony WAVE B GO — RMD-3A ONLY (2026-08-11)
→ RMD-3A only
→ local/unit/integration tests
→ controlled live deployment
→ prove conversation_id reaches CRT
→ RMD-3B release
→ RMD-3G single-path live causal gate
→ only on PASS: RMD-4 retirement
```

# 5. Explicit HOLD

```text
RMD-4 workspace/bootstrap retirement       HOLD
RMD-4 legacy code deletion                 HOLD
RMD-4V                                    HOLD
RMD-5~8                                   HOLD
ASR/TTS/VAD changes                        HOLD / not planned
new proxy/middleware                       REJECT / not planned
parallel frontend cognition POST           REJECT
semantic history transfer                  REJECT
```
