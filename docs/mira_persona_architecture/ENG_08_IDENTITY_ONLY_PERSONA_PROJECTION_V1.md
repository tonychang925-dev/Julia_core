# ENG-08 Identity-only PersonaProjection V1

Date: 2026-09-10
Repository: `tonychang925-dev/Julia_core`
Branch: `mira/persona-architecture-v1`
Effective delegation base SHA: `cd98d168ecc5a83a9628890687774d25a847c59f`
Historical ENG-07 implementation SHA: `f4357b5311934cbcc1d99e1ca0a901856ad6df84`
Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING REMOTE PERSISTENCE`
C0-03..C0-08 status: `CONTRACT DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY`

## 1. Changed files

- `julia_core/projection/__init__.py`
- `julia_core/projection/contracts.py`
- `julia_core/projection/policy.py`
- `tests/projection/test_identity_only_persona_projection.py`
- `tests/identity/test_identity_minimal_slice.py`
- `docs/mira_persona_architecture/ENG_08_IDENTITY_ONLY_PERSONA_PROJECTION_V1.md`
- `artifacts/mira_persona_architecture/ENG_08_RESULT_V1.json`

## 2. Authorized test-governance amendment

Issue #19 comment `5617295090` authorizes exactly one additional path:

```text
tests/identity/test_identity_minimal_slice.py
```

The amendment replaces the ENG-07 single-task branch exclusivity assertion with cumulative authorized branch-scope semantics. The updated test still rejects arbitrary paths and continues to protect legacy persona, Self Model, runtime, providers, Context OS, Context Assembly, Memory, and Continuity from mutation. No `julia_core/identity/**` implementation or ENG-07 semantic invariant was changed.

This is test governance repair, not projection implementation or architectural scope expansion.

## 3. Pre-implementation audit and reuse

Reused read-only:

- ENG-07 `GovernedIdentity`, `IdentityVersion`, `IdentityRef`, `IdentityStatus`, and `IdentityResolver` as the sole semantic input authority.
- Existing canonical JSON plus SHA-256 digest conventions.
- Existing frozen typed-object, exact-reference, and fail-closed resolver conventions.

Audited but deliberately not reused:

- Legacy `julia_core/persona/**` mixes identity, biography, appearance, preferences, relationship history, and voice. It is not parsed or imported.
- `julia_core/self_model/**` combines self, biography, relationship, and narrative semantics. It is not parsed or imported.
- `julia_core/context_os/**` blocks are short-lived context candidates and some paths are already coupled to model-facing composition. ENG-08 does not import Context OS or emit Context OS blocks.
- Existing runtime `identity_frame` dictionaries are prompt-construction outputs with legacy/persona inputs and are not authoritative typed frames.

This is not a second parallel projection/admission system. It is one bounded derived-view package over ENG-07 Identity, with no persistence, context admission, or runtime behavior.

## 4. PersonaProjectionPolicy semantics

`PersonaProjectionPolicy` exposes:

- policy ID: `persona_projection.identity_only`
- policy version: `1.0.0`

It accepts only `GovernedIdentity`, or an exact `IdentityRef` plus `IdentityResolver`. Unknown exact references fail closed. There is no latest-version fallback. The policy copies existing ENG-07 identity anchors, values, boundaries, relationship-role anchors, provenance references, exact source reference, source digest, lifecycle state, and predecessor metadata. It performs no semantic selection, rewriting, inference, completion, admission, retirement, or mutation.

## 5. IdentityFrame shape

`IdentityFrame` is a frozen typed object containing:

- frame schema/version and frame kind;
- non-authoritative projection metadata;
- exact source ref, source digest, lifecycle status, and predecessor version;
- identity ID;
- identity anchors;
- stable values;
- stable boundaries;
- stable relationship-role anchors;
- identity provenance references.

The frame explicitly records:

```text
non_authoritative = true
canonical_authority = IdentityVersion
model_visibility = NOT_DECIDED
```

The shape has no autobiography, MemoryExperience, full relationship history, conversation body, causal-chain corpus, current conversation state, Context OS block, system prompt, provider instruction, voice instruction, embedding, inferred consent, or standing-authorization field.

## 6. Lifecycle handling

Projection copies lifecycle state exactly:

- `CANDIDATE`
- `ADMITTED`
- `SUPERSEDED`
- `RETIRED`

It never promotes a candidate, changes another lifecycle state, or determines model visibility. Those decisions remain for future governed admission policy.

`WATCH-ENG07-01` is untouched: projection reads resolved status once and does not invoke or rely on repeated admission.

## 7. Fidelity, immutability, and digest

Each semantic collection in the frame is a fresh dictionary copy of the corresponding ENG-07 object. Projection preserves all four semantic collections exactly, leaves the canonical version digest unchanged, and cannot invent an absent anchor.

`IdentityFrame.canonical_serialization()` emits sorted, compact, UTF-8 JSON. `digest()` is SHA-256 over that representation. Equal governed input plus the same policy produces equal serialization and digest; identity semantic changes change the frame digest.

## 8. Authority boundaries

ENG-08 does not implement or modify:

- C-03 admission or CognitiveContextPackage;
- C-05 MemoryExperience;
- C-06 hydration;
- runtime or provider behavior;
- Context OS or Context Assembly;
- Memory, Experience, or Continuity;
- legacy persona, Self Model, relationship, alignment, or voice;
- Mira migration, admission, or lineage policy.

## 9. Tests and regression

ENG-07 identity tests:

```text
/opt/miniconda3/bin/pytest tests/identity/test_identity_minimal_slice.py -q
10 passed
```

ENG-08 projection tests:

```text
/opt/miniconda3/bin/pytest tests/projection/test_identity_only_persona_projection.py -q
11 passed
```

Full tracked regression:

```text
/opt/miniconda3/bin/pytest -q $(git ls-files 'tests/**test_*.py' 'tests/**/test_*.py')
1204 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
```

The exact failure ID set matches the accepted `f4357b5311934cbcc1d99e1ca0a901856ad6df84` baseline:

```text
48 failed + 3 errors
```

The passing count increases because ENG-08 adds tests. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## 10. No Critical Fallback Review

The gate script named by repository instructions remains absent from the branch. Manual critical-path review:

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

- The frame is an in-memory typed candidate and has no durable frame store.
- The policy is identity-only and intentionally has no persona expression, compression, localization, or provider adaptation behavior.
- Projected provenance supports traceability but confers no authority.
- Model visibility and lifecycle admission policy remain deferred to C-03.

## 12. Next seam

Define a separately governed C-03 admission policy over typed frames without constructing provider prompts or importing MemoryExperience.
