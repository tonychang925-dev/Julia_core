# W3-A0 — Diary / Reflection Authority Freeze

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary / Reflection / Experience Governance (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: Wave-1 Protocol FINAL @ `f1d5734` · Wave-2 Protocol FINAL @ `6d4cfe7` · STO-D0 @ `261521f` · STO-F1 @ `23ecc1f` · STO-F2 @ `edc0692`

## Dependency reality (Wave 3 MUST NOT assume prior cutovers)

```text
CM-S1B                FINAL
CM-S1C / AT-BIND-20   NOT CLOSED
CM-S1D / AT-BIND-17   NOT CLOSED
LegacyRepository      ACTIVE authority
Segmented repository  READY candidate / NOT ACTIVE
Wave-2 implementation NOT PROVEN
```

Wave 3 protocols may proceed; Wave 3 implementation must not assume prior cutovers.

## Authority topology

```text
Canonical Conversation
        │  source evidence
        ▼
Context OS
        │  model-visible reflection context
        ▼
ReflectionService / ReflectionRuntime
        │  asks Julia to reflect
        ▼
Julia cognition
        │
        ├── NO_ENTRY
        │
        └── DiaryCandidate
                 │
                 ▼
        Diary Governance
                 │
                 ▼
          Accepted DiaryEntry
                 │
                 ▼
 Assistant-owned persistence  (memory/diary/)
```

Independent path (NOT automatic):

```text
DiaryEntry / Conversation / Experience
        │
        ▼
Memory Governance
        │
        ▼
Accepted Memory
```

```text
DiaryEntry → automatically Memory   is FORBIDDEN.
```

## Who decides what

```text
"what happened"                     → ConversationRuntime / canonical conversation
"what Julia can see now"            → Context OS
"whether reflection is warranted"   → Reflection policy / trigger
"diary content authorship"          → Julia cognition
"candidate → durable DiaryEntry"    → Diary Governance
"physical persistence"              → Julia-AI-Assistant
"who MUST NOT write diary"          → Electron / Voice / HTTP / storage adapter
```

## Core disambiguation

```text
DiaryService ≠ conversation authority
DiaryService ≠ memory authority
DiaryService ≠ context authority
DiaryService ≠ LLM cognition authority

DiaryService = governance / orchestration, never "another Julia".
```

## Boundary invariants (carried from prior freeze)

```text
Diary ≠ conversation summary
Diary ≠ automatic daily log
Diary ≠ Context compact
Diary ≠ Memory
```

## Invariants

**W3-A0-I01 — Runtime Sole Conversation Authority**

```text
ConversationRuntime remains canonical conversation authority.
```

**W3-A0-I02 — Context Sole Visibility Authority**

```text
Context OS remains the sole model-visible context authority.
```

**W3-A0-I03 — Cognition Authors, Governance Accepts**

```text
Julia cognition authors reflection content. Diary Governance decides
acceptance. No layer conflates the two.
```

**W3-A0-I04 — DiaryService Is Orchestration**

```text
DiaryService is governance/orchestration, never a second Julia and never
a second conversation/memory/context authority.
```

**W3-A0-I05 — No Client Diary Authority**

```text
Electron / Voice / HTTP / persistence adapters hold no diary authority.
```

## Sabotage suite (AT-DA0-01…05) — SPEC (not PASS)

```text
AT-DA0-01  diary flow consumes canonical conversation (not client transcript)  [REQUIRED]
AT-DA0-02  Context OS is the only model-visible reflection context path        [REQUIRED]
AT-DA0-03  DiaryService never authors content itself                            [REQUIRED]
AT-DA0-04  DiaryEntry does NOT auto-become Memory                              [REQUIRED]
AT-DA0-05  Electron/Voice/HTTP cannot write diary truth                        [REQUIRED]
```

## Acceptance gate

```text
[ ] authority topology frozen (conversation → Context → reflection → governance → persistence)
[ ] DiaryService = orchestration, never authority
[ ] Diary ≠ summary / daily log / compact / Memory
[ ] diary physical persistence = Assistant-owned
[ ] no client diary authority
```

## Document status vocabulary

- FROZEN: freeze accepted and sealed (current).
