# Wave5 AT-07 Segment Boundary Audit

Status: AUDIT COMPLETE / R0 BLOCKED BY P0 IMPLEMENTATION GAP
Date: 2026-08-22
Scope: AT-07 — Segment boundary
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Observed HEAD: `3c63c26`
Core lane: `/Users/admin/julia_core_wave4_integration`

## 1. Checkpoint

```text
Wave5 Authority Boundary Set         FROZEN
AT-01 Conversation Create Durability  FROZEN
AT-02 Accepted User Crash             FROZEN READY
AT-03 Text → Voice → Text             FROZEN READY / evidence committed
AT-04 Voice reconnect UUID identity   FROZEN
AT-05 Retry Idempotency               FROZEN
AT-06 Cross-conversation sabotage     FROZEN
AT-07 Segment boundary                AUDIT START
```

## 2. AT-07 Source Requirement

From `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-07 — Segment boundary

Generate enough messages to rotate transcript segment.

Resume/context behavior unchanged.
```

Related implementation task:

```text
CM-S1-T07 — Segment rotation
Operational trigger only.
16–32 MB OR 5,000–10,000 messages.
Segment rotation must not change conversation_id, turn identity,
chronological semantic order, or resume behavior.
```

AT-07 validates that physical transcript segmentation is invisible to conversation semantics.

## 3. Non-Goals

AT-07 does not test:

- pagination behavior, reserved for AT-08
- search/index rebuild, reserved for later ATs
- segment optimization or compaction
- transcript format redesign beyond minimal rotation boundary
- multi-writer/distributed locking
- provider/context quality
- retry/reconnect semantics already frozen by AT-04/AT-05
- cross-conversation isolation already frozen by AT-06

## 4. Authority Baseline

Relevant frozen rules from `STO_D0_DECISION_REGISTER_v1.0.md`:

- Segment boundary has no semantic meaning.
- Context boundary, session boundary, voice/text switch, and conversation boundary are independent of segment boundary.
- Segment rotation is a physical persistence concern only.
- A message must not be split across segment boundaries.
- Segment counters/active-segment metadata/catalog hints are derived and must not override canonical files.
- Electron / Context OS / S2S callers must be segment-unaware.

## 5. Audit Questions

AT-07 must answer:

1. Does StorageV2 actually rotate from `transcript-000001.jsonl` to later transcript segment files after threshold?
2. If rotation occurs, are `conversation_id`, `turn_id`, message order, and status preserved across the boundary?
3. Does fresh runtime/repository resume recover all messages across segment files?
4. Does Context OS active tail remain unchanged by physical segment boundary?
5. Are segment filenames/details hidden from runtime/management/provider DTOs?
6. Do existing tests prove rotation, or only ordering in one physical segment?

## 6. Evidence Commands

### Existing segment/order tests

```bash
cd /Users/admin/julia_core_wave4_integration
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at09_ordering_preserved \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at10_cross_conversation_isolation \
  tests/rt2_r3/test_core_acceptance.py::test_r3_at08_conversation_isolation
```

Observed result:

```text
3 passed in 0.20s
```

These tests prove baseline ordering/isolation but do not prove segment rotation.

## 7. Audit Probe

Probe:

```text
create StorageV2 conversation
append 250 user messages
list transcript-*.jsonl
read messages
```

Observed:

```text
segments ['transcript-000001.jsonl']
segment_count 1
message_count 250
first_last msg_000 msg_249
```

Assessment:

- Ordering/read in one segment: GREEN.
- Rotation capability: RED / P0 implementation gap for AT-07.

## 8. Code Path Findings

### F1 — StorageV2 has segment filename shape but no rotation policy

Evidence:

- `StorageV2ConversationRepository._segment_path(conv_id, seg=1)` can construct numbered segment names.
- `_write_canonical_message(conv_id, msg)` always calls `_segment_path(conv_id)` with default `seg=1`.
- No active segment selection, projected size/count check, or threshold constants were found in the current StorageV2 write path.

Impact:

AT-07's source requirement says to generate enough messages to rotate transcript segment. Current implementation cannot satisfy that behavior because all appends go to `transcript-000001.jsonl`.

### F2 — Reads are already segment-transparent if multiple files exist

Evidence:

- `_iter_transcript(conv_id)` sorts `transcript-*.jsonl` and yields every line from each file.
- `get(...)`, `get_messages(...)`, `find_turn(...)`, and `search(...)` consume `_iter_transcript(...)`.

Assessment: GREEN for read traversal shape, but unproven under real rotation because writes never create later segments.

### F3 — Existing B-AT09 test is mislabeled for segment rotation

Evidence:

- `tests/rt2_r2/test_storage_v2_repository.py::test_b_at09_ordering_preserved` appends 50 messages and asserts ordering.
- It does not assert `len(transcript-*.jsonl) > 1`.
- Because StorageV2 writes only segment 1, this test passes without exercising a segment boundary.

Assessment: AMBER/RED coverage gap.

### F4 — Runtime/resume/context behavior is likely segment-transparent once rotation exists

Evidence:

- `ConversationRuntime.get_messages(...)` and `get_canonical_history(...)` obtain messages from repository session reconstruction.
- Repository reconstruction uses `_iter_transcript(...)`.
- Context OS receives canonical history from runtime, not segment files.

Assessment: likely GREEN after rotation implementation, but AT-07 R1 cannot be meaningful until actual rotation exists.

## 9. Current Coverage Assessment

GREEN:

- Single-segment ordering is preserved.
- Read traversal already scans multiple segment files if they exist.
- Runtime/Context OS are segment-unaware by interface shape.
- Existing focused storage/isolation tests pass.

AMBER:

- Existing segment/order tests do not prove actual rotation.
- Segment metadata/counter reconciliation is not visible in current StorageV2 meta/catalog.
- No Wave5 AT-07-named permanent acceptance artifact exists.

RED/P0:

- StorageV2 does not implement segment rotation. All canonical appends currently target `transcript-000001.jsonl`.

## 10. Audit Decision

```text
AT-07 Audit: COMPLETE
Core semantic intent: CLEAR
Read/resume interface shape: GREEN
Rotation implementation readiness: BLOCKED
R0 Contract: REQUIRED and must freeze rotation as physical-only boundary
Implementation: BLOCKED by missing rotation capability
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

## 11. Required AT-07-R0 Invariants

Recommended R0 invariants:

- AT07-I01 — Segment boundary is physical persistence only, never conversation semantics.
- AT07-I02 — Rotation must preserve `conversation_id`, `turn_id`, message identity, role, modality, status, and canonical order.
- AT07-I03 — New canonical messages after threshold append to a new transcript segment without splitting any message.
- AT07-I04 — Fresh runtime/repository recovery reads all durable segment files in canonical order.
- AT07-I05 — Runtime, Context OS, Electron/S2S, and management DTOs remain segment-unaware.
- AT07-I06 — Segment counters/active segment metadata are derived; canonical segment files win on recovery.
- AT07-I07 — Rotation must not alter resume/context behavior.
- AT07-I08 — Text/voice modality changes near rotation boundary do not create semantic boundary changes.

## 12. Suggested Minimal Remediation Scope

After R0 freezes scope, minimal implementation should only add physical rotation to StorageV2 write path:

```text
select active segment
project append size/message count
if threshold exceeded before append:
  create/select next segment
append whole message record to target segment
fsync target segment
```

Do not implement pagination, compaction, search optimization, transcript redesign, or distributed locking as part of AT-07.

For testability, thresholds should be configurable or injectable so R1 can trigger rotation with small fixtures without generating thousands of large messages.

## 13. Suggested R1 Tests

Suggested file:

```text
tests/wave5/test_at07_segment_boundary.py
```

Suggested cases:

```text
TC-AT07-R1-001 generate enough messages to create transcript-000002.jsonl
TC-AT07-R1-002 canonical order preserved across segment boundary
TC-AT07-R1-003 fresh runtime recovery reads both segments unchanged
TC-AT07-R1-004 Context OS active tail unchanged by segment boundary
TC-AT07-R1-005 segment filenames/details are not exposed in management/runtime DTOs
TC-AT07-R1-006 text→voice switch across segment boundary remains one conversation
TC-AT07-R1-007 message record is never split across segments
TC-AT07-R1-008 stale/derived segment metadata cannot hide a later durable segment
```

## 14. Next Gate

Proceed to:

```text
AT-07-R0 Contract
```

Hold:

```text
AT-07 Implementation
AT-07 R1
AT-07 IA
AT-07 Freeze
```

Do not start AT-08 pagination.
