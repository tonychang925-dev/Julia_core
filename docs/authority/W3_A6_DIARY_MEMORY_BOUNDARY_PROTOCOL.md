# W3-A6 — Diary ↔ Memory Boundary Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary ↔ Memory Boundary Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
Diary ≠ Memory.
```

Two different questions:

```text
Diary:   What did Julia herself find worth reflecting on?
Memory:  What durable meaning should influence Julia in the future?
```

Close, but never the same.

## Boundary (one-way, governed, never automatic)

```text
Accepted DiaryEntry
        ↓
governed Memory-candidate extraction / proposal
        ↓
MemoryCandidate
        ↓
Memory Governance
        ↓
NO_MEMORY | Accepted Memory
```

```text
DiaryEntry → Memory   is FORBIDDEN.
```

```text
Memory → automatically Diary   is also FORBIDDEN.
```

Diary acceptance never writes Memory; Memory formation never rewrites Diary. Each is governed independently.

## Invariants

**W3-A6-I01 — Separate Authorities**

```text
Diary and Memory are governed by separate authorities. Neither auto-mutates
the other.
```

**W3-A6-I02 — Candidate Producer ≠ Memory Authority**

```text
Memory-candidate extraction/proposal precedes Memory Governance.
Memory Governance alone decides MemoryCandidate → NO_MEMORY | Accepted Memory.
The candidate producer holds no Memory authority.
```

**W3-A6-I03 — No Reverse Auto-Write**

```text
Memory formation does not automatically create or rewrite a DiaryEntry.
```

## Sabotage suite (AT-DM-01…04) — SPEC (not PASS)

```text
AT-DM-01  accepted DiaryEntry auto-writes Memory → violation               [REQUIRED]
AT-DM-02  DiaryEntry → MemoryCandidate → Memory Governance (governed)      [REQUIRED]
AT-DM-03  Memory governance rejects candidate → no Memory written          [REQUIRED]
AT-DM-04  Memory formation auto-creates DiaryEntry → violation             [REQUIRED]
```

## Acceptance gate

```text
[ ] Diary ≠ Memory
[ ] one-way governed path: Diary → candidate → Memory Governance
[ ] no auto Memory write, no reverse auto Diary write
[ ] separate authorities, independently governed
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
