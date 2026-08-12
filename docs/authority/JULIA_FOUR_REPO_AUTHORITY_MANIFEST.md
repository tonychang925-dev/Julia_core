# Julia Four-Repository Authority Manifest

STATUS: CANONICAL
UPDATED: 2026-08-11
PURPOSE: one cross-repository entry point for current code/document authority.

## Repositories

| Repo | Role | Branch | Current authority commit | Manifest |
|---|---|---|---|---|
| Julia_core | Core runtime, canonical architecture, ConversationRuntime, Context OS | `main` | repo/doc head `7d29fb9dcb2719c406ac2cd66cd32ddc1e663662`; production ConversationRuntime floor `b463a3f702f9cfcb8db3cda870d8f570fc92483d` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-AI-Assistant | Brain/OpenAI-compatible API, CRT bridge, Brain observability | `phase5/rmd-3g-observability` | `2ca61102682f3ed5ee73b1034c3d13ea45c1e643` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-Voice-S2S | Voice/S2S runtime, production artifact, AutoDL supervisor/watchdog | `phase5/rmd-3g-observability` | C4 source `47c03e0357c13f97b3e584935cf7d5d98567ab51`; authority-doc head `f2e00a7e0977597a2989a9f3067419d1dfbe238a`; C1 artifact `b18d1e42ca2e1383829b6d5f0670652efa066944ba92823a815a35253291c9ac` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia_client / local `julia_electron_v2` | Electron desktop client | `codex/bugfix/electron-c10-c11-projection` | `12fd0fbc99043302a10ba4659c9114819d4730ce` plus G0 closeout successor commit | `docs/authority/CURRENT_AUTHORITY.md` |

Legacy confusion source:

- local `julia_electron` / remote `tonychang925-dev/julia_electron` is LEGACY / DO-NOT-USE for production RMD-3G/RMD-4 unless Tony explicitly re-authorizes it.

## Current production runtime authorities

Global rule: REPO HEAD is not automatically SOURCE AUTHORITY, ARTIFACT AUTHORITY, DEPLOYMENT AUTHORITY, or LIVE RUNTIME AUTHORITY. Each must be named separately.


### Voice/S2S

Authority roles are deliberately separate:

- AUTHORITY-DOCUMENT HEAD: `f2e00a7e0977597a2989a9f3067419d1dfbe238a`.
- C1 PRODUCTION SOURCE AUTHORITY: `1552470f3f8f4e33a9cb90181daa1353f0702eb2`.
- C3 DEPLOYED OBSERVABILITY SOURCE: `9721fc7aa4fa3277305b56f7217be6a4a2b80d40`; release `/root/julia_voice_v2/releases/cc1-c3-87971eb3`; artifact `87971eb33489be32d8ffea5cf51b88336da29c194efe0c6859e4697399543fe6`.
- C4 FAIL-CLOSED SOURCE AUTHORITY: `47c03e0357c13f97b3e584935cf7d5d98567ab51`; production deployment NOT STARTED.
- C1 PRODUCTION ARTIFACT AUTHORITY: `b18d1e42ca2e1383829b6d5f0670652efa066944ba92823a815a35253291c9ac`.
- CANONICAL LAUNCHER AUTHORITY: `90077d209cafcc428e9cb29498e75414973bbac9`, later superseded operationally by supervisor/watchdog commits through `09373281...`.
- INTERMEDIATE OPS COMMIT: `a5a90803794cdc7e8dd3b3ead534801c7f7bf85b` is historical/intermediate documentation commit, not C1 production source authority and not artifact authority.

- Source: `1552470f3f8f4e33a9cb90181daa1353f0702eb2`
- Artifact: `b18d1e42ca2e1383829b6d5f0670652efa066944ba92823a815a35253291c9ac`
- Manifest: `3137878712a0bf689fc9e381f8c1ab081512abdaea89dfedcd9106e65f2869c1`
- Release: `/root/julia_voice_v2/releases/rmd3g-c1-b18d1e42`
- Runtime env: `/etc/julia/julia-voice.env`
- Lifecycle: AutoDL supervisor + watchdog from Julia-Voice-S2S `deploy/autodl/`

Historical failed Voice candidates:

- `5f343195...` / `3a2feaf7...` = HISTORICAL RMD-3G LIVE FAILED CANDIDATE, not next production authority.
- CC-1-C3 production evidence confirmed `session.update` emitted `conversation_id=EMPTY`; C4 is the approved source-level remediation candidate.

### Brain

- Source authority: `9c8764af35c702a60d778b2148846d7728794f30`
- Production lifecycle commit: `2ca61102682f3ed5ee73b1034c3d13ea45c1e643`
- Runtime: Mac launchd `com.julia.brain.18089`
- Secret loader: committed; real `DEEPSEEK_API_KEY` lives only in `/Users/admin/.julia_ops/brain.env` mode `600`
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
