# ADR-025-D: Julia Voice Runtime Split Architecture v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**Source:** E3.6 Local Voice Reality Test — echo root cause → architectural boundary correction
**Depends on:** ADR-025 (Voice Architecture), ADR-028 (Media Boundary), ADR-031 (Embodied Boundary)
**Supersedes:** ADR-025-D (Audio Ingress Boundary v1.0) — replaced by this document

---

## 1. Motivation

E3.6 测试中发现 Julia "听到自己说话"的回声问题。初始修复尝试在 Client 端加 timer/mute
patch（TTS 播放时静音、播放后延迟恢复），这违反了 ADR-025 定义的边界。

深入分析后发现一个关键事实：

**麦克风和扬声器都在客户端。只有客户端同时持有 input signal 和 output reference signal。**
服务器永远拿不到扬声器实际播放的音频，因此服务器端回声消除从根本上就不完整。

ChatGPT Voice 等成熟产品之所以"听不到自己说话"，不是因为服务器端 ASR 做得好，
而是因为客户端正确处理了音频。

这要求 Voice Runtime 拆分为两个层：

## 2. Core Principle

**Principle 1: Real-time audio processing belongs to the body (Client).**

Client owns: microphone capture, speaker playback, audio reference, echo cancellation,
noise suppression, VAD, interruption detection.

**Principle 2: Julia Core never sees audio bytes.**

禁止 PCM、WAV、Opus、AudioFrame、WebRTC Track 进入 Julia Core。
Core 只接受 `{type: "message.input", source: "voice", text: "..."}`.

**Principle 3: Voice Runtime is split into Client and Server.**

Client = body reflexes (fast, hardware-adjacent).
Server = language understanding (ASR/TTS providers, speech protocol).

## 3. Split Architecture

```
                         Julia OS

              ┌──────────────────────────────┐
              │     COGNITIVE PLANE           │
              │                                │
              │  Julia Core                    │
              │  Identity / Memory / Experience│
              │  Relationship / Reasoning       │
              │                                │
              │  NEVER: PCM, AudioFrame, Opus │
              └──────────────┬─────────────────┘
                             │
                    client.voice.final (text)
                    speech.request (text)
                             │
              ┌──────────────┴─────────────────┐
              │   RUNTIME GATEWAY               │
              │                                  │
              │  WebSocket Event Plane           │
              │  HTTP Command Plane              │
              │  WebRTC Signaling                │
              └──────────────┬───────────────────┘
                             │
                    WebSocket (events)
                    WebRTC (signaling only)
                             │
              ┌──────────────┴───────────────────┐
              │   VOICE RUNTIME SERVER            │
              │                                    │
              │  ASR Provider Interface            │
              │  TTS Provider Interface            │
              │  Speech Protocol (speech.*)        │
              │  EchoFilter (defense layer only)   │
              │                                    │
              │  DOES:                             │
              │  - Accept text transcripts         │
              │  - Route to JuliaSession           │
              │  - Generate speech events          │
              │  - Provider management             │
              │                                    │
              │  DOES NOT:                         │
              │  - Process raw audio               │
              │  - Handle echo cancellation        │
              └──────────────┬───────────────────┘
                             │
                    WebRTC DataChannel (events)
                    WebRTC Media (optional, future)
                             │
              ┌──────────────┴───────────────────┐
              │   VOICE RUNTIME CLIENT             │
              │   (Electron / Mobile / Robot)       │
              │                                     │
              │  Audio Graph:                       │
              │    Mic → AEC → NS → VAD → ASR       │
              │                    ↑                 │
              │              TTS Reference           │
              │                                     │
              │  Echo Guard:                        │
              │    "Is this mic input my own TTS?"  │
              │                                     │
              │  Interrupt Detection:               │
              │    "Is Tony speaking while I am?"    │
              │                                     │
              │  DOES:                              │
              │  - Capture audio                    │
              │  - Cancel echo (has both signals)   │
              │  - Detect speech boundaries         │
              │  - Detect user interruption         │
              │  - Local ASR (optional, offline)    │
              │                                     │
              │  DOES NOT:                          │
              │  - Define who Julia is              │
              │  - Reason about relationships       │
              │  - Manage memory                    │
              └──────────────┬─────────────────────┘
                             │
                        Hardware
                    Mic + Speaker
```

## 4. Why This Split Is Correct

### 4.1 Physical Reality

麦克风和扬声器是同一物理设备上的两个换能器。回声消除需要的 reference signal
（"刚才播放了什么"）只有客户端持有。任何服务器端方案都缺少这个 reference。

### 4.2 Human Analogy

人的神经系统有脊髓反射——手碰到火，缩手信号不需要传到大脑。
语音回声处理是同样的"身体反射"：判定"这是我自己的声音"不需要 Julia Core。

### 4.3 ChatGPT Voice Works Because

ChatGPT Voice 的客户端持有：
- Mic input stream
- TTS output stream (reference)
- 两个 stream 做 AEC → 干净的 user voice
- 干净的 user voice → ASR → transcript → server

不是靠服务器 ASR 聪明，是靠客户端音频管线正确。

## 5. Component Ownership

| Component | Owner | Reason |
|-----------|-------|--------|
| Microphone capture | Client | Hardware access |
| Speaker playback | Client | Hardware access |
| Echo cancellation (AEC) | Client | Has both signals |
| Noise suppression (NS) | Client | Real-time, hardware-adjacent |
| VAD | Client | Real-time, before ASR |
| Interrupt detection | Client | Voice energy during TTS playback |
| Local ASR (offline mode) | Client | Privacy, low latency |
| ASR Provider (cloud) | Server | GPU, model management |
| TTS Provider | Server | Model management |
| EchoFilter (defense) | Server | Safety net for edge cases |
| Speech Protocol | Server | speech.* events |
| Presence State Machine | Server | Runtime cognitive state |

## 6. Echo: Layered Defense

```
Layer 1 (Client, primary):
  Audio Graph: Mic → AEC(has TTS reference) → NS → VAD
  "Physical echo cancellation"

Layer 2 (Client, secondary):
  Echo Guard: compare ASR output against recent TTS transcript
  "Semantic echo rejection — did Julia just say this?"

Layer 3 (Server, defense only):
  EchoFilter: text-level similarity check on incoming transcripts
  "Safety net for edge cases, NOT the primary solution"
```

## 7. Provider Architecture

```
voice_runtime/providers/

  local/           ← Client Voice Runtime (offline, privacy)
    asr/
      whisper_cpu.py     (faster-whisper tiny, local CPU)
      apple_speech.py    (macOS native SFSpeechRecognizer)

  cloud/            ← Server Voice Runtime (production)
    asr/
      whisper_streaming.py  (faster-whisper large-v3, GPU)
      azure.py
    tts/
      edge_tts.py
      elevenlabs.py
```

## 8. Contract

1. **Client OWNS real-time audio processing.** AEC, VAD, NS, interrupt detection.
2. **Client MAY run local ASR.** Offline mode. Not the default production path.
3. **Server MUST NOT process raw audio.** Transcripts only.
4. **Server EchoFilter is a safety net, not primary defense.** Defense in depth.
5. **Core NEVER sees audio bytes.** ADR-028 holds.
6. **Client NEVER defines who Julia is.** ADR-031 holds.
7. **One Server Voice Runtime, many Client Voice Runtimes.** Electron, Mobile, Robot share the same ASR/TTS providers.
