# Julia Core Runtime Status

> Status Baseline: C2.1 — Voice Provider Independence Verified  
> Date: 2026-08-01

## 1. Current Phase

```text
C2.1 — Voice Provider Independence Verification ✅
C2.5 — Julia AI Assistant Reference 🔄 IN PROGRESS
```

## 2. Context OS

Independent:

```text
✅ Yes
```

`julia_core.context_os` imports without any domain provider. `ContextRequest` can be created without domain data. `ContextResolver` runs with an empty provider set.

## 3. Domain Dependency

None:

```text
✅ Yes
```

Boundary scan: `julia_core/julia_core/`

Forbidden dependency terms checked:
```text
financial, stock, market, theme, ai_theme_app,
identity_facts, claude_diary, relationship_memory
```

Result: **PASS** — no forbidden dependency terms in julia_core source.

## 4. Provider Boundary

Validated:

```text
✅ Yes
```

Core depends only on:
```text
ContextRequest / ContextBlock (context_os)
DomainProvider protocol (providers)
VoiceProvider protocol (providers)
```

Provider replacement verified with mock providers. No Core code changes required when providers are replaced.

## 5. Voice Provider Independence (C2.1)

12 independence tests:
```text
✅ VoiceProvider protocol is Core-owned
✅ CognitiveEmotion is Core-owned (8 states)
✅ SpeechProsodyPlanner is Core-owned
✅ Edge TTS provider is external (example only)
✅ No hard dependency on any TTS engine
✅ Providers render audio bytes only
✅ Core owns emotion + prosody decisions
✅ VoiceProvider lifecycle matches DomainProvider (REGISTERED→ACTIVE→DISABLED)
✅ Registry supports VoiceProvider lookup
✅ VoiceProvider excluded from context assembly
✅ Persona usable without any VoiceProvider
✅ VoiceProvider replaceable without Core changes
```

## 6. Memory Boundary

`ContextBlock` is not Memory:

```text
✅ Confirmed
```

ContextBlock is a short-lived context candidate with optional TTL/expiration. Not a long-term persisted Memory object. Memory lives in julia_ai_assistant, never in julia_core.

## 7. Current Core Shape

```text
julia_core/julia_core/
  context_os/          ContextBlock, ContextRequest, Planner, Resolver
  runtime/             Lifecycle, Session Manager, Context Runtime
  providers/           DomainProvider + VoiceProvider protocols, Registry
  memory/              Governance, Lifecycle, Retrieval, Persistence
  voice_os/            CognitiveEmotion (8 states), SpeechProsodyPlanner
  persona/             Persona Compiler, Behavior Policies
  chat/                Persona, ChatSession, ChatProvider
  + 13 supporting modules
```

## 8. Test Coverage

```text
72 tests pass (zero domain dependencies in Core)
- VoiceProvider: 12 independence tests
- Persona: public demo data only
- Registry: lookup only, no router methods
```

## 9. Next Phase

```text
C2.5 — Julia AI Assistant Reference (in progress)
C3   — Developer Experience (next)
```
