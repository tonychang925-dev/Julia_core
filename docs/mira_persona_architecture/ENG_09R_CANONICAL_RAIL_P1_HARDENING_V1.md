# ENG-09R Canonical Rail P1 Hardening V1

Date: 2026-09-10
Repository: `tonychang925-dev/Julia_core`
Branch: `mira/persona-architecture-v1`
Effective execution base SHA: `2d51099367dc42841338db1fe6a6528d93a5fba5`
Pre-incident semantic baseline SHA: `20a4a8c53531975627f5ce85c1b720c5df509177`
Status: `BRANCH-ONLY HARDENING CANDIDATE / PASS PENDING REMOTE PERSISTENCE`
PR review surface: #22

## 1. Base binding and changed files

The effective execution tree at `2d51099367dc42841338db1fe6a6528d93a5fba5` was verified byte-for-byte equivalent to the pre-incident ENG-09 semantic tree at `20a4a8c53531975627f5ce85c1b720c5df509177`. The intervening commits are governance-neutral operational noise.

Changed files:

- `julia_core/identity/contracts.py`
- `julia_core/projection/contracts.py`
- `julia_core/projection/policy.py`
- `tests/identity/test_identity_minimal_slice.py`
- `tests/projection/test_identity_only_persona_projection.py`
- `tests/memory_experience/test_memory_experience_minimal_slice.py`
- `docs/mira_persona_architecture/ENG_09R_CANONICAL_RAIL_P1_HARDENING_V1.md`
- `artifacts/mira_persona_architecture/ENG_09R_RESULT_V1.json`

The MemoryExperience test change is limited to the cumulative-scope amendment authorized in Issue #24 comment `5618106470`. No `julia_core/memory_experience/**` semantic implementation was changed.

## 2. P1-01 — IdentityFrame deep immutability

Resolution: `CLOSED`

`IdentityFrame.__post_init__` now recursively freezes nested dictionary trees using `MappingProxyType`. Nested anchors, values, boundaries, relationship-role anchors, and provenance metadata reject in-place mutation. `to_dict()` recursively detaches the internal immutable tree into fresh plain dictionaries/lists. Mutating an outward dictionary cannot alter frame semantics or digest.

Tests prove:

- nested semantic mutation raises `TypeError`;
- nested provenance mutation raises `TypeError`;
- outward payload mutation does not mutate the frame;
- serialization/digest remain stable;
- source `IdentityVersion` digest remains unchanged.

## 3. P1-02 — provenance duplicate-key canonicalization

Resolution: `CLOSED`

`IdentityProvenance.admission_metadata` must be a sequence of two-item key/value string tuples. Mapping inputs are rejected, and duplicate keys are rejected. Canonical conversion to a dictionary is therefore lossless by validation rather than silently dropping values.

Tests prove:

- malformed metadata inputs fail validation;
- duplicate keys fail validation;
- materially different unique metadata changes the canonical version digest;
- storing a different provenance tuple under the same exact IdentityRef raises `IdentityConflictError`.

## 4. P1-03 — repository-backed projection governance

Resolution: `CLOSED`

Direct projection of a caller-constructed `GovernedIdentity` is forbidden. `PersonaProjectionPolicy.project()` now fails closed and directs callers to exact-reference resolution. The only projection input path is:

```text
IdentityRef
→ IdentityResolver
→ repository-backed GovernedIdentity
→ IdentityFrame
```

Tests prove:

- fabricated `GovernedIdentity(..., ADMITTED, ...)` cannot project;
- repository-backed exact admitted refs project successfully;
- unknown refs fail closed;
- no implicit latest fallback exists;
- lifecycle state is copied without promotion.

## 5. P2 dispositions

- `P2-01 historical Git-object dependence`: **OPEN**. The current environment has the required history, but replacing the cumulative diff source in a shallow/source archive would require a separately trusted branch manifest to avoid weakening governance. No unsafe fallback was introduced.
- `P2-02 forbidden untracked paths`: **CLOSED**. The identity scope test now checks all untracked paths against protected implementation prefixes and includes a mechanical detection case for an untracked runtime override.
- `P2-03 ambiguous IdentityRef URI delimiters`: **CLOSED**. URI components are percent-encoded with `/` unsafe, so identifiers containing `/` cannot introduce an extra path separator.

## 6. Authority and governance impact

The hardening strengthens canonical integrity without adding semantic authority. Identity remains the canonical source. Projection remains derived and non-authoritative. MemoryExperience remains unchanged and separate. No C-03 admission, C-06 hydration, ENG-10 behavior, Mira migration, runtime/provider wiring, context admission, or continuity hydration was implemented.

## 7. Tests and regression

Hardened cumulative suites:

```text
ENG-07 identity:       14 passed
ENG-08 projection:     13 passed
ENG-09 MemoryExperience: 16 passed
Combined:              43 passed
```

There are six hardening tests/assertions beyond the accepted ENG-09 baseline.

Full tracked regression:

```text
1226 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
```

The exact failure ID set matches the accepted `20a4a8c53531975627f5ce85c1b720c5df509177` baseline. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

`git diff --check` passes.

## 8. No Critical Fallback Review

The gate script named by repository instructions remains absent. Manual critical-path review:

```text
NO_CRITICAL_FALLBACK_REVIEW
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

## 9. Remaining limitations

- P2-01 remains open pending a trusted branch-change manifest design.
- Repository governance actor/reason fields remain structurally represented rather than externally authenticated.
- IdentityFrame remains an in-memory typed candidate; no durable frame store or model-visible admission exists.

## 10. Next gate

Independent SHA-bound review must confirm the three P1 closures and zero unresolved P1 findings before ENG-10 authorization.
