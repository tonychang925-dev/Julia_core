# ENG-09R5 Canonical Boundary Integrity Closure V1

Date: 2026-09-10

Repository: `tonychang925-dev/Julia_core`

Branch: `mira/persona-architecture-v1`

Delegation base SHA: `898ee4a336fa353b2b08e32c1dd57dea26f45ebe`

Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`

PR review surface: #22

## Binding and scope

The remote branch HEAD was verified at the exact delegation base before implementation. This task closes only the three boundary-integrity defects authorized by Issue #30. C0-03 through C0-08 remain contract drafts without frozen implementation authority.

Changed files:

- `julia_core/projection/contracts.py`
- `julia_core/memory_experience/resolver.py`
- `julia_core/identity/repository.py`
- `julia_core/memory_experience/repository.py`
- `tests/projection/test_identity_frame_mapping_integrity.py`
- `tests/memory_experience/test_memory_experience_boundary_integrity.py`
- `tests/identity/test_identity_lifecycle_boundary_integrity.py`
- `docs/mira_persona_architecture/ENG_09R5_CANONICAL_BOUNDARY_INTEGRITY_CLOSURE_V1.md`
- `artifacts/mira_persona_architecture/ENG_09R5_RESULT_V1.json`

## R5-1 — deep-freeze every Mapping

Resolution: `CLOSED`

`IdentityFrame` deep-freeze now recognizes any `collections.abc.Mapping`, copies its items, recursively freezes nested values, and stores the copied tree under `MappingProxyType`. Mutating a custom mapping's backing dictionary cannot alter frame semantics or digest. Outward serialization remains detached.

Tests prove:

- backing-map mutation cannot mutate the frame or add injected keys;
- frame digest remains stable after backing mutation;
- semantically identical mappings produce identical digests;
- outward payload mutation cannot mutate the internal frame.

## R5-2 — exact MemoryExperience resolver repository/ref

Resolution: `CLOSED`

`MemoryExperienceResolver` construction requires an exact `MemoryExperienceRepository`, and resolution requires an exact `MemoryExperienceRef`. Fake repositories, repository subclasses, and equality-compatible ref subclasses fail closed. Exact repository/ref resolution and unknown-ref fail-closed behavior remain intact.

## R5-3 — exact refs for lifecycle transitions

Resolution: `CLOSED`

Identity and MemoryExperience admission, supersession, and retirement boundaries require exact canonical ref types before lookup or event construction. Internal append/transition helpers also enforce the same exact-type boundary. Equality-compatible subclasses or proxies cannot be retained in governance events.

Tests prove:

- all Identity lifecycle methods reject `IdentityRef` subclasses;
- all MemoryExperience lifecycle methods reject `MemoryExperienceRef` subclasses;
- emitted governance events retain exact canonical ref types;
- valid exact-ref transitions continue to function.

## Tests and regression

```text
ENG-07 identity test file:       14 passed
ENG-08 projection test file:     13 passed
ENG-09 MemoryExperience tests:   16 passed
ENG-09R2 integrity tests:        21 passed
ENG-09R3 integrity tests:         7 passed
ENG-09R4 integrity tests:        15 passed
ENG-09R5 boundary tests:         13 passed
Canonical-rail combined suites:  99 passed
Full tracked regression:         1269 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
git diff --check:               PASS
```

The full-regression failure ID set was compared against a clean tracked worktree at the exact delegation base and is exactly equivalent. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## Scope audit

No semantic implementation was changed under continuity, context OS/context assembly, runtime, providers, persona, self_model, memory, experience, narrative, relationship, alignment, voice, voice OS, or deploy. `main` was not changed. No C-03, C-06, ENG-10, Mira migration/admission, autobiographical Identity schema, universal subject/event-time/epistemic schema, new MemoryExperience type, or lifecycle state was implemented.

## No Critical Fallback Review

The repository-referenced gate script remains absent, so the critical path received manual review:

```text
CRITICAL_PATH: YES
FALLBACK_INTRODUCED: NO
MOCK_OR_FIXTURE_PRODUCTION_REACHABLE: NO
LEGACY_AUTHORITY_FALLBACK: NO
SYNTHETIC_SUCCESS: NO
OUTER_SUCCESS_INNER_FAILURE: NO
AMBIENT_RESOLUTION: NO
TEST_MODE_PRODUCTION_REACHABLE: NO
FAIL_CLOSED_PRESERVED: YES
RISK: NONE
DECISION: APPROVE
```

## Known limitations

- Exact-type checks are runtime boundary validation, not cryptographic capability security.
- Resolver-backed source existence and authority-namespace verification remain deferred.
- Draft autobiographical, timing, subject, causal, epistemic, and rejection-state semantics remain unimplemented.
- A result artifact cannot embed its own final Git commit hash because that hash depends on the artifact bytes. The exact pushed HEAD is recorded and remotely verified in the delivery comment and final handoff.

## Next gate

Independent SHA-bound fresh-head review must confirm no untriaged `VALID_NOW` P1 remains. ENG-10 remains unauthorized and must not begin from this report alone.
