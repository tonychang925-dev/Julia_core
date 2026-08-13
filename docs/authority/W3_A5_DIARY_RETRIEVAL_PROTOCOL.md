# W3-A5 — Diary Retrieval + Context Exposure Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary Retrieval Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
Stored diary ≠ model-visible diary.
```

Even 500 stored diary entries are never dumped into the prompt.

```text
Diary storage
      ↓
retrieval / relevance / policy
      ↓
Context OS
      ↓
model-visible DiaryContext
```

```text
Stored information ≠ model-visible information.
```

## Retrieval path

```text
DiaryRepository (storage)
        ↓
DiaryContextSource (governed retrieval: relevance, recency, significance)
        ↓
Context OS
        ↓
governed selection
        ↓
LLM
```

Raw diary files are never a direct prompt-injection path (carries forward D0-02 / the historical Claude-Julia anti-pattern).

## Invariants

**W3-A5-I01 — Stored ≠ Visible**

```text
Stored diary entries are not automatically model-visible. Only Context OS
governed selection exposes diary content to cognition.
```

**W3-A5-I02 — Retrieval Through Context OS**

```text
Diary reaches the model only through Context OS. No raw-file glob, no
unconditional dump.
```

**W3-A5-I03 — Retrieval Ranks, Context Selects**

```text
DiaryContextSource retrieves/ranks candidate diary entries using governed
signals (relevance, recency, significance), never a full-transcript-style
concatenation.

Only Context OS decides which candidates become model-visible.

retrieval ranking ≠ model-visible selection authority.
```

## Sabotage suite (AT-RET-01…04) — SPEC (not PASS)

```text
AT-RET-01  raw diary file loaded directly into prompt → contract violation   [REQUIRED]
AT-RET-02  500 stored entries → not all dumped into context                  [REQUIRED]
AT-RET-03  diary reaches model only through Context OS source assembly      [REQUIRED]
AT-RET-04  relevance selection is governed, not ad-hoc                     [REQUIRED]
```

## Acceptance gate

```text
[ ] stored ≠ visible
[ ] retrieval only through Context OS
[ ] governed relevance, no full dump
[ ] no raw-file prompt injection
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
