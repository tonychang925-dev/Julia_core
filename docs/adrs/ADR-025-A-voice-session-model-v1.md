# ADR-025-A: VoiceSession Model v1

> **Status**: FROZEN  
> **Date**: 2026-08-05  
> **Principle**: Julia Core never processes media. Voice Runtime transforms media into experience events.

---

## 1. VoiceSession Object

```json
{
  "id": "voice_sess_abc123",
  "conversation_id": "tony-main",
  "client_id": "electron_mac",
  "transport": "webrtc",
  "codec": "opus",
  "language": "zh-CN",
  "state": "LISTENING",
  "generation_id": null,
  "speech_id": null,
  "created_at": "2026-08-05T10:30:00Z"
}
```

## 2. State Machine

```
CREATED → CONNECTING → LISTENING → PROCESSING → SPEAKING → CLOSED
                                  ↑              ↑
                                  └── INTERRUPTED ─┘
```

| State | Meaning |
|-------|---------|
| CREATED | Session allocated, no audio yet |
| CONNECTING | WebRTC handshake in progress |
| LISTENING | Mic active, ASR streaming |
| PROCESSING | voice.final received, Julia thinking |
| SPEAKING | TTS streaming to client |
| INTERRUPTED | User barge-in, cancelling gen+speech |
| CLOSED | Session ended, resources released |

## 3. Dual ID System

```
generation_id → LLM response. Cancelled on interrupt.
speech_id     → TTS output.   Cancelled on interrupt.
```

Interrupt flow: `voice.started during SPEAKING → cancel speech_id → cancel generation_id → LISTENING`

## 4. Relationship to ConversationSession

```
ConversationSession (long-term)
  │  id: "tony-main"
  │  messages, summaries, memory refs
  │
  └── VoiceSession (realtime)
       id: "voice_sess_*"
       One VoiceSession per realtime interaction.
       voice.final → message.append to ConversationSession.
```

VoiceSession is ephemeral (realtime). ConversationSession is persistent (history).
VoiceSession creates messages that ConversationSession persists.
