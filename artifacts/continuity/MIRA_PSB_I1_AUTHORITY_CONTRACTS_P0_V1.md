# MIRA PSB-I1 Authority/Contracts Evidence

## Authority

- `TASK_ID=MIRA-PSB-I1-AUTHORITY-CONTRACTS-P0`
- `EXECUTION_AGENT=LOCAL_CODEX_ONLY`
- `DESIGN_SHA=73d5ecb1c2fc0e6dd70bccfe423c79a3370c0fa5`
- `IMPLEMENTATION_BASE_SHA=73d5ecb1c2fc0e6dd70bccfe423c79a3370c0fa5`
- `PARENT_SHA=27fcc663d25892bdf9209b8ff6792231d0f634ce`
- `CANDIDATE_SHA=a31c4576d79b916cdfcaf035558b73ffc61e3da7`
- `BRANCH=mira/psb-i1-authority-contracts-p0`

The working tree was clean at the exact implementation base before the dedicated branch was created.

## Selected Paths

- `julia_core/persona_self_binding/**`
- `tests/persona_self_binding/**`
- `artifacts/continuity/MIRA_PSB_I1_AUTHORITY_CONTRACTS_P0_V1.json`
- `artifacts/continuity/MIRA_PSB_I1_AUTHORITY_CONTRACTS_P0_V1.md`

No Golden Mira runtime wiring, C03 semantic binding, provider transport, durable persistence, RelationshipFrame implementation, RD1 worktree, prompt patch, response rewrite, or real provider execution was changed.

## Contract Coverage

- Exact `PersonaSelfBinding` schema with typed authority references, lifecycle, supersession, governance provenance, and integrity policy.
- Closed lifecycle and governance event enums; arbitrary strings and user/provider events are not governance transitions.
- Relationship tri-state: `ABSENT`, `ADMITTED_BOUND`, and non-interchangeable `EXPLICITLY_EMPTY`.
- Fixed provider-neutral execution substrate policy with no durable concrete provider/model fields.
- Exact authority-family references, source digests, optional projected digests, predecessor/version validation, and duplicate-family rejection.
- UTF-8 canonical sorted-key compact JSON, SHA-256 digest, deterministic round trip, and typed verification.
- Stable typed error codes for schema, digest, relationship, provider, lifecycle, governance, predecessor, and duplicate-family failures.
- Deterministic `IdentityAuthorityAssertion` schema and closed outcomes without classifier behavior.

## Verification

- Focused: `19 passed`.
- Focused plus NCF sabotage tests: `23 passed, 16 subtests passed`.
- Required regression set: `63 passed, 1 pre-existing failure`.
- Required regression set with the pre-existing scope assertion deselected: `63 passed, 1 deselected`.
- The pre-existing failure is `tests/projection/test_identity_only_persona_projection.py::test_changed_scope_is_limited_to_authorized_eng08_paths`; it reproduces at the exact implementation base in a clean worktree.
- Changed-file NCF gate: `NCF_GATE=PASS`, `P0_NEW=0`, `P1_NEW=0`, `P2_NEW=0`.
- `git diff --check=PASS`.

The full-repository NCF command also reproduces one inherited P2 baseline mismatch at the exact base. It is unrelated to this change; the changed-file gate required for this candidate introduces no violation.

## Result

`PASS_PSB_I1_AUTHORITY_CONTRACTS_READY_FOR_OWNER_REVIEW`
