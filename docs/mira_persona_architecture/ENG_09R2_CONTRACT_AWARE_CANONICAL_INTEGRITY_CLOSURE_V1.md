# ENG-09R2 Contract-Aware Canonical Integrity Closure V1

Date: 2026-09-10  
Repository: `tonychang925-dev/Julia_core`  
Branch: `mira/persona-architecture-v1`  
Delegation base SHA: `e11a502aa07e87c2dd07c16cee8b5cb28ad07754`  
Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`  
PR review surface: #22  

## Binding and scope

The remote branch HEAD was verified at the exact delegation base before implementation. This task performs only the four `VALID_NOW` integrity repairs authorized by Issue #26. C0-03 through C0-08 remain contract drafts with no frozen implementation authority.

Changed files:

- `julia_core/identity/contracts.py`
- `julia_core/memory_experience/contracts.py`
- `tests/identity/test_identity_integrity_hardening.py`
- `tests/memory_experience/test_memory_experience_integrity_hardening.py`
- `docs/mira_persona_architecture/ENG_09R2_CONTRACT_AWARE_CANONICAL_INTEGRITY_CLOSURE_V1.md`
- `artifacts/mira_persona_architecture/ENG_09R2_RESULT_V1.json`

## Integrity repairs

### T2 — MemoryExperience provenance metadata

`MemoryExperienceProvenance.admission_metadata` now requires a tuple of exact two-item tuples whose keys and values are exact `str` objects. Malformed pair shapes and duplicate keys fail closed before dictionary canonicalization. Distinct valid metadata remains semantically distinct and changes the record digest; storing materially different provenance under the same exact ref conflicts.

### T3 — Identity payload exact-type validation

`IdentityContract` requires exact `IdentityAnchor`, `IdentityValue`, `IdentityBoundary`, and `RelationshipRoleAnchor` element types. `IdentityVersion` additionally requires an exact `IdentityContract` and exact `IdentityProvenance` elements. Anchor-like objects with custom `to_dict()` methods cannot reach canonical serialization, digest calculation, or repository admission, and therefore cannot inject runtime, provider, or MemoryExperience payload semantics.

### T7 — MemoryExperience provenance element type

`MemoryExperienceRecord.provenance_refs` requires exact `MemoryExperienceProvenance` elements. Arbitrary provenance-like objects with custom serialization are rejected before canonical payload construction or storage.

### T10 valid-now — Identity source reference syntax

`IdentityProvenance.source_ref` must be a bounded URI-shaped value with a valid scheme and authority. Empty, free-text, whitespace-bearing, oversized, and authority-less references fail closed. Resolver-backed existence, authority namespaces, and source-integrity verification remain deferred until their governing contract is frozen and implemented.

## Contract-aware triage

- **T1 Narrative/Preference event time:** `PARTIAL / DEFER` — no frozen universal `event_time` schema was implemented.
- **T2 MemoryExperience duplicate metadata:** `VALID / FIXED_NOW` — malformed and duplicate metadata keys fail closed.
- **T3 Identity payload injection:** `VALID / FIXED_NOW` — exact element types prevent custom serialization injection.
- **T4 universal subject:** `PARTIAL / DEFER` — no universal subject field was invented.
- **T5 REJECTED lifecycle:** `INVALID_AS_CURRENT_REQUIREMENT / DEFER` — no lifecycle state was added.
- **T6 stale PR transport:** `VALID / ALREADY_FIXED` — Issue #26 binding records the cumulative PR transport; no code change was needed.
- **T7 provenance element type:** `VALID / FIXED_NOW` — exact MemoryExperience provenance elements are required.
- **T8 richer Narrative causality:** `PARTIAL / DEFER` — no Narrative schema expansion was performed.
- **T9 universal epistemic status/confidence:** `PARTIAL / DEFER` — no universal field was invented.
- **T10 Identity source resolvability:** `PARTIAL` — URI-shaped syntax is fixed now; resolver-backed verification is deferred.

## Tests and regression

```text
ENG-07 identity test file:       14 passed
ENG-08 projection test file:     13 passed
ENG-09 MemoryExperience tests:   16 passed
ENG-09R cumulative hardening:    43 passed
ENG-09R2 integrity tests:        21 passed
Canonical-rail combined suites:  64 passed
Full tracked regression:         1226 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
git diff --check:               PASS
```

The full-regression failure ID set was compared against a clean tracked worktree at the exact delegation base and is exactly equivalent. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## Scope audit

No semantic implementation was changed under projection, continuity, context OS/context assembly, runtime, providers, persona, self_model, memory, experience, narrative, relationship, alignment, voice, or deploy. `main` was not changed. No C-03 model-visible admission, C-06 hydration, ENG-10 behavior, Mira migration/admission, new MemoryExperience type, new lifecycle state, universal subject/event-time schema, Narrative causal expansion, or universal epistemic-status schema was implemented.

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

- Resolver-backed Identity provenance verification is intentionally deferred.
- Draft MemoryExperience timing, subject, causal, epistemic, and rejection-state semantics remain unfrozen and unimplemented.
- These contracts remain in-memory engineering candidates; no persistent canonical store migration was authorized.
- A result artifact cannot embed its own final Git commit hash because that hash depends on the artifact bytes. The exact pushed HEAD is recorded and remotely verified in the delivery comment and final handoff.

## Next seam

Independent SHA-bound Mira review should resolve the already-triaged PR threads. ENG-10 remains unauthorized and must not begin from this report alone.
