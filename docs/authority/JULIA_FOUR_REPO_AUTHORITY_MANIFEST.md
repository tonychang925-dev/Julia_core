# Julia Four-Repository Authority Manifest

STATUS: CANONICAL
UPDATED: 2026-08-13
PURPOSE: one cross-repository entry point for current code/document authority.

## Repositories

| Repo | Role | Branch | Current authority commit | Manifest |
|---|---|---|---|---|
| Julia_core | Core runtime, canonical architecture, ConversationRuntime, Context OS, Memory OS, Continuity OS | `cm-r0-fix` | `4937f8f` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-AI-Assistant | Brain/OpenAI-compatible API, CRT bridge, application composition root, physical persistence host | `phase5/rmd-3g-observability` | `44cea89` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-Voice-S2S | Voice/S2S media transport | `phase5/rmd-3g-observability` | `315f359` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia_client / `julia_electron_v2` | Electron desktop client / projection | `codex/bugfix/electron-c10-c11-projection` | `4a08967` | `docs/authority/CURRENT_AUTHORITY.md` |

> Supersedes the 2026-08-11 envelope (Julia_core `main`/`7d29fb9`, Assistant `2ca6110`, Voice C4 `47c03e0`, client `12fd0fb`). Full reconciliation recorded in `docs/authority/STORAGE_PROGRAM_BASELINE_20260813.md`.

Legacy confusion source:

- local `julia_electron` / remote `tonychang925-dev/julia_electron` is LEGACY / DO-NOT-USE for production unless Tony explicitly re-authorizes it.

## Current production runtime authorities

Global rule: REPO HEAD is not automatically SOURCE AUTHORITY, ARTIFACT AUTHORITY, DEPLOYMENT AUTHORITY, or LIVE RUNTIME AUTHORITY. Each must be named separately.

### Voice/S2S

- **Deployed source authority:** `5c85c4f` (RP-2B turn_id UUID fix)
- **Deployed release:** `/root/julia_voice_v2/releases/manual-5c85c4f-20260812_225157`
- **Repo HEAD:** `315f359` (docs-only ahead of deployed `5c85c4f`)
- **Live runtime:** UNVERIFIED — AutoDL shut down 2026-08-12 EOD

### Brain

- **Source authority:** `44cea89` (reconciliation merge `197ada9` + closeout SHA stamp; combines CC-2/CM-FAILCLOSED lineage `bbd90af` with TUNNEL-L1/G0 lineage `9bd8963`)
- **Runtime:** Mac launchd `com.julia.brain.18089`, port `127.0.0.1:18089`
- **Provenance gate:** `deploy/brain/start-brain-18089` (RP-1: clean-worktree + SHA + import provenance)
- Secret loader: committed; real `DEEPSEEK_API_KEY` lives only in `/Users/admin/.julia_ops/brain.env` mode `600`

### Electron

- **Source authority:** `4a08967`
- Production repo: `Julia_client` remote, local `julia_electron_v2`
- Legacy repo `julia_electron` is not production authority.

## VOICE-C1 Remediation Closure

- RC-1 runtime drift → RP-1 provenance gate ✅
- RC-2 authority cutover → RP-3 ADR-002 ✅
- RC-3 turn_id boundary + collision → RP-2 UUID uniqueness ✅

## Storage Program (2026-08-13)

- Entry point: `docs/architecture/JULIA_CONVERSATION_STORAGE_AND_DIARY_DEVELOPMENT_PLAN_v1.0.md`
- Wave 0 authority reconciliation: **STO-A0 CLOSED** (`e4ca952`).
- Physical persistence ownership model frozen by **ADR-033**.
- Next: STO-D0 (implementation decision freeze).

## Document status vocabulary

- CANONICAL: implementation authority.
- DERIVED: generated/supporting document consistent with canonical authority.
- HISTORICAL: evidence/context only.
- SUPERSEDED: replaced by a named canonical document.
- DEPRECATED: retained temporarily, must not guide new work.
- EXPERIMENTAL: prototype/research only.

## Conflict precedence

1. this four-repo manifest
2. per-repo `docs/authority/CURRENT_AUTHORITY.md`
3. frozen canonical contracts / unified architecture docs listed by the manifest
4. compatible ADRs
5. committed implementation code
6. historical/archive documents
7. chat history (evidence only, never sole authority)

## Next permitted work

- STO-A0 (Authority Reconciliation) closeout.
- STO-D0 (Implementation Decision Freeze) — 8 design decisions.
- STO-F1/F2 (Private Filesystem Contract + Persistence Binding).
- CM-S1 onward only after Wave 0 gates PASS.
