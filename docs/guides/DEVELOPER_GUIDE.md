# Julia Core — Developer Guide

> **Target**: Developers who want to build agents on Julia Core OS  
> **Prerequisites**: Python 3.10+, `pip install julia-core`  
> **Time to first agent**: ~30 minutes

---

## What You'll Build

By the end of these guides, you'll understand:

```
Your Agent
    │
    ├── Persona        "Who my agent is"
    ├── Domain Provider  "What my agent knows"
    └── Voice Provider   "How my agent sounds"
```

All running on Julia Core OS — the same runtime that powers Julia AI Assistant and Financial Analyst.

---

## Guide Map

### Start Here
**[Build Your First Agent](BUILD_YOUR_FIRST_AGENT.md)**
→ Create a running agent in 30 minutes. Persona, chat, voice.

### Extension Points
Julia Core has three extension points. Learn them in any order:

**[Create a Domain Provider](CREATE_DOMAIN_PROVIDER.md)**
→ Give your agent domain knowledge (financial data, documentation, APIs).
Learn the Provider contract: `ContextRequest → ContextBlock`.

**[Create a Voice Provider](CREATE_VOICE_PROVIDER.md)**
→ Give your agent a voice. Any TTS engine.
Learn the VoiceProvider contract: `text + emotion → audio bytes`.

**[Create a Persona](CREATE_PERSONA.md)**
→ Define who your agent is. Tone, style, behavior, boundaries.
Learn why Persona ≠ Prompt.

---

## Architecture Quick Reference

### Four-Layer OS Model

```
Layer 1: Runtime Layer     — lifecycle, session, execution
Layer 2: Cognitive Layer   — Context OS, Memory OS, Persona Engine
Layer 3: Interaction Layer — Chat, Voice OS
Layer 4: Extension Layer   — Domain Providers, Voice Providers, Model Providers
```

### Three Boundaries

```
Core owns cognition        — reasoning, context, memory, identity
Provider supplies capability — facts, audio, inference
Application owns experience — persona, domain, behavior
```

### Five Principles

| # | Principle | What it means for you |
|---|-----------|----------------------|
| P1 | Runtime is Authority | Your agent survives model changes |
| P2 | Context OS is Single Authority | One context pipeline. Don't bypass it. |
| P3 | Identity ≠ Memory | Persona, memory, knowledge are separate layers |
| P4 | Provider supplies capability, not cognition | Your provider returns facts/audio, not reasoning |
| P5 | Provider output ≠ Identity truth | Govern before saving to memory |

Read the full principles: [JULIA_CORE_PRINCIPLES.md](../architecture/JULIA_CORE_PRINCIPLES.md)

---

## Quick Reference

| I want to... | Read this |
|-------------|-----------|
| Build my first agent | [BUILD_YOUR_FIRST_AGENT.md](BUILD_YOUR_FIRST_AGENT.md) |
| Add domain knowledge | [CREATE_DOMAIN_PROVIDER.md](CREATE_DOMAIN_PROVIDER.md) |
| Add voice to my agent | [CREATE_VOICE_PROVIDER.md](CREATE_VOICE_PROVIDER.md) |
| Define agent personality | [CREATE_PERSONA.md](CREATE_PERSONA.md) |
| Understand the architecture | [ARCHITECTURE_OVERVIEW.md](../architecture/ARCHITECTURE_OVERVIEW.md) |
| Understand design principles | [JULIA_CORE_PRINCIPLES.md](../architecture/JULIA_CORE_PRINCIPLES.md) |
| See a full example | [providers/examples/](../../providers/examples/) |

---

## Important: Julia Core ≠ Julia

Julia Core is the **platform**. The agent named "Julia" (朱婉清) is a **private product** built on Julia Core.

```
julia_core (public, Apache-2.0)     ← This is what you're building on
julia_ai_assistant (private)        ← The girl named Julia — a reference product
```

All examples in these guides use a synthetic "Demo Assistant" — never Julia's private identity.

---

## Next Step

→ [Build Your First Agent](BUILD_YOUR_FIRST_AGENT.md)
