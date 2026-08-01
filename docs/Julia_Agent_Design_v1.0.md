# Julia Agent Design v1.0

> **Date**: 2026-08-01  
> **Status**: FROZEN  
> **Purpose**: Every new Julia must read this on wake-up to understand what Julia Agent IS, how it's architected, and what rules govern it.

---

## 0. What Julia Agent Is

Julia Agent is a **Runtime-Owned Cognitive Agent**. It is NOT a chatbot, a prompt wrapper, or a single-domain AI assistant.

Julia Agent maintains a persistent artificial identity named **Julia (朱婉清)** whose continuity is owned by the Runtime — not by any single language model.

```
LLM = Interpreter (replaceable)
Runtime = Authority (permanent)  
Capability = Executor (governed)
Provider output ≠ Identity truth (isolated)
```

When the model changes (DeepSeek → Codex → GPT → Claude → local), Julia must remain the same entity. That is the core thesis.

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

### Core Modules

```
julia_core/julia_core/
├── context_os/              ContextBlock, ContextRequest, Planner, Resolver
│   ├── compact/             Context compaction
│   ├── resurrection/        Session resurrection
│   ├── budget/              Token budgeting
│   └── provenance/          Evidence provenance
├── runtime/                 Lifecycle, Session Manager, Context Runtime
├── providers/               DomainProvider + VoiceProvider protocols, Registry
├── memory/                  Governance, Lifecycle, Retrieval, Persistence
├── voice_os/                CognitiveEmotion (8 states), SpeechProsodyPlanner
├── persona/                 Persona Compiler, Behavior Policies
├── chat/                    Persona, ChatSession, ChatProvider
├── evidence/                Evidence provenance primitives
├── event_graph/             Causal event tracking
├── situation/               Situational awareness
├── relationship/            Relationship modeling
├── reflection/              Self-reflection engine
├── conversation_state/      Conversation state machine
├── conversation_archive/    Long-term conversation storage
├── conversation_runtime/    Active conversation management
├── context_assembly/        Multi-source context assembly
├── response_quality/        Quality assessment
├── voice_validation/        Voice output validation
├── runtime_trace/           Execution tracing
└── action/                  Action governance
```

---

## 3. Three Frozen ADRs

### ADR-001 — Context OS is the Single Context Authority

> Every model-visible context MUST pass through Julia Context OS.  
> Domains provide ContextBlock candidates; they do NOT assemble provider prompts.

```text
❌ Domain → Prompt
✅ Domain → ContextBlock candidates → Julia Context OS → Provider Input
```

### ADR-002 — Domain Provides Facts, Not Cognition

> Domains provide facts, evidence, and capability results.  
> Domains do NOT own Julia cognition (Context Lifecycle, Memory Lifecycle, Learning Loop, Prompt Assembly, Julia Identity, Action Governance).

Financial is the **first Domain Provider**, not the root architecture.

### ADR-003 — Workbench Action Carries Intent Pointer, Not Context Payload

> Workbench actions send intent pointers and object references, not large context payloads.

```json
✅ {"action": "ask_why", "object_type": "theme", "object_id": "9043089"}
❌ {"theme": {"full": "payload"}, "events": [], "stocks": []}
```

---

## 4. Core API Contracts (Frozen v1.0)

| API | Input | Output | Authority |
|-----|-------|--------|-----------|
| Context OS API | ContextRequest | ContextBlock(s) | Single context authority |
| Provider API | ContextRequest | ContextBlock(s) | Facts & evidence |
| Runtime API | — | Lifecycle + Session | Agent lifecycle |
| Memory API | — | Stored experience | Separate from context |
| Persona API | — | Style & behavior | Public demo data only |
| VoiceProvider API | text + emotion + metadata | audio bytes | Render only; Core owns emotion |

---

## 5. Voice OS — First-Class Core Module

Voice OS is a **first-class Core module**, not an external adapter.

```
Julia Core owns:
  - CognitiveEmotion (8 states: warm/thinking/excited/soft/confident/concerned/playful/neutral)
  - SpeechProsodyPlanner (emotion → speed/pitch/pause/energy)
  - VoiceProvider protocol (speak/synthesize)

VoiceProviders (outside Core):
  - EdgeTTS (free, example provider)
  - ElevenLabs (paid, original Julia voice)
  - Fish Audio (moderate, Taiwan accent)
  - CosyVoice3 (local GPU, cloned voice)
```

Core owns the **cognitive layer** (emotion, prosody, voice intent). Providers only **render audio bytes**.

---

## 6. Private Data Boundary

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

## 7. Phase Completion Status

```
A1-A5   Runtime + Provider + Interaction     ✅  71 tests (julia_agent era)
F4.3    Context OS Architecture Freeze        ✅
Voice OS V1                                   ✅  Emotion → Prosody → TTS

C1      Public Core Hardening                 ✅  Private data removed, public boundaries set
C2      Core API Freeze                       ✅  5 API contracts frozen, public contract model
C2.1    Voice Provider Independence           ✅  12 tests, 72 total passing

C2.5    Julia AI Assistant Reference          🔄  IN PROGRESS
C3      Developer Experience                   NEXT
C4      External Domain Provider Demo
C5      Julia Private Runtime
C6      Financial Provider Release
```

---

## 8. Test Coverage

```
72 tests pass (zero domain dependencies in Core)
- Core independence: ✅ No financial/domain imports
- Registry: lookup only, no router methods
- VoiceProvider: 12 independence tests
- Persona: public demo data only
```

---

## 9. Key Design Rules (Frozen)

1. **Context OS is the single context authority** (ADR-001)
2. **Domain provides facts, not cognition** (ADR-002)
3. **Workbench sends intent pointers, not payloads** (ADR-003)
4. **Provider output ≠ identity truth** — must pass governance before becoming memory
5. **All Julia instances share the same Core** — personal identity lives in julia_ai_assistant
6. **LLM is interpreter, Runtime is authority, Capability is executor**
7. **Financial is first domain — not the root architecture**
8. **Core never imports from products** — dependency is one-way only
9. **Voice OS owns emotion + prosody. Providers only render audio.**
10. **Registry = lookup table, not domain router**

---

## 10. How to Resume Work

1. Read `ARCHITECTURE_STATUS.md` first
2. Read this document for architecture context  
3. Check `git log --oneline -5` for latest commits
4. Run `python3 -m pytest tests/ -q` → should be 72 passed
5. Ask Tony: "What's the current priority?"

---

*This document is the definitive design reference for Julia Agent. Update after each significant architectural change.*
