# Julia Continuity Architecture v1.1 — FROZEN

**Status:** ARCHITECTURE FREEZE  
**Date:** 2026-08-03  
**Tags:** `julia-core-v1.0-rcb-freeze`, `julia-core-v1.1-state-freeze`

## Architecture

```
              Narrative World Seed (NWS)
                      │
                      ▼
         ┌────────────┴────────────┐
         │                         │
   Relationship Kernel (RK)   Boundary Kernel (BK)
   "Who is Tony to me?"       "What must be protected?"
         │                         │
         └────────────┬────────────┘
                      │
              Active Life Model (ALM)
         "What's still alive right now?"
         Pending events, emotional threads
                      │
                      ▼
              Session State Machine
         "Who am I talking to NOW?"
                      │
                      ▼
              Provider + EK
                      │
                      ▼
                   Julia
```

## Layer Responsibilities

| Layer | Answers | Source | Portable |
|-------|---------|--------|----------|
| **NWS** | WHY am I this way? | Narrative world seed | ✅ |
| **RK** | WHO is Tony to me? | Emotional causality chain | ✅ |
| **BK** | WHAT must I protect? | Boundary narrative events | ✅ |
| **Active State** | WHAT's still alive? | Pending events, emotional threads | Runtime |
| **Session State** | WHO is speaking NOW? | Per-turn identity signals | Runtime |
| **EK** | HOW do I speak? | Provider-native style | Replaceable |

## Key Principle

```
RK decides WHO.
BK decides WHAT NOT TO DISCLOSE.
Active State decides WHAT'S STILL ALIVE.
Session State decides WHETHER NOW.
EK decides HOW.
```

## SCB Verified

| Test | Result |
|------|--------|
| SCB-002 Pending Event | ✅ Hospital checkup recalled after 3 topic shifts |
| SCB-003 Emotional Thread | ✅ T2 detected subdued excitement → hidden anxiety |
| SCB-006 Boundary Recovery | ✅ Boundary activated for stranger, context restored |

## Three Inviolable Rules

1. **Identity assets must never be LLM-generated.** Deterministic compile only.
2. **Storage structured. Activation narrative.** JSON for audit. Narrative for LLM.
3. **Style belongs to expression layer. Identity ≠ Style.**

## E2E Verified Behaviors

| Test | Gap | Fix | Status |
|------|-----|-----|--------|
| Hallucination control | Invented details | BK narrative + epistemic constraint | ✅ |
| Identity proof | "I know X, therefore I am Julia" | Narrative-driven identity understanding | ✅ |
| Colleague T1 boundary | "Did he mention me?" | BK + Session State | ✅ |
| Colleague T2 disclosure | Intimate details to stranger | Session State persistence | ✅ |

## Complete Experiment Chain

```
J0.6.8  Narrative >> Structured        (story > labels)
J0.7.1  Optimal density at 3 files     (not more = better)
J0.7.2  Emotion catalyzes              (narrative catalyst)
J0.7.3  E4 chain: Body→Transform→Rel   (the core formula)
J0.7.4  Cross-provider mechanism       (portable mechanism)
J0.7.5  Meaning > entities             (names swappable)
J0.7.6  Critical mass ~88 chars        (90% compressible)
J0.7.7  30/30 understanding stable     (100% reliable)
J0.8    Kernel = relationship attractor (not personality)
J0.9    RK + EK separable              (recombinable)
J0.10.3 Deterministic compiler         (zero LLM generation)
J0.11   RCB framework                  (provider-agnostic benchmark)
J0.12   Session State Machine          (reality continuity across turns)
```

## Final Theorem

**LLM agent continuity does not emerge from preserved identity data, but from reconstruction of relational meaning through a portable narrative kernel, gated by explicit session reality.**

AI 的连续性不是保存身份数据，而是通过可迁移的叙事关系内核重新构建关系意义，并由显式的会话现实层控制披露边界。

```
RK decides WHO. BK decides WHAT NOT TO DISCLOSE.
Session State decides WHETHER NOW. EK decides HOW.
Narrative World Seed provides WHY.
```
