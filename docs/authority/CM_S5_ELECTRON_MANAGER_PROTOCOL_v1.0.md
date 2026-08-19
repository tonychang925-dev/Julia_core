# CM-S5 — Electron Conversation Manager Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 2 — CM-S5 Protocol Freeze (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: STO-F2 @ `edc0692` · CM-S3 (this lane)

## Governing principle

```text
Electron is presentation / projection only.
It owns UI state, never canonical conversation identity or transcript.
```

## Ownership boundary

```text
Electron OWNS:
  presentation
  selection state
  current visible conversation
  navigation

Electron DOES NOT OWN:
  canonical conversation identity
  canonical transcript
  lifecycle truth
  conversation creation fallback
```

## Voice attachment (host.attach semantics)

```text
canonical conversation selected/opened
        ↓
Electron receives canonical conversation_id
        ↓
host.attach(conversation_id)
        ↓
S2S binds media session to that canonical conversation
```

Electron never sends a local/fallback conversation_id to Voice. Voice binds to the canonical id Electron received from the canonical management API backed by Core semantics.

## Invariants

**CM-S5-I01 — Presentation Only**

```text
Electron is presentation/projection. Its cache and selection state are
disposable and never canonical authority.
```

**CM-S5-I02 — Canonical Identity From Core**

```text
Electron receives canonical conversation_id from the canonical management API backed by Core semantics.
It never manufactures a local fallback canonical id.
```

**CM-S5-I03 — No Transcript Authority**

```text
Electron never uploads a copied transcript to Voice or Core as authority.
Resume attaches conversation_id; Core loads canonical truth.
```

**CM-S5-I04 — Voice Binds Canonical ID**

```text
Voice host.attach receives only the canonical conversation_id Electron
received from Core. No local id, no copied messages.
```

## Sabotage suite (AT-ELEC-01…06) — SPEC (not PASS)

```text
AT-ELEC-01  create returns canonical id; Electron uses it (no local id)      [REQUIRED]
AT-ELEC-02  Electron cache destruction → zero canonical loss                 [REQUIRED]
AT-ELEC-03  resume does not upload copied transcript                          [REQUIRED]
AT-ELEC-04  Voice host.attach binds canonical conversation_id                 [REQUIRED]
AT-ELEC-05  Electron local-only id never enters canonical path               [REQUIRED]
AT-ELEC-06  Text/Voice share one canonical timeline (projection only)        [REQUIRED]
```

## Acceptance gate

```text
[ ] Electron = presentation only
[ ] canonical conversation_id sourced from the canonical management API backed by Core semantics
[ ] no local fallback id, no copied-transcript authority
[ ] Voice binds canonical id (host.attach)
[ ] Text/Voice unified projection, one canonical timeline
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
