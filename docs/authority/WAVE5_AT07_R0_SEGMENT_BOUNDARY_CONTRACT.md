# Wave5 AT-07-R0 Contract — Segment Boundary

Status: R0 READY FOR FREEZE / IMPLEMENTATION BLOCKED BY P0 ROTATION GAP
Date: 2026-08-22
Scope: AT-07 — Segment boundary
Source audit: `docs/project_control/reports/WAVE5_AT07_SEGMENT_BOUNDARY_AUDIT.md`

## 1. Purpose

AT-07 freezes the boundary that transcript segment files are physical persistence units only. They do not define conversation identity, turn identity, context identity, resume semantics, or model-visible history.

Source requirement:

```text
AT-07 — Segment boundary

Generate enough messages to rotate transcript segment.

Resume/context behavior unchanged.
```

Primary rule:

```text
Segment boundary is physical persistence only, never conversation semantics.
```

AT-07 is not pagination, compaction, search optimization, or transcript redesign.

## 2. Current Gate Position

```text
AT-07 Audit: COMPLETE
Core semantic intent: CLEAR
Read/resume interface shape: GREEN
Rotation implementation: BLOCKED
R0 Contract: READY FOR FREEZE
Implementation: HOLD until R0 frozen
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

Reason:

The audit confirmed StorageV2 can preserve ordering and read transcript-shaped files, but current writes always target `transcript-000001.jsonl`. Physical rotation to `transcript-000002.jsonl` is not implemented.

## 3. P0 Gap Frozen by This Contract

### P0-GAP-1 — StorageV2 has segment filename shape but no rotation behavior

Observed audit probe:

```text
append 250 messages
segments = ["transcript-000001.jsonl"]
segment_count = 1
message_count = 250
order = msg_000 → msg_249
```

Bad behavior for AT-07 acceptance:

```text
segment file naming exists
  ≠
segment rotation works
```

Current write path:

```text
_write_canonical_message(...)
  → _segment_path(conv_id)
  → default seg=1
  → transcript-000001.jsonl
```

Why this is P0 for AT-07:

AT-07 explicitly requires generating enough messages to rotate transcript segment. Without actual rotation, R1 cannot prove that resume/context behavior remains unchanged across a real physical segment boundary.

Required behavior after remediation:

```text
append enough canonical messages
  → transcript-000001.jsonl
  → transcript-000002.jsonl
  → one canonical conversation
  → same ordering / resume / context semantics
```

## 4. Frozen Invariants

### AT07-I01 — Segment split does not create a new conversation

A conversation may span one or more transcript segment files.

```text
transcript-000001.jsonl
transcript-000002.jsonl
  → same conversation_id
```

Segment number, filename, and file boundary MUST NOT create another conversation lineage.

### AT07-I02 — Canonical ordering survives segment boundaries

Canonical message order is defined by message sequence/order semantics, not by caller-visible segment file details.

Example:

```text
segment 1: msg_000 ... msg_099
segment 2: msg_100 ... msg_199

read transcript:
msg_000 → ... → msg_199
```

No duplicate, missing, or reordered message may occur because a segment boundary was crossed.

### AT07-I03 — Segment rotation is persistence concern only

Segment rotation is a storage maintenance operation.

It MUST NOT alter:

- `conversation_id`
- `turn_id`
- message identity
- role
- modality
- status
- chronological semantic order
- Context OS admission semantics
- provider-visible history semantics

### AT07-I04 — Resume/read behavior is independent from physical segment layout

The following layouts must be semantically equivalent to runtime callers:

```text
one transcript file
multiple transcript segment files
```

Runtime, management API, Context OS, Electron/S2S, and provider handoff must observe one canonical transcript, not segment files.

### AT07-I05 — Rotation failure must not corrupt canonical history

A failed rotation attempt MUST NOT create a false accepted message, hide a previously durable message, or corrupt existing canonical transcript files.

Allowed outcomes:

```text
append not acknowledged → caller may retry
already durable message → recovered by canonical files
```

Forbidden outcomes:

- acknowledged message missing after recovery
- partial message treated as valid canonical truth
- segment metadata hiding a durable segment
- split JSON record across segments

### AT07-I06 — A canonical message is never split across segments

A `ConversationMessage` is the minimum physical atom.

If a message causes rotation, the whole message is written to one target segment. If a single record exceeds a normal size threshold, it remains one oversized record in one segment rather than being split.

### AT07-I07 — Segment metadata is derived; canonical files win

Segment counters, active segment hints, catalog rows, and meta fields are derived projections.

On recovery:

```text
canonical transcript-*.jsonl files
  >
segment_count / active_segment / catalog hints
```

A stale counter must not hide a later durable segment.

### AT07-I08 — Runtime/Context OS/Electron/S2S are segment-unaware

Callers must not depend on or receive physical segment filenames as conversation semantics.

Forbidden:

- Context OS selecting context by segment filename
- Electron requesting `segment 17`
- S2S treating segment boundary as turn/session boundary
- management DTO exposing transcript filename as semantic identity

Segment traversal belongs inside the repository.

### AT07-I09 — Resume/context behavior is unchanged by rotation

After rotation and fresh runtime/repository recovery:

```text
resume conversation
get canonical history
prepare Context OS
provider-visible active tail
```

must behave as if the conversation had been stored in one continuous transcript.

### AT07-I10 — Modality changes near rotation boundary do not create semantic boundaries

Text/voice turns written around a rotation boundary remain one canonical conversation sequence.

```text
text before rotation
voice at/after rotation
text after rotation
  → same conversation_id
  → canonical order preserved
```

This preserves AT-03 while adding physical segment coverage.

## 5. Required Fix Scope Before R1

Implementation remains HOLD until this R0 contract is frozen.

Minimal remediation scope after R0:

1. Add StorageV2 active segment selection for canonical appends.
2. Add projected size/message-count threshold check before writing the next message.
3. If projected threshold is exceeded, create/select the next transcript segment.
4. Append the whole JSONL message record to exactly one target segment.
5. Preserve existing repository read shape through `_iter_transcript(...)`.
6. Make thresholds configurable or test-injectable so R1 can trigger rotation with small fixtures.

Out of scope for AT-07 remediation:

```text
AT-08 pagination
compaction
search optimization
transcript redesign
multi-writer/distributed locking
Electron redesign
Context OS redesign
```

## 6. R1 Hold Criteria

R1 remains HOLD until permanent Wave5-named tests prove:

- generating enough messages creates at least `transcript-000002.jsonl`;
- order is preserved across the segment boundary;
- fresh runtime/repository recovery reads all segments;
- Context OS active tail over recovered history is unchanged by segment boundary;
- management/runtime DTOs do not expose segment filenames as semantic fields;
- text/voice turns across rotation remain one conversation sequence;
- a message record is never split across segments;
- stale/derived segment metadata cannot hide durable segment files.

## 7. Suggested R1 Test IDs

```text
TC-AT07-R1-001 generate enough messages to create transcript-000002.jsonl
TC-AT07-R1-002 canonical order preserved across segment boundary
TC-AT07-R1-003 fresh runtime recovery reads all segment files unchanged
TC-AT07-R1-004 Context OS active tail unchanged by segment boundary
TC-AT07-R1-005 segment filenames/details are not exposed in management/runtime DTOs
TC-AT07-R1-006 text→voice switch across segment boundary remains one conversation
TC-AT07-R1-007 message record is never split across segments
TC-AT07-R1-008 stale/derived segment metadata cannot hide a later durable segment
```

## 8. Required IA Focus

AT-07 IA should prove the real governed path:

```text
ConversationManagementService create/read
  ↓
ConversationRuntime governed append/process path
  ↓
StorageV2 physical rotation
  ↓
fresh runtime/repository recovery
  ↓
Context OS prepare over recovered canonical history
  ↓
provider-visible output unchanged by segment boundary
```

IA must prove segment boundary transparency through runtime/product-facing APIs, not by reading segment files alone.

## 9. Explicit Non-Goals

AT-07-R0 does not freeze or test:

- AT-08 pagination
- catalog/search rebuild
- index deletion/rebuild
- segment compaction
- archival/tombstone semantics
- transcript format redesign
- distributed locking
- segment optimization/tuning
- provider behavior quality
- Electron UI paging

## 10. Failure Criteria

Any of the following fails AT-07:

- enough messages do not create a second segment after remediation;
- segment boundary changes `conversation_id` or turn identity;
- read/resume loses, duplicates, or reorders messages across boundary;
- Context OS active tail changes solely because of physical segment boundary;
- provider-visible context exposes segment filenames or segment semantics;
- acknowledged message disappears after rotation/recovery;
- partial/split message is treated as canonical truth;
- stale segment metadata hides a durable later segment.

## 11. Gate Decision

```text
AT-07-R0 Contract: READY FOR FREEZE
Implementation: HOLD until R0 committed
R1: HOLD
IA: HOLD
Freeze: NOT READY
```
