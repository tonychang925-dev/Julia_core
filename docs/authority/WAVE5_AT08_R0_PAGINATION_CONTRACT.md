# Wave5 AT-08-R0 Contract — Pagination

Status: R0 READY FOR FREEZE / IMPLEMENTATION BLOCKED BY P0 PAGINATION GAP
Date: 2026-08-23
Scope: AT-08 — Pagination
Source audit: `docs/project_control/reports/WAVE5_AT08_PAGINATION_AUDIT.md`

## 1. Purpose

AT-08 freezes the boundary that pagination is a read-view mechanism over canonical conversation history. Pagination must not define, mutate, hide, duplicate, or re-author canonical history.

Source requirement:

```text
AT-08 — Pagination

200+ messages, load page by page.

Zero duplicate, zero missing, canonical order preserved.
```

Primary rule:

```text
Pagination is a view mechanism, not a history authority.
```

AT-08 builds on AT-07. Segment rotation may change physical transcript layout, but pagination must still expose one canonical ordered history through stable logical pages.

AT-08 is not compaction, search optimization, transcript redesign, context selection policy, or UI virtualization.

## 2. Current Gate Position

```text
AT-08 Audit: COMPLETE
Core semantic intent: CLEAR
Segment-transparent full read baseline: GREEN
Repository cursor pagination: RED / P0 GAP
Runtime/Management pagination surface: RED/AMBER
R0 Contract: READY FOR FREEZE
Implementation: HOLD until R0 frozen
R1: HOLD
IA: HOLD
Freeze: NOT READY
```

Reason:

The audit confirmed StorageV2 can recover 200+ messages across multiple transcript segments, but cursor pagination is not implemented. `before` and `after` are declared by the repository protocol yet ignored by current StorageV2 and legacy repository implementations. Runtime and management surfaces expose only tail `max_messages`, not governed page traversal.

## 3. P0 Gaps Frozen by This Contract

### P0-GAP-1 — Repository cursor parameters are declared but ignored

Observed StorageV2 behavior:

```text
get_messages(conversation_id, limit=50)
  → PAGE_MARKER_155 ... PAGE_MARKER_204

get_messages(conversation_id, before=first_page_first_message_id, limit=50)
  → PAGE_MARKER_155 ... PAGE_MARKER_204
```

Result:

```text
page1_page2_overlap = 50 / 50
older expected marker PAGE_MARKER_104 is missing
```

Bad behavior for AT-08 acceptance:

```text
cursor argument exists
  ≠
cursor pagination works
```

Why this is P0:

AT-08 explicitly requires loading 200+ messages page by page with zero duplicate, zero missing, and canonical order preserved. Ignoring cursor parameters causes repeated tail pages, duplicate page results, and missing older history.

Required behavior after remediation:

```text
page1: latest N messages
before(page1 boundary) → previous N older messages
repeat until exhausted
combined pages → full canonical sequence exactly once
```

### P0-GAP-2 — Governed runtime/management surfaces do not expose page traversal

Observed runtime/management behavior:

```text
ConversationRuntime.get_messages(conversation_id, max_messages=100)
ConversationManagementService.get_messages(conversation_id, max_messages=100)
```

These surfaces expose a tail cap only. They do not accept or return a pagination cursor.

Why this matters:

AT-08 IA must prove the real governed path can load canonical history page by page. Repository-only behavior is necessary but not sufficient for Integration Acceptance.

Required behavior after remediation:

```text
ConversationManagementService
  → ConversationRuntime governed read path
  → repository cursor pagination
  → page-by-page canonical traversal
```

The exact DTO shape can remain minimal, but IA must not rely on raw storage shortcuts as the acceptance-level pagination surface.

## 4. Frozen Invariants

### AT08-I01 — Pagination preserves canonical ordering

Pagination returns windows over the canonical chronological transcript.

When all pages are traversed and recombined in chronological order, the result MUST equal the full canonical message sequence.

```text
page older ... page newer
  → msg_000 → msg_001 → ... → msg_N
```

No page boundary may reorder canonical messages.

### AT08-I02 — Page traversal produces zero duplicate and zero missing messages

For a conversation with 200+ durable messages:

```text
load page by page
combine all pages
```

must produce:

```text
unique_count == total_count
combined_count == full_read_count
combined_message_ids == full_read_message_ids
```

Forbidden:

- repeated tail page
- skipped middle page
- overlapping pages unless the overlap is explicitly requested by an out-of-scope API mode
- silently dropping acknowledged messages

### AT08-I03 — Pagination cannot create, remove, or mutate canonical messages

Pagination is read-only.

It MUST NOT:

- append a message
- delete a message
- change message status
- synthesize a missing message
- hide a durable message to make page traversal appear clean
- alter conversation title, catalog, or segment metadata as semantic truth

### AT08-I04 — Cursor boundaries define read position, not history identity

A cursor identifies a read boundary for pagination only.

It is not:

- `conversation_id`
- `turn_id`
- `message_id` authority beyond locating a boundary
- segment identity
- request identity
- authorization authority
- context admission authority

A cursor may encode internal position, but callers must treat it as opaque.

### AT08-I05 — `limit` is page size only

`limit` controls the maximum number of returned messages for one page.

It MUST NOT redefine:

- canonical history completeness
- Context OS policy
- ActiveTail admission
- transcript durability
- recovery truth

A small page size does not mean older history stopped existing.

### AT08-I06 — `before` and `after` have explicit direction semantics

For canonical chronological order:

```text
before=C → messages older than cursor C
```

If `after` is supported by the exposed API:

```text
after=C → messages newer than cursor C
```

A cursor boundary MUST NOT include the boundary message again unless the API explicitly documents inclusive mode. AT-08 freezes exclusive cursor boundaries for acceptance evidence.

### AT08-I07 — Segment layout is invisible to pagination semantics

Pagination crosses physical transcript segments transparently.

Forbidden:

- page boundary equals segment boundary by semantic rule
- cursor exposes `transcript-000002.jsonl` as caller contract
- callers request a physical segment as a logical page
- segment rotation changes page order or page completeness

This preserves AT-07:

```text
physical segment split
  ≠
conversation semantic split
  ≠
pagination semantic split
```

### AT08-I08 — Pagination survives fresh runtime/repository recovery

Pagination truth is derived from durable canonical repository state, not in-memory runtime cache.

After fresh repository/runtime construction over the same transcript:

```text
page traversal
  → same canonical message IDs
  → same order
  → zero duplicate
  → zero missing
```

### AT08-I09 — Invalid, stale, or foreign cursors fail closed or return defined empty/error results

A cursor that cannot be resolved for the requested conversation MUST NOT silently restart traversal from tail or head in a way that creates duplicate or missing traversal.

Allowed outcomes:

```text
explicit invalid-cursor error
explicit empty page for exhausted/defined boundary
```

Forbidden outcomes:

- treating a foreign conversation cursor as current-conversation authority
- silently returning the latest page for an unknown cursor
- exposing another conversation's messages
- changing canonical history because a cursor is invalid

### AT08-I10 — Pagination identity is scoped by conversation_id

A page request is always scoped to one canonical conversation.

```text
conversation A cursor
  ≠
conversation B page authority
```

If a cursor contains or implies a boundary from another conversation, it must not retrieve or authorize foreign conversation history.

### AT08-I11 — Runtime/Management/Electron use governed pagination semantics

Acceptance-level pagination must be available through governed read surfaces, not only by directly calling a storage primitive.

Required IA route:

```text
ConversationManagementService / governed product read path
  → ConversationRuntime or equivalent governed read boundary
  → repository cursor pagination
  → canonical page result
```

Electron/client cache may request pages but cannot define page truth.

### AT08-I12 — Pagination is not Context OS admission

Pagination may retrieve older or newer transcript windows for display/recovery. It does not decide model-visible context.

```text
paginated message returned for UI/read
  ≠
admitted to Context OS
  ≠
provider-visible context
```

This preserves W5-A-04 and AT-06.

## 5. Required Fix Scope Before R1

Implementation remains HOLD until this R0 contract is frozen.

Minimal remediation scope after R0:

1. Implement cursor-aware StorageV2 pagination over canonical chronological transcript order.
2. Define or wrap an opaque cursor/page result sufficient for AT-08 page traversal.
3. Preserve backwards-compatible tail-read behavior where existing callers only provide `limit`/`max_messages`.
4. Expose governed runtime/management pagination needed for IA.
5. Ensure pagination crosses `transcript-*.jsonl` segment files without exposing segment filenames.
6. Define invalid/stale/foreign cursor behavior as explicit error or defined empty result.
7. Add test-injectable page sizes and segment thresholds so fixtures can cover 200+ messages efficiently.

Out of scope for AT-08 remediation:

```text
AT-09 or later acceptance items
compaction
search optimization
transcript redesign
Context OS policy changes
provider retry behavior
Electron UI redesign / virtualization
multi-user authorization
```

## 6. R1 Hold Criteria

R1 remains HOLD until permanent Wave5-named tests prove:

- 200+ messages can be loaded page by page with zero duplicate and zero missing;
- combined page traversal exactly equals full canonical read order;
- pagination crosses multiple physical transcript segments transparently;
- fresh repository/runtime recovery preserves pagination results;
- `before` cursor returns older messages without repeating the boundary page;
- `after` cursor, if exposed, returns newer messages consistently;
- invalid/stale/foreign cursor behavior is fail-closed or explicitly defined;
- pagination reads do not mutate canonical transcript files;
- pagination cursors do not expose segment filenames as caller-visible authority.

## 7. Suggested R1 Test IDs

```text
TC-AT08-R1-001 200+ messages page-by-page yields zero duplicate and zero missing
TC-AT08-R1-002 combined pages equal full canonical sequence in chronological order
TC-AT08-R1-003 before cursor traverses older pages without repeating tail page
TC-AT08-R1-004 pagination crosses physical segment files transparently
TC-AT08-R1-005 fresh repository/runtime recovery preserves page traversal
TC-AT08-R1-006 invalid or stale cursor fails closed / defined empty without tail restart
TC-AT08-R1-007 foreign conversation cursor cannot authorize cross-conversation page read
TC-AT08-R1-008 pagination read path performs zero canonical mutation
```

## 8. Required IA Focus

AT-08 IA should prove the real governed route:

```text
ConversationManagementService read entry
  ↓
ConversationRuntime governed read boundary
  ↓
StorageV2 cursor pagination
  ↓
cross-segment canonical transcript traversal
  ↓
page DTO returned to caller
  ↓
combined pages equal canonical transcript
```

IA must demonstrate:

- real management/runtime path supports page traversal;
- 200+ messages across segments are retrieved exactly once;
- fresh runtime/repository recovery preserves the same page traversal;
- cursor metadata is opaque to the caller and does not expose segment filenames;
- client/request metadata does not create pagination authority.

## 9. Explicit Non-Goals

AT-08 does not freeze:

- page cache eviction policy
- UI infinite-scroll behavior
- provider prompt window trimming
- Context OS ActiveTail size or salience policy
- search index pagination
- transcript compaction
- segment optimization
- encryption or multi-user access control
- distributed pagination consistency across concurrent writers

## 10. Freeze Eligibility

AT-08 may not be marked FROZEN until all of the following are true:

1. Audit artifact exists and records the P0 pagination gap.
2. This R0 contract is committed.
3. Minimal remediation implements governed cursor pagination.
4. R1 permanent evidence passes with AT-08-named tests.
5. IA proves the governed management/runtime path.
6. Final freeze record links Audit, R0, remediation, R1, and IA artifacts.

Until then:

```text
AT-08 Freeze: NOT READY
AT-09: HOLD
compaction/search/transcript redesign: HOLD
```
