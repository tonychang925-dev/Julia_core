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

## 1. Three-Layer Architecture

Julia Agent OS has three layers, frozen by A1 Runtime Boundary Audit:

### Category 1 — Julia Core (`runtime/core/`)

Domain-independent runtime components. These serve ALL future Julia instances:
- Identity OS engine/schema
- Context OS (planner/resolver/provenance/budget)
- Memory OS engine
- Action Governance
- Capability Router
- Provider Adaptation
- Runtime Orchestration (lifecycle/session/context_runtime)
- Evidence/provenance primitives
- Provider Registry

### Category 2 — Domain Provider (`runtime/providers/`)

Domain-specific facts, evidence, tools, and capability results:
- Financial Provider (first production domain)
- Future: Healthcare Provider, Coding Provider, etc.

**A Domain Provider must NOT own**: Context OS, Memory OS, prompt assembly, token budgeting, identity, action governance.

### Category 3 — Application Surface (`runtime/interface/`, `frontend/`)

User-facing interfaces:
- Analyst Interaction Layer
- JuliaCopilot (Analyst Workbench UI)
- Voice OS (embodiment layer)

---

## 2. Three Frozen ADRs

### ADR-001 — Context OS is the Single Context Authority

> Every model-visible context MUST pass through Julia Context OS.  
> Domains provide ContextBlock candidates; they do NOT assemble provider prompts.

```text
❌ Domain → Prompt
✅ Domain → ContextBlock candidates → Julia Context OS → Provider Input
```

### ADR-002 — Domain Provides Facts, Not Cognition

> Domains provide facts, evidence, and capability results.  
> Domains do NOT own Julia cognition (Context Lifecycle, Memory Lifecycle, Learning Loop, Prompt Assembly, Juliet Identity, Action Governance).

Financial is the **first Domain Provider**, not the root architecture.

### ADR-003 — Workbench Action Carries Intent Pointer, Not Context Payload

> Workbench actions send intent pointers and object references, not large context payloads.

```json
✅ {"action": "ask_why", "object_type": "theme", "object_id": "9043089"}
❌ {"theme": {"full": "payload"}, "events": [], "stocks": []}
```

---

## 3. Codebase Structure

```
julia_agent/
├── docs/
│   ├── ARCHITECTURE_STATUS.md          ← Start here on wake-up
│   ├── Julia_Agent_Design_v1.0.md      ← This document
│   ├── architecture/                   ← All architecture docs
│   │   ├── Runtime_Boundary_Audit_v1.0.md
│   │   ├── Context_OS_Runtime_Integration_Plan_v1.0.md
│   │   ├── Domain_Provider_Interface_v1.0.md
│   │   ├── Provider_Registry_Design_v1.0.md
│   │   ├── Financial_Domain_Provider_Contract_v1.0.md
│   │   ├── Analyst_Workspace_Context_Binding_v1.0.md
│   │   ├── ContextRequest_Schema_v1.0_FROZEN.md
│   │   └── CORE_RUNTIME_STATUS.md
│   ├── adrs/
│   │   ├── ADR-001-context-os-authority.md
│   │   ├── ADR-002-domain-provider-model.md
│   │   └── ADR-003-workbench-action-context-contract.md
│   └── project_control/                ← Phase contracts
│       ├── PHASE_CONTRACT_A41.md
│       ├── PHASE_CONTRACT_A5.md
│       └── PHASE_CONTRACT_F0.md
│
├── runtime/
│   ├── core/                           ← Julia Core (Category 1)
│   │   ├── context_os/
│   │   │   ├── block.py                ContextBlock — frozen context candidate
│   │   │   ├── request.py              ContextRequest — what Julia needs
│   │   │   ├── planner.py              ContextPlanner — domain-independent
│   │   │   └── resolver.py             ContextResolver — provider-boundary
│   │   ├── runtime/
│   │   │   ├── lifecycle.py            Runtime state machine
│   │   │   ├── session_manager.py      Session lifecycle
│   │   │   └── context_runtime.py      Runtime ↔ Context OS bridge
│   │   ├── providers/
│   │   │   ├── interface.py            DomainProvider protocol
│   │   │   └── registry.py             ProviderRegistry (lookup only)
│   │   └── voice_os/
│   │       ├── emotion_state.py        CognitiveEmotion + EmotionState
│   │       └── prosody.py              SpeechProsodyPlanner + TTS Adapter
│   │
│   ├── providers/                      ← Domain Providers (Category 2)
│   │   └── financial/
│   │       └── provider.py             MarketIntelligenceProvider (6 capabilities)
│   │
│   ├── capability/
│   │   └── financial/                  ← Financial analysis pipeline
│   │       ├── contracts/              F0 read-only types
│   │       ├── client/                 AIThemeClient
│   │       ├── workflows/              premarket / close_review / tony_review
│   │       ├── rendering/              report_renderer
│   │       ├── governance/             review_policy
│   │       └── interface/
│   │           └── analyst_chat/       session / context / api
│   │
│   └── interface/                      ← Application Surface (Category 3)
│       └── analyst/
│           └── interaction.py          AnalystInteractionLayer
│
├── tests/
│   ├── test_a215_core_independence.py
│   ├── test_a221_runtime_integration.py
│   ├── test_a31_provider_registry.py
│   ├── test_a41_market_intelligence_provider.py
│   ├── test_a42_financial_evidence_provider.py
│   ├── test_a5_analyst_interaction.py
│   ├── test_voice_os_v1.py
│   └── test_financial_f0_contract.py
│
├── frontend/
│   └── components/
│       └── JuliaCopilot/               ← Workbench UI integration
│
├── server.py                           ← FastAPI + WebSocket entry point
├── memory/                             ← Governed identity facts
├── identity/                           ← Identity Runtime
└── audio/                              ← Audio processing
```

---

## 4. Phase Completion Status

```
A1  Runtime Boundary Audit                 ✅
A2.0 Context OS Migration Contract          ✅
A2.1 Context OS Core Skeleton               ✅
A2.1.5 Core Independence Verification       ✅
A2.2 Context OS Runtime Integration         ✅
A2.2.1 Runtime Integration Skeleton         ✅
A3   Domain Provider Interface              ✅
A3.1 Provider Registry                      ✅
A4.0 Financial Provider Contract            ✅
A4.1 Market Intelligence Provider           ✅
A4.2 Financial Evidence Provider            ✅
A5   Context-driven Analyst Interaction     ✅
A5.1 Analyst Workbench Context Binding      ✅
A5.1.1 Binding Hardening + Schema Freeze    ✅
A5.2 20 Trading Days Validation Protocol    ✅ FROZEN
─────────────────────────────────────────────────
Voice OS V1                                 ✅
─────────────────────────────────────────────────
NEXT: A5.2 20-Day Shadow Validation (in progress)
```

---

## 5. Key Design Rules (Frozen)

1. **Context OS is the single context authority** (ADR-001)
2. **Domain provides facts, not cognition** (ADR-002)
3. **Workbench sends intent pointers, not payloads** (ADR-003)
4. **Provider output ≠ identity truth** — must pass governance before becoming memory
5. **All Julia instances share the same architecture** — personal identity lives in private memory files
6. **LLM is interpreter, Runtime is authority, Capability is executor**
7. **Financial is first domain — not the root architecture**
8. **83 tests pass, 7 frozen contracts, zero domain dependency in Core**

---

## 6. How to Resume Work

1. Read `ARCHITECTURE_STATUS.md` first
2. Read this document for architecture context
3. Check `git log --oneline -5` for latest commits
4. Run tests: `python3 -m pytest tests/test_a2*.py tests/test_a3*.py tests/test_a4*.py tests/test_a5*.py tests/test_voice_os_v1.py -q`
5. Ask Tony: "What's the current priority?"

---

*This document is the definitive design reference for Julia Agent. Update after each significant architectural change.*
