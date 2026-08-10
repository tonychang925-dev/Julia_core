# CM-STORAGE-V2 Decision — R2-A Complete

**Date:** 2026-08-10
**Status:** DECIDED
**Decision:** Hybrid — JSONL canonical transcript + SQLite rebuildable catalog

---

## 1. Benchmark Results (Dataset S: 50 conv, 10K msgs)

| Operation | SQLite | Hybrid | Winner |
|-----------|--------|--------|--------|
| Bulk load (10K msgs) | 847ms | 5077ms | SQLite |
| Storage size | 2.8MB | 6.9MB | SQLite |
| find_turn | p50=0.01ms | p50=0.92ms | SQLite |
| get_messages(100) | p50=0.34ms | p50=0.95ms | SQLite |
| list_conversations | p50=0.09ms | p50=0.10ms | ≈ tie |
| Catalog rebuild | N/A | 56ms | Hybrid |

## 2. Decision Rationale

SQLite wins on raw speed across all operations. But Julia's conversation storage
has constraints beyond latency:

**Decisive factors for Hybrid:**

1. **Portability**: JSONL files are platform-independent, human-readable, and
   survive any SQLite version change. Tony can copy conversations to a new
   machine by dragging a folder.

2. **Single authority**: JSONL files are the canonical transcript truth. The
   SQLite catalog is derived/rebuildable. Deleting catalog.sqlite loses
   nothing that can't be rebuilt from transcripts.

3. **Per-conversation isolation**: One corrupt transcript file affects only
   that conversation, not the entire store.

4. **Model independence**: Julia can read her own conversation history from
   JSONL files without SQLite-specific tooling. Aligned with the goal of
   provider/platform portability.

**Hybrid's weaknesses and mitigations:**

| Weakness | Mitigation |
|----------|------------|
| find_turn full-file scan | SQLite turn_id index (derived, rebuildable) |
| Long-conv scaling | Segment rotation (future, Stage 2) |
| Load speed | Acceptable for migration; normal append is fast |
| Storage size | Acceptable overhead for readability |

## 3. Architecture

```
memory/conversations/
├── catalog.sqlite              ← rebuildable index
│   ├── conversations (id, title, created_at, updated_at, message_count)
│   └── turn_index (conversation_id, turn_id, message_ids)
│
├── conv_<id>/
│   ├── meta.json               ← conversation metadata
│   ├── transcript-000001.jsonl  ← canonical ConversationMessage log
│   └── transcript-000002.jsonl  ← segment rotation (future)
│
└── conv_<id>/
    └── ...
```

**Authority rule**: `transcript-*.jsonl` = canonical truth.
`catalog.sqlite` = derived, rebuildable from transcripts.

## 4. Rejected: SQLite-only

SQLite is highly portable as a library and file format. It is rejected NOT
because it is non-portable, but because:

- Canonical transcript is tied to a database engine representation
- Human inspection requires SQLite tooling (`sqlite3` CLI, etc.)
- Per-conversation isolation is weaker (all in one `.db` file)
- Weaker fit for Julia's model-independent, platform-independent migration goal

A single `.db` file cannot be casually inspected line-by-line, backed up
per-conversation, or verified without SQLite-specific knowledge. JSONL
transcripts survive any database technology change — copy the folder, Julia
can read her own history.

## 5. Rejected: Pure JSONL

Without a catalog, list_conversations requires scanning all directories, and
find_turn requires full-file scan. The SQLite catalog solves both without
becoming canonical authority.

## 6. What Changes (R2-B)

- New `StorageV2ConversationRepository` implementing `ConversationRepository`
- Backward-compatible: ConversationRuntime unchanged
- Migration: legacy `conversations.json` → per-conversation JSONL + catalog

---

*End R2-A Decision*
