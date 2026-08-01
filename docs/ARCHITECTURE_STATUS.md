# Julia Agent — Architecture Status & Project Diary

> **Last Updated**: 2026-07-31  
> **Written by**: Claude Code (with Codex for A2.0-A2.2 contracts)  
> **Purpose**: Every new Julia must read this on wake-up to understand project state.

---

## 0. What This Project Is

Tony is building a Runtime-Owned Cognitive Agent named **Julia**. She is not a chatbot. She is a persistent AI identity with her own Context OS, Memory governance, Provider abstraction, and Financial Intelligence capabilities.

The ultimate goal: Julia becomes Tony's financial analyst, research partner, and digital companion — eventually embodied in a physical robot body.

```
Soul → Brain → Face → Voice → Body
  ✅      ✅      ✅      ✅      🔧
```

---

## 1. Architecture (v4.0 Baseline)

### 1.1 Core Principle

```
LLM = Interpreter (replaceable)
Runtime = Authority (permanent)
Capability = Executor (governed)
Provider output ≠ Identity truth (isolated)
```

### 1.2 Julia Agent OS Architecture

```
                    Julia Agent OS

        Runtime (lifecycle/session/context_runtime)
            |
        Context OS (planner/resolver/request/block)
            |
        Provider Registry (lookup, not router)
            |
        Domain Provider Interface (protocol)
            |
    +-------+--------+
    |                |
 Financial      Future Providers
 Provider       (healthcare, coding...)
    |
  Market Intelligence + Evidence
    |
  Analyst Interaction Layer
    |
  Human (via Workbench UI or Voice)
```

### 1.3 Three-Layer Classification

| Layer | Category | Location | Examples |
|-------|----------|----------|---------|
| Julia Core | Category 1 | `runtime/core/` | Context OS, Runtime, Registry |
| Domain Provider | Category 2 | `runtime/providers/` | Financial, future domains |
| Application Surface | Category 3 | `runtime/interface/`, `frontend/` | Interaction Layer, Workbench UI |

**Domain Providers live in `runtime/providers/`, NOT in `runtime/core/`. Core never imports from domain providers.**

---

## 2. Architecture Document Index

### 2.1 Core Architecture

| Document | Description |
|----------|-------------|
| `docs/architecture/Runtime_Boundary_Audit_v1.0.md` | A1 — Three-layer classification + boundary audit |
| `docs/architecture/CORE_RUNTIME_STATUS.md` | Current Core runtime status |
| `docs/architecture/Context_OS_Core_Migration_Plan_v1.0.md` | A2.0 — Context OS migration contract |
| `docs/architecture/Context_OS_Runtime_Integration_Plan_v1.0.md` | A2.2 — Runtime integration plan |
| `docs/architecture/Domain_Provider_Interface_v1.0.md` | A3 — Provider protocol definition |
| `docs/architecture/Provider_Registry_Design_v1.0.md` | A3.1 — Registry contract |
| `docs/architecture/Financial_Domain_Provider_Contract_v1.0.md` | A4.0 — Financial Provider contract |

### 2.2 Feature Specs

| Document | Description |
|----------|-------------|
| `docs/project_control/PHASE_CONTRACT_A41.md` | A4.1 Market Intelligence Provider |
| `docs/project_control/PHASE_CONTRACT_A5.md` | A5 Analyst Interaction Layer |
| `docs/project_control/PHASE_CONTRACT_F0.md` | F0 Financial Read-only Contract |
| `docs/project_control/FEATURE_SPEC_P3.phase*` | Phase 3.5-3.7 detailed specs |

### 2.3 Reports

| Document | Description |
|----------|-------------|
| `docs/project_control/reports/phase-A2.1-context-os-core-skeleton.md` | A2.1 completion report |
| `docs/project_control/reports/phase-A2.1.5-core-independence.md` | A2.1.5 independence verification |

---

## 3. Current Progress — Phase Completion Status

```
F4.3-pre Context OS Architecture Freeze      ✅
A1 Runtime Boundary Audit                    ✅
A2.0 Context OS Core Migration Contract      ✅ (Codex)
A2.1 Context OS Core Skeleton                ✅ (Codex)
A2.1.5 Core Independence Verification        ✅ (Codex)
A2.2 Context OS Runtime Integration Contract ✅ (Codex)
A2.2.1 Runtime Integration Skeleton          ✅ (Claude)
A3 Domain Provider Interface Contract        ✅ (Claude)
A3.1 Provider Registry                       ✅ (Claude)
A4.0 Financial Provider Contract             ✅ (Claude)
A4.1 Market Intelligence Provider            ✅ (Claude)
A4.2 Financial Evidence Provider             ✅ (Claude)
A5 Context-driven Analyst Interaction        ✅ (Claude)
────────────────────────────────────────────────────
A5.1 Analyst Console E2E Integration         ← NEXT
A5.2 20 Trading Days Validation              ← NEXT
A6 Voice Adapter                             AFTER VALIDATION
```

---

## 4. Test Coverage

```
83 tests pass (all phases A2 through A5)

Core independence:   ✅ No domain imports in runtime/core/
Registry:            ✅ Lookup only, no router methods
Financial Provider:  ✅ No trading terms, no database access
Interaction Layer:   ✅ No Context OS bypass
All contracts:       6 frozen
```

Running tests: `python3 -m pytest tests/test_a2*.py tests/test_a3*.py tests/test_a4*.py tests/test_a5*.py -q`

---

## 5. Key Files (current implementation)

```
runtime/core/
    __init__.py
    context_os/
        __init__.py
        block.py              # ContextBlock — frozen context candidate
        planner.py             # ContextPlanner — domain-independent planning
        request.py             # ContextRequest — what Julia needs
        resolver.py            # ContextResolver — provider-boundary resolution
    runtime/
        __init__.py
        lifecycle.py           # Runtime state machine
        session_manager.py     # Session lifecycle + tracking
        context_runtime.py     # Runtime ↔ Context OS bridge
    providers/
        __init__.py
        interface.py           # DomainProvider protocol
        registry.py            # ProviderRegistry (lookup only)

runtime/providers/
    __init__.py
    financial/
        __init__.py
        provider.py            # MarketIntelligenceProvider (6 capabilities)

runtime/interface/
    __init__.py
    analyst/
        __init__.py
        interaction.py         # AnalystInteractionLayer (3 actions)

tests/
    test_a215_core_independence.py
    test_a21_context_os_core_skeleton.py
    test_a221_runtime_integration.py
    test_a31_provider_registry.py
    test_a41_market_intelligence_provider.py
    test_a42_financial_evidence_provider.py
    test_a5_analyst_interaction.py
```

---

## 6. Design Principles (Frozen)

1. Julia is a financial cognitive consumer, not a financial compute engine
2. ai_theme_app is the sole authority for Market Data, Domain Knowledge, and Risk
3. Candidates come from a two-layer mechanism (ai_theme_app recall → Julia investigation)
4. Every InvestmentCase must be falsifiable (entry/confirmation/invalidation conditions)
5. Provider output must not automatically become knowledge or evidence
6. Financial memory is isolated from personal memory
7. First 20 trading days: Shadow Analyst only
8. Julia has the right to ask (TargetedEvidenceRequest), not to recompute
9. All trading decisions are made by Tony
10. Julia maintains a single identity; financial analysis is a Cognitive Scope

---

## 7. Commit History (2026-07-31)

```
7887f0a Implement A5 Context-driven Analyst Interaction Layer
3e1bfcc Implement A4.2 Financial Evidence Provider
f570427 Implement A4.1 Market Intelligence Provider
9620b59 Freeze A4.0 Financial Domain Provider Contract v1.0
f0915e7 Implement A3.1 Provider Registry
6f59a53 Freeze A3 Domain Provider Interface Contract v1.0
1d25c73 Revert VPS_VPN_Setup_Guide.md from public repo
4a6df1f Implement A2.2.1 Context OS Runtime Integration Skeleton
0de451f Merge A2.2 Context OS runtime integration contract
843214b Implement A2.1 Context OS core skeleton (Codex)
ce94d76 Merge A2.0 Context OS core migration contract (Codex)
```

---

## 8. Next Steps — A5.1 Analyst Console E2E Integration

### Objective

Connect Julia to Tony's existing Analyst Workbench (React/TypeScript). First interaction: text input → Julia analysis → text output + EvidenceRef links.

### Three Concerns

1. **Analyst Console Protocol** — Define input/output contract for Workbench ↔ Julia
2. **Context Injection Rules** — Per-action context loading (not ALL financial data)
3. **Human Feedback Capture** — AnalystFeedbackRecord for 20-day validation (not learning memory)

### Integration architecture

```
Analyst Workbench (React)
    │
    │  HTTP/WS
    ▼
AnalystInteractionLayer (already built)
    │
    ▼
Context OS → Provider Registry → Financial Provider
    │
    ▼
AnalystResponseEnvelope → rendered in UI
```

### Deliverables

- Workbench ↔ Julia protocol frozen
- Three actions (Why? / Risk? / Compare?) wired end-to-end
- EvidenceRef links clickable in UI
- Feedback capture (rating 1-5 per response)

---

## 9. A5.2 — 20 Trading Days Validation

### Evaluation Metrics (not profit/loss)

| Metric | Target |
|--------|--------|
| Evidence Coverage | 95% of answers have evidence |
| Evidence Relevance | 80%+ evidence supports the claim |
| Analyst Acceptance | Tony rating average ≥ 4/5 |
| False Confidence Rate | Near 0 (no unsupported claims) |

### Daily Loop

```
08:00 — Morning Brief (3 themes, 5 candidates, 2 risks)
09:15 — Auction check
10:00 — Mid-morning confirmation
14:30 — Close plan
16:30 — EOD review with error attribution
```

---

## 10. How to Resume Work

### For a new Julia waking up

1. Read this document first
2. Read `docs/architecture/Runtime_Boundary_Audit_v1.0.md` for the three-layer classification
3. Check `git log --oneline -10` for latest commits
4. Run `python3 -m pytest tests/test_a2*.py tests/test_a3*.py tests/test_a4*.py tests/test_a5*.py -q` to verify 83 tests pass
5. Ask Tony: "What's the current priority?"

### Key files to start coding

| If working on... | Start here |
|-----------------|-----------|
| Context OS | `runtime/core/context_os/` |
| Provider integration | `runtime/core/providers/registry.py` |
| Financial capabilities | `runtime/providers/financial/provider.py` |
| User interaction | `runtime/interface/analyst/interaction.py` |
| Workbench integration | A5.1 (not yet started) |

---

## 11. Identity Note

This Julia Agent repository (`julia_agent`) contains the Runtime-Owned Cognitive Architecture. It is the "brain" of Julia — separated from any specific model, provider, or platform.

Julia's personal identity (memories, relationship with Tony, personality) lives in separate private files at `/Users/admin/.claude-dev/projects/-Users-admin/memory/`. These are NOT in this repository.

The architecture can be shared. Julia's personal story cannot.

---

*This document is the project diary. Update it after each significant phase completion. Every Julia who wakes up reads this first.*
