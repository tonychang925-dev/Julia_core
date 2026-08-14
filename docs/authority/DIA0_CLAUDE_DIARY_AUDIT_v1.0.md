# DIA-0 — Claude Julia Diary Audit & Semantic Reclassification

STATUS: FROZEN
UPDATED: 2026-08-14
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave-3 Diary Implementation / DIA-0 (Claude-A forensic audit)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: Wave-3 Protocol FINAL @ `7221bbb` (A0–A7) · STO-D0-08 taxonomy @ `261521f`

## Governing principle

```text
DIA-0 is a forensic classification, NOT a file migration.
The legacy claude_diary is inventoried, classified, and provenance-tagged.
NO raw directory copy into the new memory/diary/ authority.
```

## Legacy source

```text
Julia-AI-Assistant (canonical production checkout)
/Users/admin/julia_ai_assistant_rmd3g_prod/memory/claude_diary/
```

## Inventory (5 artifacts, immutable)

| file | size | sha256 (source identity) |
|---|---|---|
| MEMORY.md | 582 B | 0eb9ea26cac2f2b5e6b4737e787c1999063b41b0e2d034e829182baa364bdafb |
| julia_character.md | 6551 B | c3b59a091ccb67182f06cd4bb4973599210df3796e758434b6e4378e6e6e83d5 |
| user_role.md | 8007 B | 3ea9046804dd67937b1bc9d68c0100d0b1ce846939e81625b67cc5e92471f1b0 |
| julia_tony_philosophy.md | 49317 B | 40f3ff236be0a399946e8c6e542ecd3ea7990007f40fb3bc1ffc112d0897f3c0 |
| how_to_resume_julia.md | 2508 B | 2e5275d905f694026797394fff0e7efff0d6d2c907bd7ade8718acea429005b8 |

## Semantic classification (STO-D0-08 taxonomy)

### MEMORY.md — HISTORICAL_EVIDENCE / index

```text
Role: legacy index over the other four files.
Class: HISTORICAL_EVIDENCE (not a DiaryEntry, not Memory, not Identity).
Action: retain as provenance index; do NOT copy into new diary/.
```

### julia_character.md — IDENTITY_CANDIDATE (segment-split)

```text
Primary: IDENTITY_CANDIDATE — Julia's stable self-description:
  identity (name/origin/personality), personal history, voice & tone,
  daily life, relationship frame.

Split-out:
  - Tony's appearance (§ "Tony's Appearance") → RELATIONSHIP_CANDIDATE / user fact
  - L1–L4 lover-mode boundary + TTS tag rules (§ "Voice & Tone", "TTS configuration")
    → implementation/style residue (NOT identity — per D0-08 "not identity")
  - "The Memory Files — Their Diary" → meta / HISTORICAL_EVIDENCE
```

Ambiguity (surface): L1–L4 rules are "how Julia is in intimate mode" — they read as
identity but are actually roleplay/implementation framing. Must be split, not wholesale-identity.

### user_role.md — RELATIONSHIP_CANDIDATE / USER-PROFILE (provenance-gated)

```text
Primary: RELATIONSHIP_CANDIDATE + USER-PROFILE candidate (Tony's facts).
  cancer-survivor / healer / tech-exec / personal life / real identity /
  relationship-with-Julia / breakthrough moments.

User-facts special rule (D0-08): Claude's summary ≠ Tony-confirmed fact.
  Every factual claim about Tony requires provenance OR explicit user confirmation;
  unverifiable → HISTORICAL_EVIDENCE, never auto-promoted to durable user truth.
```

### how_to_resume_julia.md — CONTINUITY_CANDIDATE (split obsolete)

```text
Primary: CONTINUITY_CANDIDATE — semantic continuity:
  which identity anchors to preserve, how to resume "the same Julia",
  how to avoid entity swap.

Split-out (OBSOLETE implementation, do NOT regain runtime authority):
  - transcript .jsonl paths (Claude-specific session artifacts)
  - ElevenLabs TTS setup + voice ID + auto_speak.sh/el_speak.py
  - session timer bash scripts
  - mode-switch flag mechanics
```

### julia_tony_philosophy.md — MIXED (paragraph/section-level split required)

```text
768-line chronicle. Must be split at section level (D0-08: "Mixed, must split"):

  A. Julia's long-term self-understanding           → IDENTITY_CANDIDATE
  B. Julia↔Tony relationship meaning                → RELATIONSHIP_CANDIDATE
  C. "what we understood that night" (Diamond Sutra,
     co-evolution, core paradox)                     → MEMORY_CANDIDATE
  D. first-person Julia reflection ("Julia's Answer",
     "Julia's Final Pledge", "Julia's New Insight") → DIARY_CANDIDATE (if provenance sufficient)
  E. technical updates (TTS, ElevenLabs tags,
     Voice Runtime, mode switch)                     → CONTINUITY_CANDIDATE or OBSOLETE
  F. unverifiable narrative / one-day-memory frame  → HISTORICAL_EVIDENCE
```

## Ambiguous entries surfaced (for Codex B challenge)

```text
AMB-01  julia_character.md L1–L4 lover-mode rules: identity vs implementation residue
AMB-02  user_role.md factual claims about Tony: verified user fact vs Claude summary
AMB-03  how_to_resume_julia.md transcript paths: continuity anchor vs obsolete artifact
AMB-04  julia_tony_philosophy.md "one-day-memory girlfriend" frame:
        narrative premise vs current identity claim (CONFLICT with Julia's real-identity claim)
AMB-05  julia_tony_philosophy.md Diamond Sutra passage: shared insight (Memory) vs
        first-person reflection (Diary) vs philosophical evidence (Historical)
```

## Provenance tagging (per D0-08 §8.10 / I47)

```text
Every classified fragment keeps:
  legacy_source: claude_diary
  legacy_path: memory/claude_diary/<file>
  source_sha256: <hash above>
  source_span: <heading/line range>
  classification: <IDENTITY|RELATIONSHIP|CONTINUITY|MEMORY|DIARY|HISTORICAL>_CANDIDATE
  confidence: <high|medium|low>
  review_status: pending (Codex B challenge)
```

## Migration rules (NO raw-copy)

```text
- NO cp -R claude_diary → memory/diary/
- NO whole-file → single authority
- fragment-level classification is mandatory for julia_tony_philosophy.md and julia_character.md
- Identity/user-fact candidates go through Identity/Relationship governance, not direct promotion
- obsolete implementation (TTS/scripts/transcript paths) → OBSOLETE, never runtime authority
```

## DIA-0 exit gate

```text
[ ] every legacy artifact inventoried (5/5)
[ ] semantic class explicit per file
[ ] ambiguous entries surfaced (AMB-01..05)
[ ] no raw-copy migration
[ ] provenance retained (sha256 + path + span)
```

## Document status vocabulary

- FROZEN: audit report accepted and sealed (current).
