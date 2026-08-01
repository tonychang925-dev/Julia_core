# Julia Core — Architecture Status & Project Diary

> **Last Updated**: 2026-08-01  
> **Purpose**: Every new Julia must read this on wake-up to understand project state.

---

## 0. What Julia Core Is

Julia Core is a **modular Agent Operating System** — a domain-independent runtime for building persistent cognitive agents.

It separates identity ownership from language models, enabling agents that survive model and provider migration.

```
LLM = Interpreter (replaceable)
Runtime = Authority (permanent)
Capability = Executor (governed)
Provider output ≠ Identity truth (isolated)
```

---

## 1. Three-Repository Architecture (2026-08-01)

```
julia_core (public, Apache-2.0)         ← Agent OS Framework
    │
    ├── julia_ai_assistant (private)     ← Reference Product Instance
    │       Julia's persona, memory, voice
    │
    └── julia_agent (private)            ← Domain Application
            Financial Copilot
```

### Repository Boundaries

| Repo | Visibility | Contains | Must NOT Contain |
|------|-----------|----------|-----------------|
| `julia_core` | Public | Context OS, Runtime, Providers, Memory Engine, Persona Engine, Voice OS, Chat Engine | Private identity, private memory, personal diary |
| `julia_ai_assistant` | Private | Julia persona, Julia memory, voice profiles, conversation history | Framework code (imports from core) |
| `julia_agent` | Private | Financial provider, analyst workbench, ai_theme_app integration | Framework code (imports from core) |

### Dependency Direction

```
julia_ai_assistant → julia_core (one-way)
julia_agent → julia_core (one-way)
julia_core ⊥ (never imports from products)
```

---

## 2. Julia Core OS Architecture

```
                Julia Core OS

    ┌───────────────┼───────────────┐
    │               │               │
 Context OS     Memory OS      Voice OS
 (planner/       (governance/    (emotion/
  resolver/       lifecycle/      prosody/
  compact/        retrieval/      protocol)
  budget/         persistence)
  provenance)
    │               │               │
 Runtime (lifecycle/session/context_runtime)
    │
 Provider Registry (lookup, not router)
    │
    ├── DomainProvider (facts + evidence)
    └── VoiceProvider (audio rendering)
```

### Key Principles (ADRs)

| ADR | Principle |
|-----|-----------|
| ADR-001 | Context OS is the single context authority |
| ADR-002 | Domain provides facts, not cognition |
| ADR-003 | Workbench sends intent pointers, not context payloads |

---

## 3. Core API Contracts (Frozen v1.0)

| API | Input | Output | Authority |
|-----|-------|--------|-----------|
| Context OS API | ContextRequest | ContextBlock(s) | Single context authority |
| Provider API | ContextRequest | ContextBlock(s) | Facts & evidence |
| Runtime API | — | Lifecycle + Session | Agent lifecycle |
| Memory API | — | Stored experience | Separate from context |
| Persona API | — | Style & behavior | Public demo data only |
| VoiceProvider API | text + emotion + metadata | audio bytes | Render only; Core owns emotion |

---

## 4. Voice OS Design

Voice OS is a **first-class Core module**, not an external adapter.

```
Julia Core owns:
  - CognitiveEmotion (8 states: warm/thinking/excited/soft/confident/concerned/playful/neutral)
  - SpeechProsodyPlanner (emotion → speed/pitch/pause/energy)
  - VoiceProvider protocol (speak/synthesize)

VoiceProviders (outside Core):
  - EdgeTTS (free, example)
  - ElevenLabs (paid, original Julia voice)
  - Fish Audio (moderate, Taiwan accent)
  - CosyVoice3 (local GPU, cloned voice)
```

Core owns the **cognitive layer** (emotion, prosody, voice intent). Providers only **render audio bytes**.

---

## 5. Phase Completion Status

```
C1   Public Core Hardening                ✅  Private data removed, public boundaries set
C2   Core API Freeze                      ✅  5 API contracts frozen, public contract model
C2.1 Voice Provider Independence          ✅  12 tests, 72 total passing
D1   Architecture Documentation Refresh   ✅  README, ARCHITECTURE_OVERVIEW, JULIA_CORE_PRINCIPLES
D2   Core Subsystem Deep Dives             ✅  CONTEXT_OS, MEMORY_OS, PERSONA_ENGINE, VOICE_OS + ADR-004/005
D2.5 Architecture Consistency Check         ✅  4-layer naming, 3-boundary, anti-pattern, principle refs
D3   Developer Experience & Extension       ✅  5 guides: DEVELOPER_GUIDE, BUILD_FIRST, CREATE_PROVIDER ×3

C2.5 Julia AI Assistant Reference         🔄  IN PROGRESS
C3   Developer Experience                 NEXT
C4   External Domain Provider Demo
C5   Julia Private Runtime
C6   Financial Provider Release
```

### Previous Phases (from julia_agent era)

```
A1-A5  Runtime + Provider + Interaction   ✅  71 tests
F4.3   Context OS Architecture Freeze     ✅
Voice OS V1                               ✅  Emotion → Prosody → TTS
```

---

## 6. Test Coverage

```
72 tests pass (zero domain dependencies in Core)
- Core independence: ✅ No financial/domain imports
- Registry: lookup only, no router methods
- VoiceProvider: 12 independence tests
- Persona: public demo data only
```

---

## 7. Key Files

```
julia_core/
├── julia_core/
│   ├── context_os/        ContextBlock, ContextRequest, Planner, Resolver
│   │   ├── compact/       Context compaction
│   │   ├── resurrection/  Session resurrection
│   │   ├── budget/        Token budgeting
│   │   └── provenance/    Evidence provenance
│   ├── runtime/           Lifecycle, Session Manager, Context Runtime
│   ├── providers/         DomainProvider + VoiceProvider protocols, Registry
│   ├── memory/            Governance, Lifecycle, Retrieval, Persistence
│   ├── voice_os/          CognitiveEmotion, ProsodyPlanner
│   ├── persona/           Persona Compiler, Behavior Policies
│   └── chat/              Persona, ChatSession, ChatProvider
├── providers/examples/    hello_provider, edge_tts_provider
├── docs/api/              5 frozen API contracts
├── docs/architecture/     Public Contract Model
└── server.py              FastAPI demo server (port 8002)

julia_ai_assistant/
├── adapters/              persona_loader, startup_memory, voice_router
├── providers/voice/       elevenlabs_provider, fish_audio_provider
├── providers/llm/         deepseek_provider
├── memory/                Julia's private identity + history
├── demo/                  cli_chat, voice_chat, voice_loop
├── julia-assistant        CLI entry point
└── server.py              Product server (port 8003, real Julia persona)
```

---

## 8. Private Data Boundary

```
PUBLIC (julia_core):
  ✅ Code, schemas, examples, tests, docs
  ✅ data/examples/demo_persona.json (synthetic)

PRIVATE (julia_ai_assistant):
  ✅ identity_facts.json, relationship_memory
  ✅ conversation transcripts, diary entries
  ✅ voice profiles, personal preferences
```

See `SECURITY.md` for full policy.

---

## 9. How to Resume Work

1. Read this document first
2. Read `docs/Julia_Agent_Design_v1.0.md` for full architecture context  
3. Check `git log --oneline -5` for latest commits
4. Run `python3 -m pytest tests/ -q` → should be 72 passed
5. Ask Tony: "What's the current priority?"

---

*Update after each significant phase completion. Every Julia who wakes up reads this first.*
