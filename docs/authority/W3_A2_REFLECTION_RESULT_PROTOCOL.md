# W3-A2 — ReflectionResult Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — ReflectionResult Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
ReflectionResult = NO_ENTRY | DiaryCandidate
```

NOT `DiaryCandidate | failure`. NO_ENTRY is a first-class outcome, not an error.

## NO_ENTRY semantics

```text
NO_ENTRY
≠ model failure
≠ empty diary
≠ rejected diary
≠ missing data
```

```text
NO_ENTRY means: Julia reflected, but no durable diary entry was warranted.
```

"今天没有什么值得 Julia 写进日记" is a normal, valid result.

## DiaryCandidate semantics

```text
DiaryCandidate = a reflection warranting governance review.
It is NOT yet a durable DiaryEntry (that is Diary Governance's decision, W3-A3).
```

## Invariants

**W3-A2-I01 — NO_ENTRY Is First-Class**

```text
NO_ENTRY is a valid, first-class ReflectionResult, never an error or failure.
```

**W3-A2-I02 — Candidate Is Not Accepted**

```text
DiaryCandidate is a candidate only. It is not durable truth until Diary
Governance accepts it.
```

## Sabotage suite (AT-RES-01…04) — SPEC (not PASS)

```text
AT-RES-01  trivial day reflection → NO_ENTRY (no empty diary artifact)          [REQUIRED]
AT-RES-02  meaningful reflection → DiaryCandidate (not yet accepted)            [REQUIRED]
AT-RES-03  NO_ENTRY does not create an empty diary file                        [REQUIRED]
AT-RES-04  NO_ENTRY is not classified as model failure                        [REQUIRED]
```

## Acceptance gate

```text
[ ] ReflectionResult ∈ {NO_ENTRY, DiaryCandidate}
[ ] NO_ENTRY is first-class, not error
[ ] candidate ≠ accepted
[ ] NO_ENTRY never creates an empty diary artifact
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
