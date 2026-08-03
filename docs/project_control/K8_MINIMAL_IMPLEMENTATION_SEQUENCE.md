# K8 Minimal Implementation Sequence

## Principle

```text
Implement the smallest non-speaking cognition chain first.
```

Do not implement natural final replies until the intermediate objects and failure attribution are testable.

## Sequence

### Step 1 — K8 Object Schemas

Implement dataclasses / serialization only:

- ConversationUnderstanding
- ResponseIntention
- ContextArbitration
- ContextRequirement
- ExpressionBoundary

Gate:

```text
all objects serialize without final response text
```

### Step 2 — Boundary Validators

Implement validators for:

- no final answer text
- no keyword-to-reply route
- no context dump
- no fixed expression template
- no artifact mutation

### Step 3 — Fixture Cognition Pipeline

Implement a deterministic fixture pipeline only for tests that produces intermediate objects, not Julia replies.

Gate:

```text
K8.1-K8.4 unit tests pass
```

### Step 4 — Failure Injection Harness

Implement FI-001 through FI-008 injection harness and attribution expectations.

Gate:

```text
K8.6 failure attribution tests pass
```

### Step 5 — Provider-facing Contract

Only after steps 1-4, build provider-facing request containing:

- user message
- understanding summary
- response intention
- context requirement
- expression boundary
- selected context references

Gate:

```text
Core still does not write Julia final text
```

### Step 6 — Natural Conversation Behavior Validation

Run K8.5 behavior scenarios.

Gate:

```text
NBS >= threshold
JCRS >= threshold
Architecture PASS + Behavior FAIL impossible to mark PASS
```

## Stop Conditions

Stop and run K8.6 attribution if:

- output repeats `Tony，我在。`
- output echoes user input
- output dumps identity archive
- output overuses relationship/persona context
- provider output is generic assistant voice

## Non-Goals

- No prompt-only fixes.
- No fixed Julia sentence library.
- No emotion/gesture templates.
- No direct mutation of continuity artifacts.

## K8.1 Required Minimal Order

```text
K8.1.0 Understanding Object Runtime
        ↓
K8.1.1 Boundary Validator
        ↓
K8.1.2 Ambiguity Handling
        ↓
K8.1.3 Intent Hypothesis Generation
        ↓
K8.1.4 Understanding Benchmark
```

Do not connect K8.1 directly to provider reply generation.

## Early Failure Injection Rule

Failure injection must run after the K8.0.5 skeleton and before full K8.1 implementation.

Required early injections:

- K8-001 Cognition Bypass Detection
- FI-003 Context Over-selection
- CU-006 Ambiguous Reference
- NC-011 Same Words Different Meaning Test

## K8.1.5 Inserted Runtime Order

K8.1.5 must run after K8.1 ambiguity handling and before K8.2 response intention planning.

```text
K8.1 Conversation Understanding
        ↓
K8.1.5 Contextual Meaning Validation
        ↓
K8.2 Response Intention Planning
```

First K8.1.5 implementation target:

```text
Validate meaning in current conversation reality; do not answer.
```

## Updated K8 Implementation Route — after K8.0.6

```text
K8.0.6 Cognition Runtime Harness
        ↓
K8.1.0 Understanding Object Model
        ↓
K8.1.1 Meaning Candidate Engine
        ↓
K8.1.5 Meaning Validation Runtime
        ↓
K8.1 Gate Tests
        ↓
K8.2 Intention Planning
        ↓
K8.3 Context Arbitration Runtime
        ↓
K8.4 Expression Boundary Runtime
        ↓
K8.5 Natural Conversation E2E
```

Rule:

```text
No Provider connection before trace-only cognition harness passes.
```

