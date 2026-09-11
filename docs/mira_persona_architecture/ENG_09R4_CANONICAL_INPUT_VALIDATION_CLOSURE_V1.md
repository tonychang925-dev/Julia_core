# ENG-09R4 Canonical Input Validation Closure V1

Date: 2026-09-10

Repository: `tonychang925-dev/Julia_core`

Branch: `mira/persona-architecture-v1`

Delegation base SHA: `faa05aaa7db3dfde12d34e59202b9b99ffbf33f4`

Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`

PR review surface: #22

## Binding and scope

The remote branch HEAD was verified at the exact delegation base before implementation. This task closes only the four input-validation defects authorized by Issue #28. C0-03 through C0-08 remain contract drafts without frozen implementation authority.

Changed files:

- `julia_core/identity/contracts.py`
- `julia_core/identity/repository.py`
- `julia_core/memory_experience/contracts.py`
- `julia_core/memory_experience/repository.py`
- `tests/identity/test_identity_input_integrity.py`
- `tests/memory_experience/test_memory_experience_input_integrity.py`
- `docs/mira_persona_architecture/ENG_09R4_CANONICAL_INPUT_VALIDATION_CLOSURE_V1.md`
- `artifacts/mira_persona_architecture/ENG_09R4_RESULT_V1.json`

## R4-1 — exact IdentityVersion repository input

Resolution: `CLOSED`

`IdentityRepository.store_candidate()` now requires an exact `IdentityVersion` before accessing its ref, digest, lineage, contract, or provenance behavior. Duck-typed objects, proxies, and subclasses fail closed.

Tests prove fake and subclassed versions are rejected while exact versions still store, admit, and resolve.

## R4-2 — exact MemoryExperienceRecord candidate/store input

Resolution: `CLOSED`

`MemoryExperienceCandidate` requires an exact `MemoryExperienceRecord`, and `MemoryExperienceRepository.store_candidate()` independently requires both an exact candidate and exact wrapped record before canonicalization or storage. Record-like objects and record subclasses fail closed.

Tests prove fake/subclassed records and non-exact candidates are rejected while an exact five-type-suite record remains valid and can store, admit, and resolve.

## R4-3 — exact Identity metadata strings

Resolution: `CLOSED`

`IdentityProvenance.admission_metadata` now requires exact string keys and values without coercion. Non-string typed values such as integer `1` cannot normalize to string `"1"`. Duplicate-key rejection remains unchanged.

## R4-4 — parsed MemoryExperience URI references

Resolution: `CLOSED`

MemoryExperience source references now use bounded parsed URI validation with a valid scheme and authority. Empty, free-text, whitespace-bearing, authority-less, and malformed scheme values fail closed. Resolver-backed existence verification and namespace policy remain deferred and unimplemented.

## Tests and regression

```text
ENG-07 identity test file:       14 passed
ENG-08 projection test file:     13 passed
ENG-09 MemoryExperience tests:   16 passed
ENG-09R2 integrity tests:        21 passed
ENG-09R3 integrity tests:         7 passed
ENG-09R4 input tests:            15 passed
Canonical-rail combined suites:  86 passed
Full tracked regression:         1254 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
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

## Next seam

Independent SHA-bound Mira review should resolve R4-1 through R4-4 threads. ENG-10 remains unauthorized and must not begin from this report alone.
