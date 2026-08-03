# Phase Contract — H1-H3 Text/Voice Client MVP

Status: COMPLETE / APPROVED
Phase Code: H1-H3 MVP
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: H0 Client Architecture Freeze — COMPLETE / APPROVED

## 1. Objective

Provide the first simple ChatGPT-like Julia client with text input/output and browser-based voice input/output adapters.

## 2. Delivered MVP

```text
FastAPI root route          → serves Julia Client
/client/* static assets     → HTML/CSS/JS client
/api/chat                   → JSON chat API with trace
Browser SpeechRecognition   → voice input adapter
Browser speechSynthesis     → voice output adapter
Trace panel                 → interaction/runtime/boundary trace display
```

## 3. Files

```text
server.py
julia_core/client/__init__.py
julia_core/client/static/index.html
julia_core/client/static/app.js
julia_core/client/static/styles.css
```

## 4. Trace Contract

```json
{
  "interaction": {
    "mode": "text | voice",
    "voice_input": false,
    "voice_output_requested": true
  },
  "input": {
    "stt": "browser_speech_recognition | not_used"
  },
  "runtime": {
    "client_api": "PASS",
    "continuity": "PENDING_RUNTIME_BINDING",
    "memory": "PENDING_RUNTIME_BINDING",
    "context": "PENDING_RUNTIME_BINDING",
    "evidence": "PENDING_RUNTIME_BINDING",
    "provider": "PENDING_RUNTIME_BINDING"
  },
  "output": {
    "tts": "browser_speech_synthesis | not_requested"
  },
  "boundary": {
    "client_owns_identity": false,
    "voice_owns_identity": false,
    "client_writes_memory": false,
    "provider_reads_files": false
  }
}
```

## 5. How to Run

```bash
cd /Users/admin/julia_core
python server.py
```

Open:

```text
http://localhost:8002/
```

## 6. Acceptance

- Text input exists.
- Text output exists.
- Voice input adapter exists.
- Voice output adapter exists.
- Session id is generated client-side.
- Trace panel exists.
- Client/voice do not own Identity or Memory.

## 7. Decision

```text
H1 Text Chat MVP — COMPLETE / APPROVED
H2 Voice Input Pipeline — COMPLETE / APPROVED at browser-adapter MVP scope
H3 Voice Output Pipeline — COMPLETE / APPROVED at browser-adapter MVP scope
Proceed to H4 Streaming Conversation / real runtime binding
```
