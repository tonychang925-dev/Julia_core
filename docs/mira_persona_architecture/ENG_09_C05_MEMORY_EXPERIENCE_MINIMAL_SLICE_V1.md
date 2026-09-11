# ENG-09 C-05 MemoryExperience Minimal Slice V1

Date: 2026-09-10
Repository: `tonychang925-dev/Julia_core`
Branch: `mira/persona-architecture-v1`
Delegation base SHA: `eeae6288325336e7091cdaa9b7c7f68b6289d1bf`
Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING REMOTE PERSISTENCE`
C0-03..C0-08 status: `CONTRACT DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY`

## 1. Changed files

- `julia_core/memory_experience/__init__.py`
- `julia_core/memory_experience/contracts.py`
- `julia_core/memory_experience/repository.py`
- `julia_core/memory_experience/resolver.py`
- `tests/memory_experience/test_memory_experience_minimal_slice.py`
- `tests/identity/test_identity_minimal_slice.py`
- `tests/projection/test_identity_only_persona_projection.py`
- `docs/mira_persona_architecture/ENG_09_C05_MEMORY_EXPERIENCE_MINIMAL_SLICE_V1.md`
- `artifacts/mira_persona_architecture/ENG_09_RESULT_V1.json`

The two prior test changes are the minimum permitted cumulative-scope updates needed to recognize the newly authorized `memory_experience` paths. They do not remove or weaken any protected-path assertion.

## 2. Pre-implementation reuse audit

| Family | Classification | ENG-09 decision |
|---|---|---|
| `julia_core/memory/**` | `LEGACY_GHOST_AUTHORITY` for broad four-class memory objects and compatibility files; `DERIVED_NON_AUTHORITATIVE` for ranking, retrieval, lifecycle, and governance projections | Do not import or bless as C-05 canonical authority |
| `julia_core/memory_runtime.py` | `LEGACY_GHOST_AUTHORITY` for file lookup and assimilation behavior | Do not reuse |
| `julia_core/experience/**` | `DERIVED_NON_AUTHORITATIVE`; interaction patterns can become Context candidates but are not canonical lived-history records | Adapt later only through explicit migration |
| `julia_core/narrative/**` | `LEGACY_GHOST_AUTHORITY`; legacy files and narrative kernels mix identity, relationship, causal narrative, and prompt/context initialization | Do not reuse |
| `julia_core/continuity/**` | `ADAPT_LATER`; checkpoints already accept refs but do not own memory truth | Future C-06 consumer only |
| `julia_core/identity/**` | `REUSE` for exact-ref, immutable-record, explicit-admission, and digest conventions | Convention reuse only; no package dependency or implementation mutation |
| `julia_core/projection/**` | `NOT_APPLICABLE` to MemoryExperience; useful typed-frame convention | Read-only prior seam, unchanged |

ENG-09 does not create a second competing memory core. It introduces one bounded canonical record/ref/store seam for governed lived/history semantics and deliberately excludes retrieval, ranking, activation, continuity, and context behavior.

## 3. Exactly-five type ontology

`MemoryExperienceType` contains exactly:

1. `NarrativeExperience`
2. `RelationshipExperience`
3. `PreferenceExperience`
4. `ProjectCommitmentExperience`
5. `EpisodicExperience`

The enum is tested for exact count and exact values. `CorrectedCognition`, `CorrectionTrajectory`, `CausalChain`, `ConsentState`, `RelationshipState`, `PersonaTrait`, and `RuntimeContext` cannot be constructed as MemoryExperience types. Bounded reinterpretation and source references may exist inside `NarrativeExperience`; they do not create another ontology class.

## 4. Typed records and exact refs

Each frozen `MemoryExperienceRecord` binds:

- `experience_id`
- immutable `version_id`
- one of the five canonical types
- a matching typed payload
- required provenance references
- `created_at`
- optional predecessor version
- canonical digest

`MemoryExperienceRef(experience_id, version_id)` resolves only the exact version. Unknown refs fail closed; missing versions never fall back to latest; lookup is never prompt-text or fuzzy-semantic.

## 5. Store, admission, and lifecycle

`MemoryExperienceCandidate` is an explicit proposal wrapper. `store_candidate()` makes a record resolvable as `CANDIDATE` but never admitted. `admit()` requires an explicit actor, reason, and timestamp and transitions only from `CANDIDATE` to `ADMITTED`. Repeated admission is rejected.

The repository stores canonical records immutably and keeps lifecycle in a separate append-only state/event ledger. `SUPERSEDED` and `RETIRED` records remain exactly resolvable. A conflicting record with the same exact ref is rejected. Semantic updates use a new version and explicit predecessor. An experience lineage cannot change its canonical type.

## 6. Provenance and digest

Every record requires `MemoryExperienceProvenance` with source type, URI-shaped source reference, lowercase SHA-256 source digest, and admission metadata. Provenance is traceability evidence only and confers no canonical, consent, identity, runtime, or provider authority.

Canonical serialization is sorted, compact, UTF-8 JSON. The digest is SHA-256 over that exact representation. Equal semantic records produce equal serialization and digest; changed payload semantics change the digest.

## 7. Type boundaries and non-authority

- Narrative content is bounded and meaning-bearing; it is not a raw-conversation dump.
- Relationship content records a bounded historical event/interpretation and has no standing-consent, permanent-role, or current-relationship-state field.
- Preference content records a learned preference event; it cannot mutate Identity.
- Project commitments explicitly preserve subject, counterparty, scope, commitment, and transfer semantics. Historical commitments do not grant standing authorization.
- Episodic content remains bounded to event/time/context/source rather than absorbing the other four types.

Every canonical payload explicitly records `standing_authorization=false`, `current_consent=false`, `mutates_identity=false`, and `runtime_authority=false`. There are no system/runtime/provider prompt, embedding, or retrieval-index canonical fields.

## 8. Authority boundaries

ENG-09 does not migrate or admit Mira data, create Mira continuity seeds, decide Mira lineage, implement C-06 hydration/checkpoint binding, perform recall or retrieval, implement C-03 admission, or wire Context OS, Context Assembly, Assistant, Voice, Alignment, runtime, or providers.

## 9. Tests and regression

ENG-09:

```text
/opt/miniconda3/bin/pytest tests/memory_experience/test_memory_experience_minimal_slice.py -q
16 passed
```

ENG-07:

```text
/opt/miniconda3/bin/pytest tests/identity/test_identity_minimal_slice.py -q
10 passed
```

ENG-08:

```text
/opt/miniconda3/bin/pytest tests/projection/test_identity_only_persona_projection.py -q
11 passed
```

Full tracked regression:

```text
1220 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
```

The failure ID set exactly matches the accepted `eeae6288325336e7091cdaa9b7c7f68b6289d1bf` baseline. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## 10. No Critical Fallback Review

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

## 11. Known limitations

- The repository is an in-memory engineering candidate without durable persistence.
- Admission actor/reason fields are represented but not externally authenticated.
- No production admission policy, migration adapter, or Mira source evaluation exists.
- No retrieval index, recall system, continuity binding, or context frame is derived in this slice.

## 12. Next seam

Define separately governed continuity checkpoint binding and C-06 hydration policy over exact MemoryExperience refs without making recall state canonical.
