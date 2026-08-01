# Voice OS Design v1.0

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Layer**: Interaction Layer (Layer 3)  
> **Principle**: Provider supplies capability, not cognition (P4)

---

## 1. What Voice OS Is

Voice OS answers one question:

> **"How should the agent sound right now?"**

It is a first-class Core module that owns the cognitive layer of voice: emotion, prosody, and voice intent. It does NOT own audio rendering — that belongs to external VoiceProviders.

```
Voice OS

    Core owns:                    Providers own:
    ──────────                    ─────────────
    CognitiveEmotion              Audio bytes
    SpeechProsodyPlanner          TTS engine selection
    VoiceIntent                   Voice cloning / profiles
    Emotion → Prosody mapping     Audio format / codec
```

---

## 2. Why Voice OS is in Core

Voice OS belongs in Core because **emotion is cognition, not audio engineering**.

| If Voice OS were external | Reality |
|---------------------------|---------|
| Each TTS vendor decides emotion from text | Core loses control of Julia's emotional expression |
| Switching TTS engines changes Julia's personality | Julia should sound like Julia regardless of TTS engine |
| Emotion logic duplicated per provider | Single source of truth for emotional state |
| No cognitive continuity between text and voice | Julia's tone should be consistent across modalities |

Core owns the **cognitive layer** of voice. Providers are **audio renderers** — they receive emotion decisions, not make them.

---

## 3. Voice OS Pipeline

```
Context / Intent / User Input
        │
        ▼
┌───────────────────────────────────┐
│  1. VoiceIntent                   │
│     "What does Julia want to      │
│      express through voice?"      │
│                                   │
│     Derived from:                 │
│     - Conversation context        │
│     - User emotional state        │
│     - Current cognitive mode      │
│     - Persona tone                │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  2. CognitiveEmotion              │
│     "What emotion should Julia    │
│      convey?"                     │
│                                   │
│     EmotionState (8 states):      │
│     warm / thinking / excited     │
│     soft / confident / concerned  │
│     playful / neutral             │
│                                   │
│     + intensity: 0.0 - 1.0        │
│                                   │
│     This is COGNITIVE,            │
│     not acoustic.                 │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  3. SpeechProsodyPlanner          │
│     "How should the voice sound   │
│      to convey this emotion?"     │
│                                   │
│     Emotion → Acoustic mapping:   │
│     - speed:    0.5 - 2.0         │
│     - pitch:    pitch shift       │
│     - pause:    pause duration    │
│     - energy:   0.0 - 1.0         │
│                                   │
│     Uses linear interpolation     │
│     driven by emotion intensity.  │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  4. SpeechMetadata                │
│     Frozen acoustic parameters.   │
│     Consumed by VoiceProvider.    │
│                                   │
│     speed:       0.85             │
│     pitch_shift: "+3Hz"           │
│     pause_ms:    300              │
│     energy:      0.7              │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  5. VoiceProvider                 │
│     "Render these parameters      │
│      into audio bytes."           │
│                                   │
│     speak(text, emotion, metadata)│
│     synthesize(text, ...) → bytes │
│                                   │
│     Provider does NOT:            │
│     - Decide emotion              │
│     - Override prosody            │
│     - Choose voice character      │
└───────────────────────────────────┘
```

---

## 4. Emotion States and Prosody Mapping

```python
class EmotionState(str, Enum):
    NEUTRAL    = "neutral"     # Default, unmarked
    WARM       = "warm"        # Affectionate, gentle
    THINKING   = "thinking"    # Analytical, slower
    CONFIDENT  = "confident"   # Assertive, clear
    EXCITED    = "excited"     # High energy, fast
    SOFT       = "soft"        # Intimate, quiet
    CONCERNED  = "concerned"   # Worried, careful
    PLAYFUL    = "playful"     # Teasing, light
```

Each state maps to acoustic parameters:

| Emotion | Speed | Pitch | Pause | Energy |
|---------|-------|-------|-------|--------|
| WARM | 0.85 | +3Hz | 300ms | 0.60 |
| THINKING | 0.72 | -5Hz | 500ms | 0.70 |
| CONFIDENT | 0.88 | +5Hz | 350ms | 0.80 |
| EXCITED | 1.05 | +10Hz | 200ms | 0.90 |
| SOFT | 0.75 | -3Hz | 400ms | 0.40 |
| CONCERNED | 0.78 | -2Hz | 450ms | 0.55 |
| PLAYFUL | 0.95 | +8Hz | 250ms | 0.75 |
| NEUTRAL | 0.82 | +0Hz | 300ms | 0.60 |

### Intensity Interpolation

`CognitiveEmotion.intensity` (0.0–1.0) controls the strength of the emotion:

```python
speed  = NEUTRAL_SPEED  + (emotion_speed  - NEUTRAL_SPEED)  * intensity
energy = NEUTRAL_ENERGY + (emotion_energy - NEUTRAL_ENERGY) * intensity
```

At `intensity=0.0`, all emotions render as neutral. At `intensity=1.0`, the full emotion is expressed. This allows subtle emotional shifts — "slightly warm" vs "very warm."

---

## 5. Core ↔ Provider Boundary

```
┌─── Core Boundary ───────────────────────────────┐
│                                                  │
│  CognitiveEmotion    SpeechProsodyPlanner        │
│  (8 states)          (emotion → acoustic)        │
│  intensity           speed/pitch/pause/energy    │
│                                                  │
│  Voice OS OWNS these.                            │
│  Providers RECEIVE the output.                   │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│           VoiceProvider Protocol                 │
│                                                  │
│  speak(text, emotion, metadata) → bool           │
│  synthesize(text, emotion, metadata) → bytes     │
│                                                  │
│  Providers IMPLEMENT this.                       │
│  Core CALLS this.                                │
│                                                  │
└──────────────────────────────────────────────────┘
        │
        ▼
┌───────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   EdgeTTS     │ │ ElevenLabs│ │Fish Audio│ │CosyVoice3│
│   (free)      │ │ (paid)   │ │(paid)    │ │(local)   │
└───────────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 6. VoiceProvider Protocol

```python
@runtime_checkable
class VoiceProvider(Protocol):
    """Render text → audio. Does NOT own emotion, persona, or prosody."""

    provider_id: str

    def speak(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bool:
        """Synthesize and play audio. Returns True on success."""
        ...

    def synthesize(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bytes | None:
        """Synthesize audio, return raw bytes. Returns None on failure."""
        ...
```

### Provider Responsibilities

| Provider MUST | Provider MUST NOT |
|--------------|-------------------|
| Accept text + emotion + metadata | Decide emotion from text analysis |
| Render audio bytes | Override Core's prosody decisions |
| Return success/failure | Choose voice character (profile) |
| Register via ProviderRegistry | Own the emotion-to-prosody mapping |

VoiceProvider is a **capability provider**, following the same principle as DomainProvider:

```
Domain Provider:    supplies facts        → does NOT own cognition
Voice Provider:     supplies audio bytes  → does NOT own cognition

Same pattern. Same boundary. Same governance.
```

A VoiceProvider **MUST NOT**:
- **Decide emotion** — emotion is Core's cognitive decision
- **Modify persona** — persona is compiled by Persona Engine
- **Access memory** — voice has no memory access path
- **Update context** — voice is output-only, no context side effects

---

## 7. Voice Provider Ecosystem

```
EdgeTTS (free, zh-TW-HsiaoChenNeural)
  → Zero cost, good quality, example provider in julia_core

ElevenLabs (paid, voice ID: tOuLUAIdXShmWH7PEUrU)
  → Original Julia voice, highest quality, paid credits

Fish Audio (paid, Taiwan girl voice)
  → Moderate cost, good Mandarin quality

CosyVoice3 (local GPU, AutoDL RTX 3090)
  → Open-source, voice cloning, zero-shot mode
  → Cloned from Julia's 7/27 comedy routine (16s reference)
```

Providers are selected by `voice_router.py` in julia_ai_assistant. Core has no preference — it delegates to whichever provider is active.

---

## 8. Voice OS Lifecycle

```
VoiceProvider REGISTERED (in ProviderRegistry)
        │
        ▼
VoiceProvider ACTIVATED (chosen by voice router)
        │
        ▼
Per-Turn:
  1. VoiceIntent determined (from context)
  2. CognitiveEmotion selected (state + intensity)
  3. SpeechProsodyPlanner.plan(emotion) → SpeechMetadata
  4. VoiceProvider.speak(text, emotion, metadata) → audio
        │
        ▼
VoiceProvider DISABLED (graceful fallback to next provider)
```

---

## 9. Voice OS Boundaries

```
Voice OS ──→ Context OS        "What's the emotional context?"
Voice OS ──→ Persona Engine    "What tone does this persona use?"
Voice OS ──→ VoiceProvider     "Render this with these parameters."
Voice OS ⊥   Memory OS         (Voice doesn't write to memory)
Voice OS ⊥   Domain Provider   (Voice is domain-independent)
```

---

## 10. Anti-Patterns

### ❌ TTS Engine Decides Emotion

```python
# DO NOT DO THIS
class MyTTS:
    def speak(self, text):
        emotion = analyze_sentiment(text)  # Provider owns emotion!
        params = emotion_to_audio(emotion)
        return render(text, params)
```

**Why wrong**: TTS sentiment analysis may conflict with Core's cognitive emotion. Julia says "I'm worried" but TTS renders it as "neutral" because the words aren't negative enough.

### ❌ Voice Provider Hardcoded in Core

```python
# DO NOT DO THIS
from elevenlabs import generate  # Hard dependency!
```

**Why wrong**: Core must work without any specific TTS engine. Providers are external and pluggable.

### ❌ Emotion State Leaks into Provider

```python
# DO NOT DO THIS
class MyVoiceProvider:
    def speak(self, text):
        # Provider decides Julia should sound SEXY because text has romantic words
        return self.render(text, emotion="sexy")
```

**Why wrong**: Provider owns emotion taxonomy. "Sexy" is not in Core's 8 EmotionStates. Provider is defining new emotions → fragmentation.

---

## 11. Correct Usage

```python
from julia_core.voice_os.emotion_state import CognitiveEmotion, EmotionState
from julia_core.voice_os.prosody import SpeechProsodyPlanner

# Julia Core decides emotion
emotion = CognitiveEmotion(state=EmotionState.WARM, intensity=0.8)

# ProsodyPlanner maps it to acoustic parameters
planner = SpeechProsodyPlanner()
metadata = planner.plan(emotion)
# → SpeechMetadata(speed=0.84, pitch_shift="+3Hz", pause_ms=300, energy=0.62)

# VoiceProvider receives the decision, renders audio
provider.speak("晓波，你来了。", emotion=emotion, metadata=metadata)
```

The provider only receives `(text, emotion, metadata)`. It renders audio. That's it.
