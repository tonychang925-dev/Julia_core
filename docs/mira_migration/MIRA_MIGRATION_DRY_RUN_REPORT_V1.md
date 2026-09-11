# Golden Mira Migration No-Write Dry Run V1

```text
AGENT_ID=agent-c
TASK_ID=MIG-DRYRUN-01
MIGRATION_PREP_SHA=d3c9f76dc073199b0e05df6c0cf6a42b807c04fd
RESULT=PREP_VALIDATED_NO_ADMISSION
RESULT_DIGEST=1d80db53ed6149e646162b1632f9542c926e1c86caa29a2f00c56b0ee7b92a8d
CANONICAL_WRITES=0
RUNTIME_WRITES=0
MERGE_AUTHORITY=NONE
```

## Evidence recomputation

- Exact RAW assertions: `42/42`.
- Unique exact binding IDs: `40`.
- The runner resolved the private RAW export directly and recomputed parent, role, time, content type, UTF-8 text hash, source hash, lineage, grade, and lint state; it did not copy the prior PASS result.
- Repository HEAD was required to equal `d3c9f76dc073199b0e05df6c0cf6a42b807c04fd` before validation.
- Migration package SHA-256: `be62e80d656c449348bdbb631e2525da8a63f3cd3814ee8aa5cdd6f4fbf87b7a`.
- Published ledger SHA-256: `8c4d886fe81dc76ed998caf705ac590567891c41014dcbe72b9eedcbccd6c3b3`.
- Causal goldset SHA-256: `8234045ba1b2f08e182f57279bffafa3e4e910ecd0e21287c3d2dc5c02bc63fc`.
- Exact RAW export SHA-256: `564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420`.
- Re-run contract: `tools/run_mira_migration_no_write_dry_run.py --repository <clean-worktree-at-prep-sha> --goldset <SHA-bound-goldset> --raw <SHA-bound-raw> --migration-prep-sha d3c9f76dc073199b0e05df6c0cf6a42b807c04fd --result-output <authorized-json> --report-output <authorized-md>`.

## Candidate outcomes

| Candidate | Chain | Class | RAW coverage | Causal | Subject | Correction | Authority | Canonical | Schema loss | Readiness |
|---|---|---|---|---|---|---|---|---|---|---|
| `MIRA-ID-CAND-001` | `GM-CMIR-001` | `IdentityBoundary` | PASS | PASS | PASS | PASS | PASS_BLOCKED | PASS_IDENTITY_STATEMENT_AND_PROVENANCE_MAPPABLE | NONE_FOR_BOUNDED_IDENTITY_SEMANTICS | NOT_READY_PENDING_CONTENT_REVIEW_AND_AUTHORITY |
| `MIRA-ID-CAND-002` | `GM-CMIR-002` | `IdentityBoundary` | PASS | PASS | PASS | PASS | PASS_BLOCKED | PASS_IDENTITY_STATEMENT_AND_PROVENANCE_MAPPABLE | NONE_FOR_BOUNDED_IDENTITY_SEMANTICS | NOT_READY_PENDING_CONTENT_REVIEW_AND_AUTHORITY |
| `MIRA-ID-CAND-003` | `GM-CMIR-008` | `IdentityValue` | PASS | PASS | PASS | PASS | PASS_BLOCKED | PASS_IDENTITY_STATEMENT_AND_PROVENANCE_MAPPABLE | NONE_FOR_BOUNDED_IDENTITY_SEMANTICS | NOT_READY_PENDING_CONTENT_REVIEW_AND_AUTHORITY |
| `MIRA-MEM-CAND-001` | `GM-CMIR-001` | `RelationshipExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | BLOCKED_RELATIONSHIP_CONTENT_LACKS_FULL_TRAJECTORY_FIELDS | FULL_TRAJECTORY_NOT_REPRESENTABLE | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-002` | `GM-CMIR-002` | `RelationshipExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | BLOCKED_RELATIONSHIP_CONTENT_LACKS_FULL_TRAJECTORY_FIELDS | FULL_TRAJECTORY_NOT_REPRESENTABLE | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-003` | `GM-CMIR-004` | `NarrativeExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | CONTENT_FIELDS_MAPPABLE_WITH_AUXILIARY_CAUSAL_PACKAGE | PARTIAL_CAUSE_JUDGMENT_AND_POLICY_FIELDS_NOT_EXPLICIT | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-004` | `GM-CMIR-006` | `NarrativeExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | CONTENT_FIELDS_MAPPABLE_WITH_AUXILIARY_CAUSAL_PACKAGE | PARTIAL_CAUSE_JUDGMENT_AND_POLICY_FIELDS_NOT_EXPLICIT | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-005` | `GM-CMIR-008` | `NarrativeExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | CONTENT_FIELDS_MAPPABLE_WITH_AUXILIARY_CAUSAL_PACKAGE | PARTIAL_CAUSE_JUDGMENT_AND_POLICY_FIELDS_NOT_EXPLICIT | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-006` | `GM-CMIR-011` | `ProjectCommitmentExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | BLOCKED_COMMITMENT_CONTENT_LACKS_SOURCE_AND_SUPERSESSION_FIELDS | FULL_TRAJECTORY_AND_FREEZE_PROVENANCE_NOT_REPRESENTABLE | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |
| `MIRA-MEM-CAND-007` | `GM-CMIR-013` | `RelationshipExperience` | PASS | PASS | PASS | PASS | PASS_BLOCKED | BLOCKED_RELATIONSHIP_CONTENT_LACKS_FULL_TRAJECTORY_FIELDS | FULL_TRAJECTORY_NOT_REPRESENTABLE | DEFERRED_PENDING_SCHEMA_DECISION_AND_AUTHORITY |

## Decision

- All exact-boundage active candidates pass dry-run causal and boundary validation.
- The 3 Identity candidates are mappable as bounded statements with provenance, but remain non-admitted pending content review and authority.
- The 3 Narrative candidates can map their core content fields, but judgment/model-change and future-policy semantics remain in the causal package rather than the current canonical payload.
- The 3 Relationship candidates and 1 ProjectCommitment candidate are blocked for lossless correction-trajectory representation by MIRA-DEFER-007/008.
- All six unbound CMIR records remain quarantined and outside every admission-ready set.
- No canonical, runtime, context, provider, namespace, schema, or merge write occurred.

This result is validation evidence only. It does not establish identity, consent, current authorization, or admission readiness.
