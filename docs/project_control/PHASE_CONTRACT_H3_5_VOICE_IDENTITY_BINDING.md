# Phase Contract — H3.5 Julia Voice Identity Binding

Status: COMPLETE / APPROVED at Edge TTS Service MVP scope
Phase Code: H3.5
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H3 Voice Output Pipeline — browser MVP COMPLETE / APPROVED

## 1. Objective

Replace browser-default `speechSynthesis` as the primary Julia voice output with a Julia-owned Voice Service using Edge TTS, so the client voice is consistent with the previous julia_agent voice pipeline.

## 2. Architecture

```text
Julia Response Text
  ↓
Julia Voice Service
  ↓
VoiceProfile
  ↓
EdgeTTSProvider
  ↓
audio/mpeg
  ↓
Client Audio Player
```

## 3. VoiceProfile

Default:

```json
{
  "voice_id": "julia.voice.v1",
  "provider": "edge_tts",
  "engine": "neural",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "0%",
  "pitch": "0Hz",
  "volume": "+0%"
}
```

Environment overrides:

```text
JULIA_TTS_VOICE
JULIA_TTS_RATE
JULIA_TTS_PITCH
JULIA_TTS_VOLUME
```

## 4. API

```text
GET  /api/voice/profile
POST /api/voice/synthesize
```

Synthesize request:

```json
{
  "text": "Tony，我记得我们之前讨论过 Continuity OS。"
}
```

Response:

```text
audio/mpeg
```

## 5. Boundary

Voice is expression, not identity authority.

Forbidden:

```text
Voice → Identity mutation
Voice → Persona mutation
Voice transcript → automatic Memory write
Audio device → Continuity mutation
TTS Provider → Provider reasoning authority
```

## 6. Decision

```text
H3.5 Julia Voice Identity Binding — COMPLETE / APPROVED at Edge TTS Service MVP scope
Proceed to H5.5 Provider Stream Integration and then H6 Real Tony-Julia Collaboration Pilot
```


## 7. Environment Resolution

Edge TTS is resolved from the Python environment that starts `server.py`.

```text
No separate Voice identity state is created by installing or importing edge_tts.
The dependency is an execution adapter only.
```

Current verified runtime:

```text
/Users/admin/julia_core/.venv/bin/python -> edge_tts 7.2.8
```

Recommended startup for consistent Edge TTS output:

```bash
cd /Users/admin/julia_core
./.venv/bin/python server.py
```

If `edge_tts` is unavailable in the active Python environment, `/api/voice/synthesize` returns 503 and the browser fallback remains available.
