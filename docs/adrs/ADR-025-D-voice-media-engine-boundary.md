# ADR-025-D: Voice Media Engine Boundary

> **Status**: FROZEN  
> **Date**: 2026-08-05  
> **Principle**: Voice Runtime owns the audio device lifecycle. Core never touches media bytes.

---

## 1. Architecture

```
Electron UI         — renderer: buttons, text, presence
     │
Voice SDK           — getUserMedia, WebRTC, audio element
═══════════════════════════════════════════════════
Voice Runtime       — owns audio device lifecycle
     │
 ├─ Capture         — microphone, echoCancellation, AEC
 ├─ Playback        — speaker, audio routing
 ├─ VAD             — voice activity detection
 ├─ ASR Provider    — transcript output (swappable)
 └─ TTS Provider    — speech synthesis (swappable)
═══════════════════════════════════════════════════
Julia Core          — text only. Never PCM/WAV/Opus.
```

## 2. Client: Device Interface Only

Electron owns: mic handle, speaker handle, UI state.
Electron does NOT own: audio processing, VAD, ASR, TTS.

One engine manages both capture AND playback so AEC has the reference signal.

## 3. Core: Text Only

Core receives `client.voice.final {text}`. Core sends `speech.request {text}`.
Core never sees audio bytes. ADR-028 preserved.

## 4. Provider Swappability

ASR: Apple Speech → Whisper → Riva → Azure. TTS: EdgeTTS → ElevenLabs → CosyVoice.
Interface frozen: `ASRProvider.feed_audio(pcm) → text`. `TTSProvider.synthesize(text) → audio`.
