# ENG-10R6 Replacement Helper Authorization Closure V1

```text
AGENT_ID=Agent A
TASK_ID=ENG-10R6
DELEGATION_BASE_SHA=2758cfa55413c67c3f353088add79a97feeab0ea
STATUS=IMPLEMENTATION_COMPLETE_WAITING_FRESH_REVIEW
MERGE_AUTHORITY=NONE
```

## Scope

This repair closes only the fresh-review VALID_NOW P1 finding:

- R1: Repository copy-on-write replacement and lifecycle orchestration helpers are name-mangled class-private methods. Exact repository holders can no longer invoke `_replace_events`, `_replace_version`, `_replace_state`, `_replace_record`, `_append_event`, or `_transition` as external mutation bypasses.

Validated public lifecycle operations remain the only external mutation path. Lock-protected copy-on-write semantics, deterministic resolver output, and `project_ref` behavior are unchanged.

No schema expansion, C-03, C-06, continuity, runtime, provider, context, alignment, voice, persona, self-model, migration, P2 backlog, merge, or second-authority behavior was introduced.

## Verification

```text
Targeted exactness tests:  97 passed
Canonical rail:            216 passed
Full isolated regression:  1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
ENG-10R5 isolated base:    1399 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
Failure/error ID diff:     EMPTY / BASELINE_EQUIVALENT
git diff --check:          PASS
```

The result artifact intentionally omits its own final Git hash because that hash depends on the artifact bytes. The exact remote HEAD and parent are recorded in the Issue #49 completion comment.
