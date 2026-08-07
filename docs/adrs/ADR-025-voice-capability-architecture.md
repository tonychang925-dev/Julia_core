# ADR-025: Julia Voice Capability Architecture v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**Supersedes:** ADR-004 (Voice Provider Boundary)

## Core Principle

Julia Core never processes media.
Voice Runtime transforms media into experience events.
Client = Body. WebRTC = Neural Transport. Gateway = Brain Stem.

## Three-Layer Boundary

### Layer 1 — Client Body
Responsible: microphone, speaker, camera, UI.
Must NOT know: ASR, TTS, Memory, Identity.

### Layer 2 — Media Capability Runtime
Responsible: WebRTC, codec, VAD, ASR, TTS, Interrupt.
Input: Audio Stream → Output: `client.voice.final` event.
Output: `speech.request` → TTS → Audio Track → Client Speaker.

### Layer 3 — Julia Core
Receives: `{"type":"message.input","source":"voice","text":"..."}`
Core unchanged: Identity → Relationship → Memory → Reasoning → Response.

## Event Namespace v1.0 (Frozen)

### Client Events (Body → Core)
- `client.voice.started` — microphone activated
- `client.voice.partial` — streaming partial transcript
- `client.voice.final` — final transcript
- `client.voice.cancelled` — recording cancelled

### Speech Events (Core → Voice Runtime → Client)
- `speech.request` — Core requests TTS
- `speech.started` — TTS playback begins
- `speech.chunk` — audio chunk
- `speech.completed` — playback done
- `speech.cancelled` — interrupted

### Runtime Events (Core → Client)
- `runtime.presence.changed` — Julia's cognitive state
- `runtime.assistant.chunk` — streaming response
- `runtime.assistant.completed` — response complete

## VoiceSession Model

```json
{
  "id": "voice_xxx",
  "client_type": "electron",
  "transport": "ws",
  "language": "zh-CN",
  "state": "listening"
}
```

## Interrupt Architecture

Julia speaking → User starts speaking → VAD detects → Stop TTS → Cancel generation → Switch to LISTENING → Process new input.

## Provider Abstraction

```
Voice Capability
├── Local Provider (Whisper + Edge TTS)
└── Cloud Provider (WebRTC + GPU Cluster)
```
