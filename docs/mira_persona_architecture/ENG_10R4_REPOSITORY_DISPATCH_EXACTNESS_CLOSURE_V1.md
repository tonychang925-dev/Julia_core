# ENG-10R4 Repository Dispatch Exactness Closure V1

```text
AGENT_ID=Agent A
TASK_ID=ENG-10R4
DELEGATION_BASE_SHA=5ae1f92b0f15220e534fa8e177c91b732f458390
STATUS=IMPLEMENTATION_COMPLETE_WAITING_FRESH_REVIEW
MERGE_AUTHORITY=NONE
```

## Scope

This repair closes only the two fresh-review VALID_NOW P1 findings:

- R1: Identity and MemoryExperience resolvers dispatch through the validated canonical repository class implementation, so an instance-shadowed `resolve` callable cannot fabricate governed output or change projection semantics.
- R2: `IdentityProvenance.source_ref` requires an exact built-in string before URI parsing, rejecting subclasses, proxies, and custom parse behavior.

No C-03, C-06, continuity, runtime, provider, context, alignment, voice, persona, self-model, migration, schema expansion, P2 backlog, or second-authority behavior was introduced.

## Verification

```text
Targeted exactness tests:  92 passed
Canonical rail:            211 passed
Full isolated regression:  1394 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
ENG-10R3 isolated base:    1387 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
Failure/error ID diff:     EMPTY / BASELINE_EQUIVALENT
git diff --check:          PASS
```

The seven additional passed tests are the new R1/R2 cases. No full-regression failure or error ID changed.

The result artifact intentionally omits its own final Git hash because that hash depends on the artifact bytes. The exact remote HEAD and parent are recorded in the Issue #44 completion comment.
