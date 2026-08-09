# ARCH-R0 — Canonical Authority Map

**Status**: FROZEN — ARCH-R0a clarified
**Date**: 2026-08-09

## Normative Precedence

```
1. JULIA_CORE_PRINCIPLES.md          SUPREME — architecture constitution
2. ARCH-R0 Canonical Authority Map    interpretation / refinement
3. Accepted ADRs                      subsystem decisions
4. Frozen subsystem contracts         implementation contracts
5. Implementation                     code
```

ARCH-R0 MUST NOT supersede, reinterpret away, or weaken JULIA_CORE_PRINCIPLES.md.
Where any document conflicts with the Principles, the Principles govern.

## Principle Compliance

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| P1 Runtime is Authority | ✅ PASS | Runtime owns agent architecture; subsystem truth delegated to canonical authorities |
| P2 Context OS is Single Authority | ✅ PASS | Six ContextSources feed Context OS; no source bypasses it |
| P3 Identity ≠ Memory | ✅ PASS | Persona=behavioral identity; Memory=governed experience; Knowledge=domain providers |
| P4 Provider supplies capability | ✅ PASS | Providers supply facts/evidence; Context OS, not providers, assembles model context |
| P5 Provider output ≠ Identity truth | ✅ PASS | All external output passes governance; Tony input has highest authority |

## Runtime Authority vs Subsystem Truth Authority

JULIA_CORE_PRINCIPLES.md P1 states: "Runtime owns the agent's identity, lifecycle, memory, and continuity."

ARCH-R0 does not weaken this. It clarifies it.

```
Runtime = top-level agent authority

  The model is not the agent authority.
  The provider is not the agent authority.
  The client is not the agent authority.

  Julia Runtime owns the agent architecture.

  Within that Runtime-owned architecture, each subsystem
  has exclusive truth authority over its own concern:
```

```
              Julia Runtime-owned Agent Architecture
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
   Runtime Authority                  Subsystem Truth Authorities
   lifecycle / orchestration          │
          │               ┌───────────┼───────────┐
          │               │           │           │
          │         Conversation  Continuity    Memory
          │         transcript    survival      memory
          │         truth         policy        truth
          │               │           │           │
          │         Persona      Context     Alignment
          │         behavioral   model-      provider
          │         identity     visible     adaptation
          │         truth        truth
          │
          └── orchestrates, MUST NOT reimplement or override
              subsystem policies
```

Runtime + six subsystem truth authorities. Runtime orchestrates them.
No subsystem is subordinate to another. No chain of ownership.
Runtime MUST NOT reimplement or override their policies.

## Foundational Principle

```
Storage location ≠ Authority
Projection ≠ Truth
Data boundary ≠ Cognitive boundary
```

Public/private data separation is a deployment concern. It does not determine who owns cognitive authority.

## Single Canonical Authority Map

### Conversation Authority
- **Owns**: complete canonical transcript, chronology, message/turn identity, modality, status
- **Artifact**: ConversationMessage (durable)
- **Location**: ConversationRuntime / SessionRepository (julia_core)
- **Does NOT own**: context selection, memory formation, continuity classification
- **Rule**: No derived representation (ContextTurn, Compact, prompt) may become transcript authority

### Continuity OS
- **Owns**: preservation/recovery policy, L0/L1/L2/L3 classification, identity checkpoints, recovery plans
- **Artifact**: ContinuityCheckpoint (identity refs + memory refs + relationship refs + active project refs)
- **Does NOT own**: raw transcript storage, context projection artifacts, conversation database
- **Rule**: ContinuityCheckpoint MUST remain valid if all Context OS derived artifacts are deleted

### Memory OS
- **Owns**: governed long-term experience, episodic/relationship/preference memory, retention lifecycle
- **Artifact**: Governed Memory Objects (with provenance, evidence_refs, governance approval)
- **Does NOT own**: raw conversation transcript, identity definition, context selection, domain knowledge
- **Rule**: Memory ≠ Conversation. Not everything that happened becomes memory.

### Persona Engine
- **Owns**: stable behavioral identity — tone, style, language, behavior constraints, mode switching
- **Artifact**: Compiled Persona (behavioral contract)
- **Does NOT own**: private identity facts (name, origin, relationships), private memories
- **Rule**: Persona = HOW Julia behaves. Private identity data = INPUT to persona compilation, stored in julia_ai_assistant.

### Context OS
- **Owns**: ALL model-visible context selection, projection, budgeting, provenance
- **Artifact**: ContextBlock[] → assembled model messages
- **Sources**: PersonaContextSource, ConversationContextSource, InteractionContextSource, ExperienceContextSource, CapabilityContextSource, DomainEvidenceSource
- **Does NOT own**: raw transcript storage, memory governance, continuity classification
- **Rule**: Every piece of information reaching the model MUST pass through Context OS. No domain, provider, or application surface may assemble model context independently.

### Runtime OS
- **Owns**: top-level agent execution orchestration and lifecycle authority
- **Role**: The model is not the agent authority. The provider is not the agent authority. The client is not the agent authority. Runtime is the agent authority — it orchestrates Conversation, Continuity, Memory, Persona, Context, and Alignment subsystems.
- **Does NOT reimplement**: persona truth (delegated to Persona Engine), memory truth (delegated to Memory OS), context-selection policy (delegated to Context OS), continuity classification (delegated to Continuity OS)
- **Rule**: Runtime owns the agent. Subsystem authorities own their governed truth. Runtime orchestrates — it does not collapse all truth into one module.

### Alignment OS
- **Owns**: provider-specific behavioral adaptation of a governed identity/behavior contract
- **Does NOT own**: identity definition, continuity preservation, context assembly
- **Rule**: Alignment = how the same identity contract is realized on a specific provider. Continuity = what makes it the same agent.

## Forbidden Claims

| Claim | Why Wrong | Correct |
|-------|-----------|---------|
| "Runtime owns identity, memory, context" (imprecise) | Runtime owns agent architecture. Subsystems own specific truth domains | Persona=identity truth, Memory=memory truth, Context=context truth — all Runtime-owned at architectural level, delegated to canonical subsystems |
| "Persona ≠ identity" (without qualification) | Persona = behavioral identity. Private facts = input | Persona = HOW. Private identity data = WHO facts (input) |
| "Memory OS owns Identity Memory" | Identity is Persona's domain, not Memory's | Persona Engine owns behavioral identity. Memory stores governed experiences only |
| "Alignment keeps the same agent the same agent" | This is Continuity OS's job | Alignment adapts expression; Continuity preserves identity |
| "Context OS = Domain Provider Aggregator" | Context OS is ALL model-visible context, not just domain facts | Six ContextSources feed Context OS; domain is one of them |
| "Conversation is an Interaction Layer detail" | Conversation truth is a first-class authority | ConversationRuntime is canonical transcript authority |
| "Private data boundary = cognitive authority boundary" | Data residency ≠ authority ownership | Core owns schemas/governance; private repos own instance data |

## Document Disposition

Documents that contain claims conflicting with this Authority Map are superseded where they conflict. They remain valid for non-conflicting content and as historical architecture record.

Full reconciliation required for:
- README.md (§ "runtime owns identity, memory, context, and voice")
- ARCHITECTURE_STATUS.md (§ "julia_ai_assistant contains Julia's persona, memory, voice")
- ARCHITECTURE_OVERVIEW.md (§ Layer 3 places conversation as interaction detail)
- CONTEXT_OS_DESIGN.md (§ pipeline places Persona AFTER Context OS assembly)
- MEMORY_OS_DESIGN.md (§ Identity Memory claiming "Who I am")
- ALIGNMENT_OS_DESIGN.md (§ claiming Continuity OS's question)
- PERSONA_ENGINE_DESIGN.md (§ body text claims "defines agent's stable identity" — correct; not conflicting)
- ADR-005 (§ "Persona Engine owns HOW. Private Identity provides WHO" — correct direction)
- Public_Contract_Model_v1.md (§ Persona API "Persona ≠ identity" — imprecise)
- Persona_API_v1.md (§ "Persona ≠ identity" — imprecise)
- CORE_RUNTIME_STATUS.md (§ claims "Memory lives in julia_ai_assistant" — confuses data boundary with authority)
