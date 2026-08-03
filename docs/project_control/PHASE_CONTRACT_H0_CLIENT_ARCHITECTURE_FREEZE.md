# Phase Contract — H0 Client Architecture Freeze

Status: COMPLETE / APPROVED
Phase Code: H0
Parent Phase: H — Julia Human Interface Layer
Risk Level: P0
Generated At: 2026-08-02
Predecessor: M6 Julia Agent Evidence Intelligence Proof v1.0 — COMPLETE / APPROVED

## 1. Objective

Freeze the first Human-Agent Interaction Layer boundary before daily-use pilots.

## 2. Client Boundary

```text
Browser Client
  ↓
Julia Assistant API
  ↓
Julia Core Runtime
```

Client owns:

```text
text input UI
voice input adapter
voice output adapter
session display
trace display
```

Client does not own:

```text
Persona
Memory
Continuity
Context
Evidence
Provider selection authority
```

## 3. Voice Boundary

Correct:

```text
Persona → Voice Style Request → TTS Adapter
```

Forbidden:

```text
Voice → Identity authority
Voice transcript → automatic Memory write
Audio device → Core state mutation
```

## 4. First Implementation Route

Use Web MVP first:

```text
HTML/CSS/JS
Browser SpeechRecognition for voice input when available
Browser speechSynthesis for voice output when available
FastAPI static hosting + JSON chat API
```

Desktop packaging is deferred.

## 5. Decision

```text
H0 Client Architecture Freeze — COMPLETE / APPROVED
Proceed to H1 Text Chat MVP + H2/H3 browser voice adapters
```
