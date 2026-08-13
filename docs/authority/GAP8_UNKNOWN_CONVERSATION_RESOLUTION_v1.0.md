# GAP-8 — Unknown Canonical Conversation Resolution v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — GAP-8 Resolution (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-D0 @ `261521f` · CM-S3 (this lane)

## Question

```text
A canonical append/open request arrives with an unknown conversation_id.
Should the storage/management layer auto-create the conversation?
```

## Resolution

```text
UNKNOWN canonical conversation_id → REJECT (CONVERSATION_NOT_FOUND).
NEVER auto-create.
```

## Rationale

```text
create conversation   ≠  append/open existing conversation
```

These are distinct semantic operations. Auto-create on `conversation_id = typo123` would let a typo, stale client state, or a Voice reconnect bug silently manufacture canonical truth.

```text
UNKNOWN_CANONICAL_CONVERSATION
  → CONVERSATION_NOT_FOUND
  → caller explicitly decides:
      create new / recover / select existing
```

The storage/management layer never guesses. It surfaces the miss and lets the caller choose.

```text
存储层不替语义层做决定。
```

## Invariant

**GAP8-I01 — No Implicit Create**

```text
An unknown conversation_id MUST NOT be implicitly created by append,
open, or resume. It resolves to CONVERSATION_NOT_FOUND; canonical
creation requires an explicit create operation.
```

## Sabotage suite (AT-GAP8-01…04) — SPEC (not PASS)

```text
AT-GAP8-01  append to unknown conversation_id → CONVERSATION_NOT_FOUND, no create   [REQUIRED]
AT-GAP8-02  typo conversation_id → no canonical truth manufactured                  [REQUIRED]
AT-GAP8-03  voice reconnect with stale conversation_id → rejected, no ghost          [REQUIRED]
AT-GAP8-04  explicit create then append → succeeds (distinct operations)            [REQUIRED]
```

## Acceptance gate

```text
[ ] unknown conversation_id never implicitly created
[ ] append/open/resume on unknown → CONVERSATION_NOT_FOUND
[ ] explicit create is the only creation path
[ ] no typo/stale/reconnect path manufactures canonical truth
```

## Document status vocabulary

- FROZEN: resolution accepted and sealed (current).
