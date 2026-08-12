# STO-A0-T01 — Storage Program Baseline 2026-08-13

**Status:** PROPOSED FOR FREEZE
**Purpose:** Capture the authoritative repository baseline BEFORE Storage/Diary implementation. Two worlds are recorded: what the previous manifest asserted vs. what is currently verified.

## Evidence Rules

- A cell is written `UNVERIFIED` unless supported by direct inspection.
- `MANIFEST_RECORDED` = what `JULIA_FOUR_REPO_AUTHORITY_MANIFEST.md` (2026-08-11) asserted.
- `CURRENT_VERIFIED` = what was directly inspected today (2026-08-13).
- REPO HEAD is NOT automatically SOURCE AUTHORITY / DEPLOYMENT AUTHORITY / LIVE RUNTIME AUTHORITY.

## Repository Baseline Matrix

| Repo | Role | Manifest Recorded | Current Branch | Current HEAD | Worktree | Remote upstream | Evidence |
|---|---|---|---|---|---|---|---|
| Julia_core | Core runtime, canonical architecture, ConversationRuntime, Context OS, Memory OS, Continuity OS | `main` / `7d29fb9` | `cm-r0-fix` | `4937f8f` | DIRTY (38 files) | `ffc7c38` (stale tracking) | VERIFIED local HEAD; upstream tracking ref NOT refreshed |
| Julia-AI-Assistant | Brain / OpenAI-compatible API / CRT bridge / application composition root | `2ca6110` | DETACHED | `bbd90af` | DIRTY (1 dir: `data/`) | NONE | VERIFIED local HEAD |
| Julia_client / `julia_electron_v2` | Electron desktop shell / projection | `12fd0fb` | `codex/bugfix/electron-c10-c11-projection` | `4a08967` | CLEAN | `4a08967` (in sync) | VERIFIED local HEAD + upstream |
| Julia-Voice-S2S | Voice/S2S media transport | C4 `47c03e0` | `phase5/rmd-3g-observability` | `315f359` | DIRTY (4 files, docs) | `315f359` (in sync) | VERIFIED local HEAD + upstream |

## Per-Repo Authority Detail

### Julia_core

- **Approved production ConversationRuntime floor (from manifest):** `b463a3f702f9cfcb8db3cda870d8f570fc92483d` — KEEP until a later manifest explicitly supersedes.
- **Current HEAD `4937f8f` includes (since last freeze):**
  - ADR-001 (S2S Ephemeral Turn Context — superseded in intent by ADR-002 direction)
  - ADR-002 (Authority Cutover Contract, RP-3)
  - CM-I12 fixed (`get_canonical_history` no fixed last-N cap)
  - `ConversationMessage.source` + `ConversationSession.summary_status` fields
  - RP-1 Brain startup provenance gate (`deploy/brain/start-brain-18089`)
- **Worktree dirt:** 38 files — `data/`, `artifacts/`, `docs/` drafts, experimental modules. These are NOT source authority (per frozen rule: "local runtime/data mutations not committed to Git" are LEGACY/DO-NOT-USE).

### Julia-AI-Assistant

- **Current HEAD `bbd90af`:** nested conversation_id lookup + CRT turn_id generation.
- **Runtime:** Mac launchd `com.julia.brain.18089`, port `127.0.0.1:18089`.
- **Brain provenance gate (RP-1):** `deploy/brain/start-brain-18089` enforces clean-worktree + HEAD==approved-SHA + julia_core import provenance.
- **Worktree dirt:** `data/` only. Source tree clean.

### Julia_client / julia_electron_v2

- **Current HEAD `4a08967`:** VoiceSessionCache id+role dedup, turn_id filter fixes, workspace.bootstrap restoration.
- **Worktree:** CLEAN.

### Julia-Voice-S2S

- **Current HEAD `315f359`** — commits since last deployed release:
  - `5c85c4f` RP-2B turn_id UUID (DEPLOYED to AutoDL)
  - `7190d90` docs (definitive wrong-answer root cause)
  - `315f359` baseline freeze
- **Deployed artifact on AutoDL:** `manual-5c85c4f-20260812_225157` (manifest source_commit `5c85c4f`).
- **Live runtime:** AutoDL SHUT DOWN as of 2026-08-12 EOD. Re-verify on next boot.
- **Worktree dirt:** 4 files — deleted legacy runbooks (`RMD3G_PRODUCTION_RUNBOOK.md`, `VOICE-C1B.md`, `VOICE-GOLDEN-C0_RUNBOOK.md`) + new SOP v1.1 untracked.

## VOICE-C1 Remediation Closure (already frozen)

- RC-1 runtime drift → RP-1 provenance gate ✅
- RC-2 authority cutover → RP-3 ADR-002 ✅
- RC-3 turn_id boundary + collision → RP-2 UUID uniqueness ✅

## Cross-Repo Authority Model (to be frozen by ADR-003)

```
Julia_core            = semantic authority (Conversation/Memory/Diary/Continuity semantics)
Julia-AI-Assistant    = physical application persistence host / composition root
Julia_client/electron = presentation / projection only
Julia-Voice-S2S       = media transport only

Physical persistence ownership does NOT transfer semantic authority.
```

## Open Items (NOT part of this baseline — deferred to STO-D0)

1. `<PRIVATE_JULIA_DATA>` default path (proposed `~/Library/Application Support/JuliaAI/`)
2. Diary physical format (single append-only day file vs. date directory)
3. accepted-user fsync policy
4. segment rotation defaults
5. archive/tombstone/hard-delete semantics
6. search index technology (SQLite FTS as derived, proposed)
7. backup retention
8. Claude Julia legacy migration taxonomy

## Gate STO-A0-T01

- [x] Four repos inspected directly (not inferred from chat)
- [x] Manifest-recorded vs current-verified both captured
- [x] Dirty/clean worktree states recorded
- [x] Deployed artifact identity recorded where applicable
- [x] Live runtime marked UNVERIFIED (AutoDL shut down)
