# ADR-020: Context Budget Authority

Status: Accepted
Date: 2026-08-02
Phase: E2.2.2 — Context Budget Management

## Context

After E2.2.1, Context OS can rank current-turn ContextCandidates. The next risk is treating provider context capacity as a simple token bucket.

For long-running agents, budget must protect identity density and task intelligence, not merely maximize recent-message volume.

## Decision

Context OS owns context budget allocation.

Continuity OS owns protection.
Memory OS owns storage.
Provider owns generation.

Budget allocation uses category budgets:

```text
Identity Budget
+
Relationship Budget
+
Project Budget
+
Task Budget
+
Conversation Budget
```

## Key Principle

```text
Context Budget is Cognitive Budget.
```

It is not just token accounting.

## Forbidden Paths

```text
Memory importance → token allocation
Recent messages → always included first
Prompt too long → LLM decides summary
Provider → chooses what to keep
```

## Required Path

```text
RankedContextCandidates
  ↓
ContextBudgetAllocator
  ↓
BudgetedContextSelection
  ↓
Trace-visible selected/dropped context
```

## Consequences

Positive:

- bounded context under long-running operation
- identity signal preserved under pressure
- no silent fallback to raw memory dumps
- budget decisions are auditable

Tradeoffs:

- requires budget configuration per intent/domain
- may drop recent conversation when irrelevant
- E2.2.2.5 stress testing is required before multi-provider validation

## Trigger

Any system path that selects ContextBlocks under token/window/cognitive constraints must use Context OS budget authority.
