# ADR-032: Voice Provider Validation Strategy v1.0

**Status:** FROZEN
**Date:** 2026-08-05
**Source:** E3.6 Voice Reality Test Planning
**Depends on:** ADR-025 (Voice Architecture), ADR-029 (Action Execution Model), ADR-031 (Embodied Boundary)

---

## 1. Motivation

E3 Voice Runtime 完成后，最自然的冲动是接入最好的 ASR（GPU Whisper large-v3）。但这是错误的下一步。

当前需要验证的不是 ASR 精度，而是 **Runtime 闭环**：听 → 理解 → 思考 → 决定 → 说 → 被打断 → 重新听。

如果在验证 Runtime 之前引入 GPU Whisper，问题域会爆炸：模型问题、音频问题、stream 问题、显存问题、部署问题——无法区分是 Runtime 坏了还是 Provider 坏了。

## 2. Core Principle

**Runtime contract must be validated before any provider is optimized.**

```
Phase 1: Runtime Contract Validation
  ASR: simplest available provider (Google Speech / Apple Speech)
  TTS: simplest available provider (Edge TTS)
  Goal: validate the NERVOUS SYSTEM, not the ears

Phase 2: Provider Independence Verification
  ASR: swap between 2+ providers without Runtime change
  TTS: swap between 2+ providers without Runtime change
  Goal: validate ADR-031 boundary

Phase 3: Provider Optimization
  ASR: GPU Whisper / Riva / Azure
  TTS: ElevenLabs / Azure Neural
  Goal: production quality
```

## 3. Validation Tiers

### Tier 1: Runtime Contract (E3.6 — NOW)

| Test | What It Validates | Provider |
|------|------------------|----------|
| Basic Conversation | presence state machine transitions are correct | Google Speech → JuliaSession → Edge TTS |
| Memory Recall | Wake State loads identity without re-reading files | Google Speech → JuliaSession |
| Interrupt | speech.cancelled fires, no old chunk after new question | Google Speech → JuliaSession → Edge TTS |
| Latency | voice.final → first token <2s, speech.request → first audio <1s | Google Speech → JuliaSession → Edge TTS |

**Pass criteria:**
- All presence state transitions follow the state machine (no invalid transitions)
- Interrupt produces `speech.cancelled` within 300ms on localhost
- New question never receives chunks from old question
- Memory recall uses Wake State (session continuity), not file re-reading

### Tier 2: Provider Independence (E4.x)

| Test | What It Validates |
|------|------------------|
| ASR Provider Swap | Switch Google Speech → Apple Speech → Whisper CPU without Runtime change |
| TTS Provider Swap | Switch Edge TTS → system `say` → ElevenLabs without Runtime change |
| Simultaneous Swap | Swap both ASR and TTS in a single session without session loss |

**Pass criteria:**
- JuliaSession.chat() behavior is identical regardless of provider
- No provider-specific code in cognitive path
- Session continuity preserved across provider swaps

### Tier 3: Provider Performance (E4.x+)

| Test | What It Validates |
|------|------------------|
| ASR Accuracy | WER comparison across providers |
| TTS Naturalness | A/B listening tests |
| Latency Budget | End-to-end latency under production load |
| GPU Utilization | Whisper throughput, memory, scaling |

## 4. Provider Interface Contract

ASR and TTS providers MUST implement the same interface so Core never knows which provider is active:

```python
# ASR Provider Interface
class ASRProvider:
    async def start(self) -> None: ...
    async def feed_frame(self, frame) -> None: ...
    async def stop(self) -> str: ...       # returns final transcript
    async def transcribe(self, pcm: bytes) -> str: ...  # one-shot

# TTS Provider Interface
class TTSProvider:
    async def synthesize(self, text: str, emotion: str) -> bytes: ...  # returns audio
    async def stream(self, text: str, emotion: str) -> AsyncIterator[bytes]: ...
```

## 5. E3.6 Provider Choice

### Recommended: Google Speech Recognition

```
Pros:
  - Zero setup (speech_recognition library already in use)
  - zh-CN support verified
  - No GPU needed
  - Latency ~500ms (acceptable for Runtime validation)

Cons:
  - Requires internet
  - Rate limited (not for production)
```

### Alternative: Apple Speech

```
Pros:
  - On-device (zero latency, no network)
  - Privacy-preserving
  - Free, unlimited

Cons:
  - macOS-only
  - Python binding less mature (PyObjC required)
  - Need to test zh-CN accuracy
```

### NOT recommended for E3.6: GPU Whisper

```
Reason:
  - Adds deployment complexity (model download, CUDA, VRAM)
  - Runtime bugs become indistinguishable from model bugs
  - Provider optimization before Runtime validation = wrong order
```

## 6. Upgrade Path

```
E3.6: Google Speech (Runtime Validation)
  │
  ▼
E4.x: Add Apple Speech Provider (Provider Independence proof)
  │
  ▼
E4.x: Add Whisper CPU tiny Provider (Provider swap test)
  │
  ▼
E4.x+: GPU Whisper Provider (Production ASR)
```

## 7. Contract

1. **Never optimize a provider before validating the Runtime contract.**
2. **Core NEVER imports provider-specific code.** Provider selection is Gateway configuration.
3. **Provider swap MUST be possible without session loss.** Julia's identity and memory survive provider changes.
4. **E3.6 test scripts MUST produce machine-verifiable pass/fail, not manual judgment.**
