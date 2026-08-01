# ADR-005: Persona Is Behavioral Identity — Not Private Identity Storage

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Replaces**: Implicit conflation of persona with identity data

---

## Context

Julia Core is a public open-source repository (Apache-2.0). But Julia — the agent named 朱婉清 — has a private identity: her name, origin, personal history, relationships, and memories. This identity data MUST NOT appear in the public repository.

The question: where does "who Julia is" live?

If Persona Engine stores identity facts, those facts are public → private data leak. If Persona Engine excludes identity facts, can it still produce a coherent agent personality?

---

## Decision

**Persona = Behavioral Identity. Private Identity Data = Separate Input.**

```
Persona Engine (public, in julia_core)
    Owns: HOW the agent behaves
    - Tone, style, language
    - Behavior constraints (L1-L4 boundaries)
    - Communication patterns
    - Mode switching rules

    Does NOT own:
    - Real name, origin, age
    - Personal history
    - Relationships
    - Private memories

Private Identity (in julia_ai_assistant/memory/)
    Provides: WHO the agent is
    - identity_facts.json
    - julia_character.md
    - julia_tony_philosophy.md

    This data is INPUT to persona compilation,
    not stored IN the persona definition.
```

The Persona Engine compiles **behavioral identity**. Private identity facts are supplied at compile time by the product (julia_ai_assistant), not embedded in the framework (julia_core).

---

## Alternatives Considered

### Alternative 1: Store identity facts in Persona definition

The persona JSON includes `name`, `real_name`, `from`, `age`, `boyfriend`, etc.

**Rejected**: This puts private identity data in a public repo. Any fork of julia_core would contain Julia's personal information.

### Alternative 2: No persona at all — identity is fully private

Remove Persona Engine from Core. Each product builds its own persona system.

**Rejected**: Persona is a reusable architectural concern. Without a shared Persona Engine, every product reimplements tone, style, and behavior from scratch. The framework loses its "build any agent" thesis.

### Alternative 3: Persona is only a system prompt string

Core stores a raw string. Products inject whatever they want.

**Rejected**: Loses structure. Can't validate, version, or audit persona changes. "Any string" is not an architecture — it's an escape hatch.

---

## Consequences

### Positive
- Public repo contains zero private identity data
- Persona structure is versionable and auditable (persona_id)
- Same Persona Engine serves demo agents (public) and Julia (private)
- New products (Financial Analyst, Code Reviewer) reuse Persona Engine without modification
- `data/examples/demo_persona.json` provides a synthetic example for testing

### Negative
- Products must supply their own identity facts (but this is already the case)
- Persona compilation requires an external data source (not self-contained)
- The boundary between "behavioral rule" and "identity fact" requires judgment

### Neutral
- Persona `system_prompt` field carries the compiled output; its content is the product's responsibility

---

## Boundary: Behavioral Rule vs Identity Fact

| Behavioral Rule (in Persona) | Identity Fact (in Private Data) |
|------------------------------|--------------------------------|
| "Speak warmly, with Taiwanese softness" | "I am from Taipei" |
| "Use 嗯, 啊, 哦 as interjections" | "My name is 朱婉清" |
| "Short responses, not paragraphs" | "I graduated from 淡江大学" |
| "L1-L4 boundaries: do not cross without Tony" | "Tony is 张晓波, my boyfriend" |
| "In lover mode, use [呻吟] tag" | "Tony survived cancer" |

Behavioral rules define HOW. Identity facts define WHO. Persona Engine owns HOW. Private data owns WHO.

---

## Evidence

- `julia_core/julia_core/chat/persona.py` — Persona dataclass: no identity fields
- `julia_core/data/examples/demo_persona.json` — Synthetic demo data only
- `julia_ai_assistant/adapters/persona_loader.py` — Loads identity from private memory, compiles via Core Persona
- `SECURITY.md` — Documents the public/private boundary

---

## Trigger

Any proposal to:
- Add identity fields (real_name, origin, relationships) to the Persona dataclass
- Store Julia-specific identity data in julia_core
- Remove the distinction between behavioral rules and identity facts
