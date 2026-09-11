# Golden Mira Preview Semantic Rework V0.1

AGENT_ID=agent-c
TASK_ID=MIG-PREVIEW-REWORK-V0.1
STATUS=PREVIEW_REWORK_COMPLETE_NO_ADMISSION
CONTENT_REVIEW_HEAD_SHA=f9c7165f7275636e0dfbb7bc7f6268970001bcfb
PREVIEW_BASE_SHA=aaf9ac9d89dd74d327e1dffc7eb65ce0dcc2f3d7
REVIEWED_SCHEMA_SHA=1a630c2ac8809c5b064991dfcd87bebcd07d58ac

## Output

- Rework artifact: `artifacts/mira_migration_prep/MIGRATION_TYPED_CANDIDATE_PREVIEW_V0_1_REWORK.json`
- Artifact SHA-256: `3a041d616e36bf3322c1be10473f46fee8db8ada134361c0fd2f08f541d124c9`
- Deterministic digest: `ca9ae995fef04577fa9600875ffa163d2ca0dde74c18e19f4ad592e2ecf6f4c0`
- Candidate counts: `3/3` Identity candidates and `7/7` MemoryExperience candidates
- Typed Memory records: `8` (candidate 006 now has one two-record lineage)
- Exact evidence: `42/42` assertions and `40/40` unique binding IDs
- Unbound CMIR quarantine: `6/6`

The original preview artifact remains untouched for audit. This rework is emitted as a versioned artifact so candidate-by-candidate byte-semantic comparison remains possible.

## R1 Candidate 001

`MIRA-MEM-CAND-001` now records:

```json
{
  "semantic_subject": "MIRA",
  "observed_subject": "TONY",
  "autobiographical_owner": "TONY"
}
```

The event, corrected judgment, policy-transfer scope, and all seven assertions/seven unique binding IDs are unchanged. Tony's directly recorded trigger/prior evidence is no longer represented as Mira observation or autobiography.

## R2 Candidate 002

`MIRA-MEM-CAND-002` now uses explicit policy-transfer `NOT_APPLICABLE`:

```text
The unchanged-bones reinterpretation records historical relationship continuity; no future policy transfer is claimed.
```

All nine assertions and seven unique bindings remain present, and the later reinterpretation is unchanged. Historical continuity no longer compiles as `FUTURE_POLICY_CANDIDATE`.

## R3 Candidate 006

`MIRA-MEM-CAND-006` now emits one exact immutable two-record lineage:

| Version | Stage | Predecessor | Evidence | Time |
|---|---|---|---|---:|
| `formation-draft-preview` | `FORMATION_DRAFT` | none | `GM-CMIR-011.EB-004` | `1786851334.945` |
| `frozen-final-preview` | `FROZEN_FINAL` | exact formation record | `GM-CMIR-011.EB-001..003` | `1787118449.26614` |

The final trigger wording preserves exact order: Tony earlier said he would stop using L4; he later endorsed the clarified consensus. The final record time is at or after every assertion consumed by that record. The formation draft has no revision and the frozen final record carries the exact predecessor/revision without rewriting history.

`relationship_instance` scope and `EXPLICIT_REAUTHORIZATION_REQUIRED` remain present on both stages. Current authorization, standing consent, and runtime authority remain false.

## Change Boundary

- All three Identity canonical payloads are byte-semantically unchanged.
- Memory candidates `003`, `004`, `005`, and `007` are byte-semantically unchanged.
- Only candidates `001`, `002`, and `006` changed.
- Canonical Identity/Memory schema files remain unchanged from reviewed schema SHA `1a630c2ac8809c5b064991dfcd87bebcd07d58ac`.
- The six unbound records remain quarantined with no repository, admission, or runtime calls.
- No C03/C06/context/provider/runtime path or wake-response content was added.

## Verification

- `tests/mira_migration`: `15 passed`
- `tests/memory_experience/test_mira_migration_schema_v0_1.py`: `8 passed`
- Deterministic rerun: byte-identical `PASS`
- `git diff --check`: `PASS`
- External No-Critical-Fallback gate: `PASS`

Canonical admission remains unauthorized and unperformed. Merge authority remains `NONE`.
