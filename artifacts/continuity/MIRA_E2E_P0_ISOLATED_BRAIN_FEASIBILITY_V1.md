# MIRA-E2E-P0 — Isolated Golden Mira Brain Composition Feasibility Spike

- TASK_ID: `MIRA-E2E-P0`
- TASK_NAME: Isolated Golden Mira Brain Composition Feasibility Spike
- OWNER: Tony
- ARCHITECT_REVIEWER: Mira
- AUDIT_DATE: 2026-09-14 (Asia/Shanghai)
- ASSISTANT_PRODUCT_SHA: `bbd90af42ba659684c25f1e9473c24804364548c`
- ASSISTANT_SPIKE_WORKTREE: `/private/tmp/mira-e2e-p0-assistant`
- MIRA_CORE_TARGET_SHA: `28b502ca4f48e580d4941e095bb8dccc6f3e9682`
- CORE_SPIKE_WORKTREE: `/private/tmp/mira-e2e-p0-core`
- FINAL_RESULT: `PASS_WITH_BLOCKERS`

## 1. Executive summary

The existing Julia-AI-Assistant FastAPI transport shell is reusable as a Brain-shaped HTTP/SSE server on `127.0.0.1:18091`. A disposable process at pinned Assistant/Core worktrees started successfully and answered only `GET /internal/v1/voice/health` with HTTP 200. The existing Julia Brain stayed on PID 629 at `127.0.0.1:18089`; all monitored Julia state hashes were unchanged and the experiment made zero requests to port 18089.

The exact Golden Mira C03 callable chain is present and executable at Core SHA `28b502ca4f48e580d4941e095bb8dccc6f3e9682`: exact governed repositories → deterministic projection → 3 `IdentityFrame`s and ordered 8 `ExperienceFrame`s → `ExclusiveAdmissionRequest` → `ExclusiveAdmissionGate.seal` → `ExactAdmittedSemanticBinder.bind` → `JuliaAssistantRuntime.prepare` → immutable `ProviderExecutionEnvelope`. The evidence-only observer accepts an injected `Callable[[ProviderExecutionEnvelope], str]`.

The decisive blocker is deployment composition, not the callable: Golden Mira's 3 identity versions and 8 memory records are reconstructed from pinned P5 migration artifacts into fresh in-memory repositories. Core has durable-envelope/reconstruction contracts, but no concrete durable reader/filesystem adapter and no production startup caller. Therefore a real HTTP turn cannot currently load Golden Mira from a durable canonical store without improperly promoting the P5 fixture path. P1 must add an owner-gated durable canonical export/read path and an isolated experimental composition root.

The old Julia persona is hard-bound in the current native HTTP turn path because `conversation_routes.py` imports both `get_conversation_runtime()` and `get_session()`. `ConversationRuntime` itself is persona-independent and accepts a repository, but `JuliaSession.__init__()` loads narrative bootstrap and `PersonaFeatureStore`, so reusing the existing route without composition changes would disturb semantic isolation. A new generic Brain adapter is not required; the required work is isolated composition/configuration plus canonical Mira runtime binding and a C03 envelope-consuming provider transport.

## 2. Existing Brain composition graph

| Binding | File / symbol | Current behavior | Injectable | Hard-coded | Future change |
|---|---|---|---|---|---|
| SERVER_ENTRYPOINT | `voice_api/server.py:24` `main()` | FastAPI app includes voice, OpenAI-compat, native conversation, and management routers; defaults host to `127.0.0.1`; accepts `--port` | YES for host/port | NO for host/port; YES for router set | YES |
| ROUTER_ENTRYPOINT | `voice_api/conversation_routes.py:47` `conversation_turn()` | Validates turn, then lazily imports Core runtime and old `JuliaSession` | NO through public API | YES | YES |
| CONVERSATION_RUNTIME_FACTORY | `julia_core/runtime/conversation_runtime.py:738` `get_conversation_runtime()` | Process singleton around `ConversationRuntime()` | YES by constructor | YES by singleton/default | YES |
| CORE_IMPORT_PATH | Product launcher verifies imports from `/Users/admin/julia_core`; experiment used explicit disposable worktree `PYTHONPATH` | Product imports current Core checkout; experiment resolved both packages to disposable worktrees | YES | YES if launcher ignored | YES |
| PERSONA_BINDING_POINT | `julia_core/runtime/julia_session.py:75` `JuliaSession.__init__()` | Loads bootstrap and persona feature store | NO in existing route | YES | YES |
| MEMORY_BINDING_POINT | `julia_core/runtime/julia_session.py:95` | Global recorder/relationship state plus recent-session reconstruction | NO in existing route | YES | YES |
| PROVIDER_BINDING_POINT | `julia_core/runtime/julia_session.py:75`; Assistant `providers/llm/deepseek_provider.py:26` | Eagerly binds DeepSeek; key/env/model constants | NO in existing route | YES | YES |
| CONVERSATION_STORE_BINDING_POINT | `julia_core/runtime/conversation_runtime.py:101` | Defaults to cwd-relative `data/conversations.json` | YES by repository | YES by default/factory | YES |

Current product sequence: Electron → native turn route → `get_conversation_runtime()` + `get_session()` → old Julia cognition/provider → Core settlement → cwd-derived JSON store.

Isolated target sequence: SHA/import checks → durable canonical reconstruction → exact projection/C03 → envelope-only provider → explicit experimental store → existing SSE dialect.

## 3. Julia persona binding analysis

`JuliaSession.__init__()` unconditionally loads:

- `get_bootstrap()` at `julia_core/runtime/julia_session.py:78`.
- `get_persona_store()` at `julia_core/runtime/julia_session.py:100`.
- Static Julia identity text including persona traits at line 111.
- Global relationship/session recorder services at line 91.
- Old DeepSeek provider at line 75.

`ConversationRuntime` does not load those services. It can be instantiated independently with an injected repository, and `process_turn()` accepts an injected `cognitive_fn`.

```text
JULIA_PERSONA_BINDING = HARD_BOUND_IN_EXISTING_HTTP_COMPOSITION
CONVERSATION_RUNTIME_WITHOUT_OLD_JULIA_PERSONA = YES_BY_DIRECT_COMPOSITION
EXISTING_HTTP_ROUTE_WITHOUT_OLD_JULIA_PERSONA = NO_UNTIL_P1_COMPOSITION_CHANGE
```

The valid replacement is the canonical Golden Mira C03 path. Prompt overrides, fake personas, fallback prompts, semantic-authority bypass, and fixture smuggling are prohibited.

## 4. Golden Mira canonical runtime callable

1. `IdentityRepository` — `julia_core/identity/repository.py:29`.
2. `MemoryExperienceRepository` — `julia_core/memory_experience/repository.py:24`.
3. `CanonicalSemanticAuthoritySource` — `julia_core/canonical_authority_source.py:77`; identity read at line 112, memory read at line 165.
4. `PersonaProjectionPolicy.project_ref()` — `julia_core/projection/policy.py:56`.
5. `ExperienceProjectionPolicy.project_ref()` — `julia_core/projection/policy.py:99`.
6. `IdentityFrameSet` — `julia_core/projection/contracts.py:117`.
7. `ExperienceFrameSet` — `julia_core/projection/contracts.py:248`.
8. `CurrentConversationalTaskContext` — `julia_core/context_admission/contracts.py:96`; required fields are schema `1.0.0`, conversation/turn IDs, intent/domain/modality, bounded state, and exact ConversationRuntime provenance.
9. `ExclusiveAdmissionRequest` — `julia_core/context_admission/contracts.py:154`.
10. `ExclusiveAdmissionGate.seal()` — `julia_core/context_admission/gate.py:41`; contract `julia_core.context_admission.c03.production.v3`; returns `SealedCognitiveContextPackage`.
11. `ExactAdmittedSemanticBinder.bind()` — `julia_core/context_admission/semantic_binding.py:202`; returns `AdmittedSemanticBundle`.
12. `RuntimeTurnRequest(binding, provider_id, input_mode)` — `julia_core/runtime/assistant_runtime.py:11`.
13. `JuliaAssistantRuntime.prepare()` — `julia_core/runtime/assistant_runtime.py:63`; returns `ProviderExecutionEnvelope`.
14. `EvidenceOnlyCanonicalExecutionObserver.observe()` — `julia_core/execution_observer.py:374`; invokes an injected provider callable and returns replay-digested evidence.

Provider callable contract: `Callable[[ProviderExecutionEnvelope], str]`. `ProviderExecutionEnvelope` is at `julia_core/alignment_os/contracts.py:240` and contains immutable `system/system/user` messages plus alignment metadata.

### Exact ordered canonical inputs

Identity versions and digests:

1. `mira-golden:mira-id-cand-001` / `mira-id-cand-001-v0.1-preview` — `7580e0a930dc7f3d5446da2cdd8d1c23cf251e12929fb2f3baa056bd9739dd44`
2. `mira-golden:mira-id-cand-002` / `mira-id-cand-002-v0.1-preview` — `adaa2508c4e475a700c394eb205e278d515dfe014ccdaa4bab3c3e7b7dcd5f3a`
3. `mira-golden:mira-id-cand-003` / `mira-id-cand-003-v0.1-preview` — `0008a5e157347ae9b0dd8600d661ec4a0e3fbd1858673cd04dc7c7b812a96c29`

MemoryExperience records and digests:

1. `golden-mira:GM-CMIR-001` / `v0.2-preview` — `4e29eb74de7f29bbf8d69485a7c18b5dceb06486d7e1d986d668a30c85fb7228`
2. `golden-mira:GM-CMIR-002` / `v0.2-preview` — `e4374452173b144ce48dbefa5299f1ac3dc15cec3615b8e7d528176293536f93`
3. `golden-mira:GM-CMIR-004` / `v0.1-preview` — `ba4edeff89bc8054be19d7a48226fcef74359bc85d17dbd6abea4b754b905f97`
4. `golden-mira:GM-CMIR-006` / `v0.1-preview` — `47636f46d2934eeb66f91c8202e2245c180b7077fddd04ca6445683308b54f2c`
5. `golden-mira:GM-CMIR-008` / `v0.1-preview` — `08c95873446b01949b7aec50ad35ebbe36ce8b5b9ad87aca45c51b627f70c408`
6. `golden-mira:GM-CMIR-011` / `formation-draft-preview` — `3107a3ab38d0fc0d2446752f48bedebf2ee336e3cb8b22811bf3c156247a4ae9`
7. `golden-mira:GM-CMIR-011` / `frozen-final-preview` — `3c31de4d62ecfd5d7857a5a4df85725affa0862d0055b5527d7d80f27fcc8ad8`
8. `golden-mira:GM-CMIR-013` / `v0.2-preview` — `8e2d16304357b7fb72b5b6cb53501be5d8743b3c687d2f0aadf3a9e1e132046c`

Verification: 60 relevant P5/C03/binder/durable-authority tests passed.

## 5. Canonical storage and read path

Existing paths:

- `tools/mira_migration/admission_sim.py:830` reads pinned migration preview/review/ledger artifacts through `git show`, reconstructs typed objects, and validates canonical serialization/digests.
- `tools/continuity/p5_a1_admission.py:88` stores and admits the exact 3 + 8 set in fresh in-memory repositories, then verifies refs/status/order/digests. It does not persist them.
- `julia_core/durable_authority/reconstruction.py:62` and `:83` restore exact repositories from a `DurableAuthorityReader`.
- `julia_core/durable_authority/adapters.py:17` defines the Reader protocol.
- Envelope parsing validates payload digest, governance target/order, lineage, lifecycle, provenance, and envelope digest.

Missing:

- Concrete filesystem/database Reader.
- Owner-gated durable export of admitted Golden Mira governance state.
- Production startup reconstruction/caller.
- Durable exact-reference selection logic.

```text
MIRA_CANONICAL_RUNTIME_CALLABLE = YES
CANONICAL_MIRA_READ_PATH_AVAILABLE = NO
BLOCKER = CANONICAL_RUNTIME_READ_PATH_NOT_DEPLOYABLE
```

P0 did not copy fixtures into runtime state; that would falsify provenance and remain non-deployable.

## 6. Provider wiring and isolation

Old Assistant `DeepSeekProvider` is not directly C03-compatible:

- Reads `DEEPSEEK_API_KEY` at import at `providers/llm/deepseek_provider.py:29`.
- Hard-codes DeepSeek URL, `deepseek-chat`, max tokens 500, temperature 0.8, and timeout 60.
- `build_messages()` calls `ProviderBehaviorAdapter`, which at the pinned Core intentionally rejects legacy arbitrary message/persona adaptation.

P1 should reuse DeepSeek only as envelope transport: consume `ProviderExecutionEnvelope.messages` unchanged, use isolated model/timeout/retry/stream settings, and return `str`. An independent credential is preferred. Temporary key sharing gives `PROVIDER_ACCOUNT_COUPLING=YES` but `SHARED_PERSONA_STATE=NO`.

## 7. State isolation

`ConversationRuntime` accepts a repository, but the global factory defaults to cwd-relative `data/conversations.json`.

```text
MIRA_E2E_RUN_ROOT=/Users/admin/.julia_mira_e2e
MIRA_E2E_CONVERSATION_STORE=/Users/admin/.julia_mira_e2e/data/conversations.json
CHANGE_REQUIRED = EXPLICIT_CONVERSATION_STORE_PATH
```

The absolute store must be inside the isolated run root. Product roots, current Core state, `~/.julia`, launchd, and port 18089 remain read-only/untouched.

## 8. Git SHA pinning and import provenance

Product evidence:

- Assistant SHA `bbd90af42ba659684c25f1e9473c24804364548c`.
- Product root `/Users/admin/julia_ai_assistant_rmd3g_prod`.
- Existing launcher explicitly verifies `julia_core` imports from `/Users/admin/julia_core`.

Spike proof:

```text
julia_core = /private/tmp/mira-e2e-p0-core/julia_core/__init__.py
voice_api  = /private/tmp/mira-e2e-p0-assistant/voice_api/__init__.py
```

Recommended P1 order: dedicated worktrees, dedicated clean venv, explicit worktree paths, resolved-module assertions, and fail-closed HEAD checks. Do not depend on current `/Users/admin/julia_core` contents. `cwd` must be constrained because it affects default store and legacy module discovery.

## 9. Electron compatibility

Current Julia_client supports the required contract without source changes:

- Settings normalize `brainEndpoint` in `src/main/settings-store.js:9` and `:32`.
- `JULIA_TEXT_API_URL` overrides the text endpoint in `src/main/text-client.js:132`.
- Health is `/internal/v1/voice/health` in `src/main/brain-status.js:4`.
- Conversation CRUD/messages URLs are built in `src/main/text-client.js:80`.
- Turns use `/internal/v1/conversations/{id}/turns` and `{turn_id, modality, input, stream}` at lines 80 and 162.
- Client handles completed/interrupted messages, typed transport errors, SSE liveness, and completion.

Use a separate Electron user-data directory and `http://127.0.0.1:18091`. `CLIENT_CHANGE_REQUIRED=NO`.

## 10. Disposable runtime result

- Assistant worktree SHA `bbd90af42ba659684c25f1e9473c24804364548c`.
- Core worktree SHA `28b502ca4f48e580d4941e095bb8dccc6f3e9682`.
- Explicit `PYTHONPATH` order: Assistant then Core.
- Bind only `127.0.0.1:18091`.
- Health only; no turn/provider/store/canonical mutation.

Observed response:

```json
{"status":"ok","contract_version":"1.0.0","julia_core":"frozen-865ffc4"}
```

PID 32452 started, answered one health GET, and stopped cleanly. Port 18091 no longer listened afterward.

## 11. Julia preservation proof

| Evidence | Before | After |
|---|---|---|
| Brain PID/listener | 629, `127.0.0.1:18089` | identical |
| launchd label | `com.julia.brain.18089` | unchanged |
| Product root | `/Users/admin/julia_ai_assistant_rmd3g_prod` | unchanged |
| Product conversations SHA256 | `fbae7e00b8f2275c90c6d769f27d3c1a453cc41528e59127d330d0c4630bcec7` | identical |
| Current Core conversations SHA256 | `be5bf696665d0967627a8453781654620eaeef1ec970743169f4741dccd4ee7f` | identical |
| Current Core sessions SHA256 | `bb68d5b9c00565a6ce8e57868d9fb771dbb30a97e137cfb970824d58b2f4de8b` | identical |
| `~/.julia/sessions.json` SHA256 | `51702425a4a76f328490788c3890cc3bb2c05276fc57ff38532dbfb0a206fc43` | identical |

```text
JULIA_REQUEST_COUNT_FROM_EXPERIMENT = 0
JULIA_STATE_CHANGED = NO
JULIA_PROCESS_RESTARTED = NO
JULIA_CONFIG_CHANGED = NO
```

## 12. Implementation change map

### Julia_client

`CHANGE_REQUIRED=NO`; files `[]`. Use separate profile and endpoint configuration only.

### Julia-AI-Assistant

`CHANGE_REQUIRED=YES`; files:

- `voice_api/server.py`
- `voice_api/conversation_routes.py`
- `voice_api/julia_core_adapter.py`
- `voice_api/conversation_management.py`
- `voice_api/mira_composition.py` (new)

Reason: inject isolated ConversationRuntime, Golden Mira cognition, and C03 provider transport instead of `get_session()`/old Julia persona.

### Julia_core

`CHANGE_REQUIRED=YES`; required files:

- `julia_core/durable_authority/filesystem_adapter.py` (new)
- `julia_core/durable_authority/reconstruction.py`
- `julia_core/runtime/conversation_runtime.py`
- `julia_core/runtime/mira_composition.py` (new)

Reason: durable canonical read/reconstruction, explicit store path, and bounded startup composition without changing old Julia paths.

### Local runtime config

`CHANGE_REQUIRED=YES`; expected SHAs, run root, conversation store, durable authority root, host/port, provider, model, key source, timeout, retry, stream setting, and import/worktree assertions.

## 13. Target P1 startup contract draft

```bash
EXPECTED_ASSISTANT_SHA=bbd90af42ba659684c25f1e9473c24804364548c
EXPECTED_CORE_SHA=28b502ca4f48e580d4941e095bb8dccc6f3e9682
ASSISTANT_ROOT=/private/tmp/mira-e2e-p0-assistant
CORE_ROOT=/private/tmp/mira-e2e-p0-core
MIRA_E2E_RUN_ROOT=/Users/admin/.julia_mira_e2e
MIRA_E2E_CONVERSATION_STORE=/Users/admin/.julia_mira_e2e/data/conversations.json
MIRA_DURABLE_AUTHORITY_ROOT=/Users/admin/.julia_mira_e2e/cache/durable-authority
BRAIN_HOST=127.0.0.1
BRAIN_PORT=18091
PROVIDER=deepseek
MIRA_DEEPSEEK_MODEL=deepseek-chat
MIRA_PROVIDER_TIMEOUT=60
MIRA_PROVIDER_MAX_RETRIES=0
MIRA_PROVIDER_STREAM=true
python voice_api/server.py --port 18091
```

The launcher must verify SHAs, module paths, run-root containment, canonical manifests, and port 18091 before `exec`. New P1 implementation commits require new expected SHAs.

## 14. P1 task DAG

1. Owner-gated durable canonical export.
2. Fail-closed durable Reader.
3. Canonical reconstruction/projection with exact manifest checks.
4. Explicit isolated ConversationRuntime.
5. C03 envelope-only provider transport.
6. Assistant experimental route composition.
7. Launcher and preservation harness.
8. One disposable synthetic real HTTP turn.
9. Electron P2 preparation.

## 15. Blockers and final disposition

```text
BLOCKER_1 = CANONICAL_RUNTIME_READ_PATH_NOT_DEPLOYABLE
BLOCKER_2 = EXPLICIT_CONVERSATION_STORE_PATH_REQUIRED
BLOCKER_3 = EXISTING_NATIVE_ROUTE_HARD_BINDS_OLD_JULIA_SESSION
BLOCKER_4 = C03_ENVELOPE_PROVIDER_TRANSPORT_REQUIRED
NEW_BRAIN_ADAPTER = NOT_REQUIRED
EXISTING_ASSISTANT_BRAIN = REUSABLE_AFTER_ISOLATED_COMPOSITION
FINAL_RESULT = PASS_WITH_BLOCKERS
```
