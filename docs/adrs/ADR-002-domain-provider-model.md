# ADR-002 — Domain Provides Facts, Not Cognition

## Status

Proposed / F4.3-pre

## Context

The financial domain provides market state, themes, events, candidate evidence, risk signals, and read-only typed contracts. This is domain intelligence, but it is not Julia cognition.

Julia cognition belongs to Julia Agent Runtime: Context OS, Memory OS, Identity OS, Action Governance, and Provider Adaptation.

## Decision

Domains provide facts, evidence, and capability results. Domains do not own Julia cognition.

A Domain Provider may expose:

- typed domain facts;
- evidence references;
- read-only capability results;
- candidate `ContextBlock` objects;
- domain governance metadata.

A Domain Provider must not own:

- Context Lifecycle;
- Memory Lifecycle;
- Learning Loop;
- Prompt Assembly;
- Julia Identity;
- Julia Action Governance.

Financial domain is the first production Domain Provider, not the root architecture of Julia Agent.

## Alternatives Considered

1. Treat Julia Financial Analyst as the main product architecture.
   - Rejected because it hides the generic Agent OS behind one domain.
2. Let each domain bring its own reasoning/memory/context stack.
   - Rejected because it duplicates Agent OS layers.
3. Treat domains as capability/evidence providers behind Julia OS.
   - Accepted.

## Consequences

Positive:

- Julia Agent remains domain-general.
- Financial, healthcare, coding, and other domains can share one runtime.
- Domain governance stays isolated from Julia cognitive ownership.

Tradeoffs:

- Domain-specific workflows must be explicit about whether they are facts, evidence, evaluations, or governed memory candidates.
- Existing financial modules may need classification before merge.

## Trigger

Any new domain package or domain-specific workflow must declare whether it is a provider, workflow, surface, or core OS module.
