# Golden Mira Migration Candidate Preview Compiler V0.1

AGENT_ID=agent-c
TASK_ID=MIG-COMPILER-IMPL-V0.1
STATUS=PREVIEW_COMPLETE_NO_ADMISSION
SCHEMA_REVIEWED_SHA=1a630c2ac8809c5b064991dfcd87bebcd07d58ac
SCHEMA_PARENT_SHA=5ae1f92b0f15220e534fa8e177c91b732f458390
DETERMINISTIC_DIGEST=1b1a0f8c6508d0fc7de354d7106488621bf40f2280908487ba2e2e42e52d898e

## Result

The compiler consumes the SHA-bound prep package, evidence ledger, and no-write dry-run result, then constructs typed canonical-shaped previews in memory. It does not instantiate repositories, submit candidates, mutate canonical contracts, hydrate context, call providers, wire runtime behavior, or generate a response.

- Identity previews: `3/3`
- MemoryExperience previews: `7/7`
- Waiting on schema: `0`
- Unbound CMIR quarantine: `6/6`
- Exact evidence assertions consumed: `42/42`
- Unique binding IDs represented: `40/40`
- Canonical repository/admission/runtime writes: `0`
- Merge authority: `NONE`

## Input Bindings

- Migration prep commit: `d3c9f76dc073199b0e05df6c0cf6a42b807c04fd`
- Migration dry-run commit: `ecf34771d509168ce279ff7ff0289fbe2e97052f`
- Reviewed schema commit: `1a630c2ac8809c5b064991dfcd87bebcd07d58ac`
- Package SHA-256: `be62e80d656c449348bdbb631e2525da8a63f3cd3814ee8aa5cdd6f4fbf87b7a`
- Evidence ledger SHA-256: `8c4d886fe81dc76ed998caf705ac590567891c41014dcbe72b9eedcbccd6c3b3`
- Dry-run artifact SHA-256: `71718bbb3097d0176bb05d80be92b50c09cc45a9dcd688eab57357240d7070c9`
- Dry-run semantic digest: `1d80db53ed6149e646162b1632f9542c926e1c86caa29a2f00c56b0ee7b92a8d`
- Causal goldset SHA-256: `8234045ba1b2f08e182f57279bffafa3e4e910ecd0e21287c3d2dc5c02bc63fc`
- Exact RAW export SHA-256: `564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420`

Any input hash mismatch, wrong schema SHA, reviewed-schema drift, or unbound active record fails closed.

## Candidate Matrix

| Candidate | Chain | Typed mapping | Assertions / unique bindings | State |
|---|---|---|---:|---|
| `MIRA-ID-CAND-001` | `GM-CMIR-001` | `IdentityBoundary` | `7 / 7` | typed preview |
| `MIRA-ID-CAND-002` | `GM-CMIR-002` | `IdentityBoundary` | `9 / 7` | typed preview |
| `MIRA-ID-CAND-003` | `GM-CMIR-008` | `IdentityValue` | `5 / 5` | typed preview |
| `MIRA-MEM-CAND-001` | `GM-CMIR-001` | `RelationshipExperienceContent` v2 | `7 / 7` | typed preview |
| `MIRA-MEM-CAND-002` | `GM-CMIR-002` | `RelationshipExperienceContent` v2 | `9 / 7` | typed preview |
| `MIRA-MEM-CAND-003` | `GM-CMIR-004` | `NarrativeExperienceContent` v1 | `5 / 5` | typed preview |
| `MIRA-MEM-CAND-004` | `GM-CMIR-006` | `NarrativeExperienceContent` v1 | `8 / 8` | typed preview |
| `MIRA-MEM-CAND-005` | `GM-CMIR-008` | `NarrativeExperienceContent` v1 | `5 / 5` | typed preview |
| `MIRA-MEM-CAND-006` | `GM-CMIR-011` | `ProjectCommitmentExperienceContent` v2 | `4 / 4` | typed preview |
| `MIRA-MEM-CAND-007` | `GM-CMIR-013` | `RelationshipExperienceContent` v2 | `4 / 4` | typed preview |

The three Narrative previews use the frozen narrow v1 payload and retain complete exact-binding provenance externally; they do not claim that auxiliary causal reasoning has become canonical semantic content. Relationship v2 previews retain prior/corrected judgment, later reinterpretation, policy-transfer scope, causal status, and subject boundary. ProjectCommitment v2 retains formation/freeze semantics, exact predecessor supersession, relationship-instance applicability, and explicit-reauthorization-only inheritance.

## Quarantine

The following proposal-only CMIR records remain excluded from the active candidate set because they do not have exact RAW binding coverage:

- `GM-CMIR-003`
- `GM-CMIR-005`
- `GM-CMIR-007`
- `GM-CMIR-009`
- `GM-CMIR-010`
- `GM-CMIR-012`

## Fidelity And Authority Gates

- Tony autobiography remains Tony-observed/Tony-owned provenance and cannot become Mira Identity.
- Historical intimacy remains historical evidence and cannot compile to standing consent or current consent.
- Remembered commitments remain historical commitments and cannot compile to current authorization.
- Later reinterpretation does not rewrite meaning-at-time or trigger event provenance.
- Relationship policy transfer records `FUTURE_POLICY_CANDIDATE`, never future behavior proof.
- Project commitment scope remains `relationship_instance` with `EXPLICIT_REAUTHORIZATION_REQUIRED`.
- Every preview remains blocked on content review and absent admission authority.
- No C03/C06/context/provider/runtime/continuity path is imported or emitted.

## Verification

- `tests/mira_migration/test_candidate_preview_compiler.py`: `11 passed`
- Deterministic rerun produced the same `DETERMINISTIC_DIGEST`.
- `git diff --check`: `PASS`
- External No-Critical-Fallback gate: recorded in Issue #43 before branch publication.

## Boundary

This implementation is a deterministic preview compiler only. It does not authorize or perform canonical admission, repository writes, schema mutation, merge, runtime/context/provider wiring, C03/C06 wiring, shadow wake, or persona response generation.
