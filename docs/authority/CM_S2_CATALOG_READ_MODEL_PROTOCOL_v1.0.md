# CM-S2 — Catalog & Read Model Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 1 — CM-S2 Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-D0 @ `261521f` (D0-06) · STO-F1 @ `23ecc1f` · STO-F2 @ `edc0692`

## Governing principle

```text
Catalog and search are DERIVED read models.
The canonical transcript (memory/conversations/*) is the only truth.
No read model may become transcript, lifecycle, or cognition authority.
```

CM-S2 is decoupled from the segmented physical layout; it consumes the same canonical truth through the repository port.

## 1. Catalog identity

```text
memory/conversations/index.json = derived read model
  - holds list/resume metadata only (conversation_id, title, state, updated_at, counts)
  - MUST NOT become a transcript substitute
  - MUST NOT be canonical transcript authority
```

Canonical conversation directories remain source evidence; the catalog is a projection.

## 2. Catalog rebuild

```text
delete / corrupt index.json
→ scan canonical conversation directories
→ rebuild catalog
```

Rebuild MUST be deterministic and produce zero semantic loss. The catalog is fully reconstructable from canonical files; a missing or stale catalog never changes canonical truth.

```text
stale derived counter (message_count, segment_count) NEVER overrides
canonical files. Reconcile derived counters from canonical truth.
```

## 3. Pagination (cursor-based, segment-transparent)

```text
get_messages(conversation_id, before=cursor, after=cursor, limit=N)
```

Requirements:

```text
- stable canonical ordering (append order, not arrival order)
- cursor is opaque; segment boundaries are invisible to the caller
- zero duplicate, zero missing across segment boundaries
- caller (Electron/Context OS/S2S) is segment-unaware
```

The repository alone handles cross-segment traversal (`000003 → 000002`).

## 4. Derived search (visibility-gated)

```text
indexes/conversation_fts.db = derived, rebuildable
```

Two-stage pipeline (inherits D0-06):

```text
FTS candidate recall (ids / rank / opaque match)
        ↓
CANONICAL VISIBILITY GATE (read canonical lifecycle state)
        ↓
hydrate + safe snippet + projection
```

```text
- tombstoned / purged conversation MUST NOT be exposed via search
- default search = ACTIVE; include_archived=true → ACTIVE+ARCHIVED
- stale FTS row ≠ permission to expose deleted content
- eventual consistency: false negative (new message lag) allowed;
  false positive (deleted content visible) forbidden
```

Search rank / snippet / score / cursor are projection semantics, never durable identity (durable identity = conversation_id + message_id).

## 5. Failure isolation

```text
Catalog / search unavailability, corruption, or rebuild failure MUST NOT
impair canonical conversation create / append / read / durability (D0-03).
```

Read-model failure degrades read/search only, never canonical acceptance.

## Invariants

**CM-S2-I01 — Derived Read Model**

```text
Catalog and search are derived, reconstructable read models.
They MUST NOT become canonical transcript, lifecycle, or cognition authority.
```

**CM-S2-I02 — Rebuildability**

```text
Deletion or corruption of catalog and search indexes MUST be recoverable
from canonical persistence without semantic loss.
```

**CM-S2-I03 — Segment-Transparent Pagination**

```text
Pagination is cursor-based, canonical-ordered, and segment-transparent.
Zero duplicate, zero missing across segment boundaries.
```

**CM-S2-I04 — Visibility Gate**

```text
Search results MUST pass canonical lifecycle/visibility adjudication before
any user-visible content. Tombstoned/purged content MUST NOT be exposed.
```

**CM-S2-I05 — Read-Model Failure Isolation**

```text
Catalog/search failure MUST NOT impair canonical write/durability acceptance.
```

**CM-S2-I06 — Projection Is Not Identity**

```text
Search rank, snippet, score, and search cursor are projection semantics only.
They MUST NOT become durable source identity or canonical ordering.
```

## Sabotage suite (AT-CAT-01…10) — SPEC (not PASS)

```text
AT-CAT-01  delete index.json → rebuild → canonical conversations/messages unchanged  [REQUIRED]
AT-CAT-02  corrupt index.json → rebuild → canonical unchanged                        [REQUIRED]
AT-CAT-03  pagination 200+ messages across segments → zero dup/missing, canonical order [REQUIRED]
AT-CAT-04  search tombstoned conversation → zero user-visible result                [REQUIRED]
AT-CAT-05  search purged conversation → zero result                                 [REQUIRED]
AT-CAT-06  catalog/search failure → canonical create/append still works             [REQUIRED]
AT-CAT-07  stale catalog counter → canonical files win, counter reconciled         [REQUIRED]
AT-CAT-08  search cursor reused as durable source_ref → rejected                   [REQUIRED]
AT-CAT-09  FTS candidate → missing/non-resolvable canonical message → drop + drift evidence [REQUIRED]
AT-CAT-10  Context OS bypass attempt (FTS as cognition source) → rejected          [REQUIRED]
```

`[REQUIRED]` = frozen acceptance specification, NOT production PASS.

## Acceptance gate

```text
[ ] catalog is a derived read model, never transcript authority
[ ] catalog/search fully rebuildable from canonical files
[ ] pagination segment-transparent, zero dup/missing, canonical order
[ ] search visibility-gated (tombstone/purged never exposed)
[ ] read-model failure isolated from canonical write/durability
[ ] rank/snippet/cursor are projection, never durable identity
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
