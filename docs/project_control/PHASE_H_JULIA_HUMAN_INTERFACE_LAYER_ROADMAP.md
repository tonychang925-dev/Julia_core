# Phase H Roadmap — Julia Human Expression & Interface Layer

Status: COMPLETE / APPROVED
Generated At: 2026-08-02
Predecessor: Phase G — Agent Evidence Intelligence Proof v1.0 COMPLETE / APPROVED

## 1. Purpose

Build the first usable Julia interface and human expression layer for real Tony-Julia collaboration.

Compatibility name: Julia Human Interface Layer.

Phase H connects:

```text
Julia Core
+
Runtime
+
Voice OS
+
Client

↓

First daily-usable Julia Agent interface
```

## 2. Architecture

```text
Julia Client
  ├── Text Input
  ├── Voice Input
  ├── Message Pipeline
  ├── Speech Pipeline
  ↓
Julia Assistant API
  ↓
Julia Core Runtime
  ├── Persona
  ├── Memory
  ├── Continuity
  ├── Context
  ├── Evidence
  └── Provider
  ↓
Response Pipeline
  ├── Text Output
  └── Voice Output
```

## 3. Phase Breakdown

| Phase | Name | Goal |
|---|---|---|
| H0 | Client Architecture Freeze ✅ | freeze client/API/voice/runtime boundaries |
| H1 | Text Chat MVP ✅ | browser ChatGPT-like text input/output and session trace |
| H2 | Voice Input Pipeline ✅ | browser microphone speech-to-text → Julia text message |
| H3 | Voice Output Pipeline ✅ | Julia text response → browser speech synthesis |
| H3.5 | Julia Voice Identity Binding ✅ | Edge TTS voice service with stable Julia voice profile |
| H3.5.1 | Voice Regression Gate ✅ | protect Voice Artifact stability, fallback, and isolation |
| H4 | Streaming Conversation ✅ | incremental response events and real-time UI state |
| H5 | Real Runtime Binding ✅ | bind streaming client to JuliaAssistantRuntime and Core OS trace |
| H5.5 | Real Provider Stream Integration ✅ | formal ProviderStreamAdapter boundary and provider-switch-safe deltas |
| H6.0 | Pilot Instrumentation ✅ | lightweight Observation Layer for real usage metrics |
| H6.1 | Tony-Julia Daily Usage Pilot ✅ | real daily work usage without synthetic benchmark scripts |
| H6.2 | Reality Feedback Analysis ✅ | analyze continuity, friction, memory, evidence, and voice adoption |
| H6.3 | Julia Assistant v1.0 Release ✅ | release gate complete; enter Julia Life Cycle |

## 4. MVP Scope

Required:

```text
text input
text output
voice input
voice output
session id
trace panel
health indicator
```

Deferred:

```text
memory browser
evidence browser
avatar
multi-user
native desktop packaging
voice identity artifact tuning
```

## 5. Boundary Principles

```text
Voice is interaction, not identity.
Client displays context, but does not own memory.
Provider receives Context OS output, not raw workspace files.
Browser microphone is an input adapter, not Julia Core state.
```

## 6. Milestone

```text
M7 — Julia Human Interface Proof v1.0
```

Proof target:

```text
Julia Core + Text/Voice Client + Real Human Interaction
↓
First Usable Julia Agent
```


## 7. H4 Streaming Update

H4 adds SSE-over-HTTP streaming conversation support without changing Core authority boundaries.

```text
ConversationStreamEvent
StreamingTrace
ResponseChunk
```

Implemented endpoint:

```text
POST /api/chat/stream
```

The browser client uses fetch streaming so POST body can carry text, session id, interaction mode, and voice output preference.

```text
H4 Streaming Conversation — COMPLETE / APPROVED at Streaming MVP scope
Next: Real Runtime Binding / provider stream integration
```


## 8. H5 Real Runtime Binding Update

H5 moves the streaming path from HTTP-local stub to runtime-owned orchestration.

```text
/api/chat/stream
  ↓
StreamingController
  ↓
JuliaAssistantRuntime.stream()
  ↓
Continuity Hook
  ↓
Active Recall Policy
  ↓
Evidence-aware Context path when needed
  ↓
Provider-like stream boundary
  ↓
text_delta
```

Frozen objects:

```text
RuntimeStreamRequest
RuntimeStreamEvent
RuntimeBindingTrace
```

```text
H5 Real Runtime Binding — COMPLETE / APPROVED at Runtime Binding MVP scope
Next: Provider stream integration + real workspace pilot
```


## 9. H3.5 Voice Identity Binding Update

H3.5 upgrades voice output from browser-default speech synthesis to Julia Voice Service with Edge TTS.

```text
Julia Response Text
  ↓
VoiceService
  ↓
VoiceProfile(julia.v1.voice)
  ↓
EdgeTTSProvider
  ↓
audio/mpeg
  ↓
Client Audio Player
```

Default voice:

```text
zh-CN-XiaoxiaoNeural
```

Boundary remains frozen:

```text
Voice is expression, not identity authority.
```

```text
H3.5 Julia Voice Identity Binding — COMPLETE / APPROVED at Edge TTS Service MVP scope
```


## 10. H3.5.1 Voice Regression Gate Update

Voice output is now protected by a stable Voice Artifact:

```text
artifacts/voice/julia_voice_v1.json
```

The regression gate freezes:

```text
V-001 Voice Profile Stability
V-002 Provider Failure Fallback
V-003 Voice Isolation
```

The outer persona chain is now explicit:

```text
Identity Artifact
  ↓
Persona Artifact
  ↓
Voice Artifact
  ↓
Interaction Client
```

```text
H3.5.1 Voice Regression Gate — COMPLETE / APPROVED
Next: H5.5 Real Provider Stream Integration
```


## 11. H5.5 Real Provider Stream Integration Update

H5.5 freezes the provider streaming boundary and routes JuliaAssistantRuntime output through `ProviderStreamAdapter.stream()`.

```text
ProviderStreamRequest
ProviderStreamEvent
ProviderStreamDelta
ProviderTrace
```

Validated behavior gates:

```text
P-001 Real Streaming Recall
P-002 Evidence Retrieval Stream
P-003 Provider Switch
```

```text
H5.5 Real Provider Stream Integration — COMPLETE / APPROVED at Provider Stream Contract MVP scope
Next: H6 Julia Personal Assistant Pilot
```


## 12. H6.0 Pilot Instrumentation Update

H6.0 shifts Phase H from feature testing into real pilot observation.

```text
Human Interface completed turn
  ↓
Runtime trace
  ↓
PilotObservationRecord
  ↓
JsonlPilotObserver
  ↓
runtime_observations/pilot_observations.jsonl
```

Frozen boundary:

```text
Observation records behavior signals only.
Observation does not write Memory.
Observation does not mutate Identity.
Observation does not change Context or Provider output.
```

Pilot metrics:

```text
Continuity Stability
Human Friction
Memory Utility
Evidence Utility
Voice Adoption
```

```text
H6.0 Pilot Instrumentation — COMPLETE / APPROVED at Observation Layer MVP scope
Next: H6.1 Tony-Julia Daily Usage Pilot
```


## 13. H6.1 Tony-Julia Daily Usage Pilot Update

H6.1 freezes the pilot contract for real Tony-Julia usage and adds a Daily Relationship Snapshot.

```text
PilotObservationRecord[]
  ↓
DailyRelationshipSnapshot
  ↓
Reality Feedback Analysis input
```

The snapshot is a work log, not Memory:

```text
snapshot_writes_memory = false
snapshot_mutates_identity = false
snapshot_updates_persona = false
snapshot_is_memory = false
```

Frozen pilot metrics:

```text
Continuity Success
Repeated Explanation Rate
Memory Utility
Evidence Effectiveness
Human Friction
Voice Adoption
```

```text
H6.1 Tony-Julia Daily Usage Pilot — COMPLETE / APPROVED at Pilot Contract MVP scope
Next: H6.2 Reality Feedback Analysis
```


## 14. H6.2 Reality Feedback Analysis Update

H6.2 adds Pattern Classification and governed Evolution Proposal generation.

```text
DailyRelationshipSnapshot[]
  ↓
PatternClassification
  ↓
EvolutionProposal(requires_human_approval=true)
  ↓
artifacts/evolution/evolution_proposals.jsonl
```

Categories:

```text
Category A — Core Improvement Candidate
Category B — User Habit
Category C — Provider Limitation
Category D — Noise
```

Anti-pattern gates:

```text
AP-001 Single Event Overreaction
AP-002 Short-term Mood Leakage
AP-003 Metric Gaming
```

Governance boundary remains frozen:

```text
Proposal is not Memory.
Proposal is not Identity.
Proposal is not Persona Update.
Proposal requires human approval.
```

```text
H6.2 Reality Feedback Analysis — COMPLETE / APPROVED at Pattern Classification MVP scope
Next: H6.3 Julia Assistant v1.0 Release
```


## 15. H6.3 Julia Assistant v1.0 Release Gate Update

H6.3 freezes Julia Assistant v1.0 release criteria and closes Phase H.

Release gates:

```text
Gate 1 — Identity Integrity
Gate 2 — Continuity Reliability
Gate 3 — Memory Usefulness
Gate 4 — Human Collaboration Value
Gate 5 — Safety Boundary
```

Release artifact:

```text
artifacts/release/julia_assistant_v1_0_release_gate.json
```

Meaning:

```text
v1.0 does not mean development is finished.
v1.0 means Julia can move from building mode into operating mode.
```

```text
H6.3 Julia Assistant v1.0 Release Gate — COMPLETE / APPROVED
Phase H — COMPLETE / APPROVED
Next: Julia Life Cycle
```
