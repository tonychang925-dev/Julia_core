# Julia Phase 5 — Four-Repository Development Plan v1.2
## Conversation / Voice / Context OS Production Convergence

**Status:** FROZEN / WAVE B RELEASED / RMD-3A ONLY  
**Date:** 2026-08-11  
**Parent authority:** `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md`  
**Conversation architecture:** `JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1.md`  
**Scope:** `Julia_core`, `Julia-AI-Assistant`, `Julia-Voice-S2S`, `julia_electron` / local `julia_electron_v2`  
**Purpose:** turn the Phase 5 forensic findings into an exact, gated, four-repository implementation sequence without reintroducing client/S2S cognitive authority.

---

# 0. Executive Decision

The four repositories must converge on one invariant:

```text
Client / Electron
= presentation + conversation/session identity binding

S2S
= realtime media + ASR/TTS + transport to the canonical cognitive endpoint

Julia-AI-Assistant / Brain
= protocol adapter into Julia Core, not an alternate history/cognition authority

Julia Core
= canonical conversation lifecycle + Context OS gateway
```

The target live Voice path is:

```text
Electron active conversation_id
        ↓
Voice frontend
        ↓
S2S realtime session.metadata.conversation_id
        ↓
S2S chat-completions request body includes conversation_id
        ↓
Brain /v1/chat/completions
        ↓
existing native conversation_id branch
        ↓
ConversationRuntime.begin_turn_streaming()
        ↓
Context OS / JuliaSession / provider
        ↓
commit_streaming_turn() OR cancel_streaming_turn()
        ↓
S2S TTS / playback
```

Canonical multi-turn history MUST NOT be transferred from Electron or S2S.

---


# 0.1 Version Authority Envelope — Mandatory Before Every Repo Task

A repository name is not a version identity.

Before any Phase-5 task is released, record four independent identities:

```text
REMOTE_DEFAULT
  repository
  default branch
  remote commit

LOCAL_SOURCE
  path
  branch
  HEAD
  worktree status

APPROVED_CANDIDATE
  base commit
  exact scoped diff/hash
  task IDs represented by the delta

LIVE_DEPLOYED
  deployment path
  artifact/file hashes
  process PID/cmdline/interpreter
```

Rules:

```text
REMOTE_DEFAULT ≠ LOCAL_SOURCE unless proven
LOCAL_SOURCE   ≠ APPROVED_CANDIDATE unless proven
APPROVED_CANDIDATE ≠ LIVE_DEPLOYED unless proven
Directory name ≠ version authority
Commit message PASS ≠ production PASS
```

### Known reconciliation warnings from current review

```text
Julia_core
- remote `main` contains historical Aug-10 acceptance commits including b5d2c137
- Wave-A live native validation used a separate local composite candidate
- relation MUST be re-attested before any Core mutation

Julia-Voice-S2S
- remote default history contains b2c7567 + ADR-VOICE-C1B-R generation
- current live frontend was later proven to be a C1B-R/49ef5ba-generation artifact
- remote default, current local branch and live deployment MUST NOT be conflated

Julia-AI-Assistant
- remote default branch history is older than the locally/live-audited Brain paths used in Phase 5
- WB0-02 must establish the actual implementation candidate

julia_electron
- remote default `main` is not sufficient evidence for the previously audited local Electron candidate
- local branch/upstream relation must be captured before RMD-3A mutation
```

---

# 0.2 WB-AR — Authority Reconciliation Gate

**Mode:** READ-ONLY / DOCUMENTATION-ONLY. No production code mutation.

## WB-AR-01 — Revoked / superseded acceptance register

Create a registry that records historical acceptance documents/commits whose production-level claims were superseded by Phase-5 forensics.

Minimum entries:

```text
Voice Convergence CLOSED / zero cognitive bypass
Conversation V2 baseline closure / zero shadow authority
E2E 27/27 release closure
old Golden-production C2-04/C2-05 attribution
```

Disposition is never "delete history". It is:

```text
PRESERVE EVIDENCE
REVOKE CURRENT AUTHORITY
POINT TO REPLACEMENT FINDING / GATE
```

## WB-AR-02 — Architecture document registry update

Update architecture registry/index so precedence is explicit:

```text
Unified Architecture
→ CM v1.1 once frozen
→ derived frozen contracts
→ compatible ADRs
→ API/spec
→ implementation/deployment
→ historical acceptance/audit evidence
```

## WB-AR-03 — Four-repo authority envelopes

Capture the Version Authority Envelope for all four repositories before RMD-3A GO.

**Exit Gate `G-AR`:** no Phase-5 task refers ambiguously to "main", "HEAD", "Golden", "current", or "production" without an attached identity.

---

# 1. Locked Production Truth

## 1.1 Wave A

```text
RMD-0 Contract semantics                    ✅ CLOSED
RMD-1 ConversationRuntime cancel lifecycle  ✅ VALIDATED
RMD-2 L1/L2/native regression               ✅ VALIDATED
Wave A Core remediation                     ✅ COMPLETE
```

RMD-1 guarantees:

```text
accepted user = durable canonical fact
assistant failure/cancel/interruption ≠ user failure
```

## 1.2 Deployment provenance correction

```text
b2c7567
= historical/recovery Golden baseline
≠ current live deployed frontend

Current live frontend
= C1B-R / 49ef5ba-generation artifact
```

Never use a deployment directory name such as `golden/` as version authority.

## 1.3 Current production-capable cognitive ingress

```text
Path A — current live S2S
S2S chat-completions
→ Brain /v1/chat/completions
→ live probe: session metadata does not arrive at Brain as conversation_id
→ legacy Brain branch

Path B — legacy Brain Voice HTTP
/internal/v1/voice/turns
→ JuliaCoreAdapter
→ prepare_voice_turn()
→ direct provider + legacy session.history

Path C — canonical
/internal/v1/conversations/{conversation_id}/turns
→ ConversationRuntime
→ Context OS
```

Wave B exists to remove the authority difference between A/B and C.

---

# 2. Repository Map and Authority Boundaries

| Repository | Production role | May own | Must not own |
|---|---|---|---|
| `Julia_core` | canonical runtime / Context OS / persistence | ConversationRuntime, ConversationMessage, Context OS, invariant tests | Voice session state, Electron projection, provider-local history authority |
| `Julia-AI-Assistant` | Brain/API/protocol bridge | HTTP/SSE adapters, native route binding, provider adapter access through Core | caller-owned multi-turn history, direct alternate cognition for Julia-bound canonical conversations |
| `Julia-Voice-S2S` | realtime Voice/media integration | VAD, ASR, TTS, WebSocket media, session metadata transport, reproducible S2S handler integration | canonical conversation history, memory, Context selection, independent Julia cognition authority |
| `julia_electron` | client/body/projection | conversation selection, iframe/media hosting, UI projection, disposable cache | canonical transcript, model-visible history selection, semantic workspace authority |

The AutoDL `speech-to-speech` installation is a runtime dependency. Any handler customization discovered during RMD-3A MUST be represented reproducibly through `Julia-Voice-S2S` source/deployment assets. Manual untracked `site-packages` editing is not an acceptable final state.

---

# 3. Phase 5 Dependency Graph

```text
                    WAVE A ✅ COMPLETE
                         │
                         ▼
               WB-0 Source Attestation
                         │
                         ▼
          ┌──────────── RMD-3A ────────────┐
          │ Current Live S2S → CRT         │
          └────────────────┬───────────────┘
                           │
                           ▼
          ┌──────────── RMD-3B ────────────┐
          │ Legacy Brain Voice → CRT       │
          └────────────────┬───────────────┘
                           │
                           ▼
                       RMD-3G
                Live Convergence Gate
                           │
                    PASS only ↓
                           ▼
                        RMD-4
          Transitional / Legacy Retirement
                           │
                           ▼
                        RMD-4V
             Final Live Voice Validation
                           │
                           ▼
                  WAVE C — RMD-5/6
                           │
                           ▼
                  WAVE D — RMD-7/8
```


## 3.1 Wave B Release Order

```text
G-AR PASS
  ↓
WB0-03 / WB-JA-08 PASS
  ↓
WAVE B ARCHITECTURE + TASK FREEZE
  ↓ Tony GO
RMD-3A implementation
  ↓ local/integration tests
RMD-3B implementation
  ↓ local/integration tests
RMD-3G LIVE convergence gate
  ↓ PASS only
RMD-4 retirement
  ↓
RMD-4V final production validation
```

Parallel implementation is forbidden where it would destroy causal attribution. In particular, RMD-4 must never be bundled into the RMD-3A/RMD-3B patch set.

Fail-closed rule:

```text
Gate FAIL / UNKNOWN
→ STOP
→ no opportunistic fix
→ no retirement
→ no next RMD
```

---

# 4. WB-0 — Baseline and Deployed-Source Attestation

**Mode:** READ-ONLY except an explicitly authorized provenance-only local commit if Tony separately approves it.

## WB0-01 — `Julia_core` candidate identity

Wave-A validated local composite candidate:

```text
local base HEAD 0d72b05534c79c22e58b2e4e95dca97171d8489a
+ approved RMD-1 worktree delta
+ approved RMD-2 test delta
```

Remote `Julia_core/main` independently contains later Aug-10 acceptance commits (including `b5d2c137`). This does **not** establish byte-equivalence with the Wave-A validated local composite. WB0-01 must reconcile the relation before any new Core mutation.

Tasks:

- record exact diff/hash of `julia_core/runtime/conversation_runtime.py`;
- record exact diff/hash of `tests/rt2_r3/test_core_acceptance.py`;
- preserve unrelated dirty files as out-of-scope;
- before any new Core mutation, create an immutable candidate identity record;
- do not call HEAD alone the RMD-1 candidate.

**Exit:** exact reproducible Core candidate identity.

## WB0-02 — `Julia-AI-Assistant` baseline

Tasks:

- branch / HEAD / worktree status;
- hash current `voice_api/openai_compat.py`, `conversation_routes.py`, `julia_core_adapter.py`, `shared_orchestration.py`, `sse_stream.py`;
- prove current live Brain process source path for the subsequent test environment.

**Exit:** no ambiguity about which Brain source will be changed.

## WB0-03 — `Julia-Voice-S2S` / AutoDL handler attestation — PASS

`WB-JA-08` is CLOSED. Deployed identity:

```text
PID                              2118
Python                           /root/miniconda3/bin/python (3.10)
package                          speech-to-speech==0.2.12
package root                     /root/miniconda3/lib/python3.10/site-packages
handler class                    ChatCompletionsApiModelHandler
handler file                     speech_to_speech/LLM/chat_completions_language_model.py
handler SHA256                   4aef412253731a83f649bc79895e233faafc0874638e5efc923a44a49d56e90a
base handler SHA256              4718f762d3f45bb001296595f588610c0432057039b7de08f2636e0418901c59
session metadata visible         YES
conversation_id outbound         NO
turn_id outbound                 NO
source cancel class              MARKS_STALE_ONLY
```

The deployed handler already receives a turn whose runtime config exposes the realtime session. Therefore no new session-plumbing layer is required on the server side.

**Exit:** PASS. Exact deployed source units are known.

## WB0-04 — `julia_electron` baseline

Known historical/local evidence to re-attest before mutation:

```text
local candidate previously: 12fd0fb...
remote baseline previously: 43aef03...
```

Tasks:

- current branch / HEAD / upstream relation;
- worktree cleanliness;
- hash `src/renderer/shell/app.js`, `src/main/text-client.js`, `src/main/main.js`, `src/preload/index.js`.

**Exit:** exact Electron source identity.

---

# 5. RMD-3A — Current Live S2S Session Identity → CRT Routing

**Goal:** keep the current VAD/STT/LLM-backend/TTS realtime pipeline, but make its Brain cognitive request select the canonical `conversation_id` route.

## 5.1 `julia_electron` tasks — RMD-3A production mutation = 0 expected

Current Electron already supplies `conversationId` to the hosted Voice bootstrap. The current Voice frontend's `bootstrapVoiceWorkspace(payload)` requires and stores that identifier before it calls `doStart()`. Therefore RMD-3A does **not** need a new Electron identity transport.

### EL-R3A-01 — Attest existing identity handoff

**Expected production code mutation:** `0`

Required proof:

```text
Electron active conversationId
→ julia.voice.workspace.bootstrap
→ Voice bootstrapVoiceWorkspace(payload)
→ VoiceWorkspace({ conversationId })
```

During RMD-3A the transitional bootstrap message may remain only as an identity/lifecycle carrier. `messages[]` and `baseLastMessageId` must have zero cognitive effect and are retired later in RMD-4.

**Exit:** Electron already binds identity; no RMD-3A Electron patch unless implementation evidence contradicts this attestation.

## 5.2 `Julia-Voice-S2S` tasks — exact RMD-3A mutation surface

### VS-R3A-01 — Voice frontend: bind Workspace conversation_id into realtime session metadata

**Authorized current-source files after Tony GO:**

```text
frontend/main.js
frontend/ws/s2s-ws-client.js
```

Current source facts at `49ef5ba...`:

```text
frontend/main.js::bootstrapVoiceWorkspace(payload)
  - receives conversationId
  - constructs VoiceWorkspace({ conversationId })
  - calls doStart()

frontend/main.js::doStart()
  - constructs new S2sWsRealtimeClient({...})
  - currently does not pass conversation identity

frontend/ws/s2s-ws-client.js::_sendSessionUpdate()
  - currently sends type/instructions/audio/tools
  - currently sends no metadata.conversation_id
```

Target:

```text
VoiceWorkspace.conversationId
→ S2sWsRealtimeClient option/session identity
→ _sendSessionUpdate()
→ session.metadata.conversation_id
```

Preferred minimal form:

- `main.js::doStart()` passes the already-bound current `conversationId` into the realtime client;
- `S2sWsRealtimeClient` carries it as connection/session identity;
- `_sendSessionUpdate()` conditionally adds `metadata: { conversation_id: ... }`;
- no history/messages are added;
- no second cognition POST is introduced.

No need to change Electron for this handoff.

### VS-R3A-02 — Deployed S2S handler: propagate session metadata into Brain request

**Actual deployed modification unit:**

```text
/root/miniconda3/lib/python3.10/site-packages/
  speech_to_speech/LLM/chat_completions_language_model.py

class: ChatCompletionsApiModelHandler
handler SHA256 before change:
4aef412253731a83f649bc79895e233faafc0874638e5efc923a44a49d56e90a
```

The handler's generation path already has access to `turn.runtime_config.session`; no new session/pipeline plumbing is required.

Target:

```text
turn.runtime_config.session.metadata.conversation_id
→ dynamic outbound chat-completions request field conversation_id
→ Brain /v1/chat/completions
```

Authorized implementation scope after Tony GO:

```text
ChatCompletionsApiModelHandler._generate()
and strictly necessary request-building helper in the SAME deployed file
```

`turn_id` is not required for RMD-3A unless an existing canonical idempotency contract requires it during implementation review. Core may generate it.

### VS-R3A-03 — Reproducibility ownership

Direct unexplained site-packages editing is forbidden as a final state. The `Julia-Voice-S2S` repository must own a reproducible artifact targeting the attested `speech-to-speech==0.2.12` source/hash, for example a versioned patch/overlay plus apply/verify script.

Required safety:

```text
verify expected pre-patch SHA256
apply exact patch
verify post-patch source/hash
rollback to attested source
record deployed artifact hash
```

### VS-R3A-04 — Preserve media baseline

NO CHANGE unless a gate proves otherwise:

```text
VAD 800ms
ASR model/config
TTS model/config
WebSocket audio framing
AudioWorklet/playback/body behavior
```

### VS-R3A-05 — Cancellation disposition

Current deployed source classification is:

```text
MARKS_STALE_ONLY
```

It breaks consumption when generation becomes stale but does not explicitly prove an active HTTP close. Do **not** add speculative cancellation code in the initial RMD-3A patch. First run RMD-3G.

If G3-03 proves that the Brain HTTP stream remains active and CRT does not receive cancellation, STOP and open a separate narrowly-scoped RMD-3A-CANCEL amendment. Do not silently fold it into the identity-routing patch.

**Exit:** every live S2S Brain cognitive request contains the bound conversation_id; media behavior remains unchanged.

## 5.3 `Julia-AI-Assistant` tasks for RMD-3A

### BA-R3A-01 — Native chat-completions branch verification

No production mutation expected if existing behavior remains:

```text
/v1/chat/completions + conversation_id
→ native _stream_turn()
→ ConversationRuntime
```

Add/retain integration tests proving:

- body `conversation_id` selects CRT;
- absence of `conversation_id` remains visibly legacy until RMD-3B/5 retirement;
- no caller-owned multi-turn history is imported as canonical truth on native route.

### BA-R3A-02 — Turn identifier policy

Decide and freeze one policy:

```text
preferred:
conversation_id required
turn_id optional; Core may generate
```

If Voice supplies a turn_id, it is an idempotency/correlation identifier only, not authority over transcript ordering.

**Exit:** Brain needs no new cognitive logic for live S2S routing.

## 5.4 `Julia_core` tasks for RMD-3A

### JC-R3A-01 — No new Core behavior unless test exposes a contract gap

Expected production code mutation: **0**.

Required regression proof:

- accepted user durable before cognition;
- Context OS sees canonical history for `conversation_id`;
- retry by same turn identity does not duplicate accepted user;
- conversation A/B isolation.

**Exit:** existing RMD-1/2 behavior remains intact under Voice-originated native route.

---

# 6. RMD-3B — Brain Legacy `/internal/v1/voice/turns` → CRT

This path is not the current S2S primary route, but it is still a production-capable alternate cognitive authority and must converge.

## 6.1 `Julia-AI-Assistant`

### BA-R3B-01 — Replace adapter-owned cognition

**Primary file:** `voice_api/julia_core_adapter.py`  
**Function:** `JuliaCoreAdapter.stream_response()`

Current legacy behavior:

```text
prepare_voice_turn()
→ direct get_llm_provider("deepseek") / provider call
→ legacy session.history write
```

Target:

```text
get ConversationRuntime
→ begin_turn_streaming()
→ JuliaSession.process_stream(...canonical history...)
→ commit_streaming_turn()
OR cancel_streaming_turn()
```

Disposition:

```text
prepare_voice_turn() usage on this route   SUPERSEDE
Voice direct provider ownership            RETIRE FROM ROUTE
legacy session.history mutation            RETIRE FROM ROUTE
```

### BA-R3B-02 — Transport cancel → canonical settlement

Current transport API may remain:

```text
response_id → asyncio.Event
```

but it becomes transport signaling only.

Required lifecycle:

```text
voice_cancel(response_id)
→ Event / task cancellation
→ active canonical turn generator exits
→ exactly one CRT cancel settlement
```

Tests:

- cancel before `begin_turn_streaming()` does not cancel nonexistent ctx;
- cancel during stream settles once;
- cancel after commit does not downgrade completed turn;
- accepted user remains completed.

### BA-R3B-03 — Keep route/SSE compatibility initially

Expected initial NO-CHANGE unless required:

```text
voice_api/routes.py route surface
voice_api/schemas.py VoiceTurnRequest
voice_api/sse_stream.py event shape
```

**Exit:** `/internal/v1/voice/turns` has no independent semantic/history/provider authority.

## 6.2 Other repos

`Julia_core`: regression only.  
`Julia-Voice-S2S`: no dependency on this legacy endpoint required.  
`julia_electron`: no dependency on this legacy endpoint required.

---

# 7. RMD-3G — Live Convergence Gate

RMD-3G is not a unit-test gate. It is a single-path production causal proof.

## G3-01 — Live binding

Prove for a real Voice turn:

```text
Electron active conversation_id
→ Voice frontend session metadata
→ deployed S2S handler
→ outbound Brain JSON conversation_id
→ Brain native branch
→ ConversationRuntime.begin_turn_streaming()
```

No inference between edges.

## G3-02 — Normal Voice

PASS requires:

```text
ASR final                     ✅
user canonical completed      ✅ before cognition
Context OS canonical history  ✅
assistant stream              ✅
canonical assistant commit    ✅
TTS/playback                  ✅
no duplicate user             ✅
```

## G3-03 — Real barge-in causal chain

PASS requires one traced chain:

```text
speech_started / response.cancel
→ S2S cancels or closes active Brain HTTP stream
→ Brain async stream observes cancellation
→ ConversationRuntime.cancel_streaming_turn(ctx)
→ accepted user remains completed
→ canonical history retains accepted user
→ next real cognition sees the accepted pre-barge-in user
```

If S2S only marks a generation stale while the Brain HTTP stream continues, G3-03 FAILS even if UI audio stops correctly.

## G3-04 — Cross-modality continuity

```text
Voice → Text
Text → Voice
Voice → Text → Voice
```

Requirements:

- same `conversation_id`;
- zero semantic history transfer;
- zero duplicate canonical turns;
- next cognition sees prior canonical facts.

## G3-05 — Isolation

- rapid A/B conversation switching;
- no cross-talk;
- no stale session metadata reused after conversation switch.

### RMD-3G verdict

```text
ALL PASS → Wave B retirement may begin
ANY FAIL/UNKNOWN → STOP, no RMD-4
```

---

# 8. RMD-4 — Transitional / Legacy Authority Retirement

Only after RMD-3G PASS.

## 8.1 `julia_electron`

### EL-R4-01 — Replace semantic workspace bootstrap

Retire semantic payload fields:

```text
messages[]
baseLastMessageId
voiceSessionId as semantic-history cursor
```

Move to a presentation/transport-only bind operation:

```text
conversation_id
optional media/session correlation id
```

### EL-R4-02 — Retire workspace flush as transcript transport

Retire production use of:

```text
flushVoiceWorkspace()
workspace delta parsing
commitExternalTurns() for normal Voice turns
```

`commitExternalTurns()` may remain migration-only until a separate migration decision closes it.

### EL-R4-03 — Keep projection

KEEP:

```text
iframe/media hosting
voice lifecycle/status rendering
syncCanonicalConversation()
canonical message rendering
local disposable cache
```

## 8.2 `Julia-Voice-S2S`

### VS-R4-01 — Retire deauthorized workspace remnants

Candidates after caller closure:

```text
VoiceWorkspace.exportDelta()
VoiceWorkspace.markCommitted()
workspace.flush handler
workspace.committed handler
selectBootstrapWindow()
baseMessages/baseLastMessageId fields
```

Keep only item/response correlation needed for UI projection if still required.

### VS-R4-02 — Keep media stack

KEEP:

```text
VAD
ASR
TTS
WebSocket media
playback
body/rendering
```

## 8.3 `Julia-AI-Assistant`

### BA-R4-01 — Retire production Voice legacy cognition helpers

After caller closure:

```text
prepare_voice_turn() as production Voice authority
Voice-specific direct provider route
Voice session.history writes
```

Do not delete helpers still required by unrelated legacy compatibility before RMD-5.

### BA-R4-02 — Reclassify `/external-turns`

Production Voice: not used.  
Possible historical migration: DEFER / migration-only.

## 8.4 `Julia_core`

### JC-R4-01 — Reverse-authority regression gate

Tests must fail if any client/Voice path can:

- upload full semantic history and replace canonical truth;
- downgrade accepted user during assistant interruption;
- choose model-visible history around Context OS.

---

# 9. RMD-4V — Final Current-Live Voice Canonical Validation

Only after RMD-4 retirement changes are complete.

Required:

```text
V4-01 normal live Voice              PASS
V4-02 real barge-in                  PASS
V4-03 accepted user completed        PASS
V4-04 canonical history retained     PASS
V4-05 next cognition sees user       PASS
V4-06 Voice→Text continuity          PASS
V4-07 Text→Voice continuity          PASS
V4-08 no workspace history transfer  PASS
V4-09 no legacy provider/history path PASS
V4-10 deployed artifacts attested    PASS
```

Only then may the program state:

```text
C-C007 current-live Voice production exposure = ELIMINATED
Voice→ConversationRuntime convergence           = PRODUCTION VALIDATED
```

---

# 10. Wave C — RMD-5 / RMD-6 Four-Repo Breakdown

Wave C remains HOLD until RMD-4V.

## RMD-5 — Legacy Context / Memory Authority Retirement

### `Julia-AI-Assistant`

- retire no-conversation-id caller-owned history where contract permits;
- retire manual `_prepare_turn()`/legacy memory injection from Julia-bound cognition;
- remove direct semantic history windows that bypass Context OS.

### `Julia_core`

- keep canonical conversation source + Context OS as unique model-visible path;
- add source-completeness traces/gates;
- finish long-history ActiveTail/Compact only under C-03 contract.

### `Julia-Voice-S2S`

- no semantic history authority;
- provider/S2S internal history is disposable transport state.

### `julia_electron`

- presentation-only cache; no model history authority.

## RMD-6 — Cognitive Boundary Migration

Primary repos: `Julia_core` + `Julia-AI-Assistant`.

Targets:

- retire runtime semantic routers that precompute cognition;
- preserve model agency/tool request loop;
- tool results re-enter only through Context OS;
- provider/Alignment adapt representation, not thought.

Voice/Electron only receive interface compatibility changes if required.

---

# 11. Wave D — RMD-7 / RMD-8 Four-Repo Breakdown

## RMD-7 — Alignment / Evidence / Trace Completion

### `Julia_core`

- context source provenance;
- turn/action/evidence correlation;
- canonical lifecycle trace.

### `Julia-AI-Assistant`

- adapter/provider trace IDs;
- cancellation/stream correlation.

### `Julia-Voice-S2S`

- session id / conversation id / response id correlation;
- barge-in transport evidence.

### `julia_electron`

- presentation event correlation only;
- no hidden semantic state.

## RMD-8 — Production Revalidation

Run one matrix across all four repos and deployed runtime:

```text
Text normal
Text cancellation/failure
Voice normal
Voice barge-in
Voice→Text
Text→Voice
rapid mode switching
conversation A/B switching
Brain restart
S2S restart
Electron restart/cache delete
provider switch where available
```

Final release requires provenance of the exact four-repo source SHAs + deployed artifacts.

---

# 12. Cross-Repo Task Matrix

| ID | Repo | Task | Depends on | Gate / Evidence |
|---|---|---|---|---|
| WB0-01 | Julia_core | attest RMD-1/RMD-2 candidate identity | Wave A | exact HEAD + worktree hashes |
| WB0-02 | Julia-AI-Assistant | baseline Brain source/proc | none | branch/HEAD/hash/source path |
| WB0-03 | Julia-Voice-S2S | deployed S2S handler attestation | none | package/version/path/hash/cancel source |
| WB0-04 | julia_electron | baseline Electron source | none | branch/HEAD/upstream/hash |
| EL-R3A-01 | julia_electron | bind conversation identity only | WB0-04 | no history authority |
| VS-R3A-01 | Julia-Voice-S2S | put conversation_id in session metadata | WB0-03, EL-R3A-01 | session.updated evidence |
| VS-R3A-02 | Julia-Voice-S2S | propagate session id into Brain request body | WB0-03, VS-R3A-01 | outbound body evidence |
| BA-R3A-01 | Julia-AI-Assistant | verify chat-completions native branch | WB0-02 | conversation_id → CRT trace |
| JC-R3A-01 | Julia_core | native-route invariants | WB0-01 | INV-01..08 + integration |
| BA-R3B-01 | Julia-AI-Assistant | migrate legacy voice adapter to CRT | WB0-02, RMD-1 | no direct provider/history authority |
| BA-R3B-02 | Julia-AI-Assistant | transport cancel → CRT settlement | BA-R3B-01 | cancel race suite |
| RMD-3G | all/deployed | live convergence gate | all R3A/R3B | single causal Voice path |
| EL-R4-* | julia_electron | retire semantic workspace/external turn path | RMD-3G | caller closure |
| VS-R4-* | Julia-Voice-S2S | retire workspace remnants | RMD-3G | caller closure |
| BA-R4-* | Julia-AI-Assistant | retire production legacy Voice authority | RMD-3G | no production caller |
| JC-R4-01 | Julia_core | reverse-authority tests | RMD-3G | sabotage PASS |
| RMD-4V | all/deployed | final live validation | RMD-4 | production PASS |

---

# 13. Branch / Commit Discipline

For every repository mutation batch:

```text
1. record pre-change HEAD / branch / status
2. isolate authorized files only
3. no cleanup mixed into remediation commit
4. tests before and after
5. commit message names RMD/task ID
6. no push unless separately authorized
7. deployed artifact must record source SHA + any package/overlay hash
```

Recommended commit granularity:

```text
RMD-3A Voice session identity transport      separate commit
RMD-3A S2S handler propagation               separate commit
RMD-3B Brain legacy adapter convergence      separate commit
RMD-3G tests/instrumentation                  separate commit if source changes needed
RMD-4 Electron retirement                    separate repo commit
RMD-4 Voice retirement                       separate repo commit
RMD-4 Brain retirement                       separate repo commit
```

Never combine four repositories into one undocumented "Wave B fix" narrative. Each repo retains independent provenance.

---

# 14. Phase 5 RACI

```text
Tony
= final GO / STOP / freeze / deployment authority

Mira
= architecture alignment
= evidence cross-validation
= RMD-3G / RMD-4V final verdict

Codex
= implementation owner for exact repository/file scopes explicitly released by Tony
= no inferred cross-repo writes

Julia Agent
= live S2S/AutoDL/deployed-artifact evidence owner
= runtime validation
= implementation only for scopes explicitly assigned
```

Historical governance records remain evidence. This RACI supersedes older "Codex Electron-only" rules **only for Phase 5 scopes explicitly released by Tony**.

---

# 15. Immediate GO/HOLD Matrix

```text
Architecture/document alignment             🟢 GO
Read-only source/deployed attestation        🟢 GO
WB-JA-08                                    ✅ PASS / CLOSED

RMD-3A production code                      ✅ RELEASED — RMD-3A ONLY
RMD-3B production code                      ⛔ HOLD pending RMD-3A review/closure
RMD-3G                                      ⛔ not runnable before RMD-3A/B
RMD-4                                       ⛔ HOLD until RMD-3G PASS
RMD-4V                                      ⛔ HOLD until RMD-4
RMD-5~8                                     ⛔ HOLD
Service restart / deployment                ⛔ HOLD unless gate explicitly releases
Git push / baseline promotion               ⛔ HOLD unless separately authorized
```

---

# 16. Wave B Review Gate

## 16.1 Architecture / Task Freeze Gate

```text
[x] CM Architecture v1.1 aligned through WB-JA-08
[x] four-repo WBS aligned through WB-JA-08
[x] G-AR authority reconciliation PASS
[x] WB-JA-08 exact deployed S2S handler source captured
[x] exact S2S session→handler propagation units known
[x] exact S2S cancel source behavior = MARKS_STALE_ONLY
[x] live HTTP cancellation deliberately deferred to RMD-3G
[x] RMD-3A authorized source units named
[x] RMD-3B authorized functions/scope named
[x] no ASR/TTS/VAD/media changes planned
[x] no semantic history transfer planned
[x] no parallel frontend cognition POST planned
[x] rollback/provenance method defined
```

**Architecture / Task Freeze Gate: PASS.**

Normative freeze authorized by Tony on 2026-08-11.

## 16.2 Per-Mutation Version Authority Gate

Exact baseline identity is captured **immediately before the repository is actually mutated**, rather than blocking architecture freeze for repositories whose code is not yet being changed.

```text
RMD-3A Julia-Voice-S2S   → re-attest repo HEAD/worktree + deployed pre-patch hashes before write
RMD-3B Julia-AI-Assistant→ re-attest Brain HEAD/worktree/live source before write
Julia_core               → re-attest only if a new Core production mutation becomes necessary
julia_electron           → re-attest before any later Electron mutation (RMD-3A expects 0)
```

Fail or ambiguity at the relevant per-mutation gate → STOP that mutation.

---

# 17. Definition of Done

Phase 5 conversation/Voice convergence is complete only when:

```text
one canonical ConversationRuntime lifecycle                ✅
one Context OS model-visible gateway                        ✅
current live S2S request carries conversation_id            ✅
legacy Brain Voice route converged or non-authoritative     ✅
accepted user survives assistant cancel/failure             ✅
real barge-in reaches canonical cancellation settlement     ✅
Voice/Text mode switch moves no semantic history            ✅
Electron/S2S hold no durable conversation authority         ✅
legacy workspace/external-turn production path retired      ✅
exact source/deployed provenance captured                    ✅
RMD-4V and RMD-8 production matrices pass                   ✅
```



---

# 18. Wave B Final Review Gate — Post WB-JA-08

## 18.1 Architecture verdict

```text
G-AR authority reconciliation                    PASS
WB-JA-08 deployed-source attestation             PASS
RMD-3A architecture                              PASS / LOCKED
RMD-3A exact mutation surface                    PASS / DEFINED
RMD-3B architecture                              PASS / DEFINED
RMD-3G live cancellation causal proof            DEFERRED BY DESIGN
RMD-4 retirement                                 HOLD until RMD-3G PASS
```

## 18.2 Release boundary

No production mutation is authorized by this document alone.

Required final governance transition:

```text
Tony: WAVE B GO — RMD-3A ONLY (2026-08-11)
    ↓
release RMD-3A only
    ↓
RMD-3A tests + live binding proof
    ↓
release RMD-3B
    ↓
RMD-3G
```

RMD-4 remains prohibited until RMD-3G PASS.
