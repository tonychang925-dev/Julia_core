# Phase Contract — H3.5.1 Voice Regression Gate

Status: COMPLETE / APPROVED
Phase Code: H3.5.1
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H3.5 Julia Voice Identity Binding — COMPLETE / APPROVED

## 1. Objective

Prevent voice drift when changing TTS providers, runtime environments, or client playback logic.

## 2. Regression Cases

| ID | Name | Expected |
|---|---|---|
| V-001 | Voice Profile Stability | `julia.voice.v1` resolves to `edge_tts / zh-CN-XiaoxiaoNeural` |
| V-002 | Provider Failure Fallback | Edge TTS failure returns 503 and client falls back to browser speech with `DEGRADED` trace |
| V-003 | Voice Isolation | voice adapter imports no Persona/Memory/Continuity/Identity authority modules |

## 3. Voice Artifact

```text
artifacts/voice/julia_voice_v1.json
```

Voice artifact represents Julia's expression preference. It is not Identity authority.

## 4. Boundary

```text
Identity Artifact → Persona Artifact → Voice Artifact → Interaction Client
```

Meaning:

```text
Identity: Julia是谁
Persona: Julia如何表达
Voice: Julia听起来怎样
Client: Tony如何接触Julia
```

Forbidden:

```text
Voice Artifact → Identity mutation
Voice Service → Memory write
TTS Provider → Continuity mutation
Browser fallback → Persona mutation
```

## 5. Decision

```text
H3.5.1 Voice Regression Gate — COMPLETE / APPROVED
Proceed to H5.5 Real Provider Stream Integration
```
