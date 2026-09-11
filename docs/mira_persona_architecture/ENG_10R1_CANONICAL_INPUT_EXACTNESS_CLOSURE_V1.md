# ENG-10R1 Canonical Input Exactness Closure V1

Date: 2026-09-11

Repository: `tonychang925-dev/Julia_core`

Branch: `mira/persona-architecture-v1`

Delegation base SHA: `73b4a35863173378752b958590908d10596bc7e4`

Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`

PR review surface: #22

## Binding and scope

The remote branch HEAD was verified at the exact delegation base before implementation. This repair closes only the three canonical-input exactness defects authorized by Issue #32. C0-03 through C0-08 remain contract drafts without frozen implementation authority.

Changed files:

- `julia_core/identity/contracts.py`
- `julia_core/memory_experience/contracts.py`
- `tests/identity/test_exact_identifier_inputs.py`
- `tests/memory_experience/test_canonical_input_exactness.py`
- `docs/mira_persona_architecture/ENG_10R1_CANONICAL_INPUT_EXACTNESS_CLOSURE_V1.md`
- `artifacts/mira_persona_architecture/ENG_10R1_RESULT_V1.json`

No file under `julia_core/projection/**` was changed. ENG-10 ExperienceFrame implementation remains read-only.

## R1 — exact plain-string identifiers

Resolution: `CLOSED`

Identity and MemoryExperience identifier validation now require exact built-in `str` objects. String subclasses, proxies, and spoof strings fail closed before canonical ref or repository-key construction. Existing plain-string identifiers continue to validate unchanged.

Tests prove:

- IdentityAnchor and IdentityRef reject string-subclass IDs;
- MemoryExperienceRef rejects string-subclass IDs;
- plain built-in string IDs remain valid.

## R2 — detached provenance metadata

Resolution: `CLOSED`

After validating pair shape, exact string key/value types, and unique keys, `MemoryExperienceProvenance` copies admission metadata into a fresh exact built-in tuple of exact `(str, str)` pairs. Caller-owned tuple subclasses no longer remain semantically connected to the canonical record. Duplicate-key rejection remains unchanged.

Tests prove:

- the retained metadata tuple is exact;
- mutating a caller-owned tuple subclass's backing list cannot change canonical serialization;
- duplicate metadata keys still fail closed.

## R3 — exact CommitmentTransferSemantics

Resolution: `CLOSED`

`ProjectCommitmentExperienceContent.transfer_semantics` now requires `type(...) is CommitmentTransferSemantics`. Mocks, proxies, and enum-like spoof objects fail closed. Existing exact enum values continue to serialize deterministically. No new transfer semantics or lifecycle state was added.

## Tests and regression

```text
ENG-10R1 exactness tests:       9 passed
ENG-10 ExperienceFrame tests:  20 passed
Canonical-rail combined suites: 128 passed
Full applicable regression:     1311 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
git diff --check:              PASS
```

The regression command included all tracked tests plus the two new ENG-10R1 test files. Its exact failed/error ID set was compared against the accepted exact-base failure set. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## Scope audit

No semantic implementation was changed under projection, continuity, context OS/context assembly, runtime, providers, persona, self_model, memory, experience, narrative, relationship, alignment, voice, voice OS, or deploy. `main` was not changed. No ENG-11, C-03, C-06, Mira migration/admission, C0-04/C0-05 schema expansion, new MemoryExperience type, or lifecycle state was implemented.

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
- Existing unresolved P2 backlog remains untouched.
- A result artifact cannot embed its own final Git commit hash because that hash depends on the artifact bytes. The exact pushed HEAD is recorded and remotely verified in the delivery comment and final handoff.

## Next gate

Independent SHA-bound fresh-head review must confirm no untriaged `VALID_NOW` P1 remains. ENG-11 and C-06 remain unauthorized.
