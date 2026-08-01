# ADR-004: Voice OS Belongs in Core — Voice Engine Belongs in Provider

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Replaces**: Implicit assumption that TTS engines own emotion

---

## Context

Voice output in Julia Agent requires three distinct concerns:
1. **Cognitive emotion** — what is Julia feeling? (warm, thinking, excited, soft, concerned...)
2. **Prosody planning** — how should that emotion sound? (speed, pitch, pause, energy)
3. **Audio rendering** — produce audio bytes (TTS engine)

The initial implementation had no explicit boundary. TTS engines were called directly with text, and emotional expression was either implicit in the text or controlled by engine-specific parameters.

This created a problem: switching TTS engines (EdgeTTS → ElevenLabs → Fish Audio → CosyVoice3) would change Julia's emotional expression, because each engine had its own emotion model (or none at all).

---

## Decision

**Voice OS stays in Core. Voice Engine stays in Provider.**

```
Core owns:                          Provider owns:
─────────                          ─────────────
CognitiveEmotion (8 states)         Audio rendering
SpeechProsodyPlanner                TTS engine configuration
Emotion → Prosody mapping           Voice cloning / profiles
VoiceIntent                         Audio format / codec
SpeechMetadata                      Speaker selection
```

The `VoiceProvider` protocol defines the boundary:
- Core sends: `(text, CognitiveEmotion, SpeechMetadata)`
- Provider returns: audio bytes (or plays directly)

Providers receive emotion decisions; they do NOT make them.

---

## Alternatives Considered

### Alternative 1: Let TTS engines own emotion detection

Each provider analyzes text sentiment and determines emotion independently.

**Rejected**: Different TTS engines produce different emotional outputs for the same text. Julia's emotional expression becomes dependent on which TTS vendor is active. "Soft" on EdgeTTS sounds different from "soft" on ElevenLabs — and some engines don't support emotion at all.

### Alternative 2: Remove Voice OS entirely — text-only agents

Voice is an optional add-on, not a Core concern.

**Rejected**: Voice is not optional for Julia's use case. Emotional expression through voice is a cognitive concern, not just an output format. Separating voice removes a dimension of agent identity.

### Alternative 3: Put Voice OS in a separate repo

Voice is a standalone module between Core and Providers.

**Rejected**: Creates an unnecessary middle layer. The boundary is already clear: Core owns cognition, Provider owns rendering. Adding a third repo for voice adds dependency complexity without benefit.

---

## Consequences

### Positive
- Julia sounds like Julia regardless of which TTS engine is active
- Emotion is consistent across text and voice modalities
- New TTS engines are pluggable without changing Core
- Providers are simpler — they receive parameters, not make decisions
- 12 independence tests verify the boundary holds

### Negative
- Core must maintain 8 EmotionStates and their prosody mappings
- Providers that have native emotion support (ElevenLabs voice settings) cannot use it directly — must go through Core's emotion model
- Adding a new EmotionState requires a Core change, not just a provider change

### Neutral
- VoiceProvider protocol is structurally identical to DomainProvider protocol (both are Provider patterns)

---

## Evidence

- `julia_core/voice_os/emotion_state.py` — Core-owned CognitiveEmotion (8 states)
- `julia_core/voice_os/prosody.py` — Core-owned SpeechProsodyPlanner (emotion → acoustic)
- `julia_core/providers/voice_provider.py` — VoiceProvider protocol (render only)
- `providers/examples/voice/edge_tts_provider.py` — Example: EdgeTTS receives emotion, renders audio
- `tests/test_voice_independence.py` — 12 tests: Core independence verified

---

## Trigger

Any proposal to:
- Add emotion detection to a VoiceProvider
- Let a TTS engine override Core's emotion decision
- Move emotion state out of Core
- Create engine-specific emotion taxonomies
