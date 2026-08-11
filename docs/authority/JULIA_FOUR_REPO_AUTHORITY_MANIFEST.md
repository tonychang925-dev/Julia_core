# Julia Four-Repository Authority Manifest

STATUS: CANONICAL
UPDATED: 2026-08-11
PURPOSE: one cross-repository entry point for current code/document authority.

## Repositories

| Repo | Role | Branch | Current authority commit | Manifest |
|---|---|---|---|---|
| Julia_core | Core runtime, canonical architecture, ConversationRuntime, Context OS | `main` | `0d72b05534c79c22e58b2e4e95dca97171d8489a` plus this G0 closeout successor commit | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-AI-Assistant | Brain/OpenAI-compatible API, CRT bridge, Brain observability | `phase5/rmd-3g-observability` | `37a1f72a4b505ad0b5ceb2fdd423b150a40db96c` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-Voice-S2S | Voice/S2S runtime, production artifact, AutoDL supervisor/watchdog | `phase5/rmd-3g-observability` | `a5a90803794cdc7e8dd3b3ead534801c7f7bf85b` plus G0 closeout successor commit | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia_client / local `julia_electron_v2` | Electron desktop client | `codex/bugfix/electron-c10-c11-projection` | `12fd0fbc99043302a10ba4659c9114819d4730ce` plus G0 closeout successor commit | `docs/authority/CURRENT_AUTHORITY.md` |

Legacy confusion source:

- local `julia_electron` / remote `tonychang925-dev/julia_electron` is LEGACY / DO-NOT-USE for production RMD-3G/RMD-4 unless Tony explicitly re-authorizes it.

## Current production runtime authorities

### Voice/S2S

- Source: `1552470f3f8f4e33a9cb90181daa1353f0702eb2`
- Artifact: `b18d1e42ca2e1383829b6d5f0670652efa066944ba92823a815a35253291c9ac`
- Manifest: `3137878712a0bf689fc9e381f8c1ab081512abdaea89dfedcd9106e65f2869c1`
- Release: `/root/julia_voice_v2/releases/rmd3g-c1-b18d1e42`
- Runtime env: `/etc/julia/julia-voice.env`
- Lifecycle: AutoDL supervisor + watchdog from Julia-Voice-S2S `deploy/autodl/`

Historical failed Voice candidates:

- `5f343195...` / `3a2feaf7...` = HISTORICAL RMD-3G LIVE FAILED CANDIDATE, not next production authority.

### Brain

- Source authority: `9c8764af35c702a60d778b2148846d7728794f30`
- Production lifecycle commit: `37a1f72a4b505ad0b5ceb2fdd423b150a40db96c`
- Runtime: Mac launchd `com.julia.brain.18089`
- Clean checkout: `/Users/admin/julia_ai_assistant_rmd3g_prod @ 9c8764af...`
- Production port: `127.0.0.1:18089`
- Retired legacy port: `127.0.0.1:8088`

### Electron

- Production repo: `Julia_client` remote, local `julia_electron_v2`
- Current active client path: `julia_electron_v2`
- Legacy repo `julia_electron` is not production authority.

## Document status vocabulary

Every architecture or operations document must be treated as one of:

- CANONICAL: implementation authority.
- DERIVED: generated/supporting document consistent with canonical authority.
- HISTORICAL: evidence/context only.
- SUPERSEDED: replaced by a named canonical document.
- DEPRECATED: retained temporarily, must not guide new work.
- EXPERIMENTAL: prototype/research only.

## Conflict precedence

If documents conflict, use this order:

1. this four-repo manifest
2. per-repo `docs/authority/CURRENT_AUTHORITY.md`
3. frozen canonical contracts / unified architecture docs listed by the manifest
4. compatible ADRs
5. committed implementation code
6. historical/archive documents
7. chat history (evidence only, never sole authority)

## Next permitted work

- G0 authority closeout must close before CC-1 feature/convergence development.
- RMD-4 remains HOLD until RMD-3G live/cancellation evidence is closed by Tony/Mira.
