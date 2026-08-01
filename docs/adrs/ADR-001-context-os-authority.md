# ADR-001 — Context OS is the Single Context Authority

## Status

Proposed / F4.3-pre

## Context

Julia Agent already defines a Context OS responsible for context planning, budget, provenance, projection, and provider input assembly. Financial analysis is the first production domain, but future domains may include healthcare, coding, and personal assistance.

If each domain creates its own context builder and injects prompt-ready payloads, Julia will fragment into multiple domain-specific mini-agents.

## Decision

Any model-visible context must pass through Julia Context OS.

Domains may provide candidate `ContextBlock` objects and evidence references, but they may not directly assemble provider prompts or bypass Context OS planning, budgeting, provenance, and projection.

Forbidden:

```text
Domain → Prompt
Domain → Provider Input
Application Surface → Large Context Payload → Provider Input
```

Required:

```text
Domain → ContextBlock candidates → Julia Context OS → Provider Input
```

## Alternatives Considered

1. Allow each domain to own its own context builder.
   - Rejected because it duplicates Context OS and fragments Julia cognition.
2. Keep financial context builder as the first domain template.
   - Rejected because it would make financial architecture accidentally define all future domains.
3. Centralize all context authority in Julia Context OS.
   - Accepted.

## Consequences

Positive:

- One cognitive authority.
- Unified budget/provenance/conflict handling.
- Easier multi-domain expansion.
- Lower risk of prompt/context drift.

Tradeoffs:

- Domain integrations must adapt to `ContextBlock` and `DomainContextRequest`.
- Some existing V0.1 selectors become temporary adapters rather than long-term architecture.

## Trigger

Any phase that introduces contextual workbench actions, domain-specific evidence loading, or provider-facing prompt construction must comply with this ADR.
