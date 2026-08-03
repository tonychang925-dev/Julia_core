# ADR-016: Memory OS Authority Boundary

Status: Proposed
Date: 2026-08-02
Phase: E2.1.3 — Memory Migration

## Context

E2.1.2 migrated Julia AI Assistant away from app-level giant persona prompt as the default identity source. The next migration risk is Memory ownership.

The current application baseline still has legacy memory paths:

```text
startup_memory.py → memory files → startup context/system prompt
ReadOnlyMemoryBindingAdapter → memory summaries → provider system message
```

This risks recreating identity through memory text injection rather than governed Core memory refs.

## Decision

Freeze the Memory authority boundary:

| Concern | Owner |
|---|---|
| Historical facts and memory records | Memory OS |
| Memory preservation / L2-L3 eligibility | Continuity OS |
| Current reconstruction needs | Context OS |
| Identity representation | Persona Engine |
| HTTP/product workflow | Julia AI Assistant |

Julia AI Assistant may provide user input and consume memory refs/context blocks. It must not own memory retrieval policy, inject memory text into persona/system prompt, decide identity level, or create continuity checkpoints.

## Required Migration Direction

From:

```text
memory files → summary text → system prompt/provider messages
```

To:

```text
Memory Candidate/Query → MemoryRef → Continuity Governance → Context Requirement → ContextBlock
```

## Forbidden Patterns

```text
memory_text += system_prompt
startup_memory.py → persona/system prompt
assistant_runtime.search_memory() as authority
memory decides L3 identity
memory creates checkpoint
provider receives memory dump as identity source
```

## Consequences

Positive:

- Memory no longer acts as hidden persona.
- Identity-forming events become protected refs, not prompt text.
- Context OS receives requirements/blocks rather than raw memory dumps.
- Trace can prove memory refs used for a turn.

Cost:

- Existing app memory retrieval must be downgraded to adapter or replaced.
- Existing tests expecting memory summary injection must be migrated.
- Provider message assembly must stop receiving memory dump system messages.

## Trigger

Any E2.1.3+ work touching `startup_memory.py`, `memory/`, `ReadOnlyMemoryBindingAdapter`, memory trace, context blocks, provider message construction, or identity-forming memory tests.
