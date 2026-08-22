# Wave5 AT-07 Minimal Segment Rotation Remediation Evidence

Status: MINIMAL REMEDIATION GREEN / R1 HOLD
Date: 2026-08-22
Scope: AT-07 — Segment boundary
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT07_R0_SEGMENT_BOUNDARY_CONTRACT.md`
Audit: `docs/project_control/reports/WAVE5_AT07_SEGMENT_BOUNDARY_AUDIT.md`

## 1. Checkpoint

```text
AT-07 Audit: COMPLETE
AT-07 R0 Contract: READY FOR FREEZE
AT-07 Minimal Segment Rotation Remediation: GREEN
AT-07 R1: HOLD
AT-07 IA: HOLD
AT-07 Freeze: NOT READY
```

## 2. P0 Remediated

Audit P0:

```text
append enough messages
  → transcript-000001.jsonl only
  → no physical segment rotation
```

Remediated behavior:

```text
append enough canonical messages
  → transcript-000001.jsonl
  → transcript-000002.jsonl
  → one canonical conversation
  → canonical order preserved
```

## 3. Code Changes

Modified:

```text
julia_core/conversation_state/storage_v2_repository.py
```

Added:

```text
DEFAULT_SEGMENT_MAX_BYTES = 33_554_432
DEFAULT_SEGMENT_MAX_MESSAGES = 10_000
```

Constructor now accepts test/product configurable thresholds:

```text
StorageV2ConversationRepository(
  base_dir,
  segment_max_bytes=DEFAULT_SEGMENT_MAX_BYTES,
  segment_max_messages=DEFAULT_SEGMENT_MAX_MESSAGES,
)
```

New internal physical helpers:

```text
_segment_number(path)
_latest_segment_number(conversation_id)
_segment_message_count(path)
_select_segment_for_write(conversation_id, encoded_line)
```

`_write_canonical_message(...)` now selects a target segment before writing a complete JSONL record.

## 4. Remediation Behavior

Rotation logic:

```text
current_segment = latest transcript segment
projected_count = current_count + 1
projected_bytes = current_size + next_record_bytes

if projected_count > segment_max_messages
OR projected_bytes > segment_max_bytes:
  write whole next record to next segment
else:
  write whole next record to current segment
```

Important boundary behavior:

```text
message record is never split across segments
oversized single record writes whole into one segment
segment boundary does not change conversation_id / turn_id / ordering
```

## 5. Remediation Test Artifact

Added:

```text
tests/wave5/test_at07_segment_rotation_remediation.py
```

Coverage:

| Test | Target | Status |
|---|---|---|
| `test_at07_rem_rotation_creates_second_segment_at_message_boundary` | threshold creates `transcript-000002.jsonl` at message boundary | GREEN |
| `test_at07_rem_canonical_order_preserved_across_segments` | canonical order and sequence preserved across segments | GREEN |
| `test_at07_rem_fresh_runtime_recovery_reads_all_segments` | fresh runtime reads all rotated segment files | GREEN |
| `test_at07_rem_oversized_single_record_is_not_split` | oversized record remains whole in one segment | GREEN |

## 6. Evidence Commands

### AT-07 remediation tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at07_segment_rotation_remediation.py
```

Observed result:

```text
4 passed in 0.16s
```

### AT-07 remediation + storage/cutover/management regression

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at07_segment_rotation_remediation.py \
  tests/rt2_r2/test_storage_v2_repository.py \
  tests/rt2_r2/test_cutover.py \
  tests/test_conversation_management_service.py
```

Observed result:

```text
46 passed in 1.19s
```

### Wave5 AT-03/04/05/06 + AT-07 remediation + authority focused bundle

```bash
cd /Users/admin/julia_core_wave4_integration
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
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
97 passed in 1.87s
```

### Compile check

```bash
/opt/miniconda3/bin/python -m compileall -q \
  julia_core \
  tests/wave5/test_at07_segment_rotation_remediation.py
```

Observed result:

```text
compileall_exit=0
```

## 7. Scope Control

This remediation did not change:

```text
ConversationRuntime semantic model
Context OS
Voice/S2S
Electron cache
Search
Memory/Diary
Conversation identity logic
Pagination / AT-08
Compaction
Transcript redesign
```

The change is limited to:

```text
StorageV2 physical segment selection and rollover before complete-record append
```

## 8. Gate Decision

```text
AT-07 Minimal Segment Rotation Remediation: GREEN
AT-07 R1 Permanent Evidence: NEXT
AT-07 IA: HOLD
AT-07 Freeze: NOT READY
```
