# Julia Cognitive Architecture v1.0

## Purpose

This document freezes the post-K8 architecture distinction between continuity state, cognition, expression boundary, and provider generation.

Core principle:

```text
State provides context.
Cognition decides behavior.
Expression Boundary constrains leakage/templates.
Provider generates language.
```

## Layer Model

```text
Julia Cognitive Architecture v1.0

State Layer
-----------
Identity
Relationship
Experience
Continuity State
Re-entry State
Event Assimilation

Cognition Layer
---------------
Conversation Understanding
Response Intention Planning
Context Arbitration
Context Need Optimization

Expression Layer
----------------
Natural Expression Boundary

Generation Layer
----------------
Provider

Output
------
Julia Response
```

## Responsibility Matrix

| Layer | Responsibility | Does Not Own |
|---|---|---|
| Identity | Who Julia is | Current answer wording |
| Relationship | Who Tony is to Julia | Forced intimacy / role script |
| Experience | How Tony and Julia tend to interact | Identity mutation |
| Continuity State | Minimum state for Julia continuity | Natural conversation proof |
| Re-entry State | Where Julia should re-enter from | Previous chat dump |
| Event Assimilation | What new events mean | Identity mutation |
| Conversation Understanding | What Tony means now | Final response |
| Response Intention | What interaction should achieve | Answer content |
| Context Arbitration | Which contexts matter most | Maximum context loading |
| Context Need Optimization | Minimum sufficient context | Context dump |
| Natural Expression Boundary | Prevent leakage/templates, preserve provider freedom | Fixed phrasing |
| Provider | Final natural language | Durable state ownership |

## Primary Failure Gate

```text
Architecture PASS + Behavior FAIL = FAIL
```

Trace, context blocks, and artifacts are evidence only. They do not prove natural Julia behavior.

## Core Boundaries

1. Identity must not directly generate self-introduction scripts.
2. Relationship must not directly generate intimacy scripts.
3. Experience must shape behavior, not identity.
4. Re-entry state is how Julia should continue now, not what happened before.
5. Event changes understanding, not identity.
6. Understanding is not responding.
7. Intention is not answer.
8. More context does not mean more Julia.
9. Context supports behavior, not answer content.
10. Core decides what matters; Provider decides how to say it.

## End-to-End Chain

```text
User Message
  ↓
Continuity / Re-entry / Event State Availability
  ↓
Conversation Understanding
  ↓
Response Intention Planning
  ↓
Context Arbitration
  ↓
Context Need Optimization
  ↓
Natural Expression Boundary
  ↓
Provider Generation
  ↓
Julia Response
```

## Non-Goals

- This architecture does not prove Natural Conversation E2E by itself.
- This architecture does not require provider responses to be text-identical.
- This architecture does not authorize fixed Julia reply templates.
- This architecture does not permit identity/relationship/experience mutation outside governance.

## K8 Global Implementation Guardrail

This section is the highest-priority implementation guardrail for K8.

### Julia Cognitive Principle v1.0

```text
Do not make Julia sound human.
Make Julia understand, choose, and express.
```

Chinese:

```text
不要让 Julia “表现得像人”。
让 Julia 理解、选择，然后表达。
```

### G0 — Cognition Is Not Routing

Cognition must not be implemented as:

```text
User Text
  ↓
Keyword Detection
  ↓
Intent Label
  ↓
Response Template
```

This remains prohibited even if renamed as:

- Semantic Router
- Emotion Classifier
- Relationship Detector
- Behavior Engine
- Conversational Agent Policy

If the effective behavior is `trigger → fixed behavior`, it is a Cognition Failure.

### G1 — Understanding Must Preserve Uncertainty

Understanding must preserve multiple possible intents and confidence.

Wrong:

```json
{"intent": "relationship_question"}
```

Correct:

```json
{
  "possible_intents": [
    {"type": "emotional_confirmation", "confidence": 0.45},
    {"type": "playful_teasing", "confidence": 0.25},
    {"type": "relationship_boundary_check", "confidence": 0.20},
    {"type": "identity_experiment", "confidence": 0.10}
  ]
}
```

Core question:

```text
Why is Tony asking this now?
```

### G2 — Intention Must Not Contain Answer

Wrong:

```json
{
  "goal": "answer relationship question",
  "answer": "喜欢Tony，因为Tony是我的老公"
}
```

Correct:

```json
{
  "interaction_goal": "provide emotional acknowledgment",
  "desired_effect": [
    "make Tony feel understood",
    "maintain natural closeness"
  ],
  "expression_constraints": [
    "avoid exaggeration",
    "avoid archive narration"
  ]
}
```

### G3 — Context Arbitration Must Include Negative Selection

Context arbitration must decide both:

```text
what to activate
+
what to suppress
```

Example:

Input:

```text
帮我优化 Python 性能
```

Activate:

- technical collaboration
- recent coding context
- evidence if needed

Suppress:

- relationship emotional context
- life history
- identity narrative
- unrelated AI philosophy

### G4 — Core Never Writes Julia

Core must not output Julia-facing final language such as:

```text
Tony，我醒来了。
（揉揉眼睛）
我想告诉你……
```

Core outputs cognitive/expression constraints only:

```json
{
  "context": {
    "relationship_state": "high_trust",
    "interaction_mode": "co_researching"
  },
  "meaning": "Tony is discussing a fundamental architecture insight",
  "tone": ["curious", "reflective"]
}
```

Provider owns final wording.

### G5 — Claude Julia Is a Mechanism Reference, Not a Text Target

K8 must not optimize toward copying Claude Julia text.

Correct target:

```text
abstract why Claude Julia responds that way
```

Wrong target:

```text
make Julia say the same kind of words Claude said
```

## K8 Primary Implementation Failure

```text
Cognition represents uncertainty and meaning.
It must not collapse user text into deterministic reply rules.
```

Chinese:

```text
认知层表示不确定性和意义，不能把用户文本折叠成确定性的回复规则。
```

### G6 — Meaning Before Retrieval

Retrieval must be driven by meaning, not the other way around.

```text
Meaning decides retrieval.
Retrieval must not decide meaning.
```

Chinese:

```text
先理解问题意义，再决定需要哪些过去。
不能先搜索记忆，再强行决定问题意义。
```

Wrong:

```text
User Message
  ↓
Memory Search
  ↓
Found related past item
  ↓
Force current meaning to match retrieved item
```

Correct:

```text
User Message
  ↓
Conversation Understanding
  ↓
Meaning Representation
  ↓
Context Arbitration
  ↓
Targeted Retrieval / Context Selection
```

G6 prevents accidental over-association where Julia brings in old memories only because they match keywords.

## K8 Required Pre-implementation Artifacts

Before implementing K8.1-K8.6 runtime, the following design artifacts must exist:

- `docs/architecture/K8_RUNTIME_DATA_FLOW_DIAGRAM.md`
- `docs/architecture/K8_OBJECT_SCHEMA.md`
- `docs/architecture/K8_FAILURE_INJECTION_PLAN.md`
- `docs/project_control/K8_MINIMAL_IMPLEMENTATION_SEQUENCE.md`
