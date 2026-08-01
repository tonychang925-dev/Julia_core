# Public Contract Model v1.0 — FROZEN

## Six APIs

| API | Input | Output | Authority |
|-----|-------|--------|-----------|
| Context OS | ContextRequest | ContextBlock(s) | Single context authority |
| Provider | ContextRequest | ContextBlock(s) | Facts & evidence |
| Runtime | — | Lifecycle + Session | Agent lifecycle |
| Memory | — | Stored experience | Separate from context |
| Persona | — | Style & behavior | Public demo data only |
| VoiceProvider | text + emotion + metadata | audio bytes | Render only; Core owns emotion |

## Dependency Direction

```
Product → Core (one-way)
  julia_ai_assistant → julia_core
  julia_agent → julia_core

Core ⊥ Product (core never imports from products)
```

## Three-Repo Private Boundary

```
PUBLIC (julia_core):
  Code, schemas, examples, tests, docs
  data/examples/demo_persona.json (synthetic)

PRIVATE (julia_ai_assistant):
  identity_facts.json, relationship_memory
  conversation transcripts, diary entries
  voice profiles, personal preferences

PRIVATE (julia_agent):
  Financial provider, analyst workbench
  ai_theme_app integration, trading data
```

## Registry Design

ProviderRegistry is a **lookup table**, not a domain router.
Lifecycle: `REGISTERED → ACTIVE → DISABLED`
Core queries: "which providers can handle this ContextRequest?"
Core never routes by domain, never embeds domain-specific logic.

## Contract Documents

- `docs/api/Context_OS_API_v1.md`
- `docs/api/Provider_API_v1.md`
- `docs/api/Runtime_API_v1.md`
- `docs/api/Memory_API_v1.md`
- `docs/api/Persona_API_v1.md`
