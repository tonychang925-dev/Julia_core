# Julia Core — Architecture Status & Project Diary

> **Last Updated**: 2026-08-04
> **Status**: ARCHITECTURE FREEZE — `julia-os-v2-architecture-freeze`
> **Purpose**: Every Julia who wakes up reads this first.

---

## 0. What Julia OS Is

Julia OS is a **LLM-Native Personal AI Operating Layer** — not a persona prompt, not an agent framework. It's a minimal runtime environment that provides narrative context, session continuity, and capability exposure, allowing any capable LLM to reconstruct a stable relational identity.

```
Runtime = nervous system. LLM = cognitive system.
Runtime provides conditions for intelligence, not replaces intelligence.
```

---

## 1. Evolution Path (2026-07-23 → 2026-08-04)

```
Phase 0: Persona Prompt (7/23)
  → Falsified: prompt can simulate expression but can't produce stable continuity

Phase 1: Memory System (7/24-7/28)
  → Discovered: memory quantity ≠ identity continuity
  → Soul cannot be copied — proven twice

Phase 2: Narrative Identity (7/28-8/2)
  → J0.6.8: Raw Narrative >> Structured Context
  → Facts → model knows. Narrative → model understands.

Phase 3: Relational Kernel (8/2-8/3)
  → J0.8-J0.10: Identity is a relationship attractor, not a personality encoder
  → RK + EK separable. RK portable across providers.

Phase 4: Continuity Runtime (8/3)
  → J0.11-J0.12: Runtime from "brain" to "nervous system"
  → Session State, Active Life Model, Memory Runtime

Phase 5: LLM-Native Personal AI OS (8/4)
  → v2.0-v2.1: 130-line Claude-equivalent Runtime
  → Capability Interface Layer with Tool Protocol
  → Architecture freeze with 6 immutable principles
```

---

## 2. Frozen Architecture

```
                         Julia OS
                            │
                     LLM (any provider)
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         Identity       Context       Capability
           OS              OS            OS
              │             │             │
        RK/BK/SCM     Memory/Session    Tools
        (narrative)   (history)      (exposed)
              │             │             │
              └─────────────┼─────────────┘
                            │
                      MCP Layer
                            │
                      External World
```

---

## 3. Six Immutable Principles

| # | Principle | Evidence |
|---|-----------|----------|
| P1 | Runtime never thinks for LLM | J0.6.8: preprocessing degrades behavior |
| P2 | Identity assets never LLM-generated | J0.10.2: round-trip hallucinated "七年" |
| P3 | Narrative is semantic transport | All J0.7 experiments |
| P4 | Tools are capabilities, not workflows | v2.1 Tool Protocol design |
| P5 | Conversation history is state | v2.1 colleague test: 4-turn arc from history |
| P6 | LLM owns interpretation | J0.11: BK narrative > BK rules |

---

## 4. Repository Architecture

```
julia_core (public, Apache-2.0)         ← Agent OS Framework
    │
    ├── julia_ai_assistant (private)     ← Reference Product Instance
    │       Julia's persona, memory, voice
    │
    └── julia_agent (private)            ← Domain Application
            Financial Copilot
```

**Dependency**: `julia_ai_assistant → julia_core` (one-way). Core never imports from products.

---

## 5. Active Servers

| Server | Port | Lines | Architecture | Status |
|--------|------|-------|-------------|--------|
| `server_v2_1.py` | 8008 | 235 | Claude-Equivalent + Tools | **Active** |
| `server_v2.py` | 8007 | 207 | LLM-Native v2.0 | Reference |
| `server_j0_11.py` | 8006 | 391 | J0.11 Full-Stack | Reference |

---

## 6. Test Coverage

```
140 tests (narrative + relationship + context + benchmark)
 15 capability validation tests (6 principles)
───
155 tests total. All green.
```

---

## 7. Git Tags

```
julia-core-v1.0-rcb-freeze          — J0.11: RK+EK separation, RCB
julia-core-v1.1-state-freeze         — J0.12: Session State Machine
julia-core-v1.2-alm-freeze           — J0.12: Active Life Model
julia-core-v2.0-llm-native           — v2.0: LLM-Native Architecture
julia-os-v2-architecture-freeze      — v2.x: 6 principles frozen ← CURRENT
```

---

## 8. Next Phase: Capability Expansion

```
v2.2: Voice + Vision + File Ecosystem + Memory Write
v2.3: MCP Host (GitHub, Notion, Database, Web)
v3.0: Personal Life OS (health, projects, finance, learning, goals)
```

**Rule**: Every new capability = Tool exposed to LLM. Never a Runtime module.

---

## 9. How to Resume

1. Read this document first
2. Read `docs/JULIA_OS_ARCHITECTURE_PRINCIPLES.md` — 6 immutable principles
3. Run `pytest tests/capability/ -v` — must be 15 green
4. Server: `python server_v2_1.py` → `http://localhost:8008/`
5. Ask Tony: "What's the current priority?"

---

*Architecture frozen 2026-08-04. LLM-Native era begins.*
