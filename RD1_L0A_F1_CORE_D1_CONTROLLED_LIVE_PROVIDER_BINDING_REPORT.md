# RD1-L0A-F1 Core D1 Controlled-Live Provider Binding Report

## AGENT

GLM-A

## TASK

RD1-L0A-F1 CORE D1 CONTROLLED-LIVE PROVIDER BINDING

## CORE_BASE_SHA

d11aff6b84138c2e297c475582c1525e5919f9ef

## CORE_IMPLEMENTATION_SHA

f85b7b86b2b55f5f07564419f0ae01335fea7404

## D1_SOURCE_SHA

b8ae48a9972ba5bf2f0e4b1db5a1025e38e97e82

## Provider Binding Path

`CapabilityManager`
→ `D1ResearchBridgeProvider.execute_bound(request, capability_call)`
→ pinned one-shot `D1SubprocessTransport`
→ frozen D1 `research.bridge.request.v1` / `research.bridge.response.v1`
→ `project_d1_response()`
→ `ProviderExecutionOutcome`
→ existing `CapabilityManager` `ToolResult`
→ existing `ResearchEvidenceNormalizer`

The manager continues to use its single authorization/call/result spine. The only addition is an optional concrete-provider method that receives the already-created runtime `CapabilityCall` identity required by D1-F1 runtime content bindings.

## D1_EXECUTABLE_PIN

Deployment-configured by:

- `JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE`
- `JULIA_D1_RESEARCH_BRIDGE_SHA256`

The path must resolve to an executable file and its SHA-256 must match exactly before health or execution can succeed.

## CONFIG_REQUIRED

- `JULIA_D1_SOURCE_SHA` — must equal `b8ae48a9972ba5bf2f0e4b1db5a1025e38e97e82`
- `JULIA_D1_RESEARCH_BRIDGE_EXECUTABLE`
- `JULIA_D1_RESEARCH_BRIDGE_SHA256`
- `CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET`
- `CLAUDE_CLIENT_EXECUTION_SOURCE_FD`
- `CLAUDE_CLIENT_EXECUTION_SOURCE_PATH`
- `CLAUDE_CLIENT_EXECUTION_MAX_ROOT`
- `CLAUDE_CLIENT_WEBFETCH_NETWORK_AUTHORITY_JSON`

Partial configuration leaves the provider unbound and capability execution remains typed UNAVAILABLE.

## Binding Behavior

- Accepts only exact `research.event.enrich`.
- Builds only the frozen D1 request contract.
- Launches the pinned executable once per capability call.
- Preserves D1 semantic and observation truth planes separately.
- Projects successful runtime-observed content with exact request/call IDs and immutable digest refs.
- Returns a `ProviderExecutionOutcome`; no provider code mints `verification_state`.
- Keeps `ResearchEvidenceNormalizer` as the sole C1 verification authority.

## Retry / Fallback / Ambiguity

- Provider retry count: 0
- Fallback count: 0
- D1 response retry count must be 0.
- D1 response fallback count must be 0.
- Timeout, nonzero execution policy, invalid framing, or ambiguous transport state returns typed UNAVAILABLE, preserves request/response truth, and performs no second execution.

Cancellation propagates through the Core provider/manager boundary and terminates the local one-shot transport attempt. No external provider transport abort is claimed.

## Production Files

- `julia_core/capability/manager.py`
- `julia_core/runtime/capability_bridge.py`
- `julia_core/research/d1_provider.py`
- `tests/research/test_l0a_f1_core_d1_provider_binding.py`

No Market, Voice, Julia_client, D1 repository, C1 schema, C2 schema, or Assistant files were changed.

## Tests

- Focused L0A-F1: `/opt/miniconda3/bin/python -m pytest tests/research/test_l0a_f1_core_d1_provider_binding.py -q` — 9 passed.
- Core C1/C2/L0A: `/opt/miniconda3/bin/python -m pytest tests/research/test_c1_research_event_enrichment.py tests/research/test_c2_preliminary_research_judgment.py tests/research/test_l0a_f1_core_d1_provider_binding.py -q` — 66 passed.
- Capability regressions: `/opt/miniconda3/bin/python -m pytest tests/capability -q` — 166 passed, 11 xfailed.
- I1/I4 same-turn regressions: `/opt/miniconda3/bin/python -m pytest tests/runtime/test_i1_streaming_capability_continuation.py tests/runtime/test_i4_same_turn_research_orchestration.py -q` — 15 passed.
- Cognition/review regressions: `/opt/miniconda3/bin/python -m pytest tests/review tests/runtime/test_c1_rev2_sync_stream_authority.py tests/runtime/test_c1_rev2_cognitive_boundary.py tests/runtime/test_no_fallback_hardening.py -q` — 263 passed, 2 skipped, 6 xfailed.
- Compile/whitespace: `/opt/miniconda3/bin/python -m compileall -q <changed modules>` and `git diff --check` — passed.

## Proven

- F1 binding reachable through existing provider registration and manager.
- F2 exact `research.event.enrich` only.
- F3 projected D1 provider output enters the existing C1 normalizer.
- F4 provider emits no verification state; C1 alone mints `SOURCE_VERIFIED`, `REPORT_ONLY`, `NOT_PROVEN`, or `BLOCKED`.
- F5 retry is zero and nonzero D1 retry fails closed.
- F6 fallback is zero and nonzero D1 fallback fails closed.
- F7 Core-boundary cancellation propagates.
- F8 ambiguous/stopped D1 execution returns typed UNAVAILABLE without success fabrication.
- F9 changed-file scope contains no Voice/Client/Market edits.

## Not Proven

- Live executable or live network execution.
- External provider child transport abort.
- Deployment secret rotation or source-FD lifecycle management.

## Architecture Deviations

- NONE

The binding adds one concrete provider and a narrow runtime-call identity handoff on the existing manager spine. It adds no workflow engine, generic provider family, result family, fallback path, or verification authority.

## Blockers

- NONE

## Verdict

PASS
