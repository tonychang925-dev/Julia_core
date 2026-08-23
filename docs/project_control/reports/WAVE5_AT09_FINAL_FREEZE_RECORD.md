# Wave5 AT-09 Final Freeze Record — Delete Derived Indexes

Status: FROZEN
Date: 2026-08-23
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Freeze commit candidate: `bb90443`
Scope: AT-09 — Delete derived indexes

## 1. Freeze Decision

```text
AT-09 Delete Derived Indexes: FROZEN
```

AT-09 is frozen because the full lineage is complete:

```text
Audit
  ↓
R0 Contract
  ↓
Minimal Derived Rebuild Remediation
  ↓
R1 Permanent Evidence
  ↓
Integration Acceptance
  ↓
Final Freeze Evidence
  ↓
Final Freeze Record
```

## 2. Commit Lineage

```text
b21a9ef  docs(wave5): freeze AT-09 derived indexes R0 contract
  ↓
658ff94  fix(wave5): remediate AT-09 derived rebuild boundaries
  ↓
a4ee85c  test(wave5): add AT-09 derived indexes evidence
  ↓
bb90443  test(wave5): add AT-09 integration acceptance evidence
```

## 3. Frozen Artifacts

```text
docs/project_control/reports/WAVE5_AT09_DELETE_DERIVED_INDEXES_AUDIT.md
docs/authority/WAVE5_AT09_R0_DELETE_DERIVED_INDEXES_CONTRACT.md
docs/project_control/reports/WAVE5_AT09_MINIMAL_REMEDIATION_EVIDENCE.md
docs/project_control/reports/WAVE5_AT09_R1_DERIVED_INDEXES_EVIDENCE.md
docs/project_control/reports/WAVE5_AT09_IA_FINAL_FREEZE_EVIDENCE.md
docs/project_control/reports/WAVE5_AT09_FINAL_FREEZE_RECORD.md
tests/wave5/test_at09_derived_rebuild_remediation.py
tests/wave5/test_at09_delete_derived_indexes.py
tests/wave5/test_at09_integration_acceptance.py
```

## 4. Frozen Boundary

AT-09 freezes this boundary:

```text
Derived indexes are rebuildable projections,
not canonical history authority.
```

Expanded rules:

```text
canonical transcript
  >
derived catalog/index state

delete derived catalog/index
  ≠
delete canonical history

rebuild derived state
  ≠
rewrite transcript

derived counter / sequence
  ≠
identity authority

catalog / search / list projections
  ≠
conversation truth
```

Final rule:

```text
canonical history
  →
derived projection
  →
rebuild
  →
future continuation
```

The direction is one-way. Derived artifacts may be rebuilt from canonical truth;
they must not redefine canonical truth or future identity.

## 5. Code Boundary Remediated

Minimal remediation changed only:

```text
julia_core/conversation_state/storage_v2_repository.py
```

Remediation behavior:

```text
_reconcile()
  scans transcript-*.jsonl
  computes message_count = count(canonical messages)
  computes last_sequence = max(canonical sequence)
  rebuilds turn_index from transcript truth
```

Post-rebuild append behavior:

```text
delete catalog.sqlite*
  ↓
fresh rebuild
  ↓
next append sequence = max(canonical sequence) + 1
  ↓
new message_id is unique
```

Concrete derived target for this implementation:

```text
catalog.sqlite
catalog.sqlite-wal
catalog.sqlite-shm
```

Future derived namespace covered by the same authority rule:

```text
indexes/*
```

Scope intentionally did not change:

```text
AT-10
compaction
search optimization
FTS/tokenizer work
new indexes/* architecture
transcript redesign
Context OS policy changes
Electron cache behavior
```

## 6. Verification Evidence

### AT-09 Minimal Derived Rebuild Remediation

```text
tests/wave5/test_at09_derived_rebuild_remediation.py
5 passed
```

Remediation proved:

```text
rebuild restores message_count and last_sequence
post-rebuild append uses next canonical sequence
turn_index rebuilt from canonical transcript
management handle count recovers after catalog deletion
segment-backed rebuild counts all transcript segments
```

### AT-09 R1 Permanent Evidence

```text
tests/wave5/test_at09_delete_derived_indexes.py
8 passed
```

R1 proved:

```text
delete derived catalog rebuild preserves canonical messages exactly
stale counter/sequence sabotage corrected from transcript truth
post-rebuild append uses unique next canonical message_id
turn lookup rebuild restores turn_index from transcript
fresh runtime recovery preserves append identity continuity
future indexes namespace deletion is non-authoritative/no-op for canonical history
cross-conversation rebuild preserves isolation
rebuild performs zero canonical transcript mutation
```

### AT-09 Remediation + R1 Bundle

```text
tests/wave5/test_at09_derived_rebuild_remediation.py
tests/wave5/test_at09_delete_derived_indexes.py

13 passed
```

### AT-09 Integration Acceptance

```text
tests/wave5/test_at09_integration_acceptance.py
5 passed
```

IA proved:

```text
management path reads complete canonical history after derived deletion/rebuild
fresh runtime recovery does not use catalog as history authority
governed post-rebuild append preserves message identity continuity
sabotaged derived counters are corrected from canonical transcript
multi-conversation rebuild preserves isolation through management/search
```

### AT-09 R1 + IA Bundle

```text
tests/wave5/test_at09_delete_derived_indexes.py
tests/wave5/test_at09_integration_acceptance.py

13 passed
```

### Wave5 AT-03/04/05/06/07/08/09 + Authority Focused Bundle

```text
tests/wave5/test_at03_text_voice_text.py
tests/wave5/test_at03_integration_acceptance.py
tests/wave5/test_at04_voice_reconnect_uuid_identity.py
tests/wave5/test_at04_integration_acceptance.py
tests/wave5/test_at05_retry_idempotency.py
tests/wave5/test_at05_integration_acceptance.py
tests/wave5/test_at06_context_boundary_remediation.py
tests/wave5/test_at06_cross_conversation_sabotage.py
tests/wave5/test_at06_integration_acceptance.py
tests/wave5/test_at07_segment_rotation_remediation.py
tests/wave5/test_at07_segment_boundary.py
tests/wave5/test_at07_integration_acceptance.py
tests/wave5/test_at08_pagination_remediation.py
tests/wave5/test_at08_pagination.py
tests/wave5/test_at08_integration_acceptance.py
tests/wave5/test_at09_derived_rebuild_remediation.py
tests/wave5/test_at09_delete_derived_indexes.py
tests/wave5/test_at09_integration_acceptance.py
tests/test_voice_turn_reconciliation.py
tests/test_conversation_authority.py
tests/test_conversation_management_service.py

164 passed
```

### Storage / Cutover / Migration Regression

```text
tests/rt2_r2/test_storage_v2_repository.py
tests/rt2_r2/test_cutover.py
tests/rt2_r2/test_legacy_migration.py
tests/rt2_r3/test_core_acceptance.py
tests/test_conversation_management_service.py

63 passed
```

### Compile Check

```text
/opt/miniconda3/bin/python -m compileall -q julia_core tests/wave5/test_at09_integration_acceptance.py
compileall_exit=0
```

## 7. Integration Path Confirmed

AT-09 IA proved the real governed path:

```text
ConversationManagementService create/read/search
  ↓
ConversationRuntime governed append path
  ↓
StorageV2 canonical transcript files
  ↓
delete derived catalog/index artifacts
  ↓
fresh repository/runtime/management stack rebuild
  ↓
read/search/append continue with zero semantic loss
```

This confirms derived catalog/index deletion does not become history deletion,
identity reset, or cross-conversation contamination.

## 8. Relationship to Prior Frozen Gates

AT-09 depends on and preserves:

```text
AT-06 Cross-conversation sabotage:
rebuild does not mix conversations

AT-07 Segment Boundary:
rebuild scans all transcript segments without changing segment semantics

AT-08 Pagination:
read-view continuity remains derived from canonical transcript

AT-04 / AT-05 identity/idempotency:
post-rebuild append does not reuse message identity or duplicate history
```

AT-09 adds:

```text
derived projection deletion/rebuild
  ≠
canonical history or identity authority
```

## 9. Explicit Non-Scope

AT-09 freeze does not include:

```text
AT-10 Electron cache destruction
compaction
search optimization
FTS/tokenizer work
new indexes/* architecture
transcript redesign
Context OS policy changes
Electron cache behavior
backup/restore policy
```

## 10. Final Acceptance Matrix Update

```text
Wave5 Authority Boundary Set          FROZEN
AT-01 Conversation Create Durability   FROZEN
AT-02 Accepted User Crash              FROZEN READY
AT-03 Text → Voice → Text              FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity    FROZEN
AT-05 Retry Idempotency                FROZEN
AT-06 Cross-conversation sabotage      FROZEN
AT-07 Segment Boundary                 FROZEN
AT-08 Pagination                       FROZEN
AT-09 Delete Derived Indexes           FROZEN
```

Next allowed entry:

```text
AT-10 Electron Cache Destruction Audit
```

AT-10 remains not started by this record.
