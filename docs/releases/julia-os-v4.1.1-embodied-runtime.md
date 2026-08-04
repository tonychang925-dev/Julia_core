# Julia OS v4.1.1 — Embodied Runtime

**Tag:** `julia-os-v4.1.1-embodied-runtime`
**Date:** 2026-08-04
**Status:** Code Freeze — 24h Endurance Pending

## Objective

Give Julia a body. Extract voice I/O from web frontend into a standalone daemon with direct hardware access. Establish the Event Protocol as the nervous system bus for all future interfaces.

## Architecture

```
                    Julia OS v4.1.1

                         LLM
                          |
              Julia Cognitive Core
                          |
                 Event Gateway :9000
                          |
        =================================
              Julia Event Protocol v1.0
        =================================

              ↑              ↑

      Voice Daemon        (Electron v4.2)
      身体层                (未来)
```

## Key Decisions

1. **Voice Daemon is independent** — Python daemon with direct hardware access. No browser. No Chromium. No MediaRecorder.

2. **Event Gateway as nervous system bus** — Single WebSocket endpoint (:9000) for all body interfaces. Voice, Electron, future mobile/robot all connect here.

3. **Electron is postponed** — Body first, face later. The correct order for Personal AI.

4. **TTS moved to Voice Daemon** — Runtime says WHAT to say, Voice Daemon controls HOW it sounds. Brain/Body separation.

5. **Presence Manager** — 6 states (sleeping/idle/listening/thinking/speaking/away). Single source of truth for "what Julia is doing".

## Files

### voice_daemon/ (23 files)
```
voice_daemon/
├── main.py                    # Daemon entry point
├── config.yaml + config.py    # Configuration
├── audio/
│   ├── microphone.py          # Direct hardware (sounddevice)
│   ├── stream.py              # Buffered audio recorder
│   ├── player.py              # Speaker output (afplay)
│   └── device.py              # Device enumeration
├── wakeword/detector.py       # "婉婉" wake word detection
├── vad/silero.py              # Silero VAD + SpeechDetector
├── stt/whisper_client.py      # GPU Whisper via curl
├── tts/elevenlabs.py          # ElevenLabs emotion-aware TTS
├── transport/
│   ├── protocol.py            # Julia Event Protocol v1.0 (20 events)
│   └── websocket.py           # WebSocket client (async + sync)
└── presence/
    ├── manager.py             # 6-state state machine
    └── journal.py             # Body state log (~/.julia/presence/)
```

### julia_core/
```
julia_core/event_gateway.py    # WebSocket server :9000
```

### LaunchAgents
```
~/Library/LaunchAgents/
├── com.julia.runtime.plist    # Event Gateway daemon
└── com.julia.voice.plist      # Voice Daemon daemon
```

## Julia Event Protocol v1.0

20 events across 9 categories:

| Category | Events |
|---|---|
| lifecycle | `runtime.started`, `runtime.stopped` |
| voice | `voice.wake`, `voice.listening`, `voice.final`, `voice.cancel`, `voice.state` |
| cognitive | `thinking.started`, `thinking.completed` |
| tool | `tool.started`, `tool.completed` |
| assistant | `assistant.reply` |
| tts | `tts.speak`, `tts.cancel`, `tts.finished` |
| memory | `memory.event` |
| presence | `presence.changed` |
| transport | `heartbeat`, `heartbeat.ack`, `error` |

## Validation

### Test 1: Full Perception→Cognition→Expression→Recovery Closed Loop

| Test | Result | Notes |
|---|---|---|
| 1-A Cold Start | ✅ | `runtime.started` v4.1.1 |
| 1-B Wake | ✅ | `voice.wake(activate)` → `presence.changed(listening)` |
| 1-C Short Speech | ✅ | Full chain: 3101ms (thinking→reply→TTS) |
| 1-D Tool Call | ✅ | Weather query via LLM knowledge |
| 1-E Continuity | ✅ | Turn 2 "那明天呢？" understood context |
| 1-F Personality | ✅ | Julia identity preserved — not generic template |

### Test 2: Interrupt

| Test | Result | Notes |
|---|---|---|
| Interrupt | ✅ | `tts.cancel` ×2, `presence.changed(idle)` |
| Post-interrupt | ✅ | Recovery works, conversation continues |

### Hardware

| Component | Status | Latency |
|---|---|---|
| Whisper GPU | ✅ | 162ms ping, 516ms STT |
| ElevenLabs TTS | ✅ | 13836 bytes synthesis |
| MacBook Mic | ✅ | sounddevice 0.5.5 |

## Pending

- 24h endurance test (4 scenarios × 4 metrics)
- Reliability hardening (auto-recovery, error handling)
- git tag after endurance passes

## Evolution

```
7/23  Identity     (Persona Prompt)
8/2   Memory       (Narrative Identity)
8/3   Cognition    (Continuity Runtime)
8/4   Capability   (Personal OS v4.0)
8/4   Body         (Embodied Runtime v4.1.1)  ← current
```

Each layer extends the previous. None rewrites.
```
