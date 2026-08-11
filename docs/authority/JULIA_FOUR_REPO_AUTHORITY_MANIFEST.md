# Julia Four-Repository Authority Manifest

STATUS: CANONICAL
UPDATED: 2026-08-11
PURPOSE: one cross-repository entry point for current code/document authority.

## Repositories

| Repo | Role | Branch | Current authority commit | Manifest |
|---|---|---|---|---|
| Julia_core | Core runtime, canonical architecture, ConversationRuntime, Context OS | `main` | repo/doc head `39e0263af92e223e15d2402ff7a5bede7ad6dcd5` plus this CC-1 metadata successor; production ConversationRuntime floor `b463a3f702f9cfcb8db3cda870d8f570fc92483d` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-AI-Assistant | Brain/OpenAI-compatible API, CRT bridge, Brain observability | `phase5/rmd-3g-observability` | `2ca61102682f3ed5ee73b1034c3d13ea45c1e643` | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia-Voice-S2S | Voice/S2S runtime, production artifact, AutoDL supervisor/watchdog | `phase5/rmd-3g-observability` | authority-doc head `09373281c6e8342c0728f4c2be54f4c94b9178f4` plus C2 metadata successor; C1 production source `1552470f3f8f4e33a9cb90181daa1353f0702eb2`; CC-1-C2 code `850a94b516ef71d57f74960a8161cc46be7ba03b`; CC-1-C2 source package HEAD `a4afa86173cc4321210ee96ac515f07a53a39533`; current production artifact `b18d1e42ca2e1383829b6d5f0670652efa066944ba92823a815a35253291c9ac` until C2 artifact is built/deployed | `docs/authority/CURRENT_AUTHORITY.md` |
| Julia_client / local `julia_electron_v2` | Electron desktop client | `codex/bugfix/electron-c10-c11-projection` | CC-1 code `56cac30f3f467d28f9eacca0e4a4b6167038c9d4`; CC-1-C2 code `e5553eb0e302b6c66d5b9aa84ecb9111ef31f905`; authority-doc head `381484ea03746456e7e5eed6adb4946e9d300cca` plus C2 metadata successor | `docs/authority/CURRENT_AUTHORITY.md` |

Legacy confusion source:

- local `julia_electron` / remote `tonychang925-dev/julia_electron` is LEGACY / DO-NOT-USE for production RMD-3G/RMD-4 unless Tony explicitly re-authorizes it.

## CC-1 conversation convergence authority

- Targeted delta map: `docs/authority/CC1_CONVERSATION_CONVERGENCE_DELTA.md`
- Durable conversation authority remains ConversationRuntime/Core.
- Electron/S2S/Brain compatibility layers are transport/projection only and must not create shadow conversation history authority.

## CC-1-C2 production failure and remediation

- Production E2E failure: Electron sent `julia.voice.conversation.bind`, but active Voice frontend did not consume it.
- Prior CC-1 source IV&V is superseded for this boundary; active receiver coverage is mandatory.
- Voice C2 code: `850a94b516ef71d57f74960a8161cc46be7ba03b`; source package HEAD: `a4afa86173cc4321210ee96ac515f07a53a39533`.
- Electron C2 source: `e5553eb0e302b6c66d5b9aa84ecb9111ef31f905`.
- Brain/Core unchanged.
- Server mutation: none.
- Deployment status: not started; Voice C2 requires new artifact/staging/deployment before production retry.

## Current production runtime authorities

Global rule: REPO HEAD is not automatically SOURCE AUTHORITY, ARTIFACT AUTHORITY, DEPLOYMENT AUTHORITY, or LIVE RUNTIME AUTHORITY. Each must be named separately.


### Voice/S2S

Authority roles are deliberately separate:

- AUTHORITY-DOCUMENT HEAD: `09373281c6e8342c0728f4c2be54f4c94b9178f4` plus later metadata-only successors.
- C1 PRODUCTION SOURCE AUTHORITY: `1552470f3f8f4e33a9cb90181daa1353f0702eb2`.
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
