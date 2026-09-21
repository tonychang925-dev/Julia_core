# RD1 I5 First Real Market-only User E2E — 2026-09-21

## Result

`BLOCKED_CORE_COGNITION_PROVIDER`

The exact primary query was executed through the real Assistant ASGI conversation route. Core ConversationRuntime started, but no production cognition provider was registered in a fresh exact canonical process. For a diagnostic-only composition, the harness registered the canonical Assistant `providers.llm.deepseek_provider.DeepSeekProvider` through Core's explicit production registry entry. That real provider is incompatible with Core C03: its `build_messages()` calls the fail-closed legacy `ProviderBehaviorAdapter`, which raises `C03AdmissionRejected` before a model request. No provider replacement or compliant wrapper was introduced.

- Primary query: `查一下 600519 今天的行情`
- Acceptance A: `BLOCKED_CORE_COGNITION_PROVIDER`
- Acceptance B: `BLOCKED_CORE_COGNITION_PROVIDER` (not executed after A's pre-model provider failure)
- Final result: `BLOCKED_CORE_COGNITION_PROVIDER`
- Market-only execution: no Market capability was invoked and no Research provider or call was used.

## Canonical Baselines

| Repository | Required main SHA | Verified remote `origin/main` | Fresh worktree HEAD | Result |
|---|---:|---:|---:|---|
| Julia-AI-Assistant | `ec20d4f2be6db09cfb63c8340777dcb1c76e4921` | `ec20d4f2be6db09cfb63c8340777dcb1c76e4921` | `ec20d4f2be6db09cfb63c8340777dcb1c76e4921` | PASS |
| Julia_core | `bb35496b3ea4e2e8dd03da5dbb40756560378375` | `bb35496b3ea4e2e8dd03da5dbb40756560378375` | `bb35496b3ea4e2e8dd03da5dbb40756560378375` | PASS |
| ai_theme_app | `5a38999623c2b9254865a37cbb3a7a7379d2a22e` | `5a38999623c2b9254865a37cbb3a7a7379d2a22e` | `5a38999623c2b9254865a37cbb3a7a7379d2a22e` | PASS |

## Preflight

| Check | Result | Safe detail |
|---|---|---|
| Assistant exact-source import | PASS | imported from the fresh Assistant worktree |
| Core exact-source import | PASS | imported from the fresh Core worktree |
| Market exact-source import | PASS | imported from the fresh Market worktree |
| Core production cognition registry before composition | ABSENT | `_get_cognition_provider("production")` returned `None` |
| Diagnostic production provider after explicit registration | PRESENT | canonical Assistant `DeepSeekProvider`, real provider class |
| Production cognition credential | PRESENT | `DEEPSEEK_API_KEY` present; value not recorded |
| Fresh conversation data directory | PASS | `/private/tmp/rd1_i5_market_only_e2e_20260921_0925/data_A` |
| Core public ingress composition | NONE | no composition error after diagnostic provider registration |
| Market public factory binding | PASS | `MarketPublicProviderAdapter` owned the `market` provider namespace |
| Real Market PostgreSQL backend | PASS | bounded read-only `SELECT 1` passed against Market's configured real backend |
| Research provider | ABSENT | no Research provider configured or registered |

Market capabilities available in the canonical registry:

| Capability ID | Provider | Registry status |
|---|---|---|
| `market.event.resolve` | `market` | `CapabilityStatus.AVAILABLE` |
| `market.event.read` | `market` | `CapabilityStatus.AVAILABLE` |
| `market.product.read` | `market` | `CapabilityStatus.AVAILABLE` |
| `market.product.linkage.read` | `market` | `CapabilityStatus.AVAILABLE` |
| `market.state.read` | `market` | `CapabilityStatus.AVAILABLE` |

The provider failure occurred before model selection. Therefore this evidence does not classify the failure as `BLOCKED_PRODUCT_CAPABILITY_GAP` and does not claim whether Julia could or could not select a Market capability for this query.

## Acceptance A — Real ASGI Route

Fresh process, real `voice_api.server.create_app()`, real ASGI HTTP transport, real Core public ingress, real ConversationRuntime, real Market binding, and diagnostic-only canonical Assistant DeepSeek provider registration.

### Create Conversation

| Field | Value |
|---|---|
| HTTP method/path | `POST /internal/v1/conversations` |
| Request title | `RD1 I5 Acceptance A` |
| HTTP status | `200` |
| Conversation ID | `conv_i5_a_061b50bcd4f4` |
| Started at | `2026-09-21T17:48:00.766279+08:00` |
| Completed at | `2026-09-21T17:48:00.905271+08:00` |
| Result | PASS |

### Turn

| Field | Value |
|---|---|
| HTTP method/path | `POST /internal/v1/conversations/conv_i5_a_061b50bcd4f4/turns` |
| Exact input | `查一下 600519 今天的行情` |
| Modality | `text` |
| Stream | `false` |
| Turn ID | `turn_i5_a_51a2b8171121` |
| HTTP status | `200` |
| Response status | `failed` |
| Response content | empty |
| Started at | `2026-09-21T17:48:00.905305+08:00` |
| Completed at | `2026-09-21T17:48:00.967442+08:00` |
| Failure stage | before first remote model request |

Core logged the exact causal failure as `Cognitive pipeline failed for conv_i5_a_061b50bcd4f4/turn_i5_a_51a2b8171121: providers cannot adapt arbitrary messages or persona prompts`. The observable path is canonical Assistant `DeepSeekProvider.build_messages()` → Core `ProviderBehaviorAdapter.adapt_messages()` → `C03AdmissionRejected`. No model response class or content exists.

### Canonical Ledger

| Ledger | Baseline | Delta | New records |
|---|---:|---:|---|
| `manager.capability_calls` | 0 | 0 | none |
| `manager.tool_results` | 0 | 0 | none |
| `manager.canonical_evidence` | 0 | 0 | none |

New CapabilityCalls: none.

New ToolResults: none.

New canonical Evidence: none.

- New capability call count: 0
- New `market.*` call count: 0
- New `research.*` call count: 0
- Market ToolResult count: 0
- Market Evidence count: 0
- C03 continuation before final answer: `BLOCKED_CORE_COGNITION_PROVIDER`
- Final Assistant response: `failed`, empty
- Assistant second LLM generation: NO
- Assistant Market router: NO
- Direct Market invocation as user-flow substitute: NO

## Acceptance B — Loopback Transport

Not executed. Required pre-model production cognition composition had already failed in Acceptance A. Starting a second server would repeat the same blocker and could not produce a truthful Market-only PASS.

## Integrity Attestations

- Mock used: NO
- Fixture Market used: NO
- Fake LLM used: NO
- Fallback used: NO
- Synthetic success used: NO
- Provider or route monkeypatch used: NO
- Production repository code changed: NO
- Research provider or substitute used: NO
- Market backend configured and reachable: YES
- Market-owned tool/evidence produced: NO, blocked before model cognition
- Temporary harness location: `/private/tmp/rd1_i5_market_only_e2e_20260921_0925/`
- Credentials, tokens, passwords, DSNs, cookies, and private keys: not included

## Conclusion

At the bound canonical baselines, Core exposes a production registry resolver but no canonical process composition registers a C03-compatible real production cognition provider. The available canonical Assistant DeepSeek implementation retains legacy provider-side semantic adaptation, which Core now correctly rejects as a C03 semantic-authority violation. Execution stopped without production code changes or a substitute provider. A separate production composition task must bind a real C03-compatible provider before the exact I5 Market-only user E2E can be rerun.
