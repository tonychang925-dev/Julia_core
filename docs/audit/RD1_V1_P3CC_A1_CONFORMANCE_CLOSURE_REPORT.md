# D1 — RD1 V1 P3-CC A1 Conformance Closure Report

**Task**: RD1-V1-P3CC-A1
**Title**: RD1 V1 Cognitive Capability Conformance Closure — Frozen Architecture → Current Source → Exact Implementation Contract
**Mode**: READ_ONLY_SOURCE_AUDIT + ARCHITECTURE_CONFORMANCE + CONTRACT_DRAFTING
**Implementation / source mutation**: 0
**Date**: 2026-09-08
**Governing law**: PRESERVE WORKING EXECUTION. RESTORE THE CORRECT AUTHORITY.

---

## 1. Authority Read-In Evidence

Documents read at the exact repository versions (repo `tonychang925-dev/Julia_core`, base `c14f6aa`):

| Document | Status | Evidence captured |
|---|---|---|
| `docs/architecture/ARCHITECTURE_DOCUMENT_REGISTRY.md` | GOVERNED | Normative precedence: UA v1.0 CANONICAL → C-series DERIVED → ADRs SUPPORTING → API/impl. "No other document has normative architecture authority." Rejected: IntentRouter decides semantic action. |
| `docs/architecture/ARCHITECTURE_FREEZE_RECORD_v1.0.json` | FROZEN | UA v1.0 frozen at `fafd1b8`, 7 amendments, 5 ATs. |
| `docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md` | CANONICAL | Referenced via C-series derivation; §5 authority, §7 provider, §8 context, §14 capability, §16 alignment. |
| `C-00_COGNITIVE_BOUNDARY_CONTRACT.md` | FROZEN | §3 LLM owns tool-need recognition; §4 Core allowed deterministic ops; §5 cognitive intrusion test; §6 forbidden semantic intent routing (names WorkflowRouter); §7 tool cognitive agency; §10 module dispositions. |
| `C-01_RUNTIME_EXECUTION_CONTRACT.md` | FROZEN | §1 Runtime orchestrates, does not cognize; §4 streaming = transport, shared semantics; §8 forbidden pre-cognitive intent routing / semantic workflow dispatch. |
| `C-03_CONTEXT_OS_CONTRACT.md` | FROZEN | §1 sole model-visible authority; §3 CapabilityFrame "LLM decides whether a tool is needed", forbids pre-filtering by inferred intent; §11 ToolResult re-entry; §16 Alignment placement; §18 P0-A bypass dispositions; §19 forbidden patterns. |
| `C-07_MODEL_PROVIDER_CONTRACT.md` | FROZEN | §4 input from governed path; §5 ModelInferenceRequest; §7 ModelInferenceResult.capability_requests[]; §8 stream/non-stream parity; §28 15 call sites / 5 ingress. |
| `C-08_CAPABILITY_TOOL_CONTRACT.md` | FROZEN | §1 LLM chooses need / Runtime authorizes-executes / LLM interprets; §4 CapabilityManifest via CapabilityFrame; §5 semantic router prohibited + deterministic command exception; §23 P0-A dispositions (WorkflowRouter REWRITE, capability_bridge tool_manifest KEEP WITH BOUNDARY). |
| `C-09_ALIGNMENT_CONTRACT.md` | FROZEN | §1 adaptation only; §2 placement Context OS → Alignment → ModelProvider; §6 AlignedInferencePayload + source_package_digest; §12 capability encoding (same manifest → native schema OR text protocol); §9 weak-model compensation allowed / cognitive pre-solving forbidden. |
| `C-12_EVIDENCE_ACTION_TRACE_CONTRACT.md` | FROZEN | §3 MODEL_INFERENCE ≠ TOOL_OBSERVATION; §4 tool grounding; §17 claim grounding (no new authority). |
| `docs/audit/PRODUCTION_CONTRACT_RECONCILIATION.md` | READ-ONLY PASS | 18 violations incl. WorkflowRouter pre-cognitive intent (P3), ToolResult append (P3), 10 Context bypasses; 5-ingress authority proof. |
| `.codex/skills/NO_CRITICAL_FALLBACK_REVIEW/SKILL.md` | SKILL | Fail-closed review fields; P0/P1 → REJECT. |

Baseline classification (first record):

```text
REPO_FULL_NAME           = tonychang925-dev/Julia_core
BASE_SHA                 = c14f6aa77a50dafc21a97083fac8cb97efc7231d
CURRENT_LOCAL_HEAD       = c14f6aa77a50dafc21a97083fac8cb97efc7231d  (identical)
WORKTREE_STATUS          = tracked tree CLEAN (only untracked reports/data/test files)
COMPARE_TO_BASE          = 0 for all audited source files (verified by git diff)
TAG_AT_BASE              = m1-text-research-continuity-v1
```

All seven audited source files were read from a working tree proven identical
to `c14f6aa` (`git diff c14f6aa -- <files>` empty).

---

## 2. P3-CC Governance Artifact Status

```text
DESIGN_FOUND_IN_REPO   = YES (remote review branch only)
DESIGN_SHA             = governance/p3-cc-freeze-review-v0.3 @ 24111b2,
                         blob f9afb0d4f2b86875a18bff00d31fa5df6102e8c6
                         docs/architecture/P3_COGNITIVE_AGENCY_TOOL_LOOP_CONVERGENCE_DESIGN_v0.3.md
CONTRACT_FOUND_IN_REPO = YES (remote review branch only)
CONTRACT_STATUS        = DRAFT (NOT FROZEN)
CONTRACT_SHA           = governance/p3-cc-freeze-review-v0.3 @ 24111b2,
                         blob bbe260ff7343a6932c96ff8ae49e6b9b494e5467
                         docs/project_control/P3_CC_COGNITIVE_CAPABILITY_CONVERGENCE_CONTRACT_DRAFT_v0.3.md
MERGE_STATE            = branch NOT merged into c14f6aa
P3_CC_NORMATIVE_AUTHORITY   = NO
P3_CC_IMPLEMENTATION_AUTHORITY = NO
```

Both documents were used as design input only. Upstream frozen architecture
remains normative. This report is the repository-governed formal execution of
the P3-CC-A1 workstream (contract-derived convergence design) as defined in the
design v0.3 §20.

---

## 3. Exact Source Audit — Verified Findings F1–F7

### F1 — Deterministic natural-language Research admission: CONFIRMED (VIOLATION)

`julia_session.py:130-179` `_build_research_desk_resolver_call(user_text)`:
- Rejects if trading terms present (买/卖/做多/…).
- Admits when `research_actions ∈ {研究, 调研, 查证}` AND `market_objects ∈ {市场, 行情, 事件, 主题, 简报}` co-occur in natural language.
- Then manufactures `{"name": "market.event.resolve", "arguments": {query, normalized_theme?, time_window?}}` and returns it as a tool-call JSON string.
- `julia_session.py:181-219` `_research_intent_is_negated_only()` is a keyword-window negation guard appended on top of the router (R1 patch, commit 11fc952).

Call site: `julia_session.py:305-325` inside `process_stream()`:
```python
deterministic_resolver_call = self._build_research_desk_resolver_call(text)
if deterministic_resolver_call is not None:
    ... SameTurnResearchContinuation(self).run(resolver_tool_json=...)
    async for streamed_delta in self.provider.stream_async(material.messages): yield
    return
```
This runs **before any model cognition** (before any `provider.stream_async`),
so a keyword match both (a) decides the user's semantic intent and (b) selects
the capability path, with the LLM reduced to verbalizing the research material.
Classification: C-00 §6 Forbidden Semantic Intent Routing; C-08 §5 Semantic
Router Prohibited; C-00 §3 tool-need recognition removed from LLM. Reachable =
PRODUCTION_ACTIVE (canonical streaming text research path).

The negation guard proves the task-card Case-C concern: it is an
ever-growing negation-marker list (`capability_bridge`-adjacent, 15+ markers, a
10-char window) that patches a forbidden router instead of removing it.

### F2 — Runtime tool-need classifier: CONFIRMED (VIOLATION)

`capability_bridge.py:777-808` `requires_tool(user_text)`:
- Market keyword triggers (`今天市场`, `市场怎么样`, `大盘怎么看`, …) and file triggers (`读一下`, `读取`, `帮我看看`, `代码`, `/Users/`, …) decide that "the user question needs external evidence".
- Consumed in both executors as a semantic evidence gate:
  - `julia_session.py:587` (`_chat_impl`): `needs_evidence = self.capability.requires_tool(text)`
  - `julia_session.py:341` (`process_stream`)
- When `requires_tool(text) and not tool_json`, both executors project a retry control (`project_retry_control`, reason `required_tool_call_missing`, `julia_session.py:342-355` / `590-602`) and force a **second model pass until a tool call appears** — i.e. Runtime not only recognizes need by keyword, it *coerces* a capability call out of the model.

Classification: tool-need recognition owned by Runtime keywords (C-00 §3, C-08 §1/§5 violation); retry coercion makes the model a rubber-stamp for a Runtime decision. Existing test `tests/runtime/test_c1_rev2_cognitive_boundary.py` already XFAILs this as A-01.

### F3 — Capability catalog vs capability-encoding split: CONFIRMED, refined (root convergence gap)

Current CapabilityFrame (Context OS): `context_execution_runtime.py:428-448` projects a **structured catalog** from `registry.all()`:
```text
available_tools = [ {capability_id, description, input_schema} ... ]   # provenance added
```
This is a clean derived projection (C-03 §3 compatible).

But the **textual call protocol** — the ```tool_call``` fence + tool rules —
lives only in `capability_bridge.py:497-545` `tool_manifest()`, which has **no
production caller at c14f6aa** (only tests reference it, e.g.
`test_i1_streaming_capability_continuation.py:399`). The legacy twin
`runtime/capability.py` manifest is likewise non-production.

Consequences at base:
1. The model-visible package contains capability *identities* but no *encoding* (neither provider-native schema nor text protocol) and no usage rules.
2. No C-09 Alignment seam exists to convert the same logical CapabilityFrame into the provider's supported representation.
3. The research path does not depend on model capability output at all (F1 manufactures the call), which is why this gap has been invisible in M1/RD1 acceptance.

Root production convergence gap confirmed: **CapabilityFrame → Alignment →
ModelProvider capability encoding is absent** (C-09 §12 unfulfilled in
production). `tool_manifest()` being dead is a refinement of the prior audit's
hypothesis (it is not "still injected"; it is not injected anywhere).

### F4 — C-09 not production-converged: CONFIRMED (TRANSITIONAL)

`context_execution_runtime.py:67-73`: `CognitiveContextPackage.to_messages()`
docstring states "Transitional — will be replaced by structured Alignment
projection (C-09) in P6." The actual ModelProvider input path is:

```text
pkg.to_messages(pkg.active_tail_messages, text)   # flat list[dict]
  → provider.chat(messages, cognitive_mode=...)  /  provider.stream_async(messages)
```

Call sites: `julia_session.py:323/329/334/386/411` (stream),
`julia_session.py:584/601/615` (non-stream), `julia_session.py:491` (C2
judgment). No `AlignedInferencePayload`, no `source_package_digest`, no
`ProviderAdaptationProfile`. Alignment is a declared-but-absent seam between
Context OS and ModelProvider.

### F5 — SameTurnResearchContinuation authority: CONFIRMED as open question

`research_continuation.py:150-472` `SameTurnResearchContinuation.run()`:
executes `market.event.resolve → market.event.read → research.event.enrich →
C1 normalize → C2 judgment → Research Brief → final same-turn continuation`.
Per-step authority (who selects / constructs / authorizes / executes / evidence):

| Step | Selected by | Request constructed by | Authorized / executed by | Evidence produced | Context OS projection |
|---|---|---|---|---|---|
| `market.event.resolve` | Runtime keyword admission (F1, VIOLATION) **or** model tool-call (`julia_session.py:367`) | Runtime (`_build_research_desk_resolver_call`) or model | `execute_tool_typed_async` → `manager.execute_typed` → `policy.check` (manager.py:295) | ToolResult + Evidence via manager | `_dispatch_typed_outcome` → `project_tool_result` / `project_authorization_outcome` / `project_capability_resolution_failure` |
| `market.event.read` | Runtime (deterministic follow-on) | Runtime (`research_continuation.py:241-244`, from `selected_event_id`) | same chain | ToolResult + Evidence | same dispatch |
| `research.event.enrich` | Runtime (deterministic follow-on) | `MarketEventResearchAdapter().build_request(validated_market)` (`research_continuation.py:279-284`) | `execute_capability_request_async` (research_continuation.py:302) | ToolResult + Evidence | same dispatch |
| C1 normalization | deterministic | `ResearchEvidenceNormalizer` | n/a (derived) | normalized enrichment | judgment projection |
| C2 judgment | model (provider) | `form_preliminary_research_judgment` (julia_session.py:448-500) | provider.chat | judgment object | `project_research_judgment` + post-render instruction (F7) |
| Research Brief | product hook (caller/Assistant) | `research_product_hook` | n/a | brief (research.brief.v1) | `project_research_product_continuation` |
| Final cognition | model | — | provider | assistant content | continuation package messages |

Interpretation: once the *entry* request exists, the internal sequence
resolve→read→enrich→C1→C2→brief is **deterministic execution semantics, not
hidden semantic interpretation** — each sub-call is individually authorized,
correlated, evidenced, and traced. This is de-facto Candidate A shape without a
frozen composite contract. Two authority defects remain: (1) the entry
capability may be chosen by Runtime keywords (F1); (2) no high-level governed
Research capability/program has been frozen, so the composite authority is
"NOT YET APPROVED" (P3-CC contract draft §11). Ambiguity at `resolve`
(`UNRESOLVED`/`AMBIGUOUS`) is fail-closed to `ResearchTurnNotReady` — it does
not yet return candidates to cognition for clarification (Candidate A
proof-requirement 6 unmet; see D2).

### F6 — Stream / non-stream semantic divergence: CONFIRMED (VIOLATION)

| Concern | `process_stream()` | `_chat_impl()` (via `process()`) |
|---|---|---|
| Keyword research admission (F1) | YES — before first model pass | NO |
| Model-emitted `market.event.resolve` | → SameTurnResearchContinuation full chain | → generic single `execute_tool_typed` (no chain, no C1/C2/brief) |
| `requires_tool` retry coercion | YES | YES |
| Research product produced | YES (brief + product via hook/sink) | NO |

For the same natural-language research request, stream produces a Research
Brief and non-stream produces either a generic tool echo or an ordinary model
answer. C-01 §4 ("Streaming is an output transport mode, not a separate
cognition architecture") and C-07 §8 parity are violated.

### F7 — C2 schema instruction appended after Context OS render: CONFIRMED (VIOLATION)

`julia_session.py:488-490` in `form_preliminary_research_judgment()`:
```python
messages = pkg.to_messages([], "...")
messages = list(messages) + [
    {"role": "user", "content": build_research_judgment_user_instruction(enrichment)}
]
response = self.provider.chat(messages, ...)
```
Model-visible content is added **after** Context OS package rendering. The
instruction content is a deterministic parser schema (structural, not semantic
pre-solving — `research/judgment.py:30`), so this is a C-03 §1/§19 *placement*
violation, correctly fixed by rendering through the existing `control_frame`
or through Alignment, not by deleting the schema. Reachable = PRODUCTION_ACTIVE
(the C2 step of the research chain).

---

## 4. Reachability & Legacy Classification (code existence ≠ reachability)

| Module / symbol | Reachability evidence (at c14f6aa) | Classification |
|---|---|---|
| `julia_session.process_stream()` | Called by streaming canonical text path (I-02 per P0-B); used by RD1 canonical research turns (`tests/runtime/test_l1_f2_*`, `test_i4_*`, `test_i1_*`) | **PRODUCTION_ACTIVE** |
| `julia_session.process()` → `_chat_impl()` | `process()` is the documented non-stream cognitive_fn for `ConversationRuntime.process_turn` (I-01); `_chat_impl` shared by legacy `chat()` | **PRODUCTION_ACTIVE** (non-stream native); `chat()`/`chat_async`/gateway callers = LEGACY (C-07 P0-A #15) |
| `julia_session._build_research_desk_resolver_call()` | Called `julia_session.py:305` in `process_stream` | **PRODUCTION_ACTIVE** — VIOLATION (semantic authority) |
| `julia_session._research_intent_is_negated_only()` | Called only from resolver builder | **PRODUCTION_ACTIVE** (as part of VIOLATION) |
| `julia_session._resolve_market_context()` / `_is_market_intent()` | Called from `context_execution_runtime.prepare()` (line 415) on every turn; narrow M2 phrase gate | **PRODUCTION_ACTIVE** — VIOLATION (pre-cognitive evidence prefetch) |
| `capability_bridge.requires_tool()` | Called `julia_session.py:341` and `:587` | **PRODUCTION_ACTIVE** — VIOLATION |
| `capability_bridge.detect_tool_call()` | Called `julia_session.py:338/354/588/602` | **PRODUCTION_ACTIVE** — structural decode (compliant role) |
| `capability_bridge.tool_manifest()` | No production caller; tests only | **DEAD_CODE** (production) — test-only manifest |
| `capability_bridge._resolve_tool_request()` / `_precheck_request` | Called by typed execution seams | **PRODUCTION_ACTIVE** — structural decode + fail-closed precheck |
| `context_execution_runtime.prepare()` | `_prepare_turn` → Context OS (julia_session.py:528) | **PRODUCTION_ACTIVE** — C-03 spine (converged except market prefetch + transitional to_messages) |
| `WorkflowRouter.route()` | `julia_session._resolve_market_context` → `workflow_router.route(text)` (julia_session.py:751); router registered in `JuliaSession.__init__:115` | **PRODUCTION_ACTIVE** (narrow legacy market-brief gate) — VIOLATION (C-00 §6) |
| `MarketBriefIntentResolver.resolve()` | Only via WorkflowRouter / MarketBriefPipeline | **PRODUCTION_ACTIVE** (via router) — VIOLATION |
| `MarketBriefPipeline.process()` | Only via `bridge.resolve_market_intent` (WorkflowRouter) | **PRODUCTION_ACTIVE** (via router) — domain workflow w/ semantic admission |
| `SameTurnResearchContinuation.run()` | Called `julia_session.py:311` (deterministic) and `:372` (model-emitted) | **PRODUCTION_ACTIVE** — execution valuable; composite authority NOT FROZEN |
| `runtime/capability.py` (legacy manifest/requires_tool) | No production importer found | **LEGACY** |
| `runtime/workflow_bridge.py`, `workflow/*` | No production importer found | **MIGRATION_ONLY / DEAD_CODE** relative to this path |
| `form_preliminary_research_judgment()` | Called from research chain (research_continuation.py:340) | **PRODUCTION_ACTIVE** (C2 step) |

Legacy rule applied: module existence was never treated as reachability; every
classification above was proven by caller trace.

---

## 5. Semantic Authority Ownership (every authority has exactly one owner)

| Authority | Frozen owner | Current actual owner | Verdict |
|---|---|---|---|
| "What does the user mean?" | LLM cognition (C-00 §3) | Runtime keywords (F1/F2/WorkflowRouter) | MUST MOVE TO LLM |
| "Is a capability needed?" (tool-need) | LLM cognition (C-00 §3, C-08 §1) | Runtime `requires_tool()` + retry coercion | MUST MOVE TO LLM |
| "Which logical capability + arguments?" | LLM cognition → CapabilityRequest (C-08 §3) | Runtime manufactured `market.event.resolve` (F1) or model | MUST MOVE TO LLM (research entry); sub-step sequence = deterministic execution (D2) |
| "Which provider/transport?" | Runtime/Capability binding (C-08, C-09 §12) | Runtime (registry definitions; model never offered transport fields) | COMPLIANT |
| "Is the request valid/authorized?" | Runtime validation + permission (C-01, C-08 §6) | `manager.execute_typed` → `policy.check`; typed UNKNOWN/DISABLED precheck | COMPLIANT |
| "Execute + trace + evidence" | Runtime (C-01, C-08, C-12) | Manager lifecycle + events + ToolResult/Evidence | COMPLIANT |
| "What does the result mean / what to say?" | LLM (C-00) | LLM (final provider pass) | COMPLIANT |
| "What is model-visible?" | Context OS (C-03) | prepare() mostly; **2 bypasses**: `_resolve_market_context` prefetch is inside prepare (allowed position, forbidden decision) + F7 post-render append | TRANSITIONAL → fix |
| "How is a capability represented to the model?" | Alignment (C-09 §12) | NOBODY (no seam) | GAP — assign to Alignment |
| External-claim grounding | Evidence (C-12 §4) | ToolResult/Evidence exist; grounding *instruction* not projected (manifest dead) | TRANSITIONAL |

No ambiguity remains after this table: the only un-owned responsibility is
**capability encoding**, which C-09 already assigns to Alignment.

---

## 6. Required Conformance Matrix

Columns: REQUIREMENT | FROZEN_AUTHORITY | EXACT_SOURCE | EXACT_SYMBOL | CURRENT_BEHAVIOR | REACHABILITY | CONFORMANCE | FIRST_BAD_BOUNDARY | TARGET_BEHAVIOR | TARGET_OWNER | CHANGE | TEST | RISK | EVIDENCE
Values: COMPLIANT / TRANSITIONAL / VIOLATION / LEGACY / UNKNOWN.

| REQUIREMENT | FROZEN_AUTHORITY | EXACT_SOURCE | EXACT_SYMBOL | CURRENT_BEHAVIOR | REACHABILITY | CONFORMANCE | FIRST_BAD_BOUNDARY | TARGET_BEHAVIOR | TARGET_OWNER | CHANGE | TEST | RISK | EVIDENCE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| natural-language Research ingress | LLM cognition selects capability (C-00 §3/§6, C-08 §5) | julia_session.py:305 | `_build_research_desk_resolver_call` | keyword 研究×市场 → manufactured market.event.resolve pre-cognition | ACTIVE | **VIOLATION** | before first model pass (Case B) | model-visible research capability → model selects → Runtime executes | LLM + Runtime | rework entry; keep continuation | L1-F2/CAN-A | HIGH | F1 |
| tool-need recognition | LLM (C-00 §3, C-08 §1) | capability_bridge.py:777 | `requires_tool` | keyword classifier + retry coercion | ACTIVE | **VIOLATION** | post-pass-1 gate (Case E) | Runtime never decides need; no forced retry | LLM | remove authority | C1-R2.2 | HIGH | F2 |
| CapabilityFrame construction | Context OS, derived, no intent filter (C-03 §3/§4) | context_execution_runtime.py:428 | `prepare()` capability_frame | structured registry catalog + provenance; no semantic gating | ACTIVE | **COMPLIANT** | — | unchanged; add source/policy refs | Context OS | none | existing | LOW | code |
| capability protocol encoding | Alignment encodes same manifest (C-09 §2/§12) | — (absent) | — | no seam; textual protocol dead (tool_manifest) | N/A | **VIOLATION (gap)** | model cannot request capability (Case A) | CapabilityFrame → Alignment → native schema OR text protocol → ModelProvider | Alignment | implement | A3 corpus | CRITICAL | F3/F4 |
| capability-request decoding | Runtime structural decode (C-08 §3/§9) | capability_bridge.py:810,620 | `detect_tool_call`, `_resolve_tool_request` | regex decode of text protocol; legacy-name normalize; research.enrich adapter gate | ACTIVE | **COMPLIANT** (structural) | — | keep as text-protocol decode adapter; add native-tool normalization | Runtime | keep | existing | LOW | code |
| authorization | Runtime policy (C-01, C-08 §6) | manager.py:295 | `policy.check` | typed ALLOW/DENY/…; UNKNOWN/DISABLED precheck | ACTIVE | **COMPLIANT** | — | unchanged | Runtime | none | existing | LOW | code |
| execution | Runtime/CapabilityManager (C-08 §8) | capability_bridge.py:711/724 | `_execute_request_with_events` | lifecycle + events + ToolResult/Evidence | ACTIVE | **COMPLIANT** | — | unchanged | Runtime | none | existing | LOW | code |
| ToolResult re-entry | Context OS mandatory (C-03 §11, C-08 §11) | context_execution_runtime.py:471 | `project_tool_result` | typed projection w/ evidence-ref validation (fail-closed) | ACTIVE | **COMPLIANT** (typed); legacy str shim remains | — | remove str shim; keep typed | Context OS | minor | existing | LOW | code |
| WorkflowRouter | forbidden pre-cognitive (C-00 §6, C-08 §23) | workflow_router.py:41 | `route()` | keyword intent → MarketBriefPipeline dispatch | ACTIVE (narrow) | **VIOLATION** | prepare() market prefetch (Case D vicinity) | no pre-cognitive semantic dispatch | — | retire authority | C1-R2.2 | HIGH | §7 |
| MarketBriefIntentResolver | MOVE TO LLM (C-08 §23) | reasoning/intents/market_brief.py:77 | `resolve()` | keyword → intent → capability_name | ACTIVE (via router) | **VIOLATION** | same | not in cognitive path | LLM | retire | C1-R2.2 | MED | §7 |
| `requires_tool` | no semantic need authority (C-00 §3) | capability_bridge.py:777 | `requires_tool` | market/file keywords → evidence gate + retry | ACTIVE | **VIOLATION** | Case E | REMOVE_FROM_PRODUCTION_AUTHORITY | — | remove/rewire | C1-R2.2 | HIGH | F2 |
| SameTurnResearchContinuation | composite authority not frozen (P3-CC §11; C-08 §5) | research_continuation.py:150 | `SameTurnResearchContinuation.run` | deterministic chain; sub-calls authorized/traced | ACTIVE | **TRANSITIONAL** | entry authority (F1) + no frozen composite | Candidate A executor after freeze | Runtime | freeze A; keep | I4 tests | MED | F5/D2 |
| stream/non-stream parity | shared semantics (C-01 §4, C-07 §8) | julia_session.py:281 vs 566 | `process_stream` / `_chat_impl` | stream: full research chain; non-stream: generic tool | ACTIVE | **VIOLATION** | Case B vs non-stream | one capability-selection lifecycle | Runtime | converge | PARITY | HIGH | F6 |
| C2 judgment instruction | sole model-visible gateway (C-03 §1) | julia_session.py:488 | post-render append | schema instruction appended after to_messages | ACTIVE | **VIOLATION** (placement) | C2 call | render via control_frame / Alignment | Context OS | move | C2 tests | MED | F7 |
| pre-cognitive market prefetch | no intent-based retrieval (C-03 §3, C-08 §5) | context_execution_runtime.py:415 | `_resolve_market_context(user_text)` | keyword market-intent → domain evidence prefetch | ACTIVE (narrow) | **VIOLATION** | every prepare() | evidence projected only when already authorized / model-requested | Context OS | remove decision | A3 | MED | §4 |
| external-claim grounding | Evidence grounding (C-12 §4) | capability_bridge.py:534 (dead) | tool rules | ToolResult/Evidence exist; grounding instruction not projected | ACTIVE | **TRANSITIONAL** | final chat pass | grounding rule model-visible via C-03/A; evidence refs preserved | Alignment+CtxOS | add projection | CAN-M | MED | F4 |
| WorkflowRouter/MarketBriefPipeline domain logic | domain workflow preserved if no semantic intent (C-08 §23) | market_brief_pipeline.py:82 | `MarketBriefPipeline.process` | context-block build + evidence reuse | ACTIVE (via router) | **LEGACY→REUSE** | — | preserve as domain execution below an approved capability | Domain | extract | — | LOW | §7 |

---

## 7. First-Bad-Boundary Analysis

### Case A — "你查一下7/19日 阿里qwen3.8发布对市场的影响"
- Current: `research_actions` = 研究/调研/查证 ⇒ "查一下" is NOT an action term; deterministic admission returns None. `requires_tool` file/market lists do not contain "查一下" ⇒ no evidence gate. Market prefetch `_is_market_intent` does not match. **Result today: ordinary model answer, no research** — the request silently under-serves.
- First bad boundary: **C-09 capability encoding absent** — the model sees a structured catalog with no requestable, semantically clear Research capability encoding and no instruction, so cognition cannot request Research even when it recognizes the need. The architecture question "Can Julia cognition recognize Research capability need without Runtime keyword admission?" is currently unanswerable because the request channel does not exist.
- Target: CapabilityFrame + Alignment present ⇒ model emits the intended logical Research request (A3 corpus, non-authoritative qualification).

### Case B — canonical R10 (Token 出海, expected event 215257)
- Current: contains 研究 + 主题/市场 ⇒ deterministic admission fires **before first model cognition** in `process_stream` (F1). Historical acceptance depended on this pre-cognitive keyword path.
- First bad boundary: C-00 §6 / C-08 §5 — semantic intent routing before cognition. This is the post-freeze regression the P3-CC audit records.
- Target: model cognition selects the Research capability; chain executes under an approved composite authority; event 215257 identity unchanged (Market authority preserved). Do **not** run live R10 here.

### Case C — "不要调用研究、市场或语音能力，我们只聊架构"
- Current: handled only because `_research_intent_is_negated_only()` contains 不要调用/不要 etc. in a 10-char window before 研究. The guard is a growing exception list inside a forbidden router; novel negation phrasing mis-routes.
- First bad boundary: the **existence of the keyword router itself**; the negation patch is a repair on a violation, not a compliant mechanism.
- Target: no negation list. Cognition reads the full utterance; if the user forbids capabilities, the model simply does not request one. Runtime has no semantic gate to negate.

### Case D — "我们聊聊阿里最近的新模型"
- Current: no keyword matches any list ⇒ model-only answer (acceptable by accident of narrow lists).
- First bad boundary: none exercised today; robustness is the issue — the compliant path must guarantee Julia *may* decline a capability, not merely fail to match keywords.
- Target: model decides no external capability is necessary; Runtime must not force Research (no hidden admission).

### Case E — tool need exists but model chooses none
- Current: `requires_tool(text)` true + no tool call ⇒ `project_retry_control("required_tool_call_missing")` forces a second model pass, coercing a capability call (julia_session.py:341-355, 590-602).
- First bad boundary: F2 — Runtime keyword tool-need + retry coercion. Runtime converts "model chose no capability" into "keyword classifier chose a capability".
- Target (architecture-correct): the model may decide not to use a capability even when one is available; Runtime accepts the model's response and does not auto-convert no-choice into a forced call. `required_tool_call_missing` retry control is retired as a semantic coercion (it may remain only for genuine protocol failures, separately governed).

### Case F — malformed / unavailable capability request (fail-closed contract)
| Scenario | Current behavior at c14f6aa | Fail-closed target |
|---|---|---|
| decode failure | stream: `ValueError("malformed capability request from cognition")` (julia_session.py:398); non-stream: delta None ⇒ pass-1 text (may contain raw tool block) emitted | typed `INVALID_REQUEST`/`MALFORMED_CAPABILITY_REQUEST` projected to control_frame; never raw tool text as assistant content |
| unknown capability | `CapabilityPreAuthorizationFailure(UNKNOWN)` → control_frame projection (project_capability_resolution_failure) | KEEP (typed, model-visible) |
| disabled capability | `DISABLED` → same | KEEP |
| schema failure | research.enrich: `INVALID_MARKET_CONTEXT`; others: manager/registry validation | typed `INVALID_ARGUMENTS` (validate pre-execution) |
| authorization failure | non-ALLOW AuthorizationDecision → `project_authorization_outcome` | KEEP |
| provider unavailable | typed ToolResult UNAVAILABLE (no fake result; manager fail-closed) | KEEP |
| execution failure | typed ToolResult ERROR; research chain → `ResearchTurnNotReady` (no ordinary continuation) | KEEP (fail-closed) |
No scenario may become ordinary persona text claiming success (C-08 §17, NCF).


---

## 8. Function-Level Dispositions (§12-14 of task)

### 8.1 `detect_tool_call()` — KEEP as structural text-protocol decoder
- Role: decodes the ```tool_call```/`TOOL:` textual protocol emitted by a model into capability-request JSON. It decides **structure**, not intent.
- Placement per frozen contracts: C-07 §9 (tool call = cognitive output that Runtime decodes) and C-09 §9/§12 (capability compensation: when the provider lacks native tools, encode the protocol textually and decode deterministically). It therefore belongs in the **provider/text-protocol decoding adapter** under Alignment/Runtime structural decode, NOT as a semantic intent authority.
- Derived answer (C-07/C-09): text-protocol decode is a provider-adaptation concern. Compliant home: Runtime structural decoder owned by the same layer that owns `_resolve_tool_request` (which already normalizes legacy names and gates `research.event.enrich` and `engineering.code_review`). Do not move it for code cleanliness; keep it where decode feeds typed execution.
- Forbidden future: using `detect_tool_call` output to infer user intent; using it as the only capability channel once Alignment provides native-tool support.

### 8.2 `requires_tool()` — REMOVE_FROM_PRODUCTION_AUTHORITY
- Function-level disposition: **REMOVE_FROM_PRODUCTION_AUTHORITY** (semantic part) + KEEP only the deterministic-command exception surface where the command itself carries unambiguous execution intent (none currently exercised on this path).
- Proof required by task §13: if retained in any form it must perform **zero** semantic tool-need cognition. A keyword/regex/LLM classifier that tells Runtime what the user "really wants" is not acceptable. Current implementation is exactly such a classifier (market/file trigger lists + `/Users/` path sniffing) → it cannot be retained.
- Replacement: model-visible CapabilityFrame + Alignment encoding (the model decides need); retry control `required_tool_call_missing` is retired as a semantic coercion.

### 8.3 WorkflowRouter — RETIRE SEMANTIC AUTHORITY, PRESERVE DOMAIN LOGIC

| Item | Disposition |
|---|---|
| `WorkflowRouter` | CURRENT_REACHABILITY = PRODUCTION_ACTIVE (narrow M2 market-brief phrase gate via prepare → _resolve_market_context). CURRENT_AUTHORITY = pre-cognitive semantic dispatch. FROZEN_CONTRACT_CONFORMANCE = VIOLATION (C-00 §6; the contract literally names WorkflowRouter as the forbidden example). TARGET_DISPOSITION = RETIRE from pre-cognitive production authority. |
| `MarketBriefIntentResolver` | CURRENT_REACHABILITY = via WorkflowRouter only. CONFORMANCE = VIOLATION. TARGET = REMOVE from cognitive path (intent classification = cognition). |
| `MarketBriefPipeline` | CURRENT_REACHABILITY = via WorkflowRouter. CONFORMANCE = domain workflow with semantic admission. TARGET = preserve **execution-side** logic (capability→context blocks→evidence) beneath an approved domain capability; remove keyword intent admission. |
| REUSABLE_DOMAIN_LOGIC | context-block building, prediction-id extraction, evidence record assembly (market_brief_pipeline.py:129-152) — reusable below a governed capability boundary. |
| REMOVE/REWRITE_SCOPE | remove the user-text→intent→capability semantic mapping; the pre-cognitive market prefetch hook in `prepare()` (context_execution_runtime.py:415). |

### 8.4 Pre-cognitive `_resolve_market_context(user_text)` — REMOVE decision authority
Context OS may project evidence that already exists / was retrieved through an
authorized capability; it must not *decide to retrieve domain evidence because
keywords suggest a market topic* (C-03 §3 EvidenceFrame, §5 meaning resolution
forbidden). Target: market evidence enters only via model-requested capability
ToolResult/Evidence projection or a separately governed situation need.

---

## 9. Migration-Order Assessment and NCF Review

### 9.1 Frozen WBS dependency check (task §21)
The proposed order (1 CapabilityFrame→Alignment encoding, 2 model-owned request production, 3 non-authoritative corpus qualification, 4 research composite authority freeze, 5 ingress cutover, 6 retire requires_tool, 7 retire WorkflowRouter, 8 converge stream/non-stream, 9 route C2 schema through C-03/C-09, 10 canonical acceptance) **conforms** to frozen WBS/P3-CC-Ax sequencing:
- P3-CC design v0.3 §20 defines A1→A7 in this order; A4 (composite authority freeze) is a hard prerequisite of A5 (cutover); A6 (retire legacy + parity) follows cutover.
- C-08 §23 / P0-B phase P3 place WorkflowRouter/requires_tool retirement after the compliant capability path exists ("build → prove → cut → retire", P3-CC-12). Deletion-first migration is prohibited; no dual semantic authority during migration.
- C-01 §4 parity work is safe only after the single capability-selection lifecycle exists (items 1-2), so item 8 placement conforms.
- Judgment: order CONFORMS; no frozen WBS dependency violated.

### 9.2 NCF review (per .codex/skills/NO_CRITICAL_FALLBACK_REVIEW/SKILL.md)
Static gate run on base c14f6aa: **NCF_GATE: PASS**; P0/P1/P2 new = 0;
PRODUCTION_MOCK_REACHABLE = NO; SYNTHETIC_SUCCESS_REACHABLE = NO;
FAIL_OPEN_AUTHORITY = NO; SABOTAGE_TESTS = PASS.
Control-flow review (this audit introduces no code): the future compliant path
must preserve RETRY=0 / FALLBACK=0 / SYNTHETIC_SUCCESS=0 / MOCK=0 /
LEGACY_AUTHORITY_FALLBACK=0 on the critical research path. Existing
fail-closed artifacts (ResearchTurnNotReady, CapabilityPreAuthorizationFailure,
typed ToolResult UNAVAILABLE/ERROR, authorization-outcome projection, evidence
grounding) already satisfy the no-fallback contract for downstream execution
and must not be weakened by migration.

```text
NO_CRITICAL_FALLBACK_REVIEW
CRITICAL_PATH: YES
FALLBACK_INTRODUCED: NO
MOCK_OR_FIXTURE_PRODUCTION_REACHABLE: NO
LEGACY_AUTHORITY_FALLBACK: YES (legacy semantic keyword authority exists today; to be retired, not extended)
SYNTHETIC_SUCCESS: NO
OUTER_SUCCESS_INNER_FAILURE: NO
AMBIENT_RESOLUTION: NO
TEST_MODE_PRODUCTION_REACHABLE: NO
FAIL_CLOSED_PRESERVED: YES
RISK: P2 (existing conformance debt; no new risk introduced)
DECISION: APPROVE (read-only audit) / future implementation must re-run gate
```

### 9.3 Frozen-architecture gap determination
No RD1 V1 behavior is *impossible* under the current C-00/C-01/C-03/C-07/C-08/
C-09/C-12 contracts. Every divergence is implementation convergence debt plus a
post-freeze semantic-routing regression. Therefore:

```text
FROZEN_ARCHITECTURE_GAP = NOT_PROVEN
ARCHITECTURE_AMENDMENT_REQUIRED = NO
```
