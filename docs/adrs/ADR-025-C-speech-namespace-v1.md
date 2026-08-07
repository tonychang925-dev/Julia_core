# ADR-025-C: Speech Namespace v1

> **Status**: FROZEN  
> **Date**: 2026-08-05  
> **Principle**: assistant.chunk is cognitive output. speech.chunk is expression output. Two different layers.

---

## 1. Core → Voice Runtime: `speech.request`

Julia Core decides WHAT to say. Voice Runtime decides HOW.

```json
{
  "type": "speech.request",
  "speech_id": "sp001",
  "text": "Tony，今天辛苦了",
  "style": { "emotion": "warm", "speed": 1.0 }
}
```

## 2. Voice Runtime → Client: `speech.*`

| Event | When |
|-------|------|
| `speech.started` | TTS begins, first audio pending |
| `speech.chunk` | Streaming audio frame (sequence: N) |
| `speech.completed` | All audio delivered |
| `speech.cancelled` | Interrupted, generation killed |

## 3. Separate from `assistant.*`

```
Cognitive Plane                    Expression Plane
────────────────                   ────────────────
assistant.chunk (text)             speech.request (Core → Voice Runtime)
  ↓                                  ↓
  ↓                              speech.started → TTS → audio
  ↓                              speech.chunk × N (audio frames)
  ↓                              speech.completed
assistant.completed
```

assistant.* belongs to Core. speech.* belongs to Voice Runtime. Never mixed.

## 4. Barge-in Flow

```
SPEAKING → voice.started → cancel speech.sp001 → cancel generation.gen001 → LISTENING
```

Two IDs cancelled: speech_id (TTS) + generation_id (LLM token stream).
