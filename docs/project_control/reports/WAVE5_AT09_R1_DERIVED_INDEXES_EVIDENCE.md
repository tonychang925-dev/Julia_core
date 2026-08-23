# Wave5 AT-09 R1 Permanent Acceptance Evidence — Delete Derived Indexes

Status: R1 PERMANENT ACCEPTANCE GREEN / IA HOLD
Date: 2026-08-23
Scope: AT-09 — Delete derived indexes
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base remediation: `docs/project_control/reports/WAVE5_AT09_MINIMAL_REMEDIATION_EVIDENCE.md`
R0 contract: `docs/authority/WAVE5_AT09_R0_DELETE_DERIVED_INDEXES_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT09_DELETE_DERIVED_INDEXES_AUDIT.md`

## 1. Gate Position

```text
AT-09 Audit: COMPLETE
AT-09 R0 Contract: READY FOR FREEZE
AT-09 Minimal Derived Rebuild Remediation: GREEN
AT-09 R1 Permanent Acceptance: GREEN
AT-09 IA: HOLD
AT-09 Freeze: NOT READY
```

R1 converts the AT-09 R0 derived-index invariants into permanent executable
evidence. It does not mark AT-09 frozen and does not start IA.

## 2. Frozen Rule Under Test

```text
Derived indexes are rebuildable projections, not canonical history authority.
```

Deleting or corrupting derived catalog/index artifacts must not alter canonical
conversation history, and rebuild must not reset future append identity.

## 3. Permanent Test Artifact

```text
tests/wave5/test_at09_delete_derived_indexes.py
```

## 4. Test Coverage

| Test Case | Verification Target | Status |
| --- | --- | --- |
| TC-AT09-R1-001 | Delete derived catalog rebuild preserves canonical messages exactly | GREEN |
| TC-AT09-R1-002 | Stale counter/sequence sabotage is corrected from transcript truth | GREEN |
| TC-AT09-R1-003 | Post-rebuild append uses unique next canonical message_id | GREEN |
| TC-AT09-R1-004 | Turn lookup rebuild restores turn_index from transcript | GREEN |
| TC-AT09-R1-005 | Fresh runtime recovery preserves append identity continuity | GREEN |
| TC-AT09-R1-006 | Future indexes namespace deletion is non-authoritative/no-op for canonical history | GREEN |
| TC-AT09-R1-007 | Cross-conversation rebuild preserves isolation | GREEN |
| TC-AT09-R1-008 | Rebuild performs zero canonical transcript mutation | GREEN |

## 5. Evidence Summary

### 5.1 Delete derived catalog → exact canonical recovery

R1 deletes `catalog.sqlite*`, opens a fresh StorageV2 repository, and compares
canonical message IDs, content, and transcript digest.

Result:

```text
canonical_digest_after == canonical_digest_before
message_ids_after == message_ids_before
message_count restored from transcript
```

### 5.2 Counter/sequence sabotage cannot override transcript truth

R1 sabotages derived catalog fields:

```text
message_count = 0
last_sequence = 0
```

Then rebuilds.

Result:

```text
message_count = count(transcript messages)
last_sequence = max(canonical sequence)
```

### 5.3 Post-rebuild append identity continuity

R1 verifies:

```text
existing messages: msg_..._000001..msg_..._000019
delete catalog.sqlite*
rebuild
append
  → msg_..._000020
  → zero duplicate message_id
```

### 5.4 Turn lookup rebuild

R1 deletes `turn_index` rows and rebuilds from transcript truth.

Result:

```text
find_turn(conversation_id, turn_id)
  → original user + assistant messages
```

### 5.5 Fresh runtime recovery

R1 uses a fresh Runtime/Management stack after deleting derived catalog files and
then appends through the governed runtime path.

Result:

```text
new runtime append continues canonical message identity
management message_count reflects rebuilt + appended messages
```

### 5.6 Future indexes namespace boundary

R1 creates and deletes a placeholder `indexes/conversation_fts.db` artifact.

Result:

```text
indexes/* deletion does not affect canonical transcript digest
indexes/* remains derived namespace only
```

This does not implement FTS/search architecture. It freezes the authority boundary
for future index artifacts.

### 5.7 Cross-conversation isolation

R1 rebuilds derived catalog for two conversations with distinct markers.

Result:

```text
conv_a contains ALPHA only
conv_b contains BETA only
search resolves each marker to the correct conversation
```

### 5.8 Zero canonical mutation

R1 hashes canonical transcript files before and after `rebuild_catalog()`.

Result:

```text
canonical_digest_before == canonical_digest_after
message_ids_before == message_ids_after
```

## 6. Verification Commands

### AT-09 R1

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at09_delete_derived_indexes.py
```

Observed:

```text
8 passed
```

### AT-09 remediation + R1

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at09_derived_rebuild_remediation.py \
  tests/wave5/test_at09_delete_derived_indexes.py
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
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py \
  tests/test_conversation_management_service.py
```

Observed:

```text
159 passed
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
  julia_core tests/wave5/test_at09_delete_derived_indexes.py
```

Observed:

```text
exit=0
```

## 7. R1 Decision

```text
AT-09 R1 Permanent Acceptance: GREEN
AT-09 IA: NEXT after explicit checkpoint confirmation
AT-09 Freeze: NOT READY
```

R1 proves the permanent sabotage/evidence layer. Integration Acceptance must still
prove the real governed management/runtime route after derived deletion/rebuild
before freeze.

## 8. Scope Guard

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
