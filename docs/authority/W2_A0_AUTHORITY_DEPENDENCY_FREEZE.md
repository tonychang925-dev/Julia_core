# W2-A0 — Wave 2 Authority & Dependency Freeze

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — Canonical Conversation Management (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd` (Wave-0 closeout)

## Authoritative inputs

```text
Julia_core Wave-0 closeout      c5f0fbd
STO-D0                          261521f
STO-F1                          23ecc1f
STO-F2                          edc0692
Wave-1 protocol lane FINAL      f1d5734
```

## Dependency status (Wave 2 MUST NOT assume Wave 1 has closed)

```text
Wave-1 architecture/protocol    FROZEN
Wave-1 production implementation IN PROGRESS
AT-BIND-20                      NOT CLOSED
AT-BIND-17                      NOT CLOSED
Segmented repository authority  NOT ACTIVE
LegacyRepository                CURRENT ACTIVE AUTHORITY
```

Wave 2 protocols may reference Wave-1 frozen protocols, but MUST NOT treat segmented repository authority as an established fact.

## Wave-2 authority topology

```text
ConversationRuntime
        │  sole conversation semantic authority
        ▼
ConversationManagementService
        │  governed orchestration surface
        │
        ├── create / open / list / rename / resume / archive / governed delete
        ▼
ConversationRepository Port
        ▼
Assistant persistence adapter
```

## Ownership disambiguation (the core of W2-A0)

```text
ConversationManagementService ≠ transcript authority
ConversationManagementService ≠ Context authority
ConversationManagementService ≠ physical persistence authority

ConversationManagementService = governed orchestration surface
  over ConversationRuntime + repository contracts.
```

This prevents Wave 2 from creating a second "ConversationManager holds its own history" authority. Management is orchestration, never semantic invention.

## Frozen authority invariants (carried into Wave 2)

```text
- ConversationRuntime = sole semantic conversation authority
- Context OS          = sole model-visible context authority
- Julia-AI-Assistant  = physical persistence host
- Electron            = presentation / projection only
- S2S                 = media / transport only
```

## Document status vocabulary

- FROZEN: freeze accepted and sealed (current).
