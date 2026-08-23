# Wave5 AT-09 Delete Derived Indexes Audit

Status: AUDIT COMPLETE / R0 BLOCKED BY P0 REBUILD GAP
Date: 2026-08-23
Scope: AT-09 — Delete derived indexes
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Observed HEAD: `84420f5`
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
AT-07 Segment Boundary                FROZEN
AT-08 Pagination                      FROZEN
AT-09 Delete Derived Indexes          AUDIT START
```

## 2. AT-09 Source Requirement

From `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-09 — Delete derived indexes

Delete all `indexes/*`.

Rebuild succeeds with zero semantic loss.
```

AT-09 validates that derived read models and indexes are disposable. Deleting them
must not destroy canonical conversation history, and rebuild must not create a new
or conflicting canonical identity state.

## 3. Non-Goals

AT-09 does not test:

- compaction
- search ranking optimization
- tokenizer / FTS quality
- transcript redesign
- Electron cache destruction, reserved for AT-10
- Context OS policy changes
- backup / restore policy
- multi-user authorization

## 4. Authority Baseline

Relevant frozen principles:

- Canonical authority lives in `meta.json` and `transcript-*.jsonl`.
- Derived catalogs, counters, search indexes, and read models are rebuildable.
- Derived state must not be a prerequisite for `CORE_ACCEPTED`.
- Stale derived counters must never override canonical files.
- AT-07 froze segment files as physical persistence only.
- AT-08 froze pagination as view-only, derived from durable canonical transcript.

Current implementation shape:

```text
StorageV2 canonical:
  <conversation_id>/meta.json
  <conversation_id>/transcript-*.jsonl

StorageV2 derived:
  catalog.sqlite
  catalog.sqlite-wal / catalog.sqlite-shm when active
```

The documented `indexes/*` namespace is not currently the active StorageV2 derived
artifact. The practical AT-09 target in this codebase is therefore `catalog.sqlite*`,
with future R0 needing to state how `indexes/*` maps to current/future derived
index artifacts.

## 5. Audit Questions

AT-09 must answer:

1. If derived catalog/index files are deleted, are canonical messages still readable?
2. Does rebuild restore list/search/find-turn behavior from canonical files?
3. Does rebuild restore derived counters such as `message_count` and `last_sequence`?
4. After rebuild, can new appends continue without reusing message IDs or sequences?
5. Is `indexes/*` a real active namespace, or only a planned/future layout?
6. Do existing tests prove zero semantic loss, or only partial message readability?

## 6. Existing Evidence

Existing catalog deletion tests:

```bash
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  /opt/miniconda3/bin/python -m pytest -q \
  tests/rt2_r2/test_storage_v2_repository.py::test_b_at07_catalog_rebuild \
  tests/rt2_r3/test_core_acceptance.py::test_r3_at06_catalog_destruction \
  tests/rt2_r2/test_cutover.py::test_d_at07_catalog_loss_rebuild \
  tests/rt2_r2/test_legacy_migration.py::test_c_at10_rebuild_after_migration
```

Observed:

```text
4 passed
```

Assessment:

These tests prove message content can be read after deleting `catalog.sqlite`, but
they do not prove full zero semantic loss. They do not assert rebuilt
`message_count`, `last_sequence`, post-rebuild append identity, or duplicate
message_id prevention.

## 7. Audit Probes

### Probe P-A — Delete derived catalog and rebuild read/search/list

Fixture:

```text
Conversation A: 60 messages ALPHA_IDX_000..059
Conversation B: 35 messages BETA_IDX_000..034
segment_max_messages = 25
```

Action:

```text
close repository
delete catalog.sqlite
open fresh StorageV2ConversationRepository
```

Observed:

```text
A count before/after = 60 / 60 / equal=True
B count before/after = 35 / 35 / equal=True
search("ALPHA_IDX_059") before/after = [at09_a] / [at09_a]
find_turn("a_t_059") after = ALPHA_IDX_059
list_all after = [at09_a, at09_b]
```

Assessment: GREEN for canonical message read/search/list rebuild baseline.

### Probe P-B — Management/Runtime recovery after deleting catalog

Fixture:

```text
create via ConversationManagementService
append 42 user turns via ConversationRuntime
close repository
delete catalog.sqlite
open fresh repository/runtime/management stack
```

Observed:

```text
before_after_count = 42 / 42
same_ids = True
same_contents = True
search_after = [conversation_id]
message_count_handle = 0
```

Assessment:

- Message content and message IDs survive: GREEN.
- Rebuilt `message_count` is wrong: RED/P0.

### Probe P-C — Post-rebuild append sequence collision

Fixture:

```text
create conversation
append 5 messages
close repository
delete catalog.sqlite
reopen repository
append one more message
```

Observed:

```text
before_count = 5
rebuilt_count = 0
before_ids = msg_..._000001 ... msg_..._000005
after_ids  = msg_..._000001 ... msg_..._000005, msg_..._000001
duplicate_ids = 1
```

Assessment: RED/P0.

Derived catalog rebuild does not restore `last_sequence`, so the next append after
rebuild reuses sequence 1 and generates a duplicate canonical `message_id`.

## 8. Code Path Findings

### F1 — `_reconcile()` restores conversation rows and turn index only partially

Current behavior:

```text
for each canonical conversation dir:
  insert conversation row from meta.json if absent
  scan transcript messages
  insert missing turn_index rows
```

Missing behavior:

```text
message_count = count(canonical transcript messages)
last_sequence = max(canonical message sequence)
updated_at = latest canonical message timestamp / meta timestamp reconciliation
```

Impact:

After deleting catalog, rebuilt catalog claims `message_count=0` and
`last_sequence=0` even when transcript files contain durable messages.

### F2 — `_next_sequence()` trusts derived `last_sequence`

Current behavior:

```text
_next_sequence(conv_id)
  SELECT last_sequence FROM conversations
  return row[0] + 1
```

After catalog rebuild:

```text
last_sequence = 0
next append sequence = 1
message_id = msg_<conversation_id>_000001
```

This collides with existing canonical message IDs.

### F3 — Existing tests under-assert semantic rebuild

Existing tests confirm `len(messages)` and selected content, but not:

- rebuilt `message_count`
- rebuilt `last_sequence`
- post-rebuild append sequence monotonicity
- duplicate `message_id` absence after new append
- governed management handle count after rebuild

### F4 — `indexes/*` namespace is not active in StorageV2

The current active derived artifact is `catalog.sqlite` at repository root. There
is no active `indexes/` directory for StorageV2 conversation search in the audited
path.

Assessment: AMBER.

R0 must freeze the abstraction as "all derived catalog/index artifacts", covering
current `catalog.sqlite*` and future `indexes/*`, without forcing an unrelated
search/index architecture implementation into AT-09.

## 9. Current Coverage Assessment

GREEN:

- Canonical transcript messages survive deletion of `catalog.sqlite`.
- Fresh repository can reconstruct conversation rows enough for read/search/list.
- Search currently scans canonical messages through list/read paths and can recover after catalog deletion.

AMBER:

- Literal `indexes/*` namespace is not active in current StorageV2 layout.
- Existing tests prove partial rebuild but not zero semantic loss.

RED/P0:

- Rebuilt `message_count` is zero despite durable transcript messages.
- Rebuilt `last_sequence` is zero despite durable transcript messages.
- Post-rebuild append reuses sequence/message_id and creates duplicate canonical identity.

## 10. Audit Decision

```text
AT-09 Audit: COMPLETE
Core semantic intent: CLEAR
Canonical read after derived deletion: GREEN
Search/list/find-turn rebuild baseline: GREEN
Derived counter rebuild: RED / P0 GAP
Post-rebuild append identity: RED / P0 GAP
indexes/* namespace mapping: AMBER
Implementation readiness: BLOCKED
R0 Contract: REQUIRED
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

AT-09 is not ready for R1/IA. The next step is R0 Contract to freeze derived index
rebuild semantics, including counter/sequence recovery and post-rebuild append
identity safety, before minimal remediation.

## 11. Required AT-09-R0 Invariants

Recommended R0 invariants:

- AT09-I01 — Derived catalog/index artifacts are disposable and never canonical history authority.
- AT09-I02 — Deleting all derived catalog/index artifacts must preserve canonical messages, turn IDs, message IDs, roles, modalities, status, and order.
- AT09-I03 — Rebuild must restore derived counters from canonical transcript, including `message_count` and `last_sequence`.
- AT09-I04 — Post-rebuild append must continue from canonical max sequence and must not reuse message IDs.
- AT09-I05 — Search/list/find-turn may be unavailable during rebuild, but after rebuild they must resolve through canonical conversation truth.
- AT09-I06 — Rebuild must not synthesize messages, delete messages, or trust stale derived counters over transcript files.
- AT09-I07 — Current `catalog.sqlite*` and future `indexes/*` are both treated as derived artifacts under the same authority rule.
- AT09-I08 — Rebuild failure must fail closed for derived read models without corrupting canonical transcript.

## 12. Suggested Minimal Remediation Scope

After R0 freezes scope, minimal remediation should only address the P0 rebuild gap:

1. Update StorageV2 catalog reconcile/rebuild to compute `message_count` from transcript lines.
2. Compute `last_sequence` from max canonical `sequence` across transcript segments.
3. Ensure next append after rebuild uses `max_sequence + 1`.
4. Add tests for delete catalog → rebuild → append → no duplicate message_id.
5. Treat `catalog.sqlite*` as the current derived-index deletion target for AT-09; do not implement new FTS/search architecture.

Do not expand into:

```text
AT-10 Electron cache destruction
compaction
search optimization
FTS/tokenizer work
transcript redesign
Context OS policy changes
```

## 13. Next Step

```text
AT-09 Audit
  ↓
AT-09-R0 Delete Derived Indexes Contract
  ↓
Minimal derived rebuild remediation
  ↓
R1 Permanent Evidence
  ↓
Integration Acceptance
  ↓
Final Freeze Record
```
