# CM-S3 — Conversation Management Service Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — CM-S3 Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-D0 @ `261521f` · STO-F2 @ `edc0692` · W2-A0 (this lane)

## Governing principle

```text
ConversationManagementService is a governed orchestration surface
over ConversationRuntime + repository contracts. It NEVER invents
canonical ConversationMessage truth, never holds its own transcript,
and never becomes Context or persistence authority.
```

## Service boundary

```text
create / open / list / rename / resume / archive / governed delete
```

Each operation orchestrates Core/repository; none directly writes canonical truth.

## Create semantics (fallback freeze)

```text
CANONICAL_CONVERSATION_CREATED iff:
  canonical ConversationManagementService/Core create operation succeeds
  AND returns a canonical conversation_id.

Otherwise: CREATE_FAILED.

NEVER: local fallback canonical ID
       (Electron local-only conversation ID MUST NOT enter canonical path).
```

## Create identity semantics (idempotency_key ≠ conversation_id)

```text
canonical conversation_id
  = assigned/accepted only by canonical Core create semantics
  = never an Electron/S2S local fallback identity

idempotency_key
  = retry identity only
  = NOT canonical conversation identity
  = MAY be supplied by a caller as an opaque request key

same idempotency_key      → same canonical conversation_id
different idempotency_key → independent create operation
```

## Mutation routing boundary

```text
ConversationManagementService MUST NOT directly invoke canonical-message
mutation operations on ConversationRepository.
```

```text
Canonical ConversationMessage mutation path:
  ManagementService / API
        ↓
  ConversationRuntime
        ↓
  ConversationRepository
```

```text
list / lookup / catalog   → repository/read-model ports allowed
rename / archive / delete → only through governed domain/lifecycle contracts
add_message / update_message_status / append_external_turns_atomic / import_messages_atomic
                          → NEVER directly from ManagementService
                          → ConversationRuntime authority path only
```

## Invariants

**CM-S3-I01 — Runtime Is Sole Semantic Authority**

```text
ConversationRuntime remains sole semantic conversation authority.
ManagementService does not assume, replace, or shadow it.
```

**CM-S3-I02 — Orchestrate, Never Invent**

```text
ManagementService orchestrates; it never directly invents canonical
ConversationMessage truth.
```

**CM-S3-I03 — Canonical Identity**

```text
conversation_id is canonical identity.
No client-generated or local-fallback ID becomes canonical.
```

**CM-S3-I04 — Resume Does Not Transfer Transcript**

```text
open/resume does not transfer client transcript.
Resume attaches conversation_id; Core loads canonical truth.
```

**CM-S3-I05 — Unknown Conversation Fail-Closed**

```text
unknown conversation_id behavior is explicit and fail-closed
(CONVERSATION_NOT_FOUND); see GAP-8 resolution (W2-A2).
```

**CM-S3-I06 — Idempotent Create**

```text
create is idempotent under defined idempotency-key semantics.
idempotency_key ≠ canonical conversation_id.
Same idempotency_key returns the same canonical conversation;
different idempotency_key is an independent create operation.
```

**CM-S3-I07 — Metadata Never Rewrites Transcript**

```text
Management metadata changes (rename, title) never rewrite completed
canonical transcript.
```

**CM-S3-I08 — Governed Lifecycle Mutation**

```text
All lifecycle mutation (archive/delete) is governed and observable.
```

**CM-S3-I09 — One Management Semantics**

```text
Electron / Voice / HTTP are clients of the same management semantics.
No client-specific management authority.
```

**CM-S3-I10 — Context Consumes, Never Manages**

```text
Context OS consumes conversation truth; it does not become management
authority.
```

**CM-S3-I11 — Runtime Mutation Path**

```text
ManagementService MUST NOT directly invoke canonical-message mutation
methods on ConversationRepository. Canonical ConversationMessage mutation
flows only through ConversationRuntime.
```

## Sabotage suite (AT-CMS-01…10) — SPEC (not PASS)

```text
AT-CMS-01  create returns canonical conversation_id (no local fallback)     [REQUIRED]
AT-CMS-02  Brain create fails → CREATE_FAILED, no local-only ID             [REQUIRED]
AT-CMS-03  resume does NOT transfer client transcript                       [REQUIRED]
AT-CMS-04  unknown conversation_id → CONVERSATION_NOT_FOUND (no auto-create) [REQUIRED]
AT-CMS-05  duplicate create same identity → idempotent, one conversation    [REQUIRED]
AT-CMS-06  rename/title change → transcript untouched                       [REQUIRED]
AT-CMS-07  management service never invents ConversationMessage truth       [REQUIRED]
AT-CMS-08  archive/delete governed + observable                            [REQUIRED]
AT-CMS-09  Electron/Voice/HTTP share one management semantics              [REQUIRED]
AT-CMS-10  Context OS consumes, never manages                              [REQUIRED]
```

## Acceptance gate

```text
[ ] Runtime sole semantic authority preserved
[ ] ManagementService = orchestration, never semantic invention
[ ] canonical conversation_id, no local fallback
[ ] resume = attach, never transcript transfer
[ ] unknown conversation fail-closed (GAP-8)
[ ] create idempotent
[ ] metadata never rewrites transcript
[ ] lifecycle mutation governed + observable
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
