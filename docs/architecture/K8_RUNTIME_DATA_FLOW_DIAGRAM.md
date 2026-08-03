# K8 Runtime Data Flow Diagram

## Principle

```text
Meaning before retrieval.
State provides context.
Cognition decides behavior.
Provider generates language.
```

## Runtime Flow

```text
User Message
  ↓
Conversation Understanding (K8.1)
  - literal content
  - semantic meaning
  - possible intents with uncertainty
  - emotional context
  - relationship context relevance
  - response requirement
  ↓
Response Intention Planning (K8.2)
  - primary interaction goal
  - secondary goals
  - stance / tone / depth
  - uncertainty preservation
  - response economy target
  ↓
Context Arbitration (K8.3)
  - activate relevant contexts
  - suppress irrelevant contexts
  - resolve competing context priorities
  ↓
Context Need Optimization (K8.3)
  - required context
  - optional context
  - avoid list
  - minimum sufficient context
  ↓
Natural Expression Boundary (K8.4)
  - required qualities
  - avoid leakage/templates
  - allowed natural affordances
  - provider responsibility
  ↓
Provider Generation
  - final wording
  - style variation allowed
  - must follow boundary
  ↓
Julia Response
```

## Context Sources

```text
Identity
Relationship
Experience
Continuity State
Re-entry State
Event Assimilation
Evidence / Project Context
```

Context sources are not loaded by default. They are selected only after meaning and intention are represented.

## Negative Selection Path

```text
Context Arbitration
  ├─ Activate: contexts relevant to current interaction goal
  └─ Suppress: contexts likely to pollute the current interaction
```

Example:

```text
Input: 帮我优化 Python 性能
Activate: technical collaboration, evidence/project context
Suppress: identity biography, emotional relationship, soul proof history
```

## Forbidden Flow

```text
User Message
  ↓
Keyword Detection
  ↓
Memory Retrieval
  ↓
Template Reply
```

This is a K8 cognition failure.

## K8.0.6 Cognition Runtime Harness Flow

Before K8.1 connects to any response-facing runtime, K8.0.6 runs a trace-only observation path:

```text
Tony Message
  ↓
CognitionRuntimeHarness
  ↓
Conversation Understanding Trace
  ↓
Contextual Meaning Validation Trace
  ↓
Context Need / Suppression Draft
  ↓
intention: null
provider_request: null
final_response: null
```

Purpose:

```text
Validate understanding before allowing response generation.
```

