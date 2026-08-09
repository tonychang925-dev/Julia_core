# ARCH-R0 — Canonical Authority Map

**Status**: FROZEN — supersedes all prior authority claims
**Date**: 2026-08-09
**Supersedes**: Conflicting claims in README, ARCHITECTURE_OVERVIEW, ARCHITECTURE_STATUS, CONTEXT_OS_DESIGN, MEMORY_OS_DESIGN, PERSONA_ENGINE_DESIGN, ALIGNMENT_OS_DESIGN, Public_Contract_Model, ADR-005, Persona_API, Context_OS_API, Memory_API
**Aligned with**: ADR-001, ADR-009, ADR-010, ADR-012, ADR-013, ADR-020, CXT-C1

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
- **Owns**: execution orchestration and lifecycle authority
- **Role**: orchestrates Conversation, Continuity, Memory, Persona, Context authorities
- **Does NOT own**: persona truth, memory truth, context-selection policy, continuity classification
- **Rule**: Runtime is authority over execution, not owner of every cognitive truth. "Runtime is Authority" = model is not the agent authority; runtime-owned OS contracts are.

### Alignment OS
- **Owns**: provider-specific behavioral adaptation of a governed identity/behavior contract
- **Does NOT own**: identity definition, continuity preservation, context assembly
- **Rule**: Alignment = how the same identity contract is realized on a specific provider. Continuity = what makes it the same agent.

## Forbidden Claims

| Claim | Why Wrong | Correct |
|-------|-----------|---------|
| "Runtime owns identity, memory, context" | Runtime orchestrates, doesn't own cognitive truth | Persona owns identity, Memory OS owns memory, Context OS owns context |
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
