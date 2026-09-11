# ENG-10R7 Lifecycle Capability Gate V1

```text
AGENT_ID=Agent A
TASK_ID=ENG-10R7
DELEGATION_BASE_SHA=214fd02791b55fb33bf8ada253bb4f5a5b8dfc3f
STATUS=IMPLEMENTATION_COMPLETE_WAITING_FRESH_REVIEW
MERGE_AUTHORITY=NONE
```

## Scope

This repair closes only the fresh-review VALID_NOW P1 finding:

- Repository mutation now requires a closure-scoped, per-repository exact lifecycle capability. The capability type is created inside the repository class decorator, and the live capability is held only in that decorator closure; it is not an instance slot, public argument, return value, or exported object.
- Public lifecycle wrappers acquire the exact capability internally and pass it to validated operations. Replacement and transition primitives verify exact capability type, object identity, and binding to the target repository before mutating.
- Direct mangled-helper calls fail when the capability is absent. Object, boolean, string, integer, lookalike, subclass-instance, copied, and deep-copied fakes fail closed.

Lock-protected copy-on-write semantics, lifecycle validation, deterministic resolve output, and `project_ref` behavior remain unchanged.

No schema expansion, C-03, C-06, continuity, runtime, provider, context, alignment, voice, persona, self-model, migration, P2 backlog, merge, or second-authority behavior was introduced.

## Verification

```text
Targeted exactness tests:  97 passed
Canonical rail:            216 passed
Full isolated regression:  1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
ENG-10R6 isolated base:    1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
Failure/error ID diff:     EMPTY / BASELINE_EQUIVALENT
git diff --check:          PASS
```

The result artifact intentionally omits its own final Git hash because that hash depends on the artifact bytes. The exact remote HEAD and parent are recorded in the Issue #50 completion comment.
