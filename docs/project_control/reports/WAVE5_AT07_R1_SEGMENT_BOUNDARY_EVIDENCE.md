# Wave5 AT-07-R1 Permanent Evidence — Segment Boundary

Status: R1 GREEN
Date: 2026-08-22
Scope: AT-07 — Segment boundary
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Base contract: `docs/authority/WAVE5_AT07_R0_SEGMENT_BOUNDARY_CONTRACT.md`
Remediation: `docs/project_control/reports/WAVE5_AT07_MINIMAL_REMEDIATION_EVIDENCE.md`

## 1. Checkpoint

```text
AT-07 Audit: COMPLETE
AT-07 R0 Contract: READY FOR FREEZE
AT-07 Minimal Segment Rotation Remediation: GREEN
AT-07 R1 Permanent Evidence: GREEN
AT-07 IA: HOLD
AT-07 Freeze: NOT READY
```

## 2. R1 Purpose

AT-07-R1 proves physical segment rotation does not change canonical conversation semantics.

Frozen rule:

```text
Segment boundary is physical persistence only, never conversation semantics.
```

## 3. Permanent Test Artifact

Added:

```text
tests/wave5/test_at07_segment_boundary.py
```

## 4. Test Case Coverage

| Test Case | Target | Status |
|---|---|---|
| TC-AT07-R1-001 | rotation creates multiple transcript segment files | GREEN |
| TC-AT07-R1-002 | canonical order preserved across segment boundary | GREEN |
| TC-AT07-R1-003 | fresh runtime recovery reads all segments unchanged | GREEN |
| TC-AT07-R1-004 | Context OS active tail unchanged by segment boundary | GREEN |
| TC-AT07-R1-005 | segment filenames/details are not exposed in runtime/management DTOs | GREEN |
| TC-AT07-R1-006 | text/voice turns across segment boundary remain one conversation | GREEN |
| TC-AT07-R1-007 | message record is never split across segments | GREEN |
| TC-AT07-R1-008 | derived metadata sabotage cannot hide durable segment files | GREEN |

## 5. Evidence Commands

### AT-07 R1 permanent tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at07_segment_boundary.py
```

Observed result:

```text
8 passed in 0.35s
```

### AT-07 remediation + R1 bundle

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/wave5/test_at07_segment_rotation_remediation.py \
  tests/wave5/test_at07_segment_boundary.py
```

Observed result:

```text
12 passed in 0.40s
```

### Wave5 AT-03/04/05/06/07 + authority focused bundle

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
  tests/wave5/test_at07_segment_boundary.py \
  tests/test_voice_turn_reconciliation.py \
  tests/test_conversation_authority.py
```

Observed result:

```text
105 passed in 2.10s
```

## 6. R0 Invariant Mapping

| R0 Invariant | R1 Evidence |
|---|---|
| AT07-I01 segment split does not create a new conversation | TC-AT07-R1-001, 003, 006 |
| AT07-I02 canonical ordering survives segment boundaries | TC-AT07-R1-002, 003 |
| AT07-I03 segment rotation is persistence concern only | TC-AT07-R1-005, 006 |
| AT07-I04 resume/read independent from physical segment layout | TC-AT07-R1-003 |
| AT07-I05 rotation failure must not corrupt canonical history | TC-AT07-R1-007, 008 |
| AT07-I06 canonical message never split across segments | TC-AT07-R1-007 |
| AT07-I07 segment metadata is derived; canonical files win | TC-AT07-R1-008 |
| AT07-I08 runtime/Context OS/Electron/S2S are segment-unaware | TC-AT07-R1-004, 005 |
| AT07-I09 resume/context behavior unchanged by rotation | TC-AT07-R1-003, 004 |
| AT07-I10 modality changes near rotation boundary do not create semantic boundary | TC-AT07-R1-006 |

## 7. Key Findings Proven by R1

### 7.1 Rotation actually happens

With a small test threshold, append creates:

```text
transcript-000001.jsonl
transcript-000002.jsonl
transcript-000003.jsonl
```

This proves AT-07 is testing real physical rollover, not only filename shape.

### 7.2 Cross-segment canonical order is preserved

Reading through management/runtime returns `ordered_000 → ordered_009`, and canonical JSONL records preserve sequence `1 → 10` across segments.

### 7.3 Fresh runtime recovery reads all segments

After closing the first repository and opening a fresh runtime/service over the same repository, all messages across `transcript-000001..000003` are present with the same `conversation_id`.

### 7.4 Context OS is segment-unaware

Context OS receives recovered canonical history and active tail includes the expected turns independent of physical segment placement.

### 7.5 Segment details are not exposed

Management/runtime DTO payloads do not expose `transcript-*`, `.jsonl`, or segment semantics.

### 7.6 Text/voice across boundary remains one sequence

Text before boundary, voice at boundary, and text after boundary remain one canonical conversation sequence with preserved role/modality/order.

### 7.7 Message records are atomic

Oversized record test proves one canonical message remains a whole JSONL record in a single segment. The next message rotates normally.

### 7.8 Canonical files win over derived metadata

Sabotaging derived catalog counters cannot hide later durable segment files. Fresh recovery reads all durable records from canonical transcript files.

## 8. Non-Goals Preserved

R1 did not enter:

- AT-08 pagination
- compaction
- search optimization
- transcript redesign
- distributed locking
- Electron UI paging
- provider behavior quality

## 9. Gate Decision

```text
AT-07 R1 Permanent Evidence: GREEN
AT-07 Integration Acceptance: NEXT
AT-07 Freeze: NOT READY
```
