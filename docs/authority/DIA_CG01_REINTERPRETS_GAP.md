# DIA-CG-01 — Missing `reinterprets` in AcceptedDiaryEntry

STATUS: ADJUDICATED
UPDATED: 2026-08-15
REPORTED BY: DIA-2B-R0.1 audit (Tony remote review)
AFFECTED: DIA-1 @ `7525c6f` (FINAL) — `AcceptedDiaryEntry`

## Gap

D0-02 freezes TWO distinct semantics:

```text
reinterprets = "I now understand the past differently" (old entry stays true history)
supersedes   = "a currently-adopted judgment in the old entry is explicitly corrected"
```

FINAL `AcceptedDiaryEntry` (DIA-1) carries only `supersedes: tuple[str, ...]`, no `reinterprets`.
The DIA-2B framing plan therefore cannot preserve reinterpretation provenance.

## Why not back-edit

STO-D0 discipline: implementation gaps go through `CONTRACT_GAP_REPORT → explicit
adjudication → amendment / successor decision`. Not a silent back-edit of frozen `7525c6f`.

## Proposed resolution (DIA-1A successor amendment)

```text
AcceptedDiaryEntry adds:
  reinterprets: tuple[str, ...] = ()

Same exact primitive rules as supersedes: tuple[str], non-mutable, no subclass,
empty default.
```

## Adjudication

```text
ADJUDICATION: Mira Architecture Authority — ACCEPTED (VALID CONTRACT GAP)
SUCCESSOR AMENDMENT: DIA-1A @ c221c1599833b15dbaee1ba81a667d3c73fcf4a0
VERIFICATION: Codex B — PENDING

CLOSE RULE: Codex B GREEN → DIA-CG-01 CLOSED
```
