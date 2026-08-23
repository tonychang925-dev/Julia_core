# Wave5 AT-09 Integration Acceptance / Final Freeze Evidence — Delete Derived Indexes

Status: IA GREEN / FINAL FREEZE EVIDENCE READY
Date: 2026-08-23
Scope: AT-09 — Delete derived indexes
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
R1 evidence: `docs/project_control/reports/WAVE5_AT09_R1_DERIVED_INDEXES_EVIDENCE.md`
Remediation evidence: `docs/project_control/reports/WAVE5_AT09_MINIMAL_REMEDIATION_EVIDENCE.md`
R0 contract: `docs/authority/WAVE5_AT09_R0_DELETE_DERIVED_INDEXES_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT09_DELETE_DERIVED_INDEXES_AUDIT.md`

## 1. Gate Position

```text
AT-09 Audit: COMPLETE
AT-09 R0 Contract: READY FOR FREEZE
AT-09 Minimal Derived Rebuild Remediation: GREEN
AT-09 R1 Permanent Acceptance: GREEN
AT-09 Integration Acceptance: GREEN
AT-09 Final Freeze Evidence: FROZEN READY
AT-09 Freeze: NOT READY until final freeze record is committed
```

## 2. Integration Path Under Test

AT-09 IA verifies the governed product/runtime/storage path:

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

The IA evidence does not rely on isolated repository-only behavior as the final
acceptance surface. Repository sabotage was covered by R1; IA proves the governed
runtime path.

## 3. IA Test Artifact

```text
tests/wave5/test_at09_integration_acceptance.py
```

## 4. IA Coverage

| Test Case | Verification Target | Status |
| --- | --- | --- |
| TC-AT09-IA-001 | Management path reads complete canonical history after derived deletion/rebuild | GREEN |
| TC-AT09-IA-002 | Fresh runtime recovery does not use catalog as history authority | GREEN |
| TC-AT09-IA-003 | Governed post-rebuild append preserves message identity continuity | GREEN |
| TC-AT09-IA-004 | Sabotaged derived counters are corrected from canonical transcript | GREEN |
| TC-AT09-IA-005 | Multi-conversation rebuild preserves isolation through management/search | GREEN |

## 5. IA Findings

### 5.1 Governed management read survives derived deletion

IA creates a conversation through `ConversationManagementService`, appends durable
messages through `ConversationRuntime`, deletes `catalog.sqlite*`, then constructs
a fresh StorageV2/Runtime/Management stack.

Result:

```text
management get_messages after rebuild == pre-delete canonical sequence
management detail.message_count restored from transcript
```

### 5.2 Catalog is not history authority

IA deletes derived catalog artifacts and verifies fresh runtime recovery.

Result:

```text
missing catalog
  ≠
missing history
  ≠
new conversation identity
```

The canonical transcript remains authoritative.

### 5.3 Governed post-rebuild append preserves identity continuity

IA appends through `ConversationRuntime` after derived deletion/rebuild.

Result:

```text
old messages preserved
new message_id = next canonical sequence
zero duplicate message_id
```

### 5.4 Derived counter sabotage corrected from transcript

IA corrupts derived catalog fields:

```text
message_count = 0
last_sequence = 0
```

Then invokes rebuild.

Result:

```text
message_count restored from transcript
last_sequence restored from max transcript sequence
canonical contents unchanged
```

### 5.5 Multi-conversation isolation preserved

IA creates two conversations with separate markers, deletes derived catalog files,
then reads/searches through the fresh management/runtime path.

Result:

```text
conversation A contains A markers only
conversation B contains B markers only
search A marker → A
search B marker → B
```

This preserves AT-06 after derived rebuild.

## 6. Verification Commands

### AT-09 IA

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at09_integration_acceptance.py
```

Observed:

```text
5 passed
```

### AT-09 R1 + IA

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at09_delete_derived_indexes.py \
  tests/wave5/test_at09_integration_acceptance.py
```

Observed:

```text
13 passed
```

### Wave5 / authority focused bundle

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at03_text_voice_text.py \
  tests/wave5/test_at03_integration_acceptance.py \
  tests/wave5/test_at04_voice_reconnect_uuid_identity.py \
  tests/wave5/test_at04_integration_acceptance.py \
  tests/wave5/test_at05_retry_idempotency.py \
  tests/wave5/test_at05_integration_acceptance.py \
  tests/wave5/test_at06_context_boundary_remediation.py \
  tests/wave5/test_at06_cross_conversation_sabotage.py \
  tests/wave5/test_at06_integration_acceptance.py \
  tests/wave5/test_at07_segment_rotation_remediation.py \
  tests/wave5/test_at07_segment_boundary.py \
  tests/wave5/test_at07_integration_acceptance.py \
  tests/wave5/test_at08_pagination_remediation.py \
  tests/wave5/test_at08_pagination.py \
  tests/wave5/test_at08_integration_acceptance.py \
  tests/wave5/test_at09_derived_rebuild_remediation.py \
  tests/wave5/test_at09_delete_derived_indexes.py \
  tests/wave5/test_at09_integration_acceptance.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py \
  tests/test_conversation_management_service.py
```

Observed:

```text
164 passed
```

### Storage / cutover / migration regression

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/rt2_r2/test_storage_v2_repository.py \
  tests/rt2_r2/test_cutover.py \
  tests/rt2_r2/test_legacy_migration.py \
  tests/rt2_r3/test_core_acceptance.py \
  tests/test_conversation_management_service.py
```

Observed:

```text
63 passed
```

### Compile check

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m compileall -q \
  julia_core tests/wave5/test_at09_integration_acceptance.py
```

Observed:

```text
exit=0
```

## 7. Final Boundary Review

AT-09 freeze candidate:

```text
Derived indexes are rebuildable projections, not canonical history authority.
```

Expanded:

```text
delete derived catalog/index
  ≠
delete canonical history

rebuild derived state
  ≠
rewrite transcript

derived counter/sequence
  ≠
identity authority

catalog/search/list projections
  ≠
conversation truth
```

## 8. Remaining Gate

AT-09 has complete final freeze evidence, but it is not formally frozen until the
Final Freeze Record is committed.

Next step:

```text
AT-09 Final Freeze Record
```

Still not started:

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
