# ADR-028: Voice Runtime Boundary

> **Status**: Proposed  
> **Date**: 2026-08-05  
> **Depends on**: ADR-022 (Gateway Architecture), ADR-026 (Client Boundary)

---

## Decision

**Voice capture belongs to Client Capability. Voice meaning belongs to Runtime.**

```
Client owns:                  Core owns:
───────────                   ─────────
Microphone                    Conversation state
Audio buffer                  Identity
STT (speech-to-text)          Memory binding
TTS playback                  Presence state machine
Audio level                   Relationship detection
Voice UI state                Event trace
```

**Gateway is the only contract.** Core never imports Electron. Electron never imports julia_core.

---

## Event Flow

```
Electron                    Gateway                   Core
───────                     ───────                   ────
voice.started  ──────────────────────────────→   presence.changed {listening}
voice.partial  ─────────── {text:"今天"} ────→   (UI feedback only, no memory)
voice.final    ─────────── {text:"今天市场"} →   message.send → JuliaSession.chat()
                                                    ← assistant.chunk {reply}
tts.speak      ←──────────────────────────────   presence.changed {speaking}
```

## Rejected

- Core spawning STT processes → Client owns audio hardware
- Electron storing conversation state → Core owns sessions
- Electron deciding presence → Core is the state authority
- Voice events bypassing Gateway → all events go through Gateway

## Consequences

- Client can be Electron, Mobile, Robot, AR — same protocol
- Core's voice handling is client-agnostic
- TTS is a client capability (speaker is hardware)
- Audio level is a client event (microphone is hardware)
- Presence is a Core event (state is cognitive)
