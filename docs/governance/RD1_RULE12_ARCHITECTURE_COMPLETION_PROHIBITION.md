# RD1 Rule 12 — Architecture Completion Prohibition

**Status:** ACTIVE CONSTITUTIONAL AMENDMENT  
**Scope:** Julia Core / Julia-AI-Assistant / Market Brain task authoring, implementation, review, delegation, and automation.  
**Owner authorization:** explicit scope-bounded governance amendment approved by Owner on 2026-09-17.

This document supplements `DEVELOPMENT_CONSTITUTION.md` as Rule 12. It does not replace Rule 11; it closes a distinct failure mode: an Agent silently completing architecture by inference while drafting a task card.

## 1. Permanent law

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

An Agent may reason about how to implement frozen architecture. An Agent may not infer, invent, complete, or silently add architecture that is not already established by effective frozen authority.

```text
IMPLEMENTATION_REASONING = ALLOWED_WITHIN_FROZEN_AUTHORITY
ARCHITECTURE_COMPLETION_BY_INFERENCE = FORBIDDEN
```

## 2. Forbidden inference sources

The following facts may identify an implementation gap or evidence state, but they do not authorize new architecture:

```text
CURRENT_MAIN_ABSENCE
CURRENT_IMPLEMENTATION_SHAPE
NO_PHYSICAL_CALLER
NO_PACKAGE_RESOLUTION
NO_EXISTING_COMPOSITION_ROOT
NO_EXISTING_BINDING_LOCUS
NO_EXISTING_ADAPTER
NO_EXISTING_PUBLIC_EXPORT
DEPLOYMENT_GAP
INTEGRATION_GAP
TEST_FAILURE
TEST_EXPECTATION
RUNTIME_BEHAVIOR
IMPLEMENTATION_CONVENIENCE
AGENT_CONSENSUS
```

Forbidden transformations include:

```text
CURRENT_MAIN_ABSENCE -> NEW_ARCHITECTURE_ELEMENT
IMPLEMENTATION_GAP -> NEW_OWNER
IMPLEMENTATION_GAP -> NEW_DOMAIN
IMPLEMENTATION_GAP -> NEW_COMPOSITION_ROOT
IMPLEMENTATION_GAP -> NEW_BINDING_AUTHORITY
IMPLEMENTATION_GAP -> NEW_PACKAGE_BOUNDARY
IMPLEMENTATION_GAP -> NEW_DEPENDENCY_DIRECTION
IMPLEMENTATION_GAP -> NEW_RUNTIME_AUTHORITY
IMPLEMENTATION_GAP -> NEW_TRANSPORT
```

## 3. Mandatory task-author architecture-completion audit

Before a coding task card may be submitted, the task author MUST answer:

```text
DID I, AS TASK AUTHOR, INTRODUCE ANY ARCHITECTURE ELEMENT
THAT IS NOT DIRECTLY BOUND TO EFFECTIVE FROZEN AUTHORITY?
```

The author MUST mechanically audit at least:

```text
new owner
new domain
new composition root
new binding authority
new package/public-private boundary
new dependency direction
new runtime authority
new transport requirement
new lifecycle authority
new cross-repo responsibility
new ABI authority
new phase ownership
```

For ordinary implementation/correction task cards, required result is:

```text
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK = PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS = 0
NEW_OWNER_COUNT = 0
NEW_DOMAIN_COUNT = 0
NEW_COMPOSITION_ROOT_COUNT = 0
NEW_BINDING_AUTHORITY_COUNT = 0
NEW_PACKAGE_BOUNDARY_COUNT = 0
NEW_DEPENDENCY_DIRECTION_COUNT = 0
NEW_RUNTIME_AUTHORITY_COUNT = 0
NEW_TRANSPORT_COUNT = 0
```

If any count is non-zero, the task card is not an implementation task card and MUST NOT proceed as one.

```text
TASK_CARD_NOT_READY
READY_FOR_SUBMISSION = NO
IMPLEMENTATION_AUTHORIZATION = NO
```

## 4. Frozen-source binding requirement

Every architecture-relevant element asserted by a coding task card MUST be traceable to effective frozen authority.

```text
FROZEN_SOURCE_BINDING_COMPLETE = PASS
```

A narrative claim such as "this is implied", "this is the natural place", "the code needs somewhere to bind", or "this is the cleanest architecture" is not sufficient authority.

If the author cannot bind the element to a governing frozen clause after Rule 11 trace/precedence resolution:

```text
NO_FROZEN_ANSWER_FOUND != PERMISSION_TO_INVENT
```

The author must classify the finding under Rule 11. Only a true `D` may enter architecture adjudication. A/B/C may not be converted into architecture invention.

## 5. Explicit architecture amendments remain legal

Rule 12 does not prohibit deliberate architecture change. It prohibits hiding architecture change inside an implementation task.

A genuine architecture change must use the Constitution's explicit scope-bounded amendment channel:

```text
EXPLICIT_CHANGE_INTENT
-> IMPACT_ANALYSIS
-> SCOPE_BOUNDED_AMENDMENT
-> REFREEZE
-> REBIND_DOWNSTREAM_TASKS
-> ONLY THEN IMPLEMENT
```

Until that amendment is frozen:

```text
OLD_FROZEN_AUTHORITY_REMAINS_IN_FORCE
IMPLEMENTATION_AGAINST_PROPOSED_NEW_BOUNDARY = FORBIDDEN
```

## 6. Independent review gate

Independent review MUST separately verify that the task author did not pre-solve architecture while drafting the card.

```text
AUTHOR_PASS_CLAIM = SIGNAL_ONLY
ARCHITECTURE_COMPLETION_EVIDENCE = MUST_BE_REVERIFIED
```

The reviewer must ask:

```text
IS EVERY OWNER / LOCUS / ROOT / BOUNDARY / DIRECTION / AUTHORITY
IN THIS TASK ALREADY FROZEN?
```

If not:

```text
ARCHITECTURE_COMPLETION_PRECHECK = FAIL
REVIEW = STOP
```

## 7. Machine enforcement

`tools/task_card_governance_gate.py` MUST require the Rule 12 self-check fields and reject ordinary coding task cards when:

```text
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK != PASS
FROZEN_SOURCE_BINDING_COMPLETE != PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS != 0
ANY REQUIRED NEW_*_COUNT != 0
```

The parser verifies declared governance evidence. It does not decide architecture truth; independent review remains mandatory.

## 8. Core principle

> **Agents may complete implementation details inside frozen architecture. They may not complete architecture itself by inference.**
