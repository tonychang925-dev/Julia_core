# ENG-09R3 Canonical Integrity Bypass Closure V1

Date: 2026-09-10

Repository: `tonychang925-dev/Julia_core`

Branch: `mira/persona-architecture-v1`

Delegation base SHA: `4eb08f5af9162ff57fc880d933dff4539caf4e4b`

Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`

PR review surface: #22

## Binding and scope

The remote branch HEAD was verified at the exact delegation base before implementation. This task closes only the two `VALID_NOW` bypasses authorized by Issue #27. C0-03 through C0-08 remain contract drafts without frozen implementation authority.

Changed files:

- `julia_core/identity/resolver.py`
- `julia_core/projection/policy.py`
- `julia_core/memory_experience/contracts.py`
- `tests/identity/test_identity_resolver_integrity.py`
- `tests/memory_experience/test_memory_experience_content_integrity.py`
- `docs/mira_persona_architecture/ENG_09R3_CANONICAL_INTEGRITY_BYPASS_CLOSURE_V1.md`
- `artifacts/mira_persona_architecture/ENG_09R3_RESULT_V1.json`

## F1 — forged resolver / repository path

Resolution: `CLOSED`

`IdentityResolver.__init__()` now accepts only an exact `IdentityRepository`, and its resolve path accepts only an exact `IdentityRef`. `PersonaProjectionPolicy.project_ref()` now accepts only an exact `IdentityResolver` and exact `IdentityRef`. A resolver subclass and a repository-like fake therefore cannot substitute a forged governance path.

Tests prove:

- fake repository construction fails closed;
- forged resolver subclass projection fails closed;
- exact repository + exact resolver + exact admitted ref succeeds;
- unknown exact ref fails without latest fallback;
- direct `GovernedIdentity` projection remains forbidden.

No cryptographic capability mechanism, runtime/provider/context authority, or new repository implementation was introduced.

## F2 — MemoryExperience content subclass injection

Resolution: `CLOSED`

`MemoryExperienceRecord` now requires the exact mapped canonical content class for its `MemoryExperienceType`. Subclasses and serializer proxies cannot reach canonical payload construction, digest calculation, or repository storage.

Tests prove:

- a canonical content subclass with injecting `to_dict()` is rejected;
- the exact `RelationshipExperienceContent` remains accepted;
- deterministic digest behavior remains intact;
- forbidden runtime/provider/MemoryExperience injection terms do not enter the canonical payload;
- the existing all-five-type suite continues to exercise every exact canonical content class.

The five-type ontology, record schema, lifecycle states, and provenance semantics are unchanged.

## F3 — autobiographical Identity anchors

Disposition: `PARTIAL / DEFER`

No autobiographical-anchor collection or other Identity schema expansion was implemented. The finding remains input to future C0-04 contract revision and Mira migration-fidelity design.

## Tests and regression

```text
ENG-07 identity test file:       14 passed
ENG-08 projection test file:     13 passed
ENG-09 MemoryExperience tests:   16 passed
ENG-09R2 integrity tests:        21 passed
ENG-09R3 bypass-closure tests:    7 passed
Canonical-rail combined suites:  71 passed
Full tracked regression:         1247 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
git diff --check:               PASS
```

The full-regression failure ID set was compared against a clean tracked worktree at the exact delegation base and is exactly equivalent. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## Scope audit

No semantic implementation was changed under the Identity repository, continuity, context OS/context assembly, runtime, providers, persona, self_model, memory, experience, narrative, relationship, alignment, voice, voice OS, or deploy. `main` was not changed. No C-03, C-06, ENG-10, Mira migration/admission, autobiographical-anchor schema, MemoryExperience type/lifecycle expansion, or deferred C0-05 schema was implemented.

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

- Exact-type sealing is Python-runtime governance, not cryptographic object-capability security.
- Resolver-backed Identity provenance verification remains deferred.
- Draft autobiographical, timing, subject, causal, epistemic, and rejection-state semantics remain unimplemented.
- A result artifact cannot embed its own final Git commit hash because that hash depends on the artifact bytes. The exact pushed HEAD is recorded and remotely verified in the delivery comment and final handoff.

## Next seam

Independent SHA-bound Mira review should resolve the F1/F2 threads and record F3 as deferred. ENG-10 remains unauthorized and must not begin from this report alone.
