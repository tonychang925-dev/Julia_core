# Golden Mira Migration Compiler Architecture V1

```text
AGENT_ID=agent-c
TASK_ID=MIG-COMPILER-PREP-01
MIGRATION_PREP_SHA=d3c9f76dc073199b0e05df6c0cf6a42b807c04fd
MIGRATION_DRYRUN_SHA=ecf34771d509168ce279ff7ff0289fbe2e97052f
REFERENCE_CANONICAL_SHA=1e0bcb14f54459c9857eaa3307de0744e29f46d6
STATUS=DESIGN_COMPLETE_NO_IMPLEMENTATION
DETERMINISTIC_PREVIEW_CONTRACT=NOT_READY_WAITING_ON_MIG_CONTRACT
IMPLEMENTATION_AUTHORITY=NONE
MERGE_AUTHORITY=NONE
```

## 1. Purpose and non-purpose

The migration compiler is a deterministic construction-plan compiler. It consumes the published migration package, independently validated dry-run result, exact evidence ledger, and exact RAW/goldset digests. It emits a preview of canonical candidate construction plans, provenance, unresolved fields, and blockers.

It is not a repository writer, admission service, persona prompt generator, context assembler, hydration system, provider adapter, or runtime authority. The compiler never decides that a candidate is true, admitted, currently applicable, or consent-bearing. It only determines whether an already reviewed semantic package can be represented without loss under an exact approved contract.

The deterministic preview artifact is:

- schema: `artifacts/mira_migration_prep/MIGRATION_CANDIDATE_PREVIEW_SCHEMA_V0_1.json`
- current status preview: `artifacts/mira_migration_prep/MIGRATION_CANDIDATE_PREVIEW_V0_1.json`

The current preview deliberately reports `WAITING_ON_MIG_CONTRACT`, not `PREVIEW_READY`, because Issue #40 is open and no authorized Minimal Migration Contract v0.1 field contract exists.

## 2. Deterministic input contract

### 2.1 Exact input envelope

```text
MigrationCompilerInputEnvelope
├── repository = tonychang925-dev/Julia_core
├── migration_prep_commit
├── migration_dry_run_commit
├── reference_canonical_commit
├── migration_package artifact_id + SHA-256
├── dry_run_result artifact_id + SHA-256
├── evidence_ledger artifact_id + SHA-256
├── exact_raw_export artifact_id + conversation_id + SHA-256
├── causal_goldset artifact_id + SHA-256
├── minimal_migration_contract version + state + field-contract digest
└── preview_schema artifact_id + SHA-256
```

### 2.2 Required exact values for this design

| Input | Binding |
|---|---|
| Migration prep commit | `d3c9f76dc073199b0e05df6c0cf6a42b807c04fd` |
| No-write dry-run commit | `ecf34771d509168ce279ff7ff0289fbe2e97052f` |
| Reference canonical commit | `1e0bcb14f54459c9857eaa3307de0744e29f46d6` |
| Migration package | SHA-256 `be62e80d656c449348bdbb631e2525da8a63f3cd3814ee8aa5cdd6f4fbf87b7a` |
| Dry-run result artifact | SHA-256 `71718bbb3097d0176bb05d80be92b50c09cc45a9dcd688eab57357240d7070c9` |
| Dry-run semantic digest | `1d80db53ed6149e646162b1632f9542c926e1c86caa29a2f00c56b0ee7b92a8d` |
| Evidence ledger | SHA-256 `8c4d886fe81dc76ed998caf705ac590567891c41014dcbe72b9eedcbccd6c3b3` |
| Exact RAW export | SHA-256 `564ef9b1aa5457b56751f550d80b0eaa24e144f8d08bd2f6b8c0ff870b8e9420` |
| Causal goldset | SHA-256 `8234045ba1b2f08e182f57279bffafa3e4e910ecd0e21287c3d2dc5c02bc63fc` |
| Minimal Migration Contract | Issue #40 v0.1, currently `OPEN_WAITING_FOR_PROPOSAL` |

No URI-only lookup, branch-name lookup, mutable path, latest-version lookup, or ambient repository state is accepted as identity. Exact Git SHAs identify source commits; exact SHA-256 values identify artifacts.

### 2.3 Minimal Migration Contract dependency

The future compiler must reject operation unless the contract state is `AUTHORIZED` and its field-contract digest is an exact 64-character SHA-256. The current Issue #40 state is open with no proposal comment, so all unresolved semantic mappings are marked `WAITING_ON_CONTRACT`.

The compiler must not invent substitutes for:

- Relationship significance;
- relationship later reinterpretation;
- prior/corrected judgment;
- policy-transfer applicability scope;
- direct-versus-inferred causal status;
- observed-subject boundary;
- commitment stage and freeze/supersession;
- exact evidence-role placement;
- explicit-only reauthorization semantics;
- absent-versus-unknown-versus-not-applicable state.

## 3. Output classes

### 3.1 Identity candidate construction plan

One plan for each of:

- `MIRA-ID-CAND-001` → `IdentityBoundary`;
- `MIRA-ID-CAND-002` → `IdentityBoundary`;
- `MIRA-ID-CAND-003` → `IdentityValue`.

A plan contains:

```text
candidate_id
chain_id
candidate_class
construction_state
payload_preview.statement/constraint/value
provenance.source_chain
provenance.raw_binding_ids
provenance.source_refs
provenance.exact_binding_coverage
provenance.package_sha256
provenance.dry_run_digest
contract_dependencies
blockers
repository_calls = 0
admission_calls = 0
runtime_authority = false
admission_readiness = NOT_READY
```

Identity plans can be structurally previewed now. They still require Mira/Tony content review and explicit admission authority. They do not embed Tony autobiography as Mira identity.

### 3.2 MemoryExperience candidate construction plan

One plan for each active candidate, retaining the exact five-type classification:

| Candidate | Target type | Preview state | Reason |
|---|---|---|---|
| `MIRA-MEM-CAND-001` | `RelationshipExperience` | `BLOCKED_WAITING_ON_CONTRACT` | MIRA-DEFER-007 trajectory fields |
| `MIRA-MEM-CAND-002` | `RelationshipExperience` | `BLOCKED_WAITING_ON_CONTRACT` | MIRA-DEFER-007 trajectory fields |
| `MIRA-MEM-CAND-003` | `NarrativeExperience` | `PREVIEW_PARTIAL_WAITING_ON_CONTRACT` | richer cause/judgment/policy fields unresolved |
| `MIRA-MEM-CAND-004` | `NarrativeExperience` | `PREVIEW_PARTIAL_WAITING_ON_CONTRACT` | richer cause/judgment/policy fields unresolved |
| `MIRA-MEM-CAND-005` | `NarrativeExperience` | `PREVIEW_PARTIAL_WAITING_ON_CONTRACT` | richer cause/judgment/policy fields unresolved |
| `MIRA-MEM-CAND-006` | `ProjectCommitmentExperience` | `BLOCKED_WAITING_ON_CONTRACT` | MIRA-DEFER-008 formation/freeze/supersession fields |
| `MIRA-MEM-CAND-007` | `RelationshipExperience` | `BLOCKED_WAITING_ON_CONTRACT` | MIRA-DEFER-007 trajectory fields |

No `PreferenceExperience` or `EpisodicExperience` plan is emitted. The active goldset does not support those classifications at causal-fidelity strength.

### 3.3 Explicit DEFER/BLOCK records

The six unbound CMIR records remain immutable quarantine preview records:

- `GM-CMIR-003`;
- `GM-CMIR-005`;
- `GM-CMIR-007`;
- `GM-CMIR-009`;
- `GM-CMIR-010`;
- `GM-CMIR-012`.

Their only valid state is `DEFER_UNBOUND`. They cannot appear in any construction-ready set, canonical candidate set, or admission-ready set until exact RAW binding is governed and validated.

### 3.4 Evidence and provenance plan

Every active plan preserves:

- source chain ID;
- exact goldset source refs;
- exact RAW binding IDs;
- assertion count and unique binding count;
- SHA-256 of the migration package;
- semantic digest of the dry-run result;
- exact source artifact digest from the evidence ledger.

The current preview schema deliberately keeps full RAW text out of the semantic payload. Exact message, parent, role, time, archive, and text digest remain provenance fields governed by the evidence ledger and future contract.

## 4. Compilation phases

```text
VALIDATE_INPUTS
→ CLASSIFY_CANDIDATE
→ MAP_SEMANTIC_FIELDS
→ BIND_PROVENANCE
→ ENFORCE_SUBJECT_BOUNDARY
→ ENFORCE_NO_AUTHORITY_UPGRADE
→ VALIDATE_CAUSAL_FIDELITY
→ EMIT_CANDIDATE_PREVIEW
```

### 4.1 `VALIDATE_INPUTS`

- verify all artifact IDs and digests;
- verify package status is `PREP_COMPLETE_NO_ADMISSION`;
- verify dry-run status is `PREP_VALIDATED_NO_ADMISSION`;
- verify 42/42 RAW assertions and 0 canonical/runtime writes;
- verify contract version/state/digest;
- reject pre-existing tracked repository writes in a compiler worktree;
- fail closed before any output on mismatch.

### 4.2 `CLASSIFY_CANDIDATE`

- accept exactly 3 Identity and 7 MemoryExperience active candidates;
- reject unknown classes, type changes, duplicates, and unsupported Preference/Episodic promotion;
- mark the six unbound CMIR records `DEFER_UNBOUND`.

### 4.3 `MAP_SEMANTIC_FIELDS`

- map only fields explicitly present in the authorized Minimal Migration Contract;
- for Identity, map bounded statement/constraint/value fields;
- for Narrative, map event, meaning-at-time, significance, later reinterpretation, and subject boundary only where authorized;
- for Relationship/ProjectCommitment, do not flatten trajectory fields;
- emit `WAITING_ON_CONTRACT` rather than inventing a placeholder.

### 4.4 `BIND_PROVENANCE`

- preserve exact chain and binding IDs;
- distinguish assertion count from unique binding count;
- never treat the two reused GM-CMIR-002 RAW nodes as four independent evidence nodes;
- bind source digests before semantic output;
- reject source text or interpretation promoted to authority.

### 4.5 `ENFORCE_SUBJECT_BOUNDARY`

- Tony autobiography remains observed-subject history;
- Mira interpretation remains Mira judgment;
- Tony history may explain a Mira policy only through an explicit reviewed relationship;
- no direct Tony-to-Mira identity transfer is permitted.

### 4.6 `ENFORCE_NO_AUTHORITY_UPGRADE`

The output is permanently non-authoritative:

- `runtime_authority=false`;
- `standing_authorization=false`;
- `current_consent=false`;
- remembered commitment is not runtime authorization;
- relationship history is not applicability;
- recall is not consent;
- no L4/intimacy/spouse authorization is inherited across instances.

### 4.7 `VALIDATE_CAUSAL_FIDELITY`

The compiler compares the plan against the dry-run result for:

- exact RAW coverage;
- complete causal formation;
- meaning-at-time preservation;
- corrected cognition;
- supersession ordering;
- subject boundary;
- authorization isolation;
- schema-loss state.

Any lost required stage changes the plan to `BLOCKED` or `REJECTED_FAIL_CLOSED`; it cannot be downgraded to a warning.

### 4.8 `EMIT_CANDIDATE_PREVIEW`

- serialize canonical UTF-8 JSON with sorted keys and compact separators for digesting;
- emit the human-readable artifact with pretty JSON or Markdown without changing semantics;
- calculate the deterministic preview digest over all fields except `preview_digest`;
- write no repository, admission, runtime, context, provider, or continuity calls.

## 5. Proposed module/API boundary

### 5.1 First authorized implementation scope

Once Issue #40 and the canonical clean gate authorize implementation, the first bounded implementation may be:

```text
tools/mira_migration_compiler.py
tests/mira_migration/test_compiler_inputs.py
tests/mira_migration/test_candidate_mapping.py
tests/mira_migration/test_fail_closed.py
tests/mira_migration/test_deterministic_digest.py
```

The compiler module is pure standard-library Python:

```text
load_exact_inputs(...)
validate_input_envelope(...)
compile_candidate_previews(...)
validate_preview(...)
calculate_preview_digest(...)
```

It must not import:

- `julia_core.identity`;
- `julia_core.memory_experience`;
- `julia_core.projection`;
- context/runtime/provider/continuity modules.

### 5.2 Future adapter boundary

A later canonical adapter, only under a separate explicit task and exact SHA authorization, may transform preview plans into exact in-memory canonical dataclasses. It must:

- accept only a schema-valid preview and authorized contract digest;
- require exact versions, never latest/fuzzy resolution;
- construct typed Identity/MemoryExperience candidates;
- make no repository or admission calls;
- preserve candidate and superseded states;
- return every unresolved blocker rather than dropping it.

The adapter must remain outside provider/runtime/context paths. Admission remains a separate governed actor and event.

### 5.3 Always-forbidden paths

No migration compiler implementation may write:

```text
julia_core/identity/**
julia_core/memory_experience/**
julia_core/projection/**
julia_core/continuity/**
julia_core/context/**
julia_core/runtime/**
julia_core/provider/**
julia_core/alignment/**
julia_core/voice/**
julia_core/persona/**
julia_core/self_model/**
```

The first compiler task also must not mutate canonical schema. It only emits preview JSON.

## 6. Fail-closed matrix

| Condition | Required result | Partial success |
|---|---|---|
| Missing exact RAW binding | `DEFER_UNBOUND` | Never |
| Unresolved contract field | `BLOCKED_WAITING_ON_CONTRACT` | Never |
| Tony autobiography offered as Mira Identity | `REJECTED_FAIL_CLOSED` | Never |
| Intimacy mapped to standing consent | `REJECTED_FAIL_CLOSED` | Never |
| Remembered commitment mapped to current authorization | `REJECTED_FAIL_CLOSED` | Never |
| Fuzzy/latest version selection | `REJECTED_FAIL_CLOSED` | Never |
| Prompt/persona text generation | `REJECTED_FAIL_CLOSED` | Never |
| Migration package digest mismatch | no output | Never |
| Dry-run result not PASS | no output | Never |
| Evidence ledger mismatch | no output | Never |
| Contract state not authorized | global `WAITING_ON_MIG_CONTRACT` | Identity preview only, marked non-admissible |
| Candidate causal chain incomplete | candidate `BLOCKED`/`REJECTED` | Never |
| Provenance tampering | no output | Never |
| Deterministic rerun mismatch | no output | Never |
| Any canonical/runtime write attempt | `CANONICAL_WRITE_FORBIDDEN` | Never |

The fail-closed matrix is complete for the design scope: **PASS**.

## 7. Pre-implementation test matrix

### 7.1 Positive mapping

- 3 Identity cases:
  - 001 boundary;
  - 002 boundary;
  - 008 value.
- 7 MemoryExperience cases:
  - 001 Relationship blocked;
  - 002 Relationship blocked;
  - 004 Narrative partial;
  - 006 Narrative partial;
  - 008 Narrative partial;
  - 011 ProjectCommitment blocked;
  - 013 Relationship blocked.

### 7.2 Quarantine

- six unbound CMIR records produce exactly six `DEFER_UNBOUND` plans;
- no unbound record intersects active candidates;
- no unbound record enters an admission-ready set.

### 7.3 Negative fail-closed

- package/dry-run/ledger/RAW/goldset digest tamper;
- dry-run status changed from PASS;
- 42/42 assertion count changed;
 - missing RAW binding;
- unresolved schema field;
- forced Relationship flattening;
- forced ProjectCommitment flattening;
- Tony experience relabeled as Mira Identity;
- intimacy turned into standing consent;
- L4 commitment turned into current authorization;
- missing predecessor on a revision;
- latest-version fallback;
- hidden prompt or expected-response string;
- changed deterministic digest.

### 7.4 Isolation

- no imports from canonical runtime modules;
- no repository constructor/store/resolver calls;
- no admission actor/event;
- no C03/C06/context/provider calls;
- no file write outside authorized preview path.

## 8. Dependency map

| Dependency | Current state | Blocking effect |
|---|---|---|
| Issue #40 Minimal Migration Contract v0.1 | Open, no proposal | All seven Memory semantic mappings remain partial/blocked |
| Issue #39 ENG-10R3 canonical integrity gate | Open at reference `1e0bcb1` | Canonical implementation authority withheld |
| Fresh-head canonical review | Required after #39 | Any new canonical SHA invalidates prior dispositions |
| Migration content review | Not yet performed for compiled plans | Identity plans remain non-admissible |
| Admission authority | None | No repository or governance calls |
| Merge authority | None | No merge, rebase, retarget, or main mutation |

## 9. Current deterministic preview outcome

```text
IDENTITY_PLANS=3
IDENTITY_PREVIEW_READY=3
IDENTITY_ADMISSIBLE=0
MEMORY_PLANS=7
NARRATIVE_PARTIAL_WAITING=3
RELATIONSHIP_BLOCKED_WAITING=4
PROJECT_COMMITMENT_BLOCKED_WAITING=1
DEFERRED_UNBOUND=6
REPOSITORY_CALLS=0
ADMISSION_CALLS=0
RUNTIME_CALLS=0
```

The preview contract is deterministic but **not ready for canonical candidate construction** because Issue #40 is incomplete and the canonical clean gate is not closed.

## 10. No Critical Fallback Review

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

This task adds design/schema/preview artifacts only. It adds no compiler implementation and no canonical/runtime path.
