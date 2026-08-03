# ADR-018: Context Semantic Reconstruction Authority

Status: Accepted
Date: 2026-08-02
Phase: E2.1.5 — Julia Identity Migration Gate Alpha v1.0

## Context

E2.1.5 real-provider validation showed that Julia Identity migration requires more than persisted MemoryRefs and Continuity decisions.

The initial DeepSeek Alpha failure had the following evidence:

```text
MemoryRef exists
Continuity Governance PASS
Architecture Evidence 100/100
Continuity Integrity 100/100
DeepSeek semantic recall FAIL
```

E2.1.5.3 and E2.1.5.4 narrowed the gap to provider-facing meaning transmission:

```text
GovernedMemoryRef
    ↓
ContinuityDecision
    ↓
Provider-readable SemanticContextBlock
    ↓
Provider
```

## Decision

Context OS owns semantic reconstruction.

Context OS MAY:

- transform governed references into provider-readable semantic context;
- create current-turn SemanticContextBlocks;
- preserve source references in ContextBlocks;
- adapt semantic block shape for provider consumption.

Context OS MUST NOT:

- store memory;
- decide identity importance;
- modify Persona Artifact;
- create or modify Continuity checkpoints;
- restore old prompts;
- inject raw memory dumps;
- become a Provider or Provider router.

## Authority Boundary

| Layer | Authority | Not Allowed |
|---|---|---|
| Persona Engine | identity representation | memory retrieval, checkpoints |
| Memory OS | historical facts and refs | identity importance decisions |
| Continuity OS | preservation policy | provider calls, prompt assembly |
| Context OS | semantic reconstruction for current turn | memory storage, identity ownership |
| Provider | model execution | identity, memory, continuity, context authority |

## Consequences

Positive:

- Provider receives enough meaning to preserve behavior continuity.
- MemoryRef remains refs-only and governed.
- Julia avoids reverting to giant prompt or raw memory injection.
- Context OS becomes the explicit meaning reconstruction layer.

Tradeoffs:

- Context OS must now manage provider-readable wording quality.
- Future E2.2 work must define priority and budget rules for multiple semantic blocks.
- Provider variance testing is required because different models may use semantic context differently.

## Alternatives Considered

1. **Inject raw memory into provider prompt**
   - Rejected: reintroduces legacy memory dump architecture.

2. **Move origin meaning into Persona Artifact**
   - Rejected: historical meaning would pollute identity representation.

3. **Let Continuity OS generate provider text**
   - Rejected: Continuity would become a prompt/context owner.

4. **Create a new Semantic OS**
   - Rejected: semantic binding is a Context OS capability, not a new authority layer.

## Trigger

This ADR applies whenever governed MemoryRefs or Continuity decisions need to become current-turn provider context.

Required chain:

```text
MemoryRef
  ↓
Memory Governance
  ↓
Continuity Decision
  ↓
Context OS Semantic Reconstruction
  ↓
Provider-readable ContextBlock
  ↓
Provider
```
