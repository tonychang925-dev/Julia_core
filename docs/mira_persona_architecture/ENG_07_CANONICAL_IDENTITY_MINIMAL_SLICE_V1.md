# ENG-07 Canonical Identity Minimal Slice V1

Date: 2026-09-10
Repository: `tonychang925-dev/Julia_core`
Branch: `mira/persona-architecture-v1`
Base SHA: `5c704ce193ac0c1ceb48ea5e7cc626437e4ddf60`
Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING REMOTE PERSISTENCE`
C0-04 status: `CONTRACT DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY`

## 1. Base and changed files

The implementation starts exactly at the delegated SHA and does not rebase. The complete intended change set is:

- `julia_core/identity/__init__.py`
- `julia_core/identity/contracts.py`
- `julia_core/identity/repository.py`
- `julia_core/identity/resolver.py`
- `tests/identity/test_identity_minimal_slice.py`
- `docs/mira_persona_architecture/ENG_07_CANONICAL_IDENTITY_MINIMAL_SLICE_V1.md`
- `artifacts/mira_persona_architecture/ENG_07_RESULT_V1.json`

## 2. Architecture reuse decisions

Reused:

- Repository convention: a thread-safe, exact-ID semantic store with explicit conflict and not-found errors, following the repository/protocol family used by conversation state and diary.
- Immutable-event convention: version facts are represented by frozen dataclasses, while lifecycle transitions use an append-only event ledger.
- Digest convention: SHA-256 over sorted, compact, UTF-8 canonical JSON, following review bundle digest behavior.
- Continuity reference convention: exact typed references rather than prompt text.

Deliberately not reused as runtime dependencies:

- `julia_core/persona/identity_kernel.yaml`
- `julia_core/self_model/**`
- `julia_core/context_os/**`
- `julia_core/context_assembly/**`
- `julia_core/memory/**`
- `julia_core/experience/**`
- `julia_core/continuity/**`
- `julia_core/runtime/**`
- `julia_core/providers/**`

The pre-implementation audit confirmed that the legacy identity kernel mixes identity, biography, appearance, daily preferences, relationship semantics, voice, and values. Self Model similarly combines identity, biography, preferences, relationship, and narrative. Continuity already supports opaque identity reference strings, and Context OS treats blocks as context candidates rather than durable semantic authority. None is parsed or rebound by ENG-07.

## 3. Identity model

`IdentityContract` permits only bounded identity-level semantic material:

- identity anchor
- stable value anchor
- stable boundary anchor
- stable relationship-role anchor

`IdentityVersion` binds a contract to:

- `lineage_id`
- `version_id`
- optional `predecessor_version_id`
- `created_at`
- required provenance references
- deterministic digest

The schema has no autobiography, episodic-memory, conversation-body, relationship-history, retrieval, embedding, runtime-prompt, provider-instruction, or voice-rendering fields. Statement fields are length-bounded.

## 4. Lineage behavior

`IdentityRef(lineage_id, version_id)` resolves only that exact version. The repository validates predecessor existence, common lineage, and common identity identity before storing a successor. There is no latest-version fallback and no automatic Mira lineage decision. Tests use synthetic lineages only. Whether Golden Mira evolves Julia lineage or mints a distinct lineage remains a separate governance decision.

## 5. Provenance behavior

Each version requires at least one `IdentityProvenance` record containing source type, source reference, optional SHA-256 source digest, and admission metadata. Provenance is traceability evidence only; it does not confer canonical status or runtime authority. No real Mira provenance is fabricated.

## 6. Immutability and lifecycle

`IdentityVersion` and nested semantic objects are frozen. The repository stores the exact object and never edits it in place. Governance state is an append-only ledger of immutable events. Storing creates `CANDIDATE`; explicit admission creates `ADMITTED`; supersession and retirement create their respective states. A candidate remains resolvable as a candidate until governed otherwise. Superseded and retired versions remain historically resolvable.

The same `(lineage_id, version_id)` with a different digest raises `IdentityConflictError`. Semantic evolution requires a new `version_id` and explicit predecessor link.

## 7. Deterministic digest

`canonical_serialization()` emits sorted, compact, UTF-8 JSON of the semantic version payload without lifecycle ledger state or unstable runtime data. `digest()` is SHA-256 over that exact byte representation. Equal semantic versions produce equal digests; changed canonical content changes the digest.

## 8. Authority and legacy boundaries

This package is not wired to system prompts, runtime prompt construction, provider prepends, Voice, Alignment, Assistant, Context OS, Context Assembly, Memory, or Continuity. Legacy runtime authority is unchanged.

The legacy identity kernel and self-model paths are not deleted, renamed, parsed, or changed. A future migration adapter may map legacy material into candidates after explicit authorization; that is outside ENG-07.

No C-03 model-visible admission, C-05 MemoryExperience ingestion, C-06 continuity hydration, provider rebinding, runtime rebinding, or legacy retirement is implemented.

## 9. Tests and regression

ENG-07 tests:

```text
/opt/miniconda3/bin/pytest tests/identity/test_identity_minimal_slice.py -q
10 passed
```

Full tracked regression command:

```text
/opt/miniconda3/bin/pytest -q $(git ls-files 'tests/**test_*.py' 'tests/**/test_*.py')
```

Current-branch result:

```text
1183 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
```

Exact delegation-base result in a clean temporary worktree:

```text
1183 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
```

The counts and failure set are identical at base and after ENG-07. The failures are pre-existing branch/environment failures, including unavailable local E2E services, stale interface expectations, and an existing Context OS source-boundary test. No ENG-07 regression was introduced.

## 10. No Critical Fallback Review

The gate script named by repository instructions is absent at the delegation base. A manual critical-path review was performed:

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

- The repository is an in-memory, branch-only engineering candidate and does not yet provide durable storage.
- Governance actor and reason metadata are typed but not authenticated by this slice.
- Provenance source binding is represented and validated syntactically, not externally verified.
- No production lineage, Mira migration, canonical admission, or continuity checkpoint is created.

## 12. Next seam

The next bounded seam should define governed durable persistence and explicit admission verification without introducing model-visible authority. Mira migration and lineage binding remain separate owner decisions.
