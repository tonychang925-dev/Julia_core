# ENG-08 Re-Authorization Scope Amendment V1

Date: 2026-09-10
Status: OWNER-APPROVED BOUNDED RE-AUTHORIZATION
Task: ENG-08
Repository: tonychang925-dev/Julia_core
Branch: mira/persona-architecture-v1
Delegation base: f4357b5311934cbcc1d99e1ca0a901856ad6df84

## Reason

ENG-08 correctly returned BLOCKED because `tests/identity/test_identity_minimal_slice.py::test_changed_scope_is_limited_to_authorized_eng07_paths` compares the cumulative branch diff against the ENG-07 base SHA and hard-codes ENG-07-only paths. Any later authorized task on the same branch therefore creates a false regression even when its own scope is valid.

## Bounded authorization

ENG-08 is re-authorized to modify exactly one previously forbidden path:

`tests/identity/test_identity_minimal_slice.py`

The only permitted purpose is to replace ENG-07 single-task branch exclusivity semantics with cumulative authorized branch-scope semantics that remains valid for subsequent authorized ENG tasks.

Permitted behavior:
- preserve ENG-07 semantic tests;
- preserve protections against changes to legacy persona, self_model, runtime, providers, context_os, context_assembly, memory, continuity and other protected authority lanes;
- remove the false assumption that every future branch diff from the ENG-07 base must remain inside ENG-07 paths only;
- use a task-local or cumulative authorized-scope check that does not invalidate later authorized branch work.

Forbidden behavior:
- modifying any `julia_core/identity/**` implementation;
- weakening identity semantic invariants;
- deleting scope protection entirely;
- making the test vacuous;
- allowing arbitrary branch paths;
- changing runtime/provider/context/memory/continuity/persona/self_model code;
- implementing ENG-09 or later work;
- changing main.

## Required proof

After the bounded test repair, Codex must rerun:
1. ENG-07 identity tests;
2. ENG-08 projection tests;
3. full tracked regression against exact base `f4357b5311934cbcc1d99e1ca0a901856ad6df84`;
4. `git diff --check`;
5. complete changed-file scope audit.

PASS requires the full regression to return to exact baseline equivalence with no new failures.

The final ENG-08 changed-file list must explicitly call out this authorized amendment.

## Governance interpretation

This amendment repairs test-governance semantics only. It does not expand ENG-08 architectural authority.

`ENG-08 projection scope + this single test repair` remains the complete authorized implementation surface.
