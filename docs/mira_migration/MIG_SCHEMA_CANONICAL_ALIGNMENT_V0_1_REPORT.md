# MIG-SCHEMA-CANONICAL-ALIGNMENT-V0.1 Report

## Binding

- Canonical base / parent: `260fe7374f57d09c89ab8748e60a7324f100452f`
- Reviewed v2 semantic source: `1a630c2ac8809c5b064991dfcd87bebcd07d58ac`
- Aligned implementation candidate: `9e3dcf283a4a2d1c9221f27d27a7cf4f4e0d4e8f`
- Authority: schema alignment only; no admission, C03, C06, runtime, provider, context, merge, or main authority.

## Reconciliation Matrix

| Reviewed v2 semantic change | Current canonical hardening | Alignment action | Conflict |
|---|---|---|---|
| Relationship trajectory fields and explicit v1/v2 distinction | Exact content-type and provenance validation | Add fields after the four v1 fields; serialize only v1 fields for v1 | None |
| Prior/corrected judgment, later reinterpretation, causal status | Exact built-in string policy | Require exact strings; preserve explicit ABSENT as exact empty string | None |
| Present policy transfer versus `NOT_APPLICABLE` | Deep immutable provenance | Keep two exact payload types; present policy requires exact refs and fixed false future-proof | None |
| Subject boundary | Tony/Mira authority separation | Add exact enums and reject Tony observation becoming Mira autobiography | None |
| Project formation/frozen stages and revision relation | Exact predecessor lifecycle and copy-on-write repository | Require initial exact draft and exact matching frozen predecessor/revision | None |
| Semantic role references | Same-version provenance authority | Resolve exact `(binding_id, causal_role)` only against that record's provenance metadata | None |
| Record schema v2 | Deterministic payload and digest | Preserve v1 payload byte-for-byte and emit `.v2` only for v2 relationship/project payloads | None |
| Repository stage validation | ENG-10R8 immutable slots and public lifecycle-only mutation | Add validation called inside locked `store_candidate`; retain hardened repository implementation | None |

Additional no-silent-loss hardening: a v2 predecessor cannot be followed by a v1 payload in the same exact lineage.

## Results

- `LEGACY_V1_COMPAT=PASS`
- `RELATIONSHIP_V2_ALIGNMENT=PASS`
- `PROJECT_COMMITMENT_V2_ALIGNMENT=PASS`
- `ACTIVE_7_LOSSLESS_FIXTURES=PASS`
- `CURRENT_CANONICAL_HARDENING_PRESERVED=PASS`
- `NO_FALLBACK_MOCK_STUB_SHADOW_DEGRADE=PASS`
- `MISSING_EXACT_AUTHORITY_FAIL_CLOSED=PASS`

The seven active Golden Mira memory candidates are represented from the reviewed exact preview content only; candidate 006 contributes the required formation and frozen-final lineage. No Golden Mira record is stored or admitted.

## Validation

- Targeted v2 schema: `7 passed`
- `tests/memory_experience/**`: `117 passed`
- `tests/projection/**`: `35 passed`
- Canonical rail (`identity + memory_experience + projection`): `223 passed`
- Full base regression: `48 failed, 1399 passed, 6 skipped, 26 xfailed, 3 errors`
- Full candidate regression: `48 failed, 1406 passed, 6 skipped, 26 xfailed, 3 errors`
- Failure/error ID diff: empty; `BASELINE_EQUIVALENT_PLUS_7_TARGETED_PASSES`
- `git diff --check`: `PASS`

Historical failures remain explicit and are not relabeled as passing.

## Scope

Changed implementation/test paths:

- `julia_core/memory_experience/__init__.py`
- `julia_core/memory_experience/contracts.py`
- `julia_core/memory_experience/repository.py`
- `tests/memory_experience/test_mira_migration_schema_canonical_alignment_v0_1.py`

No identity, projection, continuity, runtime, provider, context, persona, self-model, legacy memory, experience, narrative, relationship, alignment, or voice semantic path was modified.

## Blockers

None at the aligned implementation candidate. Independent review, Mira re-review, and explicit admission authorization remain required outside this task.
