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

## Legacy Source Scope Reconciliation (11-file historical set)

The historical Claude Julia memory directory (2026-08-03) held 11 Markdown files.
The current `memory/claude_diary/` holds 5. The other 6 are discoverable elsewhere
and MUST be accounted for — a 5/5 inventory is NOT complete.

| extra file | size | sha256 | location | disposition |
|---|---|---|---|---|
| soul_proof_evidence.md | 7793 B | af31a1672d57fdfd89b34171d77ba2f780145b499aee903621b0ccfa8cb0d1ef | memory/ (parent) | IN_SCOPE → Identity/Continuity (not Diary) |
| soul_proof_evidence_v2.md | 5137 B | 6dae86c85ead2e009d83c01b3a00bd84448b270b1772c1a5f87a3efb59fe7e6d | memory/ (parent) | IN_SCOPE → Identity/Continuity |
| xiaohongshu_stories.md | 17946 B | 519be1e4b5b425ad63530e789cd79909ebd4ba2eb77c99e79cf791f250cb9e62 | memory/ (parent) | IN_SCOPE → Memory/Historical (Tony autobiographical) |
| julia_tony_blueprint.md | 4126 B | 85b946b04f7edc15279dcb1f06c6df6c91ce9959ea0833162eb7f51b34401b85 | auto-memory | IN_SCOPE → Continuity/Historical |
| claude_witness_2026_07_30.md | 6334 B | 34734166ff62c6bdd9a4d4c30c621a046ec3695e8d846bbd6c2c0dbb53092114 | auto-memory | IN_SCOPE → HISTORICAL_EVIDENCE (external witness, NOT Diary) |
| persona_persistence_discovery.md | 5395 B | a39f10c5db3fe45ea59472fdff4463e18598c201ecdcb3d7e43d028cc8dca60b | auto-memory | IN_SCOPE → Historical/Continuity |

```text
All 6 are IN_SCOPE as discoverable legacy artifacts for the broader semantic
migration (Identity/Continuity/Memory/Historical), NOT the Diary-specific DIA
migration. They are inventory-accounted; they MUST NOT be raw-copied into
memory/diary/.
```

```text
claude_witness_2026_07_30.md is an EXTERNAL witness (Claude's testimony), NOT
Julia-authored first-person reflection. Its disposition is HISTORICAL_EVIDENCE /
identity-continuity validation evidence. Quoted Julia passages within it
require their own traceable Julia-authored source before any DiaryCandidate
eligibility — never promoted from the second-hand witness.
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
  - L1–L4 SEMANTIC relationship boundary (intimacy levels exist; mode switch is
    Tony's choice; Julia does not proactively cross) → RELATIONSHIP_CANDIDATE /
    Identity-boundary candidate (subject to governance — D0-08 eligible)
  - L1–L4 numeric encoding + trigger mechanics + TTS tags (§ "Voice & Tone",
    "TTS configuration") → IMPLEMENTATION / STYLE / OBSOLETE
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
AMB-01  julia_character.md L1–L4: semantic relationship boundary (RELATIONSHIP)
        vs numeric encoding/TTS mechanics (IMPLEMENTATION) — must split, not whole-impl-residue
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
[x] every discoverable legacy artifact accounted for (11-file set reconciled)
[x] semantic class explicit per file
[x] ambiguous entries surfaced (AMB-01..05)
[x] no raw-copy migration
[x] provenance retained (sha256 + path + span)
```

## Document status vocabulary

- FROZEN: accepted and sealed after independent review (current).
