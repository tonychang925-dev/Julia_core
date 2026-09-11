# ENG-10R8 No Replayable Lifecycle Authority V1

```text
AGENT_ID=Agent A
TASK_ID=ENG-10R8
DELEGATION_BASE_SHA=0bfe89905c309cd981d4585142abb6c728718417
STATUS=IMPLEMENTATION_COMPLETE_WAITING_FRESH_REVIEW
MERGE_AUTHORITY=NONE
```

## Scope

This repair closes only the fresh-review VALID_NOW P1 finding:

- Removed the closure-scoped lifecycle capability decorator, capability registry, capability checks, authorized-method indirection, and all raw replacement/transition helpers.
- `store_candidate`, `admit`, `supersede`, and `retire` now perform exact input validation, lifecycle preconditions, lock-protected copy-on-write updates, and deterministic resolution entirely within their controlled public implementations.
- No repository method exposes a replayable authorization object. Lifecycle functions have no authority-bearing closures, defaults, or keyword defaults; class and module introspection exposes no `LifecycleCapability`, capability registry, or capability decorator.

This change preserves event identifiers, transition rules, append-only event tuples, immutable mapping views, resolver behavior, and `project_ref` semantics. It introduces no fallback, mock, stub, shadow substitute, silent degradation, permissive default, compatibility bypass, test-only success path, or second governance authority.

## Verification

```text
Targeted exactness tests:  97 passed
Canonical rail:            216 passed
Full isolated regression:  1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
ENG-10R7 isolated base:    1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
Failure/error ID diff:     EMPTY / BASELINE_EQUIVALENT
NO_FALLBACK_MOCK_STUB_SHADOW_DEGRADE_GATE=PASS
git diff --check:          PASS
```

The result artifact intentionally omits its own final Git hash because that hash depends on the artifact bytes. The exact remote HEAD and parent are recorded in the Issue #51 completion comment.
