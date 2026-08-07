# ADR-025-B: Julia Runtime Event Namespace v1

> **Status**: FROZEN  
> **Date**: 2026-08-05  
> **Principle**: Three namespaces. Never confused.

---

## 1. `client.*` — Body Events

What the body (Electron, Mobile, Robot) produces. Core never produces client events.

| Event | Payload | When |
|-------|---------|------|
| `client.voice.started` | `{language, codec}` | Mic pressed |
| `client.voice.partial` | `{text}` | Streaming ASR |
| `client.voice.final` | `{text}` | Final transcript |
| `client.connected` | `{type, version}` | Client joins |
| `client.disconnected` | `{}` | Client leaves |

## 2. `runtime.*` — Cognitive Events

What Julia's mind produces. Client renders, never produces.

| Event | Payload | When |
|-------|---------|------|
| `runtime.presence.changed` | `{state, phase?}` | Any state transition |
| `runtime.action.started` | `{action, params}` | Tool call begins |
| `runtime.action.completed` | `{action, result}` | Tool call ends |
| `runtime.memory.recalled` | `{refs}` | Memory accessed |
| `runtime.assistant.chunk` | `{text, index}` | Streaming response |
| `runtime.assistant.completed` | `{turn, topic}` | Response done |
| `runtime.error` | `{code, message}` | Any error |

## 3. `speech.*` — Expression Events

Core requests speech. Client renders audio. Transport is a separate concern.

| Event | Payload | When |
|-------|---------|------|
| `speech.request` | `{text, emotion, prosody}` | Core wants TTS |
| `speech.started` | `{speech_id}` | TTS begins |
| `speech.chunk` | `{speech_id, audio_base64?}` | Streaming audio |
| `speech.completed` | `{speech_id}` | TTS done |
| `speech.cancelled` | `{speech_id, reason}` | Interrupted |

## 4. One Interaction = Three Namespaces

```
Client:   client.voice.started → client.voice.partial → client.voice.final
Runtime:  runtime.presence.changed(LISTENING) → presence.changed(PROCESSING) →
          runtime.assistant.chunk → runtime.assistant.completed
Speech:   speech.request → speech.started → speech.completed
```

Namespaces never mix. Client never produces runtime events. Runtime never produces client events.
