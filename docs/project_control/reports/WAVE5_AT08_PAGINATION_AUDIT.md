# Wave5 AT-08 Pagination Audit

Status: AUDIT COMPLETE / R0 BLOCKED BY P0 PAGINATION GAP
Date: 2026-08-23
Scope: AT-08 — Pagination
Branch: `codex/bugfix/at04-reconnect-identity-boundary`
Observed HEAD: `6490168`
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
AT-08 Pagination                      AUDIT START
```

## 2. AT-08 Source Requirement

From `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`:

```text
AT-08 — Pagination

200+ messages, load page by page.

Zero duplicate, zero missing, canonical order preserved.
```

AT-08 validates that pagination is a governed read projection over canonical history.
It must not become a new source of conversation truth and must not leak physical
segment layout to runtime, Electron, Context OS, or provider-visible surfaces.

## 3. Non-Goals

AT-08 does not test:

- compaction
- search ranking or search optimization
- transcript format redesign
- segment rotation itself, already frozen by AT-07
- context selection policy or ActiveTail sizing
- provider retry behavior
- UI scroll quality or virtualized rendering performance
- multi-user authorization or tenancy

## 4. Authority Baseline

Relevant existing protocol/authority documents:

- `docs/authority/CM_S2_CATALOG_READ_MODEL_PROTOCOL_v1.0.md`
  - pagination uses `get_messages(conversation_id, before=cursor, after=cursor, limit=N)`
  - cursors are opaque
  - segment boundaries are invisible to callers
  - repository handles cross-segment traversal
  - 200+ messages across segments must yield zero duplicate and zero missing
- `docs/authority/STO_D0_DECISION_REGISTER_v1.0.md`
  - read/pagination is fully segment-transparent
  - callers ask for logical pages, never segment files
  - cursor may encode physical position internally, but remains opaque
  - Electron, Context OS, and S2S remain segment-unaware
- AT-07 freeze:
  - segment boundary is physical persistence only, never conversation semantics

## 5. Audit Questions

AT-08 must answer:

1. Does repository pagination honor `before`, `after`, and `limit` over canonical order?
2. Can 200+ messages be loaded page by page with zero duplicate, zero missing, and canonical order preserved?
3. Is pagination segment-transparent across multiple physical transcript files?
4. Do Runtime/Management surfaces expose governed pagination, or only a tail cap?
5. Is the cursor an opaque read-position token rather than a conversation/turn identity authority?
6. Are invalid or stale cursors fail-closed or explicitly defined, rather than silently restarting from a wrong page?
7. Do existing permanent tests prove AT-08 by name?

## 6. Code Path Findings

### F1 — Repository Protocol declares pagination parameters

`julia_core/conversation_state/repository_protocol.py` declares:

```python
def get_messages(
    self,
    session_id: str,
    *,
    before: str | None = None,
    after: str | None = None,
    limit: int | None = None,
) -> list[ConversationMessage]:
    ...
```

This matches the documented read-model shape, but the implementation does not yet
honor cursor semantics.

### F2 — StorageV2 ignores `before` and `after`

`julia_core/conversation_state/storage_v2_repository.py` currently reconstructs all
messages and applies only tail `limit`:

```python
msgs = []
for m in self._iter_transcript(session_id):
    msgs.append(...)
if limit is not None:
    msgs = msgs[-limit:]
return msgs
```

Observed impact:

```text
get_messages(cid, limit=50) returns tail page 155..204
get_messages(cid, before=page1_first_message_id, limit=50) returns same 155..204
```

Assessment: RED / P0 for AT-08. Cursor traversal repeats the same page, producing
duplicates and missing older canonical messages.

### F3 — Legacy wrapper also ignores `before` and `after`

`julia_core/conversation_state/legacy_json_repository.py` similarly applies only
`limit` to the tail of `session.messages`. This preserves old tail-read behavior
but is not an AT-08 pagination implementation.

### F4 — Runtime and Management expose only `max_messages`

`ConversationRuntime.get_messages(conversation_id, max_messages=100)` and
`ConversationManagementService.get_messages(conversation_id, max_messages=100)`
read a tail slice only. They do not expose `before`, `after`, or an opaque cursor.

Assessment: RED/AMBER for Integration Acceptance. Even if repository pagination is
added, the governed product path still needs a pagination surface before AT-08 IA
can prove page-by-page loading.

### F5 — Segment transparency baseline is GREEN from AT-07

AT-07 remediation and freeze evidence prove StorageV2 can create multiple physical
segments and recover canonical history across them. AT-08 should build on that
baseline, not re-open segment rotation implementation.

## 7. Audit Probe

Probe setup:

```text
StorageV2ConversationRepository(segment_max_messages=50)
conversation_id = at08-pagination-probe
append 205 messages: PAGE_MARKER_000 ... PAGE_MARKER_204
```

Observed physical segments:

```text
transcript-000001.jsonl 50 messages
transcript-000002.jsonl 50 messages
transcript-000003.jsonl 50 messages
transcript-000004.jsonl 50 messages
transcript-000005.jsonl 5 messages
```

Full canonical read:

```text
full_count      205
full_first_last PAGE_MARKER_000 -> PAGE_MARKER_204
```

Pagination probe:

```text
page1 = get_messages(cid, limit=50)
page1_first_last = PAGE_MARKER_155 -> PAGE_MARKER_204

cursor = page1[0].message_id
page2 = get_messages(cid, before=cursor, limit=50)
page2_first_last = PAGE_MARKER_155 -> PAGE_MARKER_204

page1_page2_overlap = 50
combined_unique     = 50
combined_total      = 100
older_expected_present(PAGE_MARKER_104) = False
```

Expected AT-08 behavior:

```text
page1: PAGE_MARKER_155 -> PAGE_MARKER_204
page2: PAGE_MARKER_105 -> PAGE_MARKER_154
page3: PAGE_MARKER_055 -> PAGE_MARKER_104
page4: PAGE_MARKER_005 -> PAGE_MARKER_054
page5: PAGE_MARKER_000 -> PAGE_MARKER_004

combined traversal: 205 unique messages, zero duplicate, zero missing, canonical order preserved
```

Actual behavior repeats page 1. This is a P0 pagination gap.

## 8. Current Coverage Assessment

GREEN:

- Full read across multiple segment files preserves canonical order.
- Segment files are physical-only and segment-transparent after AT-07.
- Repository protocol already names `before`, `after`, and `limit`.

AMBER:

- Search/read-model documents describe cursor semantics, but executable AT-08
  acceptance evidence does not yet exist.
- Legacy tail-read behavior may remain compatible as a storage primitive, but it
  does not satisfy AT-08 page traversal.

RED/P0:

- StorageV2 ignores `before` and `after`; repeated page calls can duplicate the
  tail page and miss older messages.
- Runtime/Management governed surfaces expose `max_messages` only; product path
  cannot yet prove cursor pagination.
- No AT-08-named permanent acceptance artifact exists.

## 9. Audit Decision

```text
AT-08 Audit: COMPLETE
Core semantic intent: CLEAR
Segment-transparent full read baseline: GREEN
Repository cursor pagination: RED / P0 GAP
Runtime/Management pagination surface: RED/AMBER
Implementation readiness: BLOCKED
R0 Contract: REQUIRED
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

AT-08 is not ready for R1/IA. The next step is R0 Contract to freeze pagination
authority and cursor semantics before minimal remediation.

## 10. Required AT-08-R0 Invariants

Recommended R0 invariants:

- AT08-I01 — Pagination is a read projection over canonical history, not canonical history authority.
- AT08-I02 — Loading 200+ messages page by page must produce zero duplicates, zero missing messages, and canonical chronological order when pages are combined.
- AT08-I03 — `limit` is page size only; it must not redefine conversation history, context policy, or transcript completeness.
- AT08-I04 — `before` returns messages older than the cursor boundary; `after`, if exposed, returns messages newer than the cursor boundary.
- AT08-I05 — Cursor tokens are opaque read-position handles. They are not conversation identity, turn identity, segment identity, or authorization authority.
- AT08-I06 — Segment boundaries and segment filenames are invisible to callers and cannot affect page semantics.
- AT08-I07 — Pagination must survive fresh repository/runtime recovery over the same canonical transcript.
- AT08-I08 — Invalid, stale, or foreign-conversation cursors must fail closed or return a defined empty/error result; they must not silently restart from tail/head and create duplicate/missing traversal.
- AT08-I09 — Runtime/Management/Electron surfaces must use governed pagination semantics rather than raw storage shortcuts for acceptance-level page reads.
- AT08-I10 — Pagination must not synthesize missing history, hide acknowledged messages, or create new canonical messages.

## 11. Suggested Minimal Remediation Scope

After R0 freezes scope, minimal remediation should be limited to:

1. StorageV2 cursor-aware `get_messages(...)` over canonical transcript order.
2. An opaque cursor/result shape or governed wrapper sufficient for page traversal.
3. Runtime/Management read path exposing the governed pagination behavior needed by AT-08 IA.
4. Tests proving 200+ messages across segments can be paged with zero duplicate, zero missing, canonical order preserved.

Do not expand into:

- AT-09 or later acceptance items
- compaction
- search optimization
- transcript redesign
- Context OS policy changes
- Electron UI redesign

## 12. Next Step

```text
AT-08 Audit
  ↓
AT-08-R0 Pagination Contract
  ↓
Minimal Pagination Remediation if contract confirms the P0 scope
  ↓
R1 Permanent Evidence
  ↓
Integration Acceptance
  ↓
Final Freeze Record
```
