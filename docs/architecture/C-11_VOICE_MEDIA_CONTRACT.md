# C-11 — Voice / Media Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §17
**Depends on**: C-00 (07f0ff0), C-01 (f79db0d), C-02 (656d625), C-03 (4b1625e), C-07 (248d42b), C-08 (915bc4e), C-10 (2d99293)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
Voice is a body of Julia, not a second cognitive architecture.
```

Voice/Media = capture + render + interruption + modality transport. NOT: cognition, conversation authority, context authority, emotional authority.

## 2. Shared Logical Turn

```
Audio input → VAD/capture → ASR → normalized user content → Conversation/RuntimeTurn → Context OS → ModelProvider → response + optional ExpressiveIntent → Conversation canonicalization → TTS → audio playback
```

```
VoiceTurn ≠ new authority. Voice → same conversation_id, same turn_id semantics, same RuntimeTurn contract (C-01).
```

Forbidden: `voice_history`, `voice_context`, `voice_session_truth`, `voice_brain` as independent cognitive layers.

## 3. ASR — Perception Normalization, Not Cognition

```
ASRResult { speech_id, transcript, confidence, timing, final/interim, provenance }
```

ASR may: speech → text, language detection, timestamps, confidence. ASR must not: "Tony is actually sad", "Tony is testing Julia", "this sentence should be understood as X."

```
ASR transcription is perception normalization, not semantic cognition.
```

## 4. Interim ≠ Canonical

```
Interim ASR → presentation / local perception state
Final ASR → governed user-turn acceptance → canonical user message
```

Interim transcript must not create multiple canonical history entries before the utterance is complete.

## 5. TTS — Render, Not Emotion Authority

```
LLM cognition → semantic response → optional ExpressiveIntent → Voice mapping → TTS parameters → audio
```

ExpressiveIntent: `warm`, `gentle`, `energetic`, `serious`, `slower`, `pause`, `emphasis`. Source must be cognition output or governed stable expression prior (C-04 PersonaProjection).

Forbidden: sentiment analyzer → "Julia is sad" → override cognition.

```
Voice may render expressive meaning; Voice may not manufacture Julia's emotional meaning.
```

## 6. ExpressiveIntent ≠ Identity / Memory

Current-turn `ExpressiveIntent = gentle` means: how this turn is expressed. It is NOT: Persona changed, Julia is permanently gentle, Julia's canonical emotion = gentle, Memory = Julia felt gentle — unless subsequent governance processes determine otherwise.

## 7. Barge-In — Three Distinct Events

```
User speech detected    ≠ playback cancelled
Playback interrupted    ≠ cognition/turn cancelled
Cognition/turn cancelled ≠ canonical assistant deleted
```

TTS playing → user starts speaking → playback cancelled. This does NOT automatically: cancel model generation, delete canonical assistant message, erase the turn. Transport interruption ≠ history mutation.

## 8. Emitted-Content Boundary

```
GeneratedText        — model produced
SpokenTextCommitted  — passed to TTS
AudioBuffered        — TTS synthesized
AudioPlayed          — speaker actually rendered
```

C-02 `interrupted` canonical assistant: content = actually emitted, not full generated text. C-11 defines the media-grounded commit boundary. Model generated 100 chars, TTS synthesized 80, speaker played 45 → canonical `interrupted` content is grounded in what was actually emitted. NOT simply model output. NOT simply TTS input.

Logical concept: `emitted_content_boundary` with states `not_spoken`, `partially_spoken`, `fully_spoken`. Specific byte/character alignment left to implementation.

## 9. TTS Completion ≠ Assistant Completion

```
Cognitive completion    — model finished generating
Media synthesis completion — TTS finished synthesizing
Playback completion     — speaker finished playing
```

Three distinct lifecycles. Voice must not conflate them into a single RuntimeTurn state.

## 10. Native S2S — Constrained

Native realtime speech-to-speech (audio in → provider realtime model → audio out) must still observe: Conversation authority (C-02), Context OS authority (C-03), Capability authorization (C-08), Identity/Memory/Continuity, canonical turn semantics.

```
Native S2S may optimize transport and inference.
It cannot create a second Julia runtime.
```

## 11. Native S2S — Transcript Requirement

Even with direct speech-in/speech-out, canonical observable artifacts must be preserved: recognized user content, assistant semantic content, turn identity, timing/provenance, interruption state. NOT solely: audio session blob. Without these, C-02 Conversation and subsequent Memory/Context cannot function.

## 12. Voice Context — Must Obey C-03

Forbidden: `voice_bootstrap`, `voice_history[-N:]`, S2S-specific persona, realtime-provider hidden history as independent context sources.

Correct: Context OS → CognitiveContextPackage → Alignment → S2S/Voice-capable ModelProvider. Voice handles modality encoding only.

## 13. Presence — Execution State Only

`LISTENING`, `TRANSCRIBING`, `PROCESSING`, `SPEAKING`, `INTERRUPTED`, `IDLE` — media/runtime presence. Not Julia psychological state. "Julia is thinking..." as UX text is acceptable; protocol truth is only: generation active.

## 14. Media Session ≠ Conversation Session

WebRTC session, audio device session, provider realtime session, TTS connection → transport/media handles. They may disconnect and reconnect. `media_session_id` changes; `conversation_id` and `turn_id` remain governed by Core canonical semantics.

## 15. Media Retry — No New Turns

ASR retry → must not duplicate user message. TTS retry → must not create second assistant message. Playback retry → must not imply Julia said a new thing. Media retry references original: `turn_id`, `message_id`, `speech_id`. Not a new cognition turn.

## 16. Audio Provenance

```
speech_id, conversation_id, turn_id, message_id
ASR provider/model, TTS provider/voice
timestamps, interruption state, source modality
```

Raw audio long-term retention is a privacy/retention policy decision, not automatic Memory.

## 17. Media Retention ≠ Memory

Audio recording, ASR transcript, TTS artifact, waveform → not automatic Memory. Canonical semantic transcript → Conversation (C-02). Meaningful experience → Memory governance (C-05). Raw media → media retention policy. Three separate concerns.

## 18. Voice Error Taxonomy

```
InputDeviceUnavailable, ASRUnavailable, ASRFailed, ASRLowConfidence
TTSUnavailable, TTSFailed, PlaybackFailed, PlaybackInterrupted
MediaDisconnected, RealtimeSessionFailed, UnsupportedAudioFormat
```

Infrastructure/media failures. Not: Julia didn't hear you emotionally, Julia refused to speak, Julia forgot.

## 19. Voice Tool Calls — Normalize Through C-08

Voice user turn → LLM → CapabilityRequest → C-08 → ToolResult → Context OS → LLM → speech response. No `VoiceToolRouter` with direct execution. Native realtime provider tool calls must normalize through C-08.

## 20. Electron GAP-2 — Contractually Resolved

C-02: canonical interrupted assistant with `emitted_content_boundary`. C-10: Client must not filter canonical interrupted content. C-11: `emitted_content_boundary` defines what was actually emitted.

Combined: canonical interrupted assistant + emitted-content boundary → must remain representable to Electron. Codex has sufficient specification to implement the rendering fix.

## 21. Core Architecture Diagram

```
Microphone → Capture/VAD → ASR → Normalized User Input
                                         ↓
                              ═══════════════════════
                                   JULIA CORE
                              Conversation → Runtime → Context → LLM
                                         ↓
                              response + ExpressiveIntent
                              ═══════════════════════
                                         ↓
                              Voice Mapping → TTS → Playback
                                                   │
                                              barge-in / stop
                                                   │
                                          media interruption event
```

Voice does not penetrate Core's canonical boundaries. The horizontal line is the C-11 contract boundary.

## 22. Forbidden Claims

```
❌ Voice = second cognition architecture
❌ ASR interprets semantic intent
❌ Voice owns history / Context / continuity
❌ S2S provider session owns continuity
❌ TTS decides current emotion
❌ ExpressiveIntent becomes Identity state
❌ Playback interruption deletes transcript
❌ TTS completion = cognitive completion
❌ Interim ASR becomes canonical immediately
❌ Native S2S bypasses Context OS
❌ Native voice tool calls bypass C-08
❌ Media retry creates new logical turn
❌ Raw audio automatically becomes Memory
```

## 23. Acceptance Gates

- [x] Voice = media/body layer (§1)
- [x] Text/voice share RuntimeTurn semantics (§2)
- [x] ASR perception boundary frozen (§3)
- [x] Interim/final transcript semantics (§4)
- [x] Canonical user-message boundary (§4)
- [x] TTS render-only boundary (§5)
- [x] ExpressiveIntent ownership (§5-6)
- [x] ExpressiveIntent ≠ Identity/Memory (§6)
- [x] Barge-in semantics (3 distinct events) (§7)
- [x] Playback cancellation ≠ conversation deletion (§7)
- [x] Cognition/TTS/playback completion separated (§9)
- [x] Emitted-content boundary frozen (§8)
- [x] Interrupted canonical assistant semantics completed (§8, §20)
- [x] Native S2S constrained by Core authorities (§10)
- [x] Native S2S transcript/canonical requirements (§11)
- [x] Voice Context bypass prohibited (§12)
- [x] Media session ≠ Conversation (§14)
- [x] Retry/idempotency semantics (§15)
- [x] Media error taxonomy (§18)
- [x] Voice tool calls normalize through C-08 (§19)
- [x] Raw media retention separated from Memory (§17)
- [x] C-10 Electron GAP-2 fully resolved contractually (§20)
- [x] Production changes = 0

## 24. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §17
Depends: C-00, C-01, C-02, C-03, C-07, C-08, C-10
Input:   P0-A, Electron GAP-2
Output:  Binding on C-12, Electron Voice implementation

C-11 FREEZE → C-12 GO.
Codex Electron implementation HOLD → partially lifted for C-10/C-11 compliance patches.
```
