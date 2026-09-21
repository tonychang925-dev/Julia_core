# RD1 I5A — C03 Provider Cutover × I3 Evidence Join Architecture Preflight

**Task:** `RD1-I5A-P0-C03-PROVIDER-CUTOVER-I3-EVIDENCE-JOIN-PREFLIGHT`
**Date:** 2026-09-21
**Mode:** architecture preflight only
**Production code changed:** NO
**Status:** ready for Mira + Owner review; this document does not authorize implementation.

## 1. Exact Canonical Baselines

| Repository / reference | Required SHA | Verified remote `main` or object | Result |
|---|---:|---:|---|
| Julia-AI-Assistant | `ec20d4f2be6db09cfb63c8340777dcb1c76e4921` | `ec20d4f2be6db09cfb63c8340777dcb1c76e4921` | PASS |
| Julia_core | `bb35496b3ea4e2e8dd03da5dbb40756560378375` | `bb35496b3ea4e2e8dd03da5dbb40756560378375` | PASS |
| ai_theme_app | `5a38999623c2b9254865a37cbb3a7a7379d2a22e` | `5a38999623c2b9254865a37cbb3a7a7379d2a22e` | PASS |
| Historical Assistant donor | `ba0fa19948fba82a22a5cc5ab7d9d3d4af2090b7` | exact object retrieved | PASS |
| Accepted I5 blocker evidence | `4d1fb0da09b1638b3c0caeba795f7e65cfe3ac20` | Julia_core PR #142, unmerged | PASS |

The frozen constitution establishes Assistant → Core → Market/Research, prohibits private cross-component dependencies, and states that C03 carries tool result/evidence into model-visible Julia context without reinterpreting Market semantics (`docs/architecture/RD1_V1_ARCHITECTURE_CONSTITUTION_LITE.md:72`, `:141`, `:157`).

## 2. Current-Path Source Map

### 2.1 Assistant canonical transport edge

| Edge | Exact source | Classification |
|---|---|---|
| HTTP conversation route → `JuliaCoreAdapter` | `voice_api/conversation_routes.py:45`, `:71` | CANONICAL |
| `JuliaCoreAdapter` → Core public ingress | `voice_api/julia_core_adapter.py:41`, `:44` | CANONICAL |
| Assistant route → Assistant LLM | absent from canonical conversation route | FORBIDDEN / NOT WIRED |
| Assistant failure → synthetic answer | forbidden by Assistant authority | FORBIDDEN |

Assistant authority explicitly limits the repo to transport/session/presentation and requires `voice_api/* → JuliaCoreAdapter → julia_core.public.CoreConversationIngress` (`docs/authority/CURRENT_AUTHORITY.md:9`, `:66`, `:74`). Canonical transport files must not call `get_llm_provider`, `provider.chat`, or Market routing (`docs/authority/CURRENT_AUTHORITY.md:130`).

### 2.2 Core public conversation composition

| Edge | Exact source | Classification |
|---|---|---|
| `CoreConversationIngress` → `ConversationRuntime` | `julia_core/public/conversation.py:252`, `:253` | CANONICAL |
| Core registry lookup → production provider | `julia_core/public/conversation.py:254`, `:255` | CANONICAL |
| Empty production registry → `CoreConversationProviderUnavailable` | `julia_core/public/conversation.py:256`, `:257` | CANONICAL fail-closed |
| Runtime → `JuliaSession.process` cognitive function | `julia_core/public/conversation.py:291`, `:296` | CANONICAL |
| External request object → provider object through ingress | not a constructor/process field | FORBIDDEN |

The registry only resolves an explicitly registered object and never synthesizes one (`julia_core/providers/core_cognition.py:14`, `:17`, `:24`). No production registration path exists at the frozen Core main; accepted I5 evidence proved a fresh process resolves `production` to `None`.

### 2.3 Current I3 model ingress

| Edge | Exact source | Classification |
|---|---|---|
| `JuliaSession` → `ContextExecutionRuntime.prepare` | `julia_core/runtime/julia_session.py:266`, `:267` | CANONICAL Context OS binding |
| `CognitiveContextPackage` → rendered messages | `julia_core/runtime/context_execution_runtime.py:68`, `:299` | TRANSITIONAL |
| `JuliaSession` → `provider.chat(messages)` through prepared messages | `julia_core/runtime/julia_session.py:301`, `:302` | TRANSITIONAL |
| `IterativeReasoningLoop` → `provider.chat(messages)` | `julia_core/runtime/iterative_reasoning.py:151`, `:158` | TRANSITIONAL |
| Continuation projection → `package.to_messages` | `julia_core/runtime/iterative_reasoning.py:220`, `:234`, `:293` | TRANSITIONAL |
| Model result → strict structured capability request | `julia_core/runtime/iterative_reasoning.py:162`, `:195` | CANONICAL |
| Runtime → C08 manager execution → ToolResult | `julia_core/runtime/iterative_reasoning.py:212`, `:213` | CANONICAL |
| ToolResult/Evidence → structured evidence frame | `julia_core/runtime/context_execution_runtime.py:617`, `:625` | CANONICAL projection |
| Evidence frame → exact provider bundle | absent | UNWIRED |

The current package already maintains an ordered, append-only `turn_evidence_ledger` with validated `generation_id`, exact ToolResult view, and Evidence views (`julia_core/runtime/context_execution_runtime.py:645`, `:648`, `:653`, `:894`). That carrier is the strongest existing I3 semantic source, but it currently stops at `to_messages()` rendering.

### 2.4 Exact C03/C07 chain present in Core

| Edge | Exact source | Classification |
|---|---|---|
| Exact three inputs → `ExclusiveAdmissionGate` | `julia_core/context_admission/gate.py:41`, `:60`, `:63` | CANONICAL |
| Gate → `SealedCognitiveContextPackage` | `julia_core/context_admission/gate.py:82`, `:94` | CANONICAL |
| Sealed package → `ExactAdmittedSemanticBinder` | `julia_core/context_admission/semantic_binding.py:202`, `:205` | CANONICAL |
| Binder → exact three-unit `AdmittedSemanticBundle` | `julia_core/context_admission/semantic_binding.py:119`, `:141`, `:151` | CANONICAL |
| Bundle → `JuliaAssistantRuntime.prepare` | `julia_core/runtime/assistant_runtime.py:63`, `:71` | CANONICAL |
| Runtime → `ProviderAlignmentBoundary` | `julia_core/runtime/assistant_runtime.py:77` | CANONICAL |
| Boundary → exact `ProviderExecutionEnvelope` | `julia_core/alignment_os/adapter.py:36`, `:69`, `:78` | CANONICAL |
| Envelope → production `JuliaSession` | no caller from public conversation | UNWIRED |

Despite the historical name `JuliaAssistantRuntime`, this class physically resides in Core and adds no semantic authority (`julia_core/runtime/assistant_runtime.py:63`). `RuntimeTurnRequest` accepts only the exact bundle, provider ID, and input mode (`julia_core/runtime/assistant_runtime.py:11`).

### 2.5 Provider edges

| Edge | Exact source | Classification |
|---|---|---|
| Current Assistant `DeepSeekProvider.build_messages` → `ProviderBehaviorAdapter` | Assistant `providers/llm/deepseek_provider.py:34`, `:44` | LEGACY |
| `ProviderBehaviorAdapter` → arbitrary semantic adaptation | `julia_core/alignment_os/adapter.py:13`, `:19`, `:28` | FORBIDDEN fail-closed remnant |
| Provider → Persona/message reconstruction | forbidden by C-07 §4 | FORBIDDEN |
| Donor envelope-only `DeepSeekProvider` | donor `providers/llm/deepseek_provider.py:20`, `:66` | HISTORICAL / MECHANICS-REUSABLE |
| Donor route → direct provider | donor `voice_api/openai_compat.py:15`, `:16`, `:132` | LEGACY / DO NOT REPLAY |
| Core → Assistant private provider import | no permitted edge | FORBIDDEN |

C-07 requires canonical authorities → Context OS → CognitiveContextPackage → Alignment → ModelProvider and forbids provider-side retrieval or prompt assembly (`docs/architecture/C-07_MODEL_PROVIDER_CONTRACT.md:46`, `:49`, `:52`).

## 3. Authority-Conflict Table

| Conflict | Current fact | Architecture rule | Resolution |
|---|---|---|---|
| C03 projection versus exact admission | `CognitiveContextPackage.evidence_frame` is structured, but exact bundle admits only identity/experience/current task | ToolResult must re-enter through C03 and Alignment (`C-07 §11`) | Extend governed admission with an exact capability-evidence semantic carrier |
| Conversation authority versus evidence plane | `CurrentConversationalTaskContext.bounded_state` can theoretically contain arbitrary state | ConversationRuntime owns conversation state; capability evidence belongs to C08/C03 | Never launder ToolResult through bounded_state |
| Provider transport versus provider semantics | Current Assistant provider reconstructs messages | Provider is replaceable cognitive substrate only | Accept exact envelope only |
| Core registry versus Assistant startup | Assistant loads credentials and starts process; Core registry is empty | Assistant is transport edge; Core owns provider binding/composition | Core constructs exactly one configured provider without caller objects |
| Historical donor versus current architecture | Donor has useful envelope transport but stale bounded-state tool-result chain | No wholesale donor cherry-pick | Replay only transport mechanics under a new Core-owned contract |
| Model evidence versus final judgment | Provider sees evidence but does not own Julia conclusion | Julia remains cognition/final-judgment owner | Preserve structured evidence and Runtime/Conversation authority |

## 4. I3 Evidence Join Gap

`CAPABILITY_EVIDENCE_JOIN_GAP = CONFIRMED`.

The exact frozen bundle order is only `identity_frame_set`, `experience_frame_set`, and `current_task_context` (`julia_core/context_admission/semantic_binding.py:21`). `AdmittedSemanticBundle` requires exactly three units and that exact manifest (`julia_core/context_admission/semantic_binding.py:141`, `:146`). `ProviderExecutionEnvelope` likewise hard-codes three messages and roles system/system/user (`julia_core/alignment_os/contracts.py:262`, `:264`).

Therefore a provider cutover that only replaces `provider.chat(messages)` with an envelope-only donor would silently reduce I3 continuation to the base three-unit bundle. It would either drop `evidence_frame`/`turn_evidence_ledger` or require an unadmitted rendering path. Both outcomes violate C-07 §11.

## 5. Provider Ownership / Composition Analysis

| Arrangement | Evaluation | Verdict |
|---|---|---|
| A. Provider implementation lives in Core | Core owns registry, construction, credentials, transport, and typed failure; no reverse dependency | RECOMMENDED immediate arrangement |
| B. Separate provider package with Core-owned public composition seam | Architecturally valid and useful for multiple vendors, but no frozen separate package exists at this baseline | Valid future extraction, not required for I5 correction |
| C. Provider remains physically in Assistant and is injected by a new public startup contract | Still risks Assistant-owned cognition implementation and provider-object injection; violates current transport-only authority unless Assistant only passes configuration | REJECTED for I5 correction |
| D. Assistant route selects/calls provider | Re-creates direct cognition and second-answer architecture | FORBIDDEN |
| E. Core imports Assistant private provider | Reverse/private dependency | FORBIDDEN |

### Recommended composition rule

`RECOMMENDED_PROVIDER_OWNERSHIP = CORE_OWNED_TRANSPORT_MODULE_WITH_EXACTLY_ONE_COLD_START_CONFIGURATION`

For the immediate correction, Core should own a transport-only DeepSeek implementation and its composition root. A later Owner-approved slice may extract it to a separate package, provided:

1. the package exposes only a Core-facing public provider contract;
2. Core owns selection and registration;
3. no conversation request or route supplies a provider object;
4. no Core code imports package-private implementation;
5. exactly one configured provider is constructed.

### Cold-start rule

A fresh process must reach `_get_cognition_provider("production") != None` through a Core-owned initialization function invoked before any conversation ingress processes a turn. Initialization:

- reads typed deployment configuration/environment, never logs values;
- requires exactly one configured production provider;
- fails typed and terminally on absent credentials/configuration/dependency;
- constructs and registers the provider only once;
- does not create fallback, mock, shadow, or default providers;
- does not accept provider objects through `CoreConversationIngress` or HTTP routes.

Assistant may remain the process host and load a private environment file, but it may pass only configuration/initialization authority to Core's public lifecycle seam. Current Assistant launch already checks credential presence and importability but performs no Core registration (`deploy/mac/start-brain-18089:9`, `:17`, `:53`, `:57`). Its FastAPI lifespan only calls Core shutdown (`voice_api/server.py:35`, `:41`); it never initializes cognition.

## 6. Historical Donor Reuse Matrix

| Donor mechanic | Source | Replay verdict |
|---|---|---|
| Exact envelope type check: `type(envelope) is ProviderExecutionEnvelope` | donor provider `:20`, `:21` | REUSE |
| `envelope.verify()` before payload/network | donor provider `:36`, `:59`, `:74`, `:87` | REUSE |
| Payload copies only `envelope.messages` | donor provider `:48`, `:50` | REUSE after envelope v2 supports incremental evidence |
| Payload maps `alignment.max_output_tokens` | donor provider `:47`, `:51` | REUSE |
| Optional alignment temperature/response format | donor provider `:53`, `:55` | REUSE |
| Missing API key fails before network | donor provider `:62`, `:64` | REUSE |
| Sync timeout 60 seconds | donor provider `:75` | REUSE unless Owner changes SLO |
| Stream timeout 60/15 seconds and malformed-event rejection | donor provider `:85`, `:107`, `:109` | REUSE |
| No Persona, history retrieval, provider prompt reconstruction, or fallback terms | donor tests `tests/test_p3_n1_provider_transport.py:336`, `:339` | REUSE invariant |
| Three-message hard-coded envelope shape | donor historical envelope contract | DO NOT REPLAY unchanged; v2 must represent incremental evidence |
| Provider physically under Assistant private module | donor/current Assistant layout | DO NOT REPLAY |
| OpenAI-compatible route directly selecting/calling provider | donor `voice_api/openai_compat.py:16`, `:132`, `:146` | DO NOT REPLAY |
| `tool_results` placed in `CurrentConversationalTaskContext.bounded_state` | donor `runtime/canonical_turn.py:65`, `:108`, `:112` | DO NOT REPLAY |
| Caller-supplied canonical frames at HTTP boundary | donor `voice_api/openai_compat.py:63`, `:86` | DO NOT REPLAY |
| Old Core SHA coupling and donor branch composition | donor tests pin `40616570...` | DO NOT REPLAY |
| Wholesale file cherry-pick | prohibited | DO NOT REPLAY |

The donor transport tests prove message preservation, exact-type rejection, alignment-only payload, fail-before-network credentials, and mutation rejection (`tests/test_p3_n1_provider_transport.py:40`, `:63`, `:72`, `:182`, `:201`). Those are non-semantic mechanics, not architecture authorization.

## 7. Candidate Architecture Options

### Option A — Add capability-evidence unit to the existing admitted bundle

| Property | Assessment |
|---|---|
| Authority owner | Core C03 gate/binder; capability evidence remains derived from ToolResult/Evidence |
| Provenance source | exact ToolResult view + resolved Evidence views + turn/generation/call/correlation IDs |
| Market/Research semantics | can preserve exact structured views without domain normalization |
| Conversation authority | no mutation if bounded_state remains untouched |
| C-07 §11 | satisfies incremental C03 → Alignment path |
| I3 ordered ledger | can serialize ledger as an additional unit |
| Contract changes | `ExclusiveAdmissionRequest`, sealed manifest, binder order, bundle cardinality, envelope roles/fingerprint |
| Compatibility risk | changes every no-evidence base turn; v1 donor transport and all three-unit tests become incompatible |
| Verdict | architecture-valid but more invasive |

### Option B — Separate exact incremental-evidence admission composed with base bundle — RECOMMENDED

| Property | Assessment |
|---|---|
| Authority owner | Core C03 incremental gate/binder; base bundle and evidence plane remain separate |
| Provenance source | one exact `CapabilityEvidenceSet` built from current projection: ordered `turn_evidence_ledger`, ToolResult view, resolved Evidence views, generation lineage |
| Market/Research semantics | copy/serialize exact typed views; no domain re-authoring |
| Conversation authority | no ConversationRuntime mutation and no bounded_state use |
| C-07 §11 | exact base C03 plus exact incremental C03 feed one Alignment/Provider execution |
| I3 ordered ledger | ledger is the canonical order source; entries remain inspectable by generation/call/evidence IDs |
| Contract changes | new exact evidence input/set/receipt/bundle; composition request accepting base + optional incremental bundle; ProviderExecutionEnvelope v2 with both fingerprints |
| Compatibility risk | envelope v1 donor needs a narrow adapter; base bundle remains stable |
| Verdict | RECOMMENDED |

The no-evidence first pass can continue to use the exact base bundle. Pass N+1 receives base semantics plus the separately sealed incremental evidence bundle. Alignment cannot select, summarize, drop, or reinterpret evidence; Context OS performs any required budgeting before admission, consistent with C-09 (`docs/architecture/C-09_ALIGNMENT_CONTRACT.md:25`, `:43`, `:51`).

### Option C — Put evidence in `CurrentConversationalTaskContext.bounded_state`

REJECTED. This launders capability evidence through Conversation authority, obscures the difference between conversation state and tool observation, and cannot preserve an explicit I3 evidence ledger/correlation contract without overloading `bounded_state`. Historical donor use of this route is evidence of the risk, not permission.

### Option D — Reuse rendered `CognitiveContextPackage` evidence text outside exact admission

REJECTED. Rendering is representation, not admission. `to_messages()` explicitly labels itself transitional (`julia_core/runtime/context_execution_runtime.py:68`, `:69`). Bypassing exact admission would permit silent truncation/drop, lose sealed lineage, and conflict with C-07 §11's prohibition on direct `messages.append(tool_result)`.

## 8. Recommended Architecture

1. Preserve the existing base three-unit admission chain unchanged for pass 1.
2. Define an exact Core `CapabilityEvidenceSet` carrier from the already validated I3 projection:
   - ordered `turn_evidence_ledger`;
   - exact ToolResult view with status, provider, schema version, structured output reference/shape, and correlation IDs;
   - resolved Evidence views with evidence IDs, source refs, provenance, observed/retrieved times, and integrity metadata;
   - parent/base package and projection generation lineage;
   - explicit distinction between evidence and control projections.
3. Seal and bind that set through a separate exact incremental-evidence gate/binder; never mutate `CurrentConversationalTaskContext.bounded_state`.
4. Create `ProviderExecutionEnvelope.v2` from `(base AdmittedSemanticBundle, optional AdmittedIncrementalEvidenceBundle)`:
   - base semantic fingerprint;
   - incremental evidence fingerprint when present;
   - immutable ordered semantic units;
   - no provider-side reconstruction;
   - verification of both receipts and combined fingerprint.
5. Replace production `provider.chat(messages)` with a Core `ModelProvider.execute(envelope)`-style exact ingress; streaming and non-streaming implement the same contract.
6. Implement a Core-owned transport-only DeepSeek provider for the immediate correction, replaying only the donor mechanics listed above.
7. Add Core cold-start initialization before serving; Assistant remains process/transport host and supplies no provider object.
8. Rerun exact Issue #140 Market-only A/B acceptance only after the above slices pass focused contract tests.

This recommendation follows C-07's same-turn generation model: G1 base → structured call → C08 → ToolResult → C03 → G2 provider continuation (`docs/architecture/C-07_MODEL_PROVIDER_CONTRACT.md:126`, `:130`).

## 9. Explicit Owner Decisions Still Required

Already determined by frozen architecture, no new Owner decision required:

- reject `bounded_state` evidence laundering;
- reject rendered-evidence bypass;
- reject provider-side Persona/message reconstruction;
- reject Core → Assistant private import;
- reject Assistant route-level provider calls and fallback;
- require ToolResult/Evidence re-entry through C03 before Alignment;
- require fail-closed provider configuration and no fallback;
- preserve Market and Research typed semantics unchanged.

Owner must approve:

1. recommended Option B versus Option A;
2. exact `ProviderExecutionEnvelope.v2` shape, message-role policy, and combined fingerprint algorithm;
3. whether the immediate provider implementation remains a Core module or is extracted to a separate package before implementation;
4. evidence budget/compaction policy and maximum serialized shape, provided budgeting remains in Context OS before admission;
5. sequencing and rollout of transitional `to_messages()` retirement.

This document's recommendation is not implementation authorization.

## 10. Exact Implementation Slices After Approval

1. **C03 evidence contract slice:** define exact `CapabilityEvidenceSet`, incremental admission request/receipt/binder, and envelope v2 composition. Contract/sabotage tests first; no runtime cutover.
2. **Projection join slice:** convert current validated `project_tool_result()` output into the exact incremental carrier without changing Market/Research types or Conversation authority.
3. **Provider contract slice:** change Core production provider ingress to exact envelope execution and add typed transport/configuration failures; no provider implementation yet.
4. **Core DeepSeek transport slice:** implement only donor-approved mechanics in Core; prove credential fail-closed, exact envelope acceptance, payload mapping, timeout/error handling, and stream/non-stream parity.
5. **Cold-start slice:** add one-shot Core initialization and wire the canonical Assistant process entrypoint to that public lifecycle seam; no provider object crosses conversation ingress.
6. **Runtime cutover slice:** replace `JuliaSession`/I3 `provider.chat(messages)` with exact envelope execution and preserve strict structured response parsing.
7. **Continuation slice:** build pass N+1 from base bundle plus all prior exact evidence entries; maintain duplicate/budget/control semantics and 7-pass/6-execution bounds.
8. **I5 rerun slice:** execute Issue #140 Acceptance A and B exactly against the original query and canonical ledger proof.

## 11. Acceptance Matrix For Later Implementation

| Acceptance | Required proof |
|---|---|
| Exact evidence admission | evidence source objects are exact types; forged/stale/duplicate/partial evidence fails closed |
| Ordered continuity | all prior evidence entries remain in generation order and resolve to canonical ToolResult/Evidence IDs |
| C03 composition | base receipt and incremental receipt are verified before provider execution |
| No authority laundering | `CurrentConversationalTaskContext.bounded_state` has no capability evidence fields |
| No semantic reconstruction | provider source contains no Persona/history retrieval/system prompt assembly/ProviderBehaviorAdapter use |
| Market fidelity | Market envelope `operation_status`, `data_state`, payload, failures, provenance, and runtime observation remain structurally unchanged |
| Research fidelity | `PARTIAL` with `findings=[]`, sources, limitations, and provenance remains unchanged |
| Controls remain controls | authorization, duplicate, decode failure, retry, and budget frames never enter evidence ledger |
| Multi-pass lineage | up to 7 cognition passes / 6 capability executions retains all evidence and pass/generation links |
| Provider cold start | fresh process registers exactly one real configured provider or returns typed unavailable; no fallback/mock/synthetic success |
| Transport parity | stream and non-stream consume the same verified envelope semantics |
| Assistant boundary | canonical routes import only Core public ingress and never select/call a provider |
| I5 acceptance | exact Market-only user flow passes canonical call/result/evidence ledger proof with zero `research.*` calls |

## 12. Non-Goals / Forbidden Shortcuts

- No production runtime change in this preflight.
- No provider registration, mock, fixture, fallback, or synthetic success.
- No direct `ToolResult → Conversation bounded_state`.
- No provider-side Persona or message reconstruction.
- No Core import from Assistant private modules.
- No wholesale donor file/branch cherry-pick.
- No reuse of donor caller-supplied frames or direct OpenAI-compatible provider route.
- No raw rendered evidence text outside exact admission.
- No Market or Research semantic normalization.
- No destructive retirement of transitional surfaces in this task.
- No merge, release, or deployment.

## 13. Source Evidence Index

- `docs/architecture/RD1_V1_ARCHITECTURE_CONSTITUTION_LITE.md`
- `docs/architecture/C-07_MODEL_PROVIDER_CONTRACT.md`
- `docs/architecture/C-09_ALIGNMENT_CONTRACT.md`
- `julia_core/context_admission/contracts.py`
- `julia_core/context_admission/gate.py`
- `julia_core/context_admission/semantic_binding.py`
- `julia_core/alignment_os/adapter.py`
- `julia_core/alignment_os/contracts.py`
- `julia_core/runtime/assistant_runtime.py`
- `julia_core/runtime/context_execution_runtime.py`
- `julia_core/runtime/iterative_reasoning.py`
- `julia_core/runtime/julia_session.py`
- `julia_core/providers/core_cognition.py`
- `julia_core/public/conversation.py`
- Assistant `docs/authority/CURRENT_AUTHORITY.md`
- Assistant `providers/llm/deepseek_provider.py`
- Assistant donor `providers/llm/deepseek_provider.py`
- Assistant donor `runtime/canonical_turn.py`
- Assistant donor provider/e2e tests
- Issue #140 / PR #142 evidence candidate `4d1fb0da09b1638b3c0caeba795f7e65cfe3ac20`
- Continuity/cold-start artifacts confirming the canonical launcher reaches transport import checks but not provider registration, and historical audits mark provider binding as Core-owned.

## 14. Preflight Result

`ARCHITECTURE_PREFLIGHT_READY_FOR_OWNER_REVIEW`
