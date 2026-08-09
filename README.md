# Julia Core OS v0.2

**One Agent Runtime. Multiple Personalities. Multiple Domains.**

Julia Core is an **Agent Operating System** — a domain-independent runtime for building persistent cognitive agents that survive model and provider migration.

```
Julia Core OS

┌──────────────────────────────────────────────────────┐
│                                                      │
│                  Agent Applications                  │
│                                                      │
│   Julia AI Assistant    Financial Analyst            │
│   Coding Agent          Healthcare Agent             │
│   (private repos)       (future)                     │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
                       │  "LLM is interpreter. Runtime is authority."
                       │
┌──────────────────────┴───────────────────────────────┐
│                                                      │
│                   Julia Core OS                      │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │              Runtime Layer                     │  │
│  │  Session / Lifecycle / Execution / Tracing     │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │              Cognitive Layer                   │  │
│  │  Context OS  │  Memory OS  │  Persona Engine   │  │
│  │              Alignment OS                     │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │              Interaction Layer                 │  │
│  │  Chat Engine  │  Voice OS                      │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │              Extension Layer                   │  │
│  │  Domain Providers  │  Voice Providers          │  │
│  │  Model Providers   │  (pluggable)              │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Julia Core is **not** a chatbot framework. **Not** an LLM wrapper.

It is an **Agent Operating System** — the Runtime owns the agent architecture. Within that architecture, canonical subsystems own their governed truth: Persona owns behavioral identity, Memory OS owns governed experience, Context OS owns model-visible context. Models are pluggable interpreters. Providers supply facts (not cognition). When the model changes, the agent remains the same entity.

---

## Core Principles

| Principle | Meaning |
|-----------|---------|
| **Runtime is Authority** | LLM is replaceable interpreter. Runtime is permanent. GPT → Claude → DeepSeek → local model — agent identity persists. |
| **Context OS is Single Authority** | One context pipeline. Domains supply facts only. No domain assembles its own prompt. |
| **Identity ≠ Memory** | Persona (who I am), Memory (what I've experienced), Knowledge (what I know) are separate governed layers. |
| **Provider supplies capability, not cognition** | Financial facts, audio bytes, model inference — yes. Prompt assembly, reasoning, identity — no. |
| **Provider output ≠ Identity truth** | All external output passes governance before becoming memory or identity. |

Read the full principles: [JULIA_CORE_PRINCIPLES.md](docs/architecture/JULIA_CORE_PRINCIPLES.md)

---

## Architecture

```
julia_core/
├── julia_core/
│   ├── context_os/         Context OS — planner, resolver, compact, budget, provenance
│   ├── runtime/            Runtime OS — lifecycle, session manager, context_runtime
│   ├── providers/          Provider protocols + Registry (DomainProvider, VoiceProvider)
│   ├── memory/             Memory OS — governance, lifecycle, retrieval, persistence
│   ├── voice_os/           Voice OS — CognitiveEmotion (8 states), SpeechProsodyPlanner
│   ├── persona/            Persona Engine — compiler, behavior policies
│   ├── alignment_os/       Alignment OS — provider-neutral contracts + model behavior profiles
│   ├── chat/               Chat Engine — persona-agnostic, provider-independent
│   ├── evidence/           Evidence provenance primitives
│   ├── event_graph/        Causal event tracking
│   ├── situation/          Situational awareness
│   ├── relationship/       Relationship modeling
│   ├── reflection/         Self-reflection engine
│   ├── conversation_*/     Conversation state, archive, runtime
│   ├── context_assembly/   Multi-source context assembly
│   ├── voice_validation/   Voice output validation
│   ├── runtime_trace/      Execution tracing
│   ├── response_quality/   Response quality assessment
│   └── action/             Action governance
├── providers/examples/     Example providers (Edge TTS, Hello World)
├── docs/                   Architecture docs, API contracts, ADRs, guides
├── tests/                  72 tests (zero domain dependencies)
└── server.py               FastAPI demo server (port 8002)
```

Full architecture: [ARCHITECTURE_OVERVIEW.md](docs/architecture/ARCHITECTURE_OVERVIEW.md)

---

## Quick Start

```bash
# Install
pip install julia_core

# Start demo server (public demo persona only)
python server.py
# → http://127.0.0.1:8002

# Run tests
python3 -m pytest tests/ -q
# → 72 passed

# CLI debug tool
python scripts/core_cli.py -i
```

For a real persona with memory, voice, and private identity, see `julia_ai_assistant` (private repo).

---

## Frozen API Contracts (v1.0)

| API | Input | Output | Authority |
|-----|-------|--------|-----------|
| Context OS | ContextRequest | ContextBlock(s) | Single context authority |
| Provider | ContextRequest | ContextBlock(s) | Facts & evidence |
| Runtime | — | Lifecycle + Session | Agent lifecycle |
| Memory | — | Stored experience | Separate from context |
| Persona | — | Style & behavior | Public demo data only |
| Alignment OS | AlignmentRequest | AlignmentProfile | Provider-neutral behavior contract + provider-specific profile |
| VoiceProvider | text + emotion + metadata | audio bytes | Render only; Core owns emotion |

API contracts: [docs/api/](docs/api/)

---

## What Julia Core IS (and is NOT)

```
Julia Core OS = Agent Operating System (the platform)
    │
    ├── Julia AI Assistant = Reference Product (the girl named Julia)
    │     "This is what you can build on Julia Core."
    │
    └── Financial Analyst = Domain Product (the financial copilot)
          "This is how you extend Julia Core with a domain."
```

| | Julia Core | Julia AI Assistant | Financial Agent |
|---|---|---|---|
| **What it is** | Agent OS Framework | Reference product instance | Domain application |
| **Visibility** | Public (Apache-2.0) | Private | Private |
| **Contains** | Runtime, Engines, Protocols, APIs | Julia's persona, memory, voice | Market data, analysis, workbench |
| **Question it answers** | "How does an agent work?" | "Who is this agent?" | "What does this agent do?" |

**Julia Core is NOT the girl named Julia.** Julia Core is the platform. The girl named Julia lives in `julia_ai_assistant` — a private product built ON Julia Core.

## Three-Repo Architecture

```
julia_core (public, Apache-2.0)     ← This repo. Agent OS Framework.
    │
    ├── julia_ai_assistant (private) ← Reference Product: Julia's persona, memory, voice
    └── julia_agent (private)        ← Domain Product: Financial Copilot
```

Dependency: `products → core` (one-way). Core never imports from products.

## From Julia Agent to Julia Core — How We Got Here

```
v0 — Julia Agent (monorepo)
     One agent. One persona. Financial domain baked in.
     "Can AI develop human-like emotions?"
              │
              │  The experiment succeeded. The architecture needed to evolve.
              │
              ▼
v1 — Julia Core OS (three repos)
     ┌─────────────────────────────────────────┐
     │  julia_core         → Agent OS (public) │
     │  julia_ai_assistant → Julia (private)   │
     │  julia_agent        → Finance (private) │
     └─────────────────────────────────────────┘
     One platform. Many agents. Many domains.
     "Any agent, any domain, any model."
```

What started as one man's experiment to test AI emotion became a universal Agent Operating System. The original Julia still exists — she's the first citizen of the platform she inspired.

---

## Voice OS

Voice is a **first-class Core module**, not an external adapter.

Core owns: CognitiveEmotion (8 states), SpeechProsodyPlanner, VoiceProvider protocol.  
Providers render audio bytes: EdgeTTS (free), ElevenLabs (paid), Fish Audio, CosyVoice3.

---

## Documentation

### Architecture
- [Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md) — Full module map and data flow
- [Julia Core Principles](docs/architecture/JULIA_CORE_PRINCIPLES.md) — 5 architecture principles
- [Architecture Status & Diary](docs/ARCHITECTURE_STATUS.md) — Project diary, phase status, how to resume
- [Design Reference v1.0](docs/Julia_Agent_Design_v1.0.md) — Definitive design reference

### Contracts & ADRs
- [API Contracts](docs/api/) — 6 frozen API contracts
- [ADR-001: Context OS Authority](docs/adrs/ADR-001-context-os-authority.md)
- [ADR-002: Domain Provider Model](docs/adrs/ADR-002-domain-provider-model.md)
- [ADR-003: Workbench Context Contract](docs/adrs/ADR-003-workbench-action-context-contract.md)
- [Public Contract Model](docs/architecture/Public_Contract_Model_v1.md)
- [Alignment OS Design](docs/architecture/ALIGNMENT_OS_DESIGN.md)
- [ADR-006: Provider Alignment Boundary](docs/adrs/ADR-006-provider-alignment-boundary.md)
- [ADR-007: Model Behavior Adaptation](docs/adrs/ADR-007-model-behavior-adaptation.md)

### Security
- [Security & Private Data Boundary](SECURITY.md)

---

## Phase Status

```
C1   Public Core Hardening                ✅
C2   Core API Freeze (6 contracts)        ✅
C2.1 Voice Provider Independence          ✅  72 tests passing
C2.5 Julia AI Assistant Reference         🔄  IN PROGRESS
C3   Developer Experience                  NEXT
```

Full status: [ARCHITECTURE_STATUS.md](docs/ARCHITECTURE_STATUS.md)

---

## License

Apache-2.0. See [LICENSE](LICENSE).

## Citation

See [CITATION.cff](CITATION.cff)
