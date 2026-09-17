# RD1 Rule 12 — Architecture Completion Prohibition

**Status:** ACTIVE CONSTITUTIONAL AMENDMENT  
**Scope:** Julia Core / Julia-AI-Assistant / Market Brain task authoring, implementation, review, delegation, and automation.  
**Consolidated operational model:** `RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md`

Rule 12 supplements `DEVELOPMENT_CONSTITUTION.md`. It does not replace Rule 11.

## 1. Permanent law

```text
NO_ARCHITECTURE_COMPLETION_BY_AGENT_INFERENCE = YES
```

```text
IMPLEMENTATION_REASONING = ALLOWED_WITHIN_FROZEN_AUTHORITY
ARCHITECTURE_COMPLETION_BY_INFERENCE = FORBIDDEN
```

Forbidden inference sources include current-code absence/shape, missing caller/binding/composition, test expectations/failures, runtime behavior, implementation convenience, and Agent consensus.

```text
NO_FROZEN_ANSWER_FOUND != PERMISSION_TO_INVENT
```

## 2. Ordinary implementation-task proof

After control-plane consolidation, ordinary implementation/correction tasks MUST declare:

```text
ARCHITECTURE_DELTA
= NONE

FROZEN_AUTHORITY_BINDING
= <exact effective frozen source / clauses>
```

If:

```text
ARCHITECTURE_DELTA != NONE
```

then:

```text
NOT_AN_IMPLEMENTATION_TASK
→ EXPLICIT ARCHITECTURE AMENDMENT / REFREEZE PATH
```

The reviewer still audits at least:

```text
owner
domain
composition root
binding authority
package/public-private boundary
dependency direction
runtime authority
transport
lifecycle authority
cross-repo responsibility
ABI authority
phase ownership
```

The historical `NEW_*_COUNT = 0` fields are reviewer checklist dimensions, not mandatory repetitive task-card syntax after consolidation.

## 3. Explicit architecture amendments remain legal

Rule 12 prohibits hiding architecture change inside implementation work. It does not prohibit deliberate, Owner-authorized architecture change.

```text
EXPLICIT_CHANGE_INTENT
→ IMPACT_ANALYSIS
→ SCOPE_BOUNDED_AMENDMENT
→ REFREEZE
→ REBIND_DOWNSTREAM_TASKS
→ ONLY THEN IMPLEMENT
```

Until refreeze:

```text
OLD_FROZEN_AUTHORITY_REMAINS_IN_FORCE
IMPLEMENTATION_AGAINST_PROPOSED_NEW_BOUNDARY = FORBIDDEN
```

## 4. Independent review

```text
AUTHOR_PASS_CLAIM = SIGNAL_ONLY
ARCHITECTURE_COMPLETION_EVIDENCE = MUST_BE_REVERIFIED
```

Reviewer asks whether every owner/locus/root/boundary/direction/authority asserted by the task is already frozen.

If not:

```text
ARCHITECTURE_COMPLETION_PRECHECK = FAIL
REVIEW = STOP
```

## 5. Machine enforcement

`tools/task_card_governance_gate.py` MUST require:

```text
ARCHITECTURE_DELTA = NONE
FROZEN_AUTHORITY_BINDING present
RESIDUAL_ARCHITECTURE_DECISIONS = 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS = 0
```

Parser verifies declarations only.

```text
PARSER = GOVERNANCE_ENFORCER
PARSER != ARCHITECTURE_LAW
```

## 6. Core principle

> **Agents may complete implementation details inside frozen architecture. They may not complete architecture itself by inference.**
