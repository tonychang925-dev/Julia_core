# WAVE5 Storage Status and Contract Boundary (RC1)

**Status:** RECORDED — VALID FOR WAVE5 RC1
**Date:** 2026-08-25
**Repo:** `/Users/admin/julia_core`
**Branch:** `wave5/authority-consolidation`

**Purpose:** Declare the boundary between the current runtime storage implementation and the target Julia Continuity Storage architecture. This is a status + contract-boundary statement, NOT a storage design. The design already exists in `STO_F1_PRIVATE_FILESYSTEM_CONTRACT_v1.0.md` and `STO_F2_APPLICATION_PERSISTENCE_BINDING_v1.0.md`.

The load-bearing distinction recorded here:

```text
Physical storage shape  ≠  Storage semantic contract
```

---

## 1. Current Runtime Storage

```text
Brain canonical store:
    /Users/admin/julia_ai_assistant_rmd3g_prod/data/conversations.json
```

Role:

- Temporary canonical conversation backend for Wave5 RC1.
- One JSON file holds multiple conversations:

```json
{
  "conversations": [
    { "id": "conv_xxx", "messages": [ ... ] },
    { "id": "conv_yyy", "messages": [ ... ] }
  ]
}
```

```text
Brain
  |
  +-- data/conversations.json
          +-- conversation A
          +-- conversation B
          +-- conversation C
```

Status: **VALID FOR RC1** — it is the runtime backend, not the target layout.

---

## 2. Target Storage Architecture

Status: **PLANNED** — `STO-F2` persistence binding migration.

```text
<PRIVATE_JULIA_DATA>/
  memory/
    conversations/
      index.json               # catalog / resume metadata only (not transcript)
      conv_<id>/
        meta.json
        transcript-000001.jsonl
        transcript-000002.jsonl
        compact/
```

---

## 3. Shape vs Semantic Contract

Physical shape may be a single JSON file during RC1. The semantic contract MUST hold regardless of shape.

### Physical shape (current)

```text
single JSON file  →  ALLOWED for RC1
```

### Semantic contract (non-negotiable, inherited from frozen invariants)

Note: `SC-` numbering is local to this document to avoid colliding with the `INV-` numbering in the development plan.

### SC-1 — Authority

Only Brain owns canonical conversation identity:

```text
conversation_id
turn_id
```

No client layer (Electron / Voice-S2S) may mint canonical identity.

- Source: frozen authority model (plan §0), INV-01 one conversation world.
- Enforcement point: AT-22 Conversation Identity Ownership.

### SC-2 — Append-first

Completed historical transcript is immutable after commit:

```text
no silent rewrite by
  compact / context budgeting / memory formation /
  diary generation / client reconciliation / cache sync
```

- Source: INV-03 canonical transcript is append-first.
- Single-file shape must still honor append-first. Convenience of one JSON file does NOT justify rewriting committed history.

### SC-3 — Idempotency

Same logical turn retry:

```text
(conversation_id, turn_id) identical
  → zero duplicate canonical messages
```

- Source: CM-S1-T06, AT-05.

---

## 4. RC1 Validation Status

| Contract | Status |
|---|---|
| Brain canonical authority | PASS |
| Electron projection only | PASS |
| Restart recovery | PASS |
| Conversation identity ownership | PASS (AT-22) |
| Storage layout migration | PENDING |

---

## 5. Known Deviation

```text
RC1 intentionally keeps the conversations.json backend.
```

This is a storage implementation choice, NOT a violation of the continuity contract.

The deviation is bounded:

- **Deferred:** physical shape (single file → conversation filesystem).
- **Already enforced:** semantic contract (authority / append-first / idempotency).

---

## 6. Future Migration

`STO-F2` Persistence Binding Migration:

```text
conversations.json
    ↓
conversation filesystem (memory/conversations/conv_<id>/transcript-*.jsonl)
```

Requirements (per ADR-002 cutover contract, INV-10):

- migration evidence
- hash verification
- message count verification
- turn_id continuity verification
- `FREEZE → RECONCILE → VERIFY → ACTIVATE → RETIRE` (no silent dual writer)

---

## 7. Acceptance Scope Extension

Original Wave5 AT plan ended at AT-20 (`JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md` §25).

RC1 validation scope has been extended:

| AT | Scope |
|---|---|
| AT-21 | Identity Continuity |
| AT-21V | Voice Continuity |
| AT-22 | Conversation Identity Ownership |

These are recorded explicitly so future readers do not interpret AT-21 / AT-22 as silently added.

---

## Decision

```text
Runtime storage:   conversations.json — KEEP for RC1
Storage migration: HOLD (STO-F2, post-RC1)
Contract boundary: documented, not re-designed
```

Continuity is determined by authority, identity, and causal history — not by file layout.

A single file is not the problem. Who is authorized to create "Julia's past" is.
