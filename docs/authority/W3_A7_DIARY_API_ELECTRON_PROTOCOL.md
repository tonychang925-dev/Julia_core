# W3-A7 — Diary API / Electron Projection Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary API / Electron Projection Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
Electron is display/projection only. It never owns diary truth.
```

## Ownership boundary

```text
Electron OWNS:
  display
  navigation
  filter
  user-facing diary interaction

Electron DOES NOT OWN:
  DiaryEntry truth
  reflection result
  acceptance status
  provenance
  physical diary persistence
```

## Manual edit semantics

If Tony is later allowed to edit Julia's diary, it MUST be:

```text
explicit governed revision
```

NEVER frontend direct file modification. A UI edit does not silently mutate Julia-authored historical reflection; it produces a governed revision/supersession (carries forward D0-02).

## API transport boundary

```text
Diary HTTP/API = application transport surface
                ≠ diary authority
                ≠ cognition authority
                ≠ governance authority
                ≠ persistence authority
```

Read path:

```text
Electron → Diary API → DiaryService/Core semantics → accepted durable DiaryEntry
```

Write path:

```text
Electron edit request → API → governed revision command → Diary Governance → persistence
```

```text
NEVER: PUT /diary with arbitrary client-authored canonical DiaryEntry → directly persist
NEVER: Electron → API → filesystem
```

API DTO MUST NOT expose:

```text
physical path / daily filename / BEGIN-END framing / fsync implementation / private root
```

## Invariants

**W3-A7-I01 — Projection Only**

```text
Electron holds no diary authority; it displays governed diary truth.
```

**W3-A7-I02 — No Local Diary Truth**

```text
Electron has no local diary cache/editor/save that becomes diary authority.
```

**W3-A7-I03 — Governed Edit**

```text
Any manual edit to Julia's diary is an explicit governed revision, never a
direct frontend file write.
```

**W3-A7-I04 — API Is Transport**

```text
Diary API is a transport/application surface only. It cannot create, accept,
revise, or persist diary truth except by delegating to the governed diary
semantic path.
```

## Sabotage suite (AT-DE-01…04) — SPEC (not PASS)

```text
AT-DE-01  Electron local diary edit writes diary truth directly → violation  [REQUIRED]
AT-DE-02  Electron displays accepted DiaryEntry (read-only projection)        [REQUIRED]
AT-DE-03  manual edit → governed revision, not silent file mutation          [REQUIRED]
AT-DE-04  Electron cache destruction → zero diary truth loss                 [REQUIRED]
AT-DE-05  API receives arbitrary client-authored DiaryEntry → cannot directly create canonical truth [REQUIRED]
AT-DE-06  API DTO exposes physical diary path/framing → violation            [REQUIRED]
```

## Acceptance gate

```text
[ ] Electron = projection only, no diary authority
[ ] no local diary truth / editor / save as authority
[ ] manual edit = governed revision
[ ] diary truth sourced from Core-governed diary semantics; physical persistence remains Assistant-owned
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
