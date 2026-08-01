# Phase Contract D1 — Julia Core Architecture Documentation Refresh

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Principle**: Contract-first → Implementation → Verification

---

## Motivation

Julia Core has crossed a critical threshold:

```
Before: Core extracted from julia_agent (refactoring artifact)
After:  Universal Agent OS capable of hosting Julia, Financial Agent, and future agents
```

The codebase now reflects this — Context OS frozen, Runtime integrated, Domain Provider model validated, Financial Provider decoupled, VoiceProvider frozen, Julia AI Assistant product-layered. But the documentation still reads like a framework README from the extraction era.

This phase upgrades documentation from **"code description"** to **"architecture constitution"**.

---

## Scope (Frozen)

### D1.1 — Rewrite README.md

Upgrade from `Julia Core v0.1.0` to `Julia Core OS v0.2`.

New README must communicate:

```
Julia Core OS = Agent Operating System
  → One Agent Runtime
  → Multiple Personalities (Persona Engine)
  → Multiple Domains (Domain Providers)
  → Cross-model migration (LLM = Interpreter, Runtime = Authority)
  → Voice capability (Voice OS — emotion, prosody, TTS protocol)
  → Memory continuity (Memory OS — governed, persistent, transferable)
```

Must include:
- New architecture diagram (4-layer: Runtime OS → Cognitive Layer → Interaction Layer → Provider Layer)
- Core positioning statement (not chatbot, not LLM wrapper)
- Quick start that actually works
- Link to all key docs

### D1.2 — Create ARCHITECTURE_OVERVIEW.md

Location: `docs/architecture/ARCHITECTURE_OVERVIEW.md`

Content:
- Four-layer OS model diagram
- Module map (every julia_core/ module with one-line purpose)
- Data flow: ContextRequest → ContextBlock → Provider → Memory
- Cross-cutting: provenance, governance, lifecycle
- Three-repo architecture diagram
- API contract summary (6 APIs)

### D1.3 — Create JULIA_CORE_PRINCIPLES.md

Location: `docs/architecture/JULIA_CORE_PRINCIPLES.md`

Five principles:
1. **Runtime is Authority** — LLM is interpreter (replaceable), Runtime is permanent
2. **Context OS is Single Authority** — one context pipeline, domains supply facts only
3. **Identity ≠ Memory** — Persona / Memory / Knowledge are separate layers
4. **Provider supplies capability, not cognition** — facts + evidence + audio, never prompt/reasoning/identity
5. **Provider output ≠ Identity truth** — all external output must pass governance

Each principle includes:
- Statement
- Why (the problem it solves)
- Anti-pattern (what NOT to do)
- Implementation evidence (where it's enforced in code)

---

## Non-Scope (Explicitly Excluded)

- D2 subsystem docs (Context OS, Memory OS, Persona, Voice OS deep-dives)
- D3 developer guides (Build Your First Agent, Create Provider)
- D4 reference demos
- New ADRs (ADR-004, ADR-005 to be written in D2)

---

## Acceptance Criteria

- [ ] README.md rewritten — positions Julia Core as Agent OS, includes 4-layer diagram
- [ ] ARCHITECTURE_OVERVIEW.md exists — complete module map, data flow, repo architecture
- [ ] JULIA_CORE_PRINCIPLES.md exists — 5 principles with anti-patterns and evidence
- [ ] All cross-references between 3 docs are consistent
- [ ] Links from README to all existing docs are valid
- [ ] No stale references to old monorepo paths (`runtime/core/`, `julia_agent/`)

---

## Verification

```bash
# Check no stale paths
grep -r "runtime/core/" docs/ README.md && echo "FAIL" || echo "PASS"
grep -r "julia_agent/" docs/ README.md && echo "FAIL" || echo "PASS"

# Check all linked files exist
python3 -c "Check all markdown links resolve"

# Check consistency
# - Test count matches (72)
# - Phase names match across docs
# - API count matches (6)
```
