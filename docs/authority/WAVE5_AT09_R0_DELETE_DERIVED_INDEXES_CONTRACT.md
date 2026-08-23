# Wave5 AT-09-R0 Contract — Delete Derived Indexes

Status: R0 READY FOR FREEZE / IMPLEMENTATION BLOCKED BY P0 REBUILD GAP
Date: 2026-08-23
Scope: AT-09 — Delete derived indexes
Source audit: `docs/project_control/reports/WAVE5_AT09_DELETE_DERIVED_INDEXES_AUDIT.md`

## 1. Purpose

AT-09 freezes the boundary that derived catalog/index artifacts are disposable
read models. Deleting them must not delete, rewrite, hide, duplicate, or
re-author canonical conversation history.

Source requirement:

```text
AT-09 — Delete derived indexes

Delete all `indexes/*`.

Rebuild succeeds with zero semantic loss.
```

Primary rule:

```text
Derived indexes are rebuildable projections, not canonical history authority.
```

In the current StorageV2 implementation, the active derived artifact is
`catalog.sqlite*`. The future/planned `indexes/*` namespace follows the same
rule. AT-09 freezes the authority boundary for all derived catalog/index
artifacts without requiring a new FTS/search architecture.

AT-09 is not compaction, search ranking optimization, tokenizer work, transcript
redesign, Context OS policy, or Electron cache destruction.

## 2. Current Gate Position

```text
AT-09 Audit: COMPLETE
Core semantic intent: CLEAR
Canonical read after derived deletion: GREEN
Search/list/find-turn rebuild baseline: GREEN
Derived counter rebuild: RED / P0 GAP
Post-rebuild append identity: RED / P0 GAP
indexes/* namespace mapping: AMBER
R0 Contract: READY FOR FREEZE
Implementation: HOLD until R0 frozen
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

Reason:

The audit confirmed canonical transcript messages remain readable after deleting
`catalog.sqlite`, but rebuild currently leaves derived `message_count` and
`last_sequence` at zero. A subsequent append can then reuse `sequence=1` and
produce a duplicate canonical `message_id`.

## 3. P0 Gaps Frozen by This Contract

### P0-GAP-1 — Derived counter rebuild is incomplete

Observed after deleting `catalog.sqlite` and opening a fresh StorageV2 repository:

```text
messages readable: yes
search/list/find_turn baseline: yes
message_count: 0
last_sequence: 0
```

Bad behavior:

```text
canonical transcript contains durable messages
  ↓
rebuilt derived catalog claims zero message count / zero last sequence
```

Why this is P0:

Derived state may be rebuilt, but it must be rebuilt from canonical truth. A
rebuild that loses counters or sequence watermark is not zero semantic loss because
those fields control future canonical append identity.

Required behavior after remediation:

```text
rebuild scans canonical transcript-*.jsonl
  → message_count = count(canonical messages)
  → last_sequence = max(canonical sequence)
```

### P0-GAP-2 — Post-rebuild append can reuse canonical message identity

Observed probe:

```text
before rebuild:
  msg_..._000001
  ...
  msg_..._000005

delete catalog.sqlite
rebuild
append one more message

after append:
  msg_..._000001
  ...
  msg_..._000005
  msg_..._000001  ← duplicate
```

Bad behavior:

```text
delete derived catalog
  ↓
rebuild incomplete
  ↓
sequence authority resets
  ↓
new canonical message_id collision
```

Why this is P0:

Derived index deletion must not redefine past identity or corrupt future identity.
A duplicate canonical `message_id` after rebuild violates AT-04 identity integrity,
AT-05 exactly-once history, and AT-08 canonical view continuity.

Required behavior after remediation:

```text
post-rebuild append sequence = canonical max(sequence) + 1
new message_id not in existing canonical transcript
```

### P0-GAP-3 — `indexes/*` source wording must map to current derived artifacts

The AT-09 source names:

```text
indexes/*
```

Current StorageV2 active derived artifact:

```text
catalog.sqlite
catalog.sqlite-wal
catalog.sqlite-shm
```

R0 freezes the abstract authority rule:

```text
all derived catalog/index artifacts are disposable
```

This includes current `catalog.sqlite*` and future `indexes/*`. AT-09 must not
expand into implementing FTS or a new index architecture solely to satisfy the
literal directory name.

## 4. Frozen Invariants

### AT09-I01 — Derived artifacts may be deleted without deleting canonical history

Deleting derived catalog/index artifacts MUST NOT delete or alter:

- conversation directories
- `meta.json`
- `transcript-*.jsonl`
- canonical message IDs
- canonical turn IDs
- roles, modalities, statuses, contents, or ordering

```text
delete derived artifacts
  ≠
delete canonical conversation history
```

### AT09-I02 — Canonical transcript remains the source of truth

On rebuild, canonical transcript files win over every derived artifact.

```text
meta.json + transcript-*.jsonl
  >
catalog.sqlite / indexes/* / caches / counters
```

A stale or missing derived row cannot prove a durable canonical message does not
exist.

### AT09-I03 — Rebuild must restore derived state without semantic loss

Rebuild must restore derived read-model fields needed for correct future behavior,
including at minimum:

```text
conversation row
message_count
last_sequence
turn_index / lookup state
updated_at where derivable from canonical/meta state
```

This does not make those fields canonical. It requires them to be reconstructed
from canonical truth.

### AT09-I04 — Rebuild must not reset identity authority

Rebuild MUST NOT reset sequence or identity watermarks to zero when canonical
messages exist.

Forbidden:

```text
transcript contains msg_000001..msg_000005
rebuild sets last_sequence=0
next append emits msg_000001
```

### AT09-I05 — Post-rebuild append preserves identity continuity

After derived deletion and rebuild, a new append must continue from canonical
state:

```text
new_sequence = max(canonical sequence) + 1
new_message_id not in existing canonical message IDs
turn/message ordering preserved
```

The append must not collide, overwrite, skip acknowledged history, or fork
conversation identity.

### AT09-I06 — Search/list/find-turn are derived views over canonical truth

Search, list, and turn lookup may use derived structures, but after rebuild they
must resolve against canonical conversation truth.

Allowed during rebuild:

```text
derived search temporarily unavailable
explicit rebuild required
```

Forbidden after successful rebuild:

- missing canonical conversation from list due to stale catalog
- missing canonical turn due to lost turn_index
- search result becoming canonical transcript authority
- search/index exposing another conversation's content without canonical gating

### AT09-I07 — Current `catalog.sqlite*` and future `indexes/*` share one rule

The following are derived artifacts under AT-09:

```text
catalog.sqlite
catalog.sqlite-wal
catalog.sqlite-shm
indexes/*
future FTS/search/catalog read models
```

They are rebuildable projections. None of them may become canonical history,
identity, or recovery authority.

### AT09-I08 — Rebuild failure fails closed for derived reads only

If rebuild fails, the system must not corrupt canonical transcript files.

Allowed outcomes:

```text
search/list derived surface unavailable
explicit rebuild failure returned
retry rebuild later
canonical read by conversation_id remains intact where possible
```

Forbidden outcomes:

- deleting transcript files to match a partial catalog
- accepting stale counters as canonical truth
- appending with reset sequence after known rebuild failure
- silently reporting successful rebuild with incomplete identity metadata

### AT09-I09 — Derived rebuild must not synthesize or mutate canonical messages

Rebuild is read-only with respect to canonical transcript files.

It MUST NOT:

- create synthetic message records
- edit message IDs or turn IDs
- change message content/status/modality
- delete transcript lines
- reorder transcript files or segments

### AT09-I10 — Rebuild is scoped by conversation_id and preserves isolation

Rebuild must not mix derived state across conversations.

```text
Conversation A transcript
  ≠
Conversation B catalog/index row authority
```

This preserves AT-06 isolation after derived index deletion.

## 5. Required Fix Scope Before R1

Implementation remains HOLD until this R0 contract is frozen.

Minimal remediation scope after R0:

1. Update StorageV2 reconcile/rebuild to compute `message_count` from canonical transcript messages.
2. Compute `last_sequence` from max canonical `sequence` across transcript segments.
3. Rebuild or refresh `turn_index` from canonical transcript messages.
4. Ensure `_next_sequence()` after rebuild returns `max_sequence + 1`.
5. Add tests proving delete `catalog.sqlite*` → rebuild → append → no duplicate `message_id`.
6. Treat current `catalog.sqlite*` as the concrete AT-09 derived deletion target.

Out of scope for AT-09 remediation:

```text
AT-10 Electron cache destruction
compaction
search optimization
FTS implementation or tokenizer work
new indexes/* architecture
transcript redesign
Context OS policy changes
backup/restore policy
```

## 6. R1 Hold Criteria

R1 remains HOLD until permanent Wave5-named tests prove:

- deleting derived catalog/index artifacts preserves all canonical messages;
- rebuild restores `message_count` and `last_sequence` from transcript files;
- post-rebuild append continues with monotonic sequence and unique message ID;
- list/search/find-turn operate after rebuild through canonical truth;
- rebuild is read-only over transcript files;
- stale/partial derived metadata cannot hide or overwrite canonical transcript;
- multiple conversations remain isolated after rebuild;
- segment-backed transcripts rebuild derived state across all segment files.

## 7. Suggested R1 Test IDs

```text
TC-AT09-R1-001 delete derived catalog → rebuild preserves canonical messages exactly
TC-AT09-R1-002 rebuild restores message_count and last_sequence from transcript
TC-AT09-R1-003 post-rebuild append uses max_sequence+1 and unique message_id
TC-AT09-R1-004 search/list/find-turn recover from canonical transcript after rebuild
TC-AT09-R1-005 rebuild reads all transcript segments and preserves order
TC-AT09-R1-006 stale/partial derived catalog cannot hide canonical messages
TC-AT09-R1-007 cross-conversation rebuild preserves isolation
TC-AT09-R1-008 rebuild performs zero canonical transcript mutation
```

## 8. Required IA Focus

AT-09 IA should prove the real governed route:

```text
ConversationManagementService create/read/search
  ↓
ConversationRuntime append/process path
  ↓
StorageV2 canonical transcript files
  ↓
delete derived catalog/index artifacts
  ↓
fresh repository/runtime/management stack rebuild
  ↓
read/search/list/find-turn/append continue with zero semantic loss
```

IA must include a post-rebuild append through the governed runtime path to prove
identity continuity is restored, not just message readability.

## 9. Explicit Non-Goals

AT-09 does not freeze:

- UI search ranking
- search pagination
- tokenizer choice
- FTS schema design
- compaction or vacuum policy
- transcript segment rotation, already frozen by AT-07
- pagination semantics, already frozen by AT-08
- Electron cache deletion, reserved for AT-10
- Context OS admission policy

## 10. Freeze Eligibility

AT-09 may not be marked FROZEN until all of the following are true:

1. Audit artifact exists and records the P0 rebuild/identity gap.
2. This R0 contract is committed.
3. Minimal remediation restores derived counters and post-rebuild append identity.
4. R1 permanent evidence passes with AT-09-named tests.
5. IA proves the governed management/runtime route after derived deletion/rebuild.
6. Final freeze record links Audit, R0, remediation, R1, and IA artifacts.

Until then:

```text
AT-09 Freeze: NOT READY
AT-10: HOLD
compaction/search/transcript redesign: HOLD
```
