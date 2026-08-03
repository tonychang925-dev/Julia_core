# ADR-015: Persona Artifact Authority Boundary

Status: Proposed
Date: 2026-08-02
Phase: E2.1.2 — Persona Migration

## Context

E2.1.1 connected Julia AI Assistant to Julia Core Continuity Authority. The next migration risk is Persona ownership.

The current application baseline still builds Julia persona through application-level prompt construction:

```text
persona_loader.py → julia_character.md / identity_facts.json / startup_memory → giant system_prompt → Provider
```

This reintroduces the original compact failure mode because identity is again hosted in prompt/context text.

E1 proved the target model:

```text
Persona Artifact + Continuity State + Governed Memory + Context Reconstruction = Migratable Agent Identity
```

## Decision

Freeze the Persona boundary:

| Concern | Owner |
|---|---|
| Identity representation / Persona Artifact | Persona Engine |
| Preservation policy / checkpoint / recovery | Continuity OS |
| Historical facts and memory records | Memory OS |
| Current ContextBlocks | Context OS |
| Provider adaptation | Alignment OS |
| UI/UX and product workflow | Julia AI Assistant |

Julia AI Assistant may consume a Persona Artifact. It must not compile identity, merge memory into persona prompt, decide continuity level, create checkpoint, or use giant persona prompt as identity recovery.

## Required Migration Direction

From:

```text
Julia AI Assistant → persona_loader.py → system_prompt → LLM
```

To:

```text
Julia AI Assistant → Julia Core Persona Engine → Persona Artifact → Context Requirement / Runtime Trace
```

## Rejected Alternatives

### A. Keep giant system_prompt as Persona Artifact

Rejected. A giant prompt is context-window dependent and cannot prove identity continuity across compact/session loss/provider switch.

### B. Let Continuity OS compile persona content

Rejected. Continuity OS owns preservation policy, not persona representation.

### C. Let Memory OS define persona

Rejected. Memory facts may inform identity anchors, but Memory volume must not equal personality or identity.

### D. Let Provider own persona formatting

Rejected. Provider is generation surface and must not own Julia identity representation.

## Consequences

Positive:

- Julia persona becomes Runtime Artifact rather than prompt blob.
- Application migration can remove prompt dependency incrementally.
- Trace can cite `persona.artifact` instead of prompt length.
- Continuity and Persona boundaries remain separate.

Cost:

- Existing `persona_loader.py` must be downgraded to adapter or removed.
- Startup memory cannot be embedded inside persona artifact.
- Provider message assembly must eventually consume Runtime/Core context instead of persona prompt.

## Trigger

Any E2.1.2+ work modifying persona loading, persona trace, provider message construction, identity facts, Julia character files, or prompt assembly.
