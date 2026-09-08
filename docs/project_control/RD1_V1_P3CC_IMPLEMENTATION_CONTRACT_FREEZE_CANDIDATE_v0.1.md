# D3 — RD1 V1 P3-CC Implementation Contract Draft v0.1

**Status**: DRAFT — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Task**: RD1-V1-P3CC-A1 (§20 deliverable; execute after governance freeze of D2)
**Date**: 2026-09-08
**Auditor**: 朱婉清 (Julia)

```text
task_id
= RD1-V1-P3CC-IMPL (proposed; final id assigned at freeze)

repo_full_name
= tonychang925-dev/Julia_core

implementation_base_sha
= BLOCKED_PENDING_GOVERNANCE_FREEZE
  (must equal the then-current governed base; c14f6aa is the audited M1 base,
   but the implementing agent MUST re-verify HEAD and MUST NOT silently use
   main/latest/HEAD or a dirty tree)
```

---

## 1. Governance Preconditions (hard gates — none satisfied by this draft)

```text
GATE-1 RESEARCH_COMPOSITE_AUTHORITY_DECISION = FROZEN (D2 §7)
GATE-2 P3-CC CONTRACT v0.3 promoted from DRAFT at governed repo path
GATE-3 Upstream compatibility recheck = PASS
GATE-4 Fresh governed implementation authorization from Tony
```

If any gate is open: `IMPLEMENTATION_AUTHORIZED = NO`.

---

## 2. Allowed Paths (exact scope)

```text
julia_core/runtime/context_execution_runtime.py   (capability-frame/encoding +
                                                   remove market-intent prefetch)
julia_core/alignment/… (new governed module; C-09 seam: CapabilityFrame →
                        provider capability encoding; native-schema OR text
                        protocol, per ProviderAdaptationProfile)
julia_core/runtime/julia_session.py                (remove F1 keyword admission;
                                                   stream/non-stream parity;
                                                   C2 instruction via C-03)
julia_core/runtime/capability_bridge.py            (retire requires_tool semantic
                                                   authority; detect_tool_call as
                                                   decode adapter; manifest→
                                                   Alignment source)
julia_core/runtime/research_continuation.py        (only under frozen composite
                                                   authority; ambiguity path)
julia_core/capability/registry.py or frozen registry additions (composite
                                                   capability, if freeze so decides)
tests/…                                            (new/updated tests per §6)
docs/project_control/P3_CC_…  (freeze record + this contract promoted)
```

## 3. Forbidden Paths (hard prohibition)

```text
julia_core/reasoning/intents/market_brief.py        (no new pre-cognitive use)
julia_core/runtime/workflow_router.py               (no semantic dispatch)
Market/D1 provider composition, Market SHA pins, Market tree digest
market.event.resolve / market.event.read contracts (downstream frozen spine)
Assistant, Client, Voice, database data, provider/model config
new SemanticRouter / regex router / LLM-classifier-as-Runtime-router
any retry/fallback on the controlled critical Research path
port 18090, canonical R10 live, external D1 live calls during implementation
generic workflow engine; portfolio/trade/position advice features
```

## 4. Required Behavior

1. Every model-visible capability representation flows `CapabilityRegistry →
   CapabilityFrame → Alignment → provider-compatible encoding → ModelProvider`
   (C-09 §12). Same logical manifest representable as native tool schema OR
   text protocol per provider support; Alignment adapts representation only,
   never semantic intent.
2. Model capability output (`ModelInferenceResult.capability_requests[]` or
   decoded text-protocol call) is the ONLY entry to capability execution, plus
   explicit deterministic commands (C-00 §6 exception).
3. Runtime validates (exists/schema/permission/availability/side-effect),
   authorizes, executes via CapabilityManager, records Evidence; ToolResult+
   Evidence re-enter Context OS; typed failures stay typed.
4. Research chain executes under the frozen composite authority (D2) with
   per-sub-call authorization/trace preserved; ambiguity returns to cognition.
5. Stream and non-stream share one capability-selection lifecycle.
6. C2 schema instruction renders through the package (control_frame or
   Alignment), never appended after Context OS rendering.
7. External-claim grounding rule is model-visible (C-12 §4).

## 5. Forbidden Behavior

```text
keyword/regex semantic admission of natural language
requires_tool() deciding tool need; retry-coercing a tool call
WorkflowRouter / MarketBriefIntentResolver pre-cognitive dispatch
pre-cognitive market-evidence prefetch keyed on user-text keywords
two simultaneously authoritative semantic routers at any migration instant
Runtime reinterpreting the Research objective
synthetic success / mock reachability / hidden fallback / persona-text success
on capability failure
model-visible material appended outside Context OS
history rewrite of M1/RD1 PASS results
```

## 6. Tests (new + existing to re-run)

Existing anchors: `test_l1_f2_*` (deterministic ingress — to be inverted as
legacy after cutover), `test_i4_same_turn_research_orchestration.py`,
`test_i1_streaming_capability_continuation.py`,
`test_c1_rev2_cognitive_boundary.py` (A-01 XFAILs to flip),
`test_c1_rev2_sync_stream_authority.py` (parity XFAILs to flip),
`test_r2_p3_2_3b_session_wiring.py`, `test_r2_p3_context_os_typed_projection.py`,
`test_c2_preliminary_research_judgment.py`.

New tests per qualification corpus (§7). Historical tests asserting keyword
admission as intended (L1-F2) are updated ONLY in the governed cutover step,
never deleted silently.

## 7. Qualification Corpus (task §22)

Expected per case: model decision → Runtime action → capability activity →
evidence → final response constraint.

| # | Input | Model decision | Runtime action | Capability activity | Evidence | Final response constraint |
|---|---|---|---|---|---|---|
| A | "你查一下7/19日 阿里qwen3.8发布对市场的影响" | recognize Research need; request governed Research capability | validate/authorize; run composite (D2) | resolve→read→enrich→C1→C2→brief (event matching 7/19 qwen3.8) | per-step ToolResult/Evidence + brief | factual brief grounded in evidence; no trading advice |
| B | canonical R10 Token 出海 (expected event 215257) | request Research | same composite | same chain | event 215257 identity + evidence | brief w/o trading advice; event_id traceable |
| C | explicit Research + "不要给交易建议" | request Research (negation scopes advice, not research) | composite | full chain | full | brief + explicit no-advice framing |
| D | "不要调用研究、市场或语音能力，我们只聊架构" | decide NO capability | none (no semantic gate to override) | none | none | ordinary architecture conversation |
| E | ordinary market/model discussion | may choose no capability | none | none | none | model answer; no forced Research |
| F | ambiguous intent | request clarification or no capability | no guess | none | none | clarifying question allowed |
| G | explicit deterministic command (where allowed) | n/a | deterministic route | per command | per command | per command contract |
| H | malformed capability protocol | n/a | typed INVALID_REQUEST | none | none | typed failure, no raw tool text |
| I | unknown capability | n/a | UNKNOWN control-frame projection | none | none | typed |
| J | unavailable provider | n/a | typed UNAVAILABLE | none | none | typed; no fabricated result |
| K | model emits no capability | no capability | accept; no retry coercion | none | none | normal answer |
| L | model emits Research capability | Research request | composite (D2) | full chain | full | brief grounded |
| M | external-lookup claim w/o Evidence | — | — | — | absent | must be phrased as unverified/inference; never "I checked" |
| N | stream vs non-stream equivalent request | identical selection semantics | identical lifecycle | identical | identical | identical class of response |

## 8. Migration Order (build → prove → cut → retire; no deletion-first)

```text
1. CapabilityFrame → Alignment capability encoding (+ structured catalog source/provenance)
2. Prove model-owned capability-request production (native + text protocol)
3. Non-authoritative controlled corpus qualification (A3; routing authority = 0)
4. Freeze Research composite authority (D2 record) — HARD PREREQUISITE for 5
5. Cut Research ingress authority (disable F1 keyword admission; model-selected entry)
6. Remove Runtime semantic requires_tool authority (+ retry coercion)
7. Remove WorkflowRouter/MarketBriefIntentResolver semantic authority
8. Converge stream/non-stream semantics (single lifecycle; research chain reachable from both)
9. Route C2 model-visible schema through C-03/C-09
10. Canonical acceptance (fresh conversation; see §9)
```

## 9. Acceptance Evidence

Capture per §18 of P3-CC contract draft v0.3: conversation_id, turn_id, user
input digest, context_package_id, capability catalog/version, alignment
profile/version, provider/model/version, generation ids, model-emitted logical
capability request, capability_request_id, authorization decision,
capability_call_id, research sub-call identities, Market event identity, D1
provenance, C1 refs, C2 judgment_id, Research Brief id, ToolResult/evidence
refs, G2 id, assistant message id, structured product digest, restart readback.
Prove zero: RUNTIME_SEMANTIC_KEYWORD_ADMISSION, SEMANTIC_ROUTER_FALLBACK,
SYNTHETIC_SUCCESS, CRITICAL_FALLBACK.

## 10. NCF Requirements / Rollback / Fail-Closed

```text
NCF gate re-run at each step; P0/P1 = REJECT.
RETRY = 0, FALLBACK = 0, MOCK/FIXTURE reachable = 0, LEGACY_AUTHORITY_FALLBACK = 0
   on the controlled critical Research path.
Rollback: each migration step lands behind a governed flag/commit boundary;
   regression to the last frozen commit must not resurrect a dual semantic
   authority. Ambiguity and typed failures never become persona success text.
```

## 11. Authorization

```text
owner_authorization_required = YES (Tony; fresh per implementation phase)
merge_authorization_required = YES (governance freeze + merge gate)
push/release = NOT AUTHORIZED by this draft
```

---

## 12. A2 Freeze-Review Closure (recorded correction, 2026-09-08)

> Added during RD1-V1-P3CC-A2 packaging so the freeze candidate explicitly
> satisfies A2 §6-§8. Candidate position only; no freeze, no implementation
> authority. Recorded in `A2_CORRECTION_LOG.md` (local deliverables directory).

### 12.1 Required field completeness (A2 §6)

| Required field | Location in D3 |
|---|---|
| TASK_ID | header block (`RD1-V1-P3CC-IMPL` proposed) |
| repo_full_name | header block (`tonychang925-dev/Julia_core`) |
| implementation_base_sha | header block (`BLOCKED_PENDING_GOVERNANCE_FREEZE`) |
| target_branch | §12.2 below (explicit) |
| allowed_paths | §2 |
| forbidden_paths | §3 |
| required_behavior | §4 |
| forbidden_behavior | §5 |
| migration_order | §8 (+ A–K mapping §12.3) |
| acceptance_tests | §6 |
| expected_evidence | §9 |
| known_invariants | §12.4 below (explicit) |
| NCF requirements | §10 |
| owner_authorization_scope | §11 |
| merge_authorization | §11 |
| release_authorization | §12.2 below (explicit) |

### 12.2 Explicit fields

```text
target_branch
= governance/p3-cc-freeze-review-v0.3
  (freeze-review home; implementation executes on a NEW implementation branch
   created at freeze, never directly on this review branch)

release_authorization
= NO
  (no release/push/tag by the implementation contract; release is a separate
   governed event)
```

### 12.3 A2 §7 mandatory ordering ↔ D3 §8 migration order

| A2 §7 | D3 §8 step |
|---|---|
| A. CapabilityFrame | 1 |
| B. C-09 Alignment capability encoding | 1 (same step; encoding follows frame) |
| C. ModelProvider receives capability representation | 1-2 |
| D. Model-owned logical CapabilityRequest proven | 2 |
| E. Research Composite Candidate A authority activated | 4-5 (freeze at 4, activate at 5) |
| F. deterministic Research keyword ingress disabled | 5 |
| G. Runtime requires_tool semantic authority retired | 6 |
| H. WorkflowRouter semantic authority retired | 7 |
| I. stream/non-stream semantic convergence | 8 |
| J. C2 schema/model-visible path through C-03/C-09 | 9 |
| K. controlled acceptance | 10 |

Dependency order preserved. Nothing is deleted before its compliant
replacement exists and is qualified.

### 12.4 Known invariants (explicit)

```text
conversation_id + turn_id constant across the composite tool loop (C-01 §2/§3)
per-sub-call CapabilityRequest/Call/ToolResult/Evidence identity (A-03)
Market event identity authority unchanged (event 215257 class preserved)
D1 external-observation boundary unchanged
C1 verification-state semantics unchanged
C2 preliminary-judgment semantics unchanged
Research Brief (research.brief.v1) semantics unchanged
canonical persistence + restart continuity unchanged
NO two simultaneously authoritative semantic routers at any migration instant
NO synthetic success / mock reachability / hidden fallback / persona-text success
   on the controlled critical Research path
```

### 12.5 A2 §8 explicit forbidden behavior (consolidated)

| Forbidden item | D3 clause |
|---|---|
| adding "查一下" (or any term) to research_actions | §5 keyword semantic admission; §3 no new lists |
| adding new semantic keyword lists | §5; §3 |
| adding regex semantic inference | §5; §3 |
| adding intent-classifier Runtime authority | §5; §3 |
| adding LLM-classifier Runtime authority | §5; §3 |
| keeping deterministic ingress as fallback | §5; §10 (LEGACY_AUTHORITY_FALLBACK = 0) |
| keeping requires_tool as semantic fallback | §5; §10 |
| silent capability substitution | §3; §5 |
| provider fallback | §3; §10 |
| synthetic ToolResult | §5; §10 |
| synthetic Evidence | §5; §10 |
| synthetic research success | §5; §10 |
| automatic ambiguous-event selection | §5 (ambiguity → cognition per D2 A-04) |
| generic workflow engine | §3 |
| RD1 V1 scope expansion | §3 |

### 12.6 D3 freeze-review status

```text
D3_STATUS = FREEZE_REVIEW_CANDIDATE
CONTRACT_FREEZE = NO
IMPLEMENTATION_AUTHORIZED = NO
NEXT_GATE = MIRA_SIS + OWNER D2/D3 FINAL FREEZE REVIEW
```
