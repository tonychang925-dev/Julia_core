# Julia Core OS — Architecture Overview v0.2

> **Date**: 2026-08-01  
> **Status**: FROZEN  
> **Purpose**: Complete module map, data flow, and architectural boundaries of Julia Core OS.

---

## 1. Positioning

```
Julia Core OS = Agent Operating System

NOT: Chatbot Framework
NOT: LLM Wrapper  
NOT: Prompt Engineering Toolkit
```

Julia Core owns the agent. Models interpret. Providers supply facts. The runtime is permanent — models come and go.

---

## 2. Four-Layer OS Model

```
                        Agent Applications
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   Julia AI Assistant    Financial Analyst        Future Agents
   (private repo)        (private repo)           (any domain)
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                │  import julia_core
                                │
┌───────────────────────────────┴───────────────────────────────┐
│                                                               │
│                       Julia Core OS                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Runtime Layer                                 │ │
│  │                                                         │ │
│  │  lifecycle.py         Agent lifecycle state machine     │ │
│  │  session_manager.py   Session create/resume/close       │ │
│  │  context_runtime.py   Runtime ↔ Context OS bridge       │ │
│  │  runtime_trace/       Execution tracing & audit         │ │
│  │                                                         │ │
│  │  Owns: agent birth → death, session lifecycle,         │ │
│  │        execution tracing, state transitions             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Layer 2: Subsystem Truth Authorities                   │ │
│  │                                                         │ │
│  │  Conversation  Continuity  Memory    Persona    Context   Alignment│ │
│  │  ────────────  ──────────  ──────    ────────   ───────   ─────────│ │
│  │  Conversation  checkpoint  governance compiler   planner   contracts│ │
│  │  Runtime       recovery    lifecycle  policies   resolver  registry │ │
│  │  SessionRepo   policy      retrieval             budget    adapter  │ │
│  │  transcript    memory_     persistence           provenance          │ │
│  │  truth         binding              ranking                          │ │
│  │                                                         │ │
│  │  Owns: transcript truth, survival policy, governed     │ │
│  │    memory, behavioral identity, model-visible context,  │ │
│  │    and provider adaptation — model-independent          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Layer 3: Interaction Layer                             │ │
│  │                                                         │ │
│  │  Chat Engine              Voice OS                      │ │
│  │  ────────────             ─────────                     │ │
│  │  persona.py               emotion_state.py              │ │
│  │  session.py               prosody.py                    │ │
│  │  provider.py              (CognitiveEmotion,            │ │
│  │                             SpeechProsodyPlanner)       │ │
│  │  context_assembly/                                      │ │
│  │                                                         │ │
│  │  Owns: how the agent communicates — text, voice,       │ │
│  │        emotion, prosody                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Layer 4: Extension Layer                               │ │
│  │                                                         │ │
│  │  Domain Providers       Voice Providers                 │ │
│  │  ────────────────       ───────────────                 │ │
│  │  interface.py           voice_provider.py               │ │
│  │  registry.py            (protocol only)                 │ │
│  │                                                         │ │
│  │  Providers are PLUGGABLE. Core owns protocols.         │ │
│  │  Implementations live outside Core:                     │ │
│  │    Domain: financial (julia_agent)                      │ │
│  │    Voice:  EdgeTTS, ElevenLabs, Fish, CosyVoice3       │ │
│  │    Model:   DeepSeek, Codex, GPT, Claude, local        │ │
│  │                                                         │ │
│  │  Owns: provider protocols, registry, lifecycle         │ │
│  │        (REGISTERED → ACTIVE → DISABLED)                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. Complete Module Map

```
julia_core/julia_core/
│
├── context_os/                 Context OS — single context authority (ADR-001)
│   ├── block.py                ContextBlock — frozen context candidate with provenance, TTL
│   ├── request.py              ContextRequest — domain-independent demand signal
│   ├── planner.py              ContextPlanner — what does Julia need to know?
│   ├── resolver.py             ContextResolver — which providers can supply this?
│   ├── compact/                Context compaction — structured, evidence-traced
│   ├── resurrection/           Session resurrection — restore from compact + archive
│   ├── budget/                 Token budgeting — allocate context window
│   └── provenance/             Evidence provenance — where did each fact come from?
│
├── runtime/                    Runtime OS — agent lifecycle authority
│   ├── lifecycle.py            Runtime state machine (booting → ready → sleeping → terminated)
│   ├── session_manager.py      Session create / resume / close
│   └── context_runtime.py      Runtime ↔ Context OS bridge
│
├── providers/                  Provider Layer — protocols + registry
│   ├── interface.py            DomainProvider protocol (ADR-002)
│   ├── voice_provider.py       VoiceProvider protocol
│   └── registry.py             ProviderRegistry — lookup table, not domain router
│
├── memory/                     Memory OS — governed, persistent, transferable
│   ├── governance/             What can become memory? Who decides?
│   ├── lifecycle/              Memory object lifecycle (candidate → governed → archived)
│   ├── retrieval/              Semantic + temporal retrieval
│   ├── persistence/            Storage backends
│   ├── ranking/                Relevance ranking
│   └── weighting/              Importance weighting
│
├── voice_os/                   Voice OS — first-class Core module
│   ├── emotion_state.py        CognitiveEmotion (8 states: warm/thinking/excited/soft/
│   │                           confident/concerned/playful/neutral)
│   └── prosody.py              SpeechProsodyPlanner — emotion → speed/pitch/pause/energy
│
├── persona/                    Persona Engine — identity separate from memory
│   ├── compiler.py             Persona compiler
│   └── policies.py             Behavior policies
│
├── chat/                       Chat Engine — persona-agnostic, provider-independent
│   ├── persona.py              Persona data class
│   ├── session.py              ChatSession — turn management
│   └── provider.py             ChatProvider protocol
│
├── evidence/                   Evidence provenance primitives
├── event_graph/                Causal event tracking
├── situation/                  Situational awareness
├── relationship/               Relationship state modeling
├── reflection/                 Self-reflection engine
├── conversation_state/         ConversationMessage — durable transcript model + SessionRepository atomic persistence
├── conversation_runtime/       ConversationRuntime — canonical transcript authority
├── context_assembly/           Multi-source context assembly
├── response_quality/           Response quality assessment
├── voice_validation/           Voice output validation
├── runtime_trace/              Execution tracing & audit
└── action/                     Action governance
```

---

## 4. Data Flow

```
                    Runtime
                       │
                 ContextRequest
                       │
                       ▼
                  Context OS  (sole model-visible authority)
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   PersonaSource  ConversationSource  InteractionSource
        │              │              │
   ExperienceSource  CapabilitySource  DomainEvidenceSource
        │              │              │
        └──────────────┴──────────────┘
                       │
                  ContextBlock[]
                       │
                     Planner → Resolver → Budget → Projection
                       │
                    Assembly
                       │
                 Alignment OS
                       │
                  Model Provider
                       │
                       ▼
                  Voice OS / Response
│  (memory)         │
└───────────────────┘
```

Key: Core (white boxes) owns the pipeline. External providers (gray) plug in at defined boundaries.

---

## 5. Three-Repository Architecture

```
julia_core/  (public, Apache-2.0)
    │
    │  "Core never imports from products"
    │
    ├── julia_ai_assistant/  (private)
    │   ├── adapters/        persona_loader, startup_memory, voice_router
    │   ├── providers/llm/   DeepSeek, Codex
    │   ├── providers/voice/ ElevenLabs, Fish Audio
    │   ├── memory/          identity_facts, relationship_memory, claude_diary
    │   └── demo/            voice_chat, voice_loop
    │
    └── julia_agent/  (private)
        ├── providers/financial/  MarketIntelligenceProvider
        ├── capability/financial/ Analysis pipeline, workflows, rendering
        └── interface/analyst/    AnalystInteractionLayer
```

### Boundary Rules

| Repo | Contains | Must NOT Contain |
|------|----------|-----------------|
| julia_core | OS, Runtime, Protocols, Engines | Private identity, diary, financial data |
| julia_ai_assistant | Julia private identity data, memory records, voice profiles | Framework code; Core owns architecture authority |
| julia_agent | Financial provider, analyst workbench | Framework code, Julia persona |

---

## 6. API Contract Summary

| # | API | Input | Output | Core Authority |
|---|-----|-------|--------|----------------|
| 1 | Context OS | ContextRequest | ContextBlock[] | Single context authority |
| 2 | Provider | ContextRequest | ContextBlock[] | Facts & evidence only |
| 3 | Runtime | — | Lifecycle + Session | Agent lifecycle |
| 4 | Memory | — | Stored experience | Governed persistence |
| 5 | Persona | — | Style & behavior | Public demo data |
| 6 | VoiceProvider | text + emotion + metadata | audio bytes | Core owns emotion/prosody |

All 6 contracts frozen at `docs/api/`. See `Public_Contract_Model_v1.md` for details.

---

## 7. Cross-Cutting Concerns

### Provenance
Every ContextBlock carries `evidence_refs` — traceable back to source. "Where did Julia learn this?" is always answerable.

### Governance
Provider output does not automatically become memory or identity. Memory OS governance layer validates before persistence.

### Lifecycle
```
Provider:  REGISTERED → ACTIVE → DISABLED
Session:   created → active → compacted → closed
Memory:    candidate → governed → active → archived
Agent:     booting → ready → sleeping → terminated
```

---

## 8. Test Coverage

```
72 tests pass — zero domain dependencies in Core
├── Context OS:       planner, resolver, block, request
├── Runtime:          lifecycle, session, context_runtime
├── Providers:        registry, interface, voice_provider
├── Voice OS:         12 independence tests
├── Memory:           governance, lifecycle, retrieval
├── Persona:          compiler, policies (public demo data)
└── Chat:             session, persona, provider
```

---

## 9. Key Files

```
julia_core/
├── README.md                           Start here
├── docs/
│   ├── ARCHITECTURE_STATUS.md          Project diary + how to resume
│   ├── Julia_Agent_Design_v1.0.md      Definitive design reference
│   ├── architecture/
│   │   ├── ARCHITECTURE_OVERVIEW.md    ← This document
│   │   ├── JULIA_CORE_PRINCIPLES.md    5 architecture principles
│   │   ├── Public_Contract_Model_v1.md 6-API contract model
│   │   └── CORE_RUNTIME_STATUS.md      Current runtime status
│   ├── api/                            6 frozen API contracts
│   ├── adrs/                           ADR-001, 002, 003
│   └── project_control/               Phase contracts
├── julia_core/                         All Core source
├── providers/examples/                 Example providers
├── tests/                              72 tests
└── server.py                           FastAPI demo (port 8002)
```
