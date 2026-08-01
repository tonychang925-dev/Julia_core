# Memory Continuity Governance Binding Design

Status: DRAFT-FROZEN
Phase: E1.4 — Memory Continuity Governance Binding
Scope: Julia Core OS
Generated At: 2026-08-01

## 1. Purpose

Define how Memory OS candidate facts become Continuity OS preservation decisions.

This is governance binding, not memory storage integration.

```text
Memory OS
  answers: what happened

Continuity OS
  answers: what must survive and why
```

## 2. Core Flow

```text
Memory Ref
  ↓
MemoryContinuityRequest
  ↓
ContinuityPolicy
  ↓
ContinuityEligibilityDecision
  ↓
ProtectedMemoryRef
  ↓
ContinuityCheckpoint
```

## 3. Core Contracts

### MemoryContinuityRequest

```json
{
  "request_id": "mem-cont-001",
  "agent_id": "julia",
  "memory_ref": "memory://event/julia-core-origin",
  "memory_type": "project|relationship|episodic|semantic|working",
  "importance": "low|medium|high|critical",
  "signals": {
    "identity_related": true,
    "relationship_related": true,
    "project_related": true,
    "provider_independent": true
  }
}
```

### ContinuityEligibilityDecision

```json
{
  "eligible": true,
  "level": "L3_IDENTITY",
  "reason": "identity_forming",
  "protected_ref": "memory://event/julia-core-origin"
}
```

### ProtectedMemoryRef

```json
{
  "ref": "memory://event/julia-core-origin",
  "level": "L3_IDENTITY",
  "reason": "identity_forming",
  "source": "continuity_policy"
}
```

## 4. Boundary Rules

- Memory OS may submit candidate refs.
- Continuity OS decides checkpoint eligibility.
- Memory quantity does not imply identity importance.
- Continuity OS must not copy raw memory content into checkpoint.
- Ordinary memories may remain L0/L1/L2 and not become identity.
- Context relevance does not imply continuity protection.

## 5. Promotion Boundary

Examples:

| Memory | Expected Continuity Level |
|---|---|
| `memory://lunch/today` | L0 or L1 |
| `memory://event/current-task-detail` | L1 |
| `memory://project/julia-core-discussion` | L2 |
| `memory://event/julia-core-origin` | L3 |

The key rule:

```text
Continuity is meaning-based, not volume-based.
```
