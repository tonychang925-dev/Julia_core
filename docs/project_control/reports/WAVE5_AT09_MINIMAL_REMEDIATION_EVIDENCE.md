# Wave5 AT-09 Minimal Derived Rebuild Remediation Evidence

Status: MINIMAL REMEDIATION GREEN / R1 HOLD
Date: 2026-08-23
Scope: AT-09 — Delete derived indexes
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base R0: `docs/authority/WAVE5_AT09_R0_DELETE_DERIVED_INDEXES_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT09_DELETE_DERIVED_INDEXES_AUDIT.md`

## 1. Gate Position

```text
AT-09 Audit: COMPLETE
AT-09 R0 Contract: READY FOR FREEZE
AT-09 Minimal Derived Rebuild Remediation: GREEN
AT-09 R1: HOLD
AT-09 IA: HOLD
AT-09 Freeze: NOT READY
```

This remediation closes the P0 rebuild/identity gap needed before R1 permanent
evidence. It does not mark AT-09 frozen.

## 2. Remediation Scope

Allowed scope:

- Rebuild StorageV2 derived `message_count` from canonical transcript files
- Rebuild StorageV2 derived `last_sequence` from canonical transcript files
- Rebuild `turn_index` from canonical transcript files
- Preserve post-rebuild append identity continuity
- Treat current `catalog.sqlite*` as the concrete derived-index deletion target

Out of scope and unchanged:

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

## 3. Files Changed

```text
julia_core/conversation_state/storage_v2_repository.py
tests/wave5/test_at09_derived_rebuild_remediation.py
```

## 4. Fix Summary

### P0-GAP-1 — Derived counter rebuild incomplete

Before:

```text
delete catalog.sqlite
fresh StorageV2 rebuild
  → messages readable
  → message_count = 0
  → last_sequence = 0
```

After:

```text
_reconcile() scans transcript-*.jsonl
  → message_count = count(canonical messages)
  → last_sequence = max(canonical sequence)
```

### P0-GAP-2 — Post-rebuild append identity collision

Before:

```text
existing: msg_..._000001..msg_..._000005
delete catalog.sqlite
rebuild
append
  → msg_..._000001 duplicate
```

After:

```text
existing: msg_..._000001..msg_..._000005
delete catalog.sqlite
rebuild
append
  → msg_..._000006
  → zero duplicate message_id
```

### P0-GAP-3 — Turn lookup rebuild completeness

Before, existing tests did not prove `turn_index` was rebuilt from canonical
transcript truth after derived deletion.

After, `_reconcile()` deletes stale `turn_index` rows for each conversation and
rebuilds them from canonical transcript messages.

## 5. Remediation Tests

New test file:

```text
tests/wave5/test_at09_derived_rebuild_remediation.py
```

Coverage:

```text
AT09-REM-001 rebuild restores message_count and last_sequence
AT09-REM-002 post-rebuild append uses next canonical sequence
AT09-REM-003 turn_index rebuilt from canonical transcript
AT09-REM-004 management handle count recovers after catalog deletion
AT09-REM-005 segment-backed rebuild counts all transcript segments
```

Verification:

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at09_derived_rebuild_remediation.py
```

Observed:

```text
5 passed
```

## 6. Regression Evidence

Focused storage/cutover/management regression:

```text
tests/wave5/test_at09_derived_rebuild_remediation.py
tests/wave5/test_at08_pagination_remediation.py
tests/wave5/test_at08_pagination.py
tests/wave5/test_at08_integration_acceptance.py
tests/wave5/test_at07_segment_rotation_remediation.py
tests/wave5/test_at07_segment_boundary.py
tests/wave5/test_at07_integration_acceptance.py
tests/rt2_r2/test_storage_v2_repository.py
tests/rt2_r2/test_cutover.py
tests/rt2_r2/test_legacy_migration.py
tests/rt2_r3/test_core_acceptance.py
tests/test_conversation_management_service.py

103 passed
```

Wave5 / authority focused bundle:

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
tests/test_voice_turn_reconciliation.py
tests/test_conversation_authority.py
tests/test_conversation_management_service.py

151 passed
```

Compile check:

```text
/opt/miniconda3/bin/python -m compileall -q julia_core tests/wave5/test_at09_derived_rebuild_remediation.py
exit=0
```

## 7. Compatibility Notes

Preserved behavior:

- Canonical transcript files remain unchanged by rebuild.
- Legacy migration digest remains stable after rebuild.
- Existing read/search/list/find-turn paths remain available after catalog rebuild.
- No new FTS/search/index architecture was introduced.

Changed behavior:

- Derived catalog rebuild now restores counters and sequence watermark from
  canonical transcript files.
- Post-rebuild append continues from canonical max sequence instead of resetting.

## 8. R1 Entry Criteria

AT-09 R1 may now start, but remains HOLD until explicitly entered.

R1 should turn this remediation into permanent acceptance evidence covering:

- delete derived catalog/index artifacts → rebuild preserves canonical messages exactly;
- message_count and last_sequence restored;
- post-rebuild append creates unique next message_id;
- search/list/find-turn recover from canonical transcript;
- stale derived metadata cannot hide canonical transcript;
- rebuild is read-only over transcript files;
- multi-conversation isolation and segment-backed rebuild.
