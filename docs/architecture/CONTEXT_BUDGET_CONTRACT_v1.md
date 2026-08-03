# Context Budget Contract v1.0

Status: FROZEN
Phase: E2.2.2 — Context Budget Management
Date: 2026-08-02

## 1. Purpose

Context Budget is a cognitive budget, not just a token limit.

It decides how Julia allocates limited provider context capacity while preserving identity density and task intelligence.

## 2. Budget Model

```python
ContextBudget(
    total_budget=8000,
    identity_budget=500,
    relationship_budget=500,
    project_budget=2000,
    task_budget=3000,
    conversation_budget=2000,
)
```

Categories:

| Category | Meaning |
|---|---|
| identity | identity-origin / identity-anchor context |
| relationship | Tony-Julia relationship state |
| project | long-running project architecture/context |
| task | current task execution context |
| conversation | recent session / active turn context |
| general | low-specificity supporting context |

## 3. Authority Boundary

Context OS owns allocation.

| Layer | Owns | Forbidden |
|---|---|---|
| Memory OS | storage / refs | token allocation |
| Continuity OS | protection | budget allocation |
| Context OS | allocation / selection | memory storage |
| Provider | generation | deciding what to keep |

## 4. Required Chain

```text
RankedContextCandidate
    ↓
ContextBudget
    ↓
ContextBudgetAllocator
    ↓
BudgetedContextSelection
    ↓
Provider-readable context
```

## 5. Pressure Rule

Under budget pressure:

```text
identity density + task relevance > recency volume
```

Forbidden:

```text
recent messages always win
LLM summarizes because prompt too long
memory importance decides token allocation
raw memory dump fills remaining context
```

## 6. Trace Requirements

Budget trace must expose:

```json
{
  "authority": "ContextOS",
  "total_budget": 10000,
  "used_tokens": 3700,
  "category_allocations": {
    "identity": 2000,
    "relationship": 1500,
    "project": 3000
  },
  "selected": ["memory://event/julia-core-origin"],
  "dropped": ["chat://noise"]
}
```

## 7. E2.2.2 Scope

Included:

- deterministic allocation
- category caps
- pressure tests
- no external authority dependencies

Excluded:

- LLM summarization
- dynamic compression
- vector ranking
- multi-provider validation
- latency optimization

