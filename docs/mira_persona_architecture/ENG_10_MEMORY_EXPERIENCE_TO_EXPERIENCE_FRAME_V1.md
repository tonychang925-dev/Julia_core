# ENG-10 MemoryExperience to ExperienceFrame V1

Date: 2026-09-11

Repository: `tonychang925-dev/Julia_core`

Branch: `mira/persona-architecture-v1`

Delegation base SHA: `e46614cdb2c82eaae2ef77099fb4bfde1cec5e45`

Status: `BRANCH-ONLY ENGINEERING CANDIDATE / PASS PENDING INDEPENDENT MIRA REVIEW`

PR review surface: #22

## Binding and pre-implementation audit

The remote branch HEAD was verified at the exact delegation base before implementation. The audit covered the canonical MemoryExperience contracts/repository/resolver, the existing projection package, and the cumulative projection tests.

Architecture reuse decisions:

- reuse `julia_core/projection/**` as the sole projection seam;
- reuse exact `MemoryExperienceRef`, `MemoryExperienceResolver`, and repository-backed `GovernedMemoryExperience`;
- reuse the IdentityFrame deterministic serialization/digest and all-`Mapping` deep-freeze convention;
- do not modify canonical `memory_experience/**` or `identity/**` implementations;
- do not create a second projection, retrieval, hydration, or context authority system.

Changed files:

- `julia_core/projection/contracts.py`
- `julia_core/projection/policy.py`
- `julia_core/projection/__init__.py`
- `tests/projection/test_memory_experience_to_experience_frame.py`
- `tests/projection/test_identity_only_persona_projection.py`
- `docs/mira_persona_architecture/ENG_10_MEMORY_EXPERIENCE_TO_EXPERIENCE_FRAME_V1.md`
- `artifacts/mira_persona_architecture/ENG_10_RESULT_V1.json`

The existing projection test change is mechanically required so the legacy-memory import guard distinguishes `julia_core.memory` from the authorized canonical `julia_core.memory_experience` package. No protection was removed.

## ExperienceFrame model

`ExperienceFrame` is a frozen, non-authoritative view of exactly one governed MemoryExperience record. It preserves:

- exact source ref and digest;
- exact lifecycle status;
- experience and version identity;
- predecessor version;
- exact one-of-five experience type;
- canonical content payload;
- canonical provenance references;
- creation timestamp;
- explicit non-authoritative projection metadata.

The frame does not invent subject, event-time, epistemic, causal, or autobiographical fields. It does not combine records and does not infer current consent, standing authorization, relationship state, retrieval rank, context admission, hydration, runtime visibility, or provider authority.

## Projection behavior

The only supported path is:

```text
exact MemoryExperienceRef
→ exact MemoryExperienceResolver
→ repository-backed GovernedMemoryExperience
→ ExperienceProjectionPolicy
→ ExperienceFrame
```

`project()` rejects direct caller-fabricated governed objects. `project_ref()` rejects resolver/ref subclasses and proxies. Unknown exact refs fail closed without latest-version fallback. Projection preserves candidate, admitted, superseded, and retired status without promotion and never mutates the source record or repository.

## Canonical integrity

`ExperienceFrame.__post_init__` requires exact canonical ref/status/type objects and Mapping-backed content/provenance payloads. Nested mappings and collections are copied into recursively frozen, detached representations. Outward serialization creates fresh plain containers. Mutating a custom mapping backing object or an outward serialized payload cannot alter frame semantics or digest.

Deterministic JSON serialization and SHA-256 digest behavior follow the existing IdentityFrame convention. Semantically identical sources produce identical frames/digests; a semantic source change changes the frame digest.

## Tests and regression

```text
ENG-10 ExperienceFrame tests:     20 passed
Canonical-rail combined suites:  119 passed
Full applicable regression:      1302 passed, 48 failed, 6 skipped, 26 xfailed, 3 errors
git diff --check:               PASS
```

The regression command included all tracked tests plus the new ENG-10 test file. Its exact failed/error ID set was compared against the accepted exact-base failure set. Result: `BASELINE_EQUIVALENT / NO NEW FAILURES`.

## Scope audit

No semantic implementation was changed under `julia_core/memory_experience/**`, `julia_core/identity/**`, continuity, context OS/context assembly, runtime, providers, persona, self_model, memory, experience, narrative, relationship, alignment, voice, voice OS, or deploy. `main` was not changed.

No C-03 model-visible admission, C-06 hydration, runtime/provider/context wiring, retrieval/ranking, Mira migration/admission, C0-05 schema expansion, new MemoryExperience type, or lifecycle state was implemented.

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

- The frame is an in-memory typed engineering candidate, not a frozen C0-06 contract.
- No durable frame store, retrieval index, hydration path, context admission, or model-visible admission exists.
- Resolver-backed source existence and authority-namespace verification remain deferred.
- Draft C0-04/C0-05 timing, subject, epistemic, causal, rejection, and autobiographical semantics remain unimplemented.
- A result artifact cannot embed its own final Git commit hash because that hash depends on the artifact bytes. The exact pushed HEAD is recorded and remotely verified in the delivery comment and final handoff.

## Next seam

Independent SHA-bound fresh-head review must confirm no untriaged `VALID_NOW` P1 was introduced. Model-visible admission remains unauthorized until a separate C-03 task.
