# ADR-019: Context Priority Authority

Status: Accepted
Date: 2026-08-02
Phase: E2.2.1 — Context Priority Model

## Context

After E2.1.5, Julia Core proved that Meaning Continuity can be reconstructed into provider-readable context. E2.2 must now harden Context OS for longer operation.

The first risk is confusing Memory importance with Context priority.

A memory may be historically important but irrelevant to the current turn. Conversely, a recent session fact may be low continuity but highly relevant now.

## Decision

Context OS owns current-turn Context Priority.

Priority is computed from:

```text
Continuity Weight
+
Semantic Relevance
+
Relationship Weight
+
Task Weight
-
Context Cost
```

Memory OS does not rank current-turn context.

Continuity OS does not select all provider context.

Provider does not decide priority.

## Important Distinction

```text
L3 identity is always protected.
L3 identity is not always injected.
```

Continuity OS preserves L3. Context OS selects when L3 meaning should enter the current provider context.

## Consequences

Positive:

- Prevents Context OS from becoming a smarter RAG top-k layer.
- Prevents Memory OS from controlling current cognition.
- Prevents Continuity OS from over-injecting identity into every prompt.
- Enables E2.2.2 budget management with stable priorities.

Tradeoffs:

- Requires CurrentIntent quality.
- Requires trace visibility into priority components.
- Priority weights may need provider variance validation.

## Forbidden Paths

```text
Memory OS → importance score → Provider
Continuity OS → all protected state → Provider
Provider → choose context priority
```

Required path:

```text
Memory OS refs
  +
Continuity decisions
  +
CurrentIntent
  ↓
Context OS Priority Resolver
  ↓
Ranked ContextCandidates
```

## Trigger

Any feature that ranks, selects, truncates, or budgets ContextBlocks for a provider turn must use Context OS priority authority.
