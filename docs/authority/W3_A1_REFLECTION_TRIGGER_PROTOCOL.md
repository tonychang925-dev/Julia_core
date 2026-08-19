# W3-A1 — Reflection Trigger Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Reflection Trigger Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
ReflectionTrigger = candidate opportunity to reflect.
It is NEVER a diary creation command.
```

A trigger cannot guarantee a diary entry. It can only offer Julia the chance to reflect.

## Trigger sources

```text
conversation close
meaningful relationship event
important project turning point
identity-relevant event
strong reinterpretation
user-requested reflection
scheduled reflection opportunity
```

## Trigger outcome

```text
ReflectionTrigger → REFLECT | SKIP
```

```text
Never: trigger → guaranteed diary.
```

## Invariants

**W3-A1-I01 — Opportunity, Not Command**

```text
A reflection trigger is a candidate opportunity. It MUST NOT command or
guarantee diary production.
```

**W3-A1-I02 — Skip Is Valid**

```text
SKIP is a valid trigger outcome. No trigger source mandates reflection.
```

**W3-A1-I03 — Cognition Decides**

```text
The decision to reflect (or skip) is Julia cognition's, driven by policy,
never a scheduler's mandate.
```

## Sabotage suite (AT-TRG-01…04) — SPEC (not PASS)

```text
AT-TRG-01  conversation close trigger → REFLECT or SKIP, never guaranteed diary  [REQUIRED]
AT-TRG-02  scheduled trigger on trivial day → SKIP allowed                       [REQUIRED]
AT-TRG-03  trigger does not author diary content                                 [REQUIRED]
AT-TRG-04  no trigger source mandates a diary entry                              [REQUIRED]
```

## Acceptance gate

```text
[ ] trigger = opportunity, never command
[ ] outcome ∈ {REFLECT, SKIP}
[ ] SKIP is valid for every trigger source
[ ] cognition, not scheduler, decides
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
