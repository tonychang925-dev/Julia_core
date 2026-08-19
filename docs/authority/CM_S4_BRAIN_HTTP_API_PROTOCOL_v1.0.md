# CM-S4 — Brain HTTP Conversation API Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — CM-S4 Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-F2 @ `edc0692` · CM-S3 (this lane)

## Governing principle

```text
Brain HTTP is a transport / application-API surface.
It delegates to ConversationManagementService → ConversationRuntime →
Repository Port. It is NEVER a semantic or persistence authority.
```

## Authority wiring

```text
HTTP route
  → ConversationManagementService
  → ConversationRuntime / Repository Port
```

```text
HTTP route MUST NOT:
  - directly edit JSONL / segmented files
  - directly construct canonical history
  - bypass ConversationRuntime for canonical-message mutation
```

## Suggested surface (names are illustrative; authority is what matters)

```text
POST   /internal/v1/conversations                    create (idempotency_key)
GET    /internal/v1/conversations                    list (updated_at DESC, state=active)
GET    /internal/v1/conversations/{id}               metadata
PATCH  /internal/v1/conversations/{id}               rename (metadata only)
POST   /internal/v1/conversations/{id}/open          open/resume (attach, no transcript transfer)
GET    /internal/v1/conversations/{id}/messages      cursor-based pagination
POST   /internal/v1/conversations/{id}/archive       archive (governed, CM-S6)
POST   /internal/v1/conversations/{id}/restore       restore (governed, CM-S6)
DELETE /internal/v1/conversations/{id}               governed delete (CM-S6)
```

The endpoint names are not frozen; the authority path and semantics are.

## Error contract

```text
400  invalid request
404  conversation not found (never silently create)
409  idempotency/state conflict
423  busy/locked (if applicable)
500  persistence failure
```

```text
404 → silently create   is FORBIDDEN (GAP-8).
```

## DTO boundary

```text
HTTP DTO MUST NOT expose storage implementation details
(segment filenames, backing-file layout).
```

## Observability

```text
Trace: conversation_id, request_id, operation, result, storage backend, duration.
Do NOT log unrestricted message content by default.
```

## Invariants

**CM-S4-I01 — Transport, Not Authority**

```text
Brain HTTP is a transport boundary. It holds no semantic or persistence
authority over conversation truth.
```

**CM-S4-I02 — Delegate, Never Bypass**

```text
HTTP routes delegate to ManagementService. They MUST NOT directly edit
canonical files, construct canonical history, or bypass ConversationRuntime.
```

**CM-S4-I03 — Stable DTO**

```text
HTTP DTOs are stable and storage-agnostic; they MUST NOT leak physical
layout details.
```

**CM-S4-I04 — Fail-Closed Error**

```text
Error responses are explicit. 404 never silently creates a conversation.
```

**CM-S4-I05 — Idempotency Key**

```text
create uses an idempotency_key (≠ conversation_id); same key returns the
same canonical conversation, different key is an independent create.
```

## Sabotage suite (AT-API-01…08) — SPEC (not PASS)

```text
AT-API-01  create returns canonical conversation_id, not client local ID     [REQUIRED]
AT-API-02  open/resume does not transfer client transcript                    [REQUIRED]
AT-API-03  unknown conversation_id → 404, never auto-create                   [REQUIRED]
AT-API-04  same idempotency_key → same canonical conversation                 [REQUIRED]
AT-API-05  rename PATCH → transcript untouched                                [REQUIRED]
AT-API-06  HTTP route cannot directly edit canonical files                    [REQUIRED]
AT-API-07  DTO does not leak segment/filename details                         [REQUIRED]
AT-API-08  canonical-message mutation via HTTP does not bypass Runtime        [REQUIRED]
```

## Acceptance gate

```text
[ ] HTTP = transport, no authority
[ ] routes delegate to ManagementService → Runtime → Port
[ ] no direct file/history mutation
[ ] error contract explicit (404 never creates)
[ ] DTO storage-agnostic
[ ] idempotency_key ≠ conversation_id
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
