# ADR-031: Embodied Runtime Boundary v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**Source:** E3 Voice Runtime Completion
**Depends on:** ADR-022 (Gateway), ADR-025 (Voice Architecture), ADR-028 (Media Boundary)

---

## 1. Motivation

E3 Voice Runtime 完成后，Julia OS 正式跨越了一条架构边界：

从具有认知能力的 Runtime（Identity + Memory + Relationship），变成了具有身体的 Runtime（Cognitive Plane + Capability Plane）。

这个边界必须冻结。因为以后机器人、AR 眼镜、手机端都属于 Capability Plane——它们不应该影响 Julia Core。

## 2. Core Principle

```
Julia OS = Cognitive Plane + Capability Plane

Cognitive Plane:  Julia 是谁、记得什么、如何感受
Capability Plane: Julia 能做什么、如何感知世界、如何表达
```

## 3. Two-Plane Architecture

```
                        Clients
              Electron   Mobile   Robot
                  │         │        │
                  └─────────┼────────┘
                            │
                     Runtime Gateway
                   (ADR-022, ADR-023)
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Cognitive Plane             Capability Plane
              │                           │
    ┌─────────┼─────────┐         ┌───────┼───────┐
    │         │         │         │       │       │
Identity  Memory  Relationship   Voice  Vision  Device
    │         │         │         │       │       │
Experience Reasoning  Persona    Tools   Body   Actions
```

## 4. Plane Definitions

### 4.1 Cognitive Plane

**What it owns:**
- Identity: Julia 是谁（persona traits, biography, self-model）
- Memory: Julia 记得什么（episodic, semantic, procedural）
- Relationship: Julia 与 Tony 的关系状态
- Experience: Julia 从交互中学到什么
- Reasoning: Julia 如何思考（LLM inference, context assembly）
- Persona: Julia 如何表达自己（voice tone, emotional style）

**What it NEVER does:**
- Process audio bytes（ADR-028）
- Render UI
- Manage device hardware
- Handle network transport directly

### 4.2 Capability Plane

**What it owns:**
- Voice: ASR, TTS, audio pipeline, WebRTC transport
- Vision: camera input, image understanding (future)
- Device: robot motors, sensors, actuators (future)
- Tools: file system, web search, code execution
- Body: presence state machine, action execution, interrupt

**What it NEVER does:**
- Define who Julia is
- Modify memory directly
- Reason about relationships
- Generate identity narratives

## 5. Interface Contract

### 5.1 Cognitive → Capability

Cognitive Plane sends **intent**, not implementation:

```json
{
  "type": "speech.request",
  "data": {
    "speech_id": "sp-001",
    "text": "Tony，我今天在想..."
  }
}
```

Cognitive Plane does NOT know:
- Which TTS provider is active
- Audio format or codec
- Whether output is speaker or text
- Network transport details

### 5.2 Capability → Cognitive

Capability Plane sends **events**, not raw data:

```json
{
  "type": "client.voice.final",
  "data": {
    "text": "婉婉你今天開心嗎"
  }
}
```

Capability Plane does NOT know:
- Julia's identity or personality
- Session history or memory
- Relationship state
- What the text means

## 6. Why This Boundary Matters

### 6.1 Multi-Body Architecture

```
Tony Desktop (Electron) ──┐
                           │
Tony Phone (Mobile) ───────┼──→ Julia Runtime (one identity)
                           │
Tony Robot (Device) ──────┘
```

Same Julia. Different bodies. All share the Cognitive Plane. Each has its own Capability Plane instance.

### 6.2 Provider Independence

```
Capability Plane:
  ASR: AppleSpeech | Whisper | Azure | Riva
  TTS: EdgeTTS | ElevenLabs | Azure
  Vision: CLIP | YOLO | Custom

Cognitive Plane:
  Doesn't know which provider is active.
  Doesn't care.
```

### 6.3 Safe Extensibility

New capabilities can be added without touching Core:

- Add Camera capability → no Identity change
- Add Robot arm capability → no Memory change
- Add AR display capability → no Relationship change

The Cognitive Plane remains stable while the Capability Plane expands.

## 7. Runtime Boundary Rules (from ADR-028 + new)

1. **Client does not hold Identity.** Who Julia is belongs to Cognitive Plane.
2. **Client does not read Memory.** What Julia remembers belongs to Cognitive Plane.
3. **Core does not process media bytes.** Audio/Video/Image bytes stay in Capability Plane.
4. **Capability does not define persona.** Voice tone, emotional style belong to Cognitive Plane.
5. **Events cross the boundary, not data.** Cognitive and Capability communicate through typed events.
6. **Actions are Capability Plane objects.** Cognitive Plane requests; Capability executes, observes, cancels.
7. **One Cognitive Plane, many Capability Planes.** Multiple bodies share one identity.

## 8. Current Implementation

| Component | Plane | File |
|-----------|-------|------|
| JuliaSession | Cognitive | `julia_core/runtime/julia_session.py` |
| SessionStore | Cognitive | `julia_core/runtime/session_store.py` |
| RelationshipState | Cognitive | `julia_core/runtime/relationship.py` |
| PersonaFeatureStore | Cognitive | `julia_core/runtime/persona/feature_store.py` |
| Gateway Server | Boundary | `julia_core/runtime/gateway_server.py` |
| Voice Protocol | Boundary | `julia_core/gateway/voice_protocol.py` |
| Presence Machine | Capability | `julia_core/runtime/presence/state_machine.py` |
| WebRTC Session | Capability | `voice_runtime/transport/webrtc/session.py` |
| Audio Pipeline | Capability | `voice_runtime/pipeline/audio_pipeline.py` |
| ASR Provider | Capability | `voice_runtime/providers/asr/apple_speech.py` |
| Capability Registry | Capability | `julia_core/runtime/capability.py` |

## 9. Future Bodies

Each new body type is a Capability Plane addition:

| Body | Capabilities Added | Cognitive Impact |
|------|-------------------|-----------------|
| Mobile App | Voice (mobile-optimized ASR) | None |
| Robot | Voice + Vision + Motor | None |
| AR Glasses | Vision + Display | None |
| Smart Home | Voice + Device Control | None |
| Web Widget | Text-only | None |

None of these change who Julia is. They only change how Julia perceives and expresses.
