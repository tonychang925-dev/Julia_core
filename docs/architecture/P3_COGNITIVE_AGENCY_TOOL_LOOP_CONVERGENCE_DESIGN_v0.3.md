# P3-CC — Cognitive Agency / Tool Loop Convergence — Cognitive Capability Convergence Design v0.3

**Document status**: DESIGN DRAFT  
**Architecture status**: DERIVED FROM EXISTING FROZEN ARCHITECTURE  
**Implementation authority**: NONE  
**Contract authority**: NONE  
**Baseline Core**: `Julia_core @ c14f6aa77a50dafc21a97083fac8cb97efc7231d`  
**Date**: 2026-09-07  
**Primary frozen WBS phase**: `P3 — Cognitive Agency / Tool Loop Convergence`  
**Cross-phase dependencies**: P2 / P6 / P7 / P8  
**Scope**: Post-M1 production convergence under frozen WBS P3  
**M1 status**: IMMUTABLE / CLOSED  
**M2 status**: independent; not modified by this design  
**Proposed repo path**: `docs/architecture/P3_COGNITIVE_AGENCY_TOOL_LOOP_CONVERGENCE_DESIGN_v0.3.md`  
**Current file authority**: external/download review copy only

---

## 0. Executive Decision

P3-CC is **not** a new Semantic Router architecture.

P3-CC is a production convergence workstream under frozen WBS P3 whose purpose is to restore the cognitive/capability boundary already frozen by Julia Core architecture:

```text
User canonical turn
        ↓
Context OS
        ↓
CognitiveContextPackage
        ↓
CapabilityFrame
        ↓
Alignment
        ↓
provider-specific capability encoding
        ↓
ModelProvider / Julia cognition
        ↓
model-selected CapabilityRequest
        ↓
Runtime authorization + execution
        ↓
CapabilityCall / ToolResult / Evidence
        ↓
Context OS incremental projection
        ↓
Alignment
        ↓
same-turn Julia cognition continuation
        ↓
ConversationRuntime canonical commit
```

The central correction is:

```text
PRESERVE WORKING EXECUTION.
RESTORE THE CORRECT AUTHORITY.
```

P3-CC must **not** introduce another runtime-owned intent classifier, semantic router, orchestration brain, or parallel cognition stack.

---

# 1. Frozen WBS Namespace and Cross-Phase Mapping

## 1.1 Namespace law

The frozen WBS owns the phase namespace.

```text
P3 = Cognitive Agency / Tool Loop Convergence
The existing frozen Identity / Memory Convergence phase remains unchanged and is out of scope.
```

Therefore this workstream SHALL use only the frozen `P3` namespace and the `P3-CC` workstream identifier.

`P3-CC` means:

```text
P3-CC = a governed design/contract family inside frozen WBS P3
      ≠ a new phase
      ≠ a replacement for frozen P3-Txx task numbering
```

Internal review steps use `P3-CC-Ax` so they cannot be confused with frozen WBS tasks `P3-T01..T09`.

## 1.2 Frozen WBS mapping

| P3-CC design area | Frozen WBS owner/dependency | Relationship |
|---|---|---|
| CapabilityFrame exposure | P2-T07 | prerequisite / reuse |
| ToolResult incremental reinjection | P2-T14 | prerequisite / reuse |
| ModelProvider tool-call normalization | P3-T01 | primary |
| Permission gate | P3-T02 | primary |
| Capability execution | P3-T03 | primary |
| ToolResult evidence | P3-T04 | primary |
| Context incremental reinjection | P3-T05 | primary |
| Model continuation | P3-T06 | primary |
| Remove broad Runtime semantic tool routers | P3-T07 | primary |
| Preserve explicit infrastructure routing exceptions | P3-T08 | primary |
| Grounding tests | P3-T09 | primary |
| Provider representation/adaptation only | P6-T05 | cross-phase dependency |
| Text/voice cognitive parity | P7-T08 | later parity dependency |
| Legacy direct/compatibility path retirement | P8 | retirement dependency |

Frozen WBS exit condition remains authoritative:

```text
model-directed tool loop works end-to-end
```

P3-CC cannot redefine that exit condition.

---

# 2. Why This Design Exists

M1 proved a complete functional Research Desk loop:

```text
Client input
→ Research Desk
→ Market authority
→ D1 research
→ C1 verification
→ C2 preliminary judgment
→ Research Brief
→ Core canonical persistence
→ Client structured rendering
→ restart continuity
```

That functional acceptance remains valid and immutable.

However, post-M1 audit found that part of the path used to *enter* Research Desk does not conform to the previously frozen cognitive boundary.

Example:

```text
你查一下7/19日阿里Qwen3.8发布对市场的影响
```

The current Research ingress relies on deterministic phrase matching. Because `"查一下"` is not one of the admitted research action words, the request remains ordinary conversation even though the user’s semantic intent is research.

The obvious patch — adding more keywords — would increase the architectural debt.

The opposite patch — adding a new Runtime semantic classifier — would violate the frozen architecture even more directly.

Therefore P3-CC must solve the problem by completing the architecture that was already frozen.

---

# 3. Normative Architecture Sources

The design derives from the following canonical authority order:

```text
1. JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0
2. Frozen C-series contracts
3. Compatible accepted ADRs
4. APIs / schemas
5. Production implementation
6. Historical documents / reports
```

Primary frozen contracts used by P3-CC:

| Contract | P3-CC-relevant authority |
|---|---|
| C-00 Cognitive Boundary | LLM owns semantic interpretation, intent understanding, tool-need recognition |
| C-01 Runtime Execution | Runtime orchestrates cognition; pre-cognitive semantic routing is forbidden; stream/non-stream parity |
| C-03 Context OS | CapabilityFrame exposes available capabilities; Context OS must not infer intent and pre-filter/force workflows |
| C-07 ModelProvider | CapabilityRequest is cognitive output from model inference; ToolResult re-enters via Context OS |
| C-08 Capability / Tool | Capability routing begins only after cognitive selection; Semantic Router prohibited |
| C-09 Alignment | CapabilityManifest is encoded into provider-native tools or textual tool protocol; capability compensation allowed |
| C-12 Evidence / Action / Trace | External observation/action claims require execution evidence and trace lineage |

This document does **not** amend those contracts.

---

# 4. P3-CC-A0 Read-Only Audit Result

```text
P3_CC_A0_FROZEN_ARCHITECTURE_AUDIT = CLOSED_PASS

CURRENT_CORE_ROUTING_CONFORMANCE = OPEN_FAIL

FROZEN_ARCHITECTURE_GAP = NOT_PROVEN
FROZEN_ARCHITECTURE_AMENDMENT_REQUIRED = NO

PRIMARY_PROBLEM =
IMPLEMENTATION_CONVERGENCE_DEBT
+
POST-FREEZE SEMANTIC ROUTING REGRESSION
```

The audit therefore rejects a big-bang Core architecture rewrite.

---

# 5. Current Production Divergence Map

## 5.1 Deterministic Research Desk ingress

Current source:

```text
JuliaSession._build_research_desk_resolver_call()
```

Semantics:

```text
research_actions = 研究 / 调研 / 查证
market_objects    = 市场 / 行情 / 事件 / 主题 / 简报

if action && object:
    manufacture market.event.resolve request
    skip first model pass
```

This is a semantic decision over ambiguous natural language performed by Runtime before model cognition.

**Disposition**: retire as production semantic authority.

## 5.2 `requires_tool()` semantic classifier

Current capability bridge contains keyword rules for market/file requests that decide whether the user “requires a tool.”

That is tool-need recognition by Runtime.

**Disposition**: retire as cognitive authority. A deterministic explicit-command path may remain where the command itself carries unambiguous execution intent.

## 5.3 WorkflowRouter / MarketBriefIntentResolver

Current path:

```text
User utterance
→ Runtime IntentResolver
→ WorkflowRouter
→ MarketBriefPipeline
```

This was already identified by the earlier Production Contract Reconciliation as a C-00/C-08 violation.

**Disposition**: remove from pre-cognitive production routing authority. Domain workflow code may survive as execution-side reusable logic if it does not own semantic intent.

## 5.4 Pre-cognitive market context resolution

`ContextExecutionRuntime.prepare()` currently may call `_resolve_market_context(user_text)`.

That means Context OS can infer “market intent” from the utterance and fetch market context before Julia cognition decides that it is needed.

**Disposition**: remove semantic prefetch authority. Context OS may project already-authorized/retrieved evidence; it must not decide to retrieve domain evidence because it interprets user meaning.

## 5.5 Incomplete CapabilityFrame → Alignment convergence

Current CapabilityFrame exposes structured capability descriptors such as:

```text
capability_id
description
input_schema
```

But the textual tool-call protocol used by current models still exists in legacy `RuntimeCapabilityBridge.tool_manifest()`.

Frozen C-09 already specifies the missing architecture:

```text
CapabilityManifest
→ Alignment
→ provider-native tool schema
  OR textual capability protocol
→ ModelProvider
```

**Disposition**: complete C-09 production convergence. Do not compensate by adding a semantic router.

## 5.6 Research chain orchestration authority

`SameTurnResearchContinuation` currently sequences:

```text
market.event.resolve
→ market.event.read
→ research.event.enrich
→ C1
→ C2
→ Research Brief
→ final cognition
```

The underlying research execution is valuable and should be preserved.

The unresolved question is **authority**, not data flow:

> Is this sequence the internal deterministic implementation of one cognitively selected high-level Research capability/program, or must Julia cognitively select each individual capability step?

No frozen high-level composite capability contract has yet been proven.

**Disposition**: formal architecture review before cutover. Do not delete the chain. Do not declare it canonical composite authority without review.

## 5.7 Streaming / non-streaming parity

C-01 requires the same tool/cognition semantics for stream and non-stream execution.

Current Research deterministic ingress is attached to streaming behavior in a way that does not represent the final modality-independent contract.

**Disposition**: converge both to one capability-selection lifecycle.

---

# 6. Design Goals

P3-CC SHALL:

1. Restore LLM-owned semantic/tool-need cognition.
2. Preserve Runtime-owned authorization, execution ordering, lifecycle, persistence and trace.
3. Complete CapabilityFrame → Alignment → ModelProvider capability representation.
4. Preserve existing `CapabilityManager`, `CapabilityRequest`, `AuthorizationDecision`, `CapabilityCall`, `ToolResult`, `Evidence`.
5. Preserve Market / D1 / C1 / C2 / Research Brief authority boundaries.
6. Preserve same-turn tool continuation.
7. Preserve fail-closed behavior.
8. Preserve M1 accepted runtime history and tags.
9. Make text and voice converge on the same cognitive/capability semantics.
10. Make capability use explainable from observable artifacts without persisting hidden chain-of-thought.

---

# 7. Explicit Non-Goals

P3-CC SHALL NOT:

- build `SemanticRouter.py`;
- build a Runtime-owned generic intent classifier;
- route ambiguous natural language by keywords;
- introduce a second cognition stack;
- move provider/transport selection into the LLM;
- make Alignment decide semantic meaning;
- make Context OS decide semantic intent;
- replace CapabilityManager;
- replace ConversationRuntime;
- rewrite Market event identity authority;
- rewrite D1 / C1 / C2 semantics;
- rewrite M1 acceptance history;
- infer that every model must produce identical decisions or wording;
- preserve private chain-of-thought as Julia continuity state.

---

# 8. Target Authority Model

```text
User
│
▼
ConversationRuntime
│  canonical turn identity / chronology
▼
Context OS
│  governed visible context
▼
Alignment
│  provider representation only
▼
ModelProvider
│
▼
Julia Cognition
│  semantic interpretation
│  decides whether capability is needed
│  chooses logical capability + arguments
▼
ModelInferenceResult.capability_requests[]
│
▼
Runtime / C-08
│  validation
│  authorization
│  execution ordering
▼
CapabilityManager
│
▼
CapabilityProvider / DomainProvider
│
▼
ToolResult + Evidence
│
▼
Context OS incremental projection
│
▼
Alignment
│
▼
ModelProvider continuation
│
▼
Julia response
│
▼
ConversationRuntime commit
```

Authority table:

| Concern | Sole / primary authority |
|---|---|
| Semantic interpretation | LLM cognition |
| Tool-need recognition | LLM cognition |
| Logical capability selection | LLM cognition |
| Explicit deterministic command decoding | Runtime structural router |
| Capability catalog | CapabilityRegistry / C-08 |
| What model sees | Context OS |
| Provider-specific capability encoding | Alignment |
| Provider/model invocation | Runtime / ModelProvider boundary |
| Permission | Capability policy |
| Provider binding | Capability definition / composition |
| Execution lifecycle | CapabilityManager / Runtime |
| Domain truth | Domain authority, e.g. Market |
| Verification state | C1 |
| Preliminary research judgment | C2 |
| Canonical conversation | ConversationRuntime |
| External observation evidence | C-12 Evidence |
| Trace / correlation | C-12 |
| Client rendering | presentation only |

---

# 9. CapabilityFrame Design

The CapabilityFrame is a **model-visible projection**, not an execution authority.

Minimum logical information:

```text
CapabilityDescriptor {
    capability_id
    description
    input_schema
}
```

Where already available and contract-compatible, the projection MAY also include:

```text
permission_scope
side_effect_class
availability_state
limitations
cost/latency hints
schema_version
```

Rules:

1. CapabilityFrame MUST derive from the canonical capability registry / policy.
2. CapabilityFrame MUST NOT be filtered because Runtime inferred the user's semantic intent.
3. CapabilityFrame MAY be filtered by deterministic permission, availability, provider-support or policy constraints.
4. CapabilityFrame is disposable projection; it is not canonical capability truth.
5. CapabilityFrame MUST carry provenance to registry/policy source.
6. CapabilityFrame MUST be identical in semantic meaning for stream/non-stream and text/voice turns, subject only to provider representational adaptation.

---

# 10. Alignment Capability Encoding

This is the major missing production convergence seam.

Alignment receives:

```text
CognitiveContextPackage
+
CapabilityFrame
+
ProviderAdaptationProfile
```

and emits provider-compatible capability representation.

## 10.1 Provider with native tools

```text
capability_descriptors[]
→ provider-native tool/function schema
```

## 10.2 Provider without native tools

Alignment emits a textual protocol that is semantically equivalent to the same CapabilityManifest.

The exact syntax is an Alignment implementation detail, not architecture truth.

## 10.3 Rules

Alignment MUST NOT:

- hide tools because it thinks Julia “should not use them”;
- decide whether a tool is needed;
- synthesize a tool request;
- select provider/domain transport;
- add a semantic conclusion to compensate for a weak model.

Alignment MAY:

- encode capability schemas textually;
- map to provider-native tool schema;
- escape/translate provider syntax;
- reject unsupported representation;
- report degraded/fail compatibility.

---

# 11. ModelInferenceResult and Capability Selection

The target logical output is consistent with frozen C-07:

```text
ModelInferenceResult {
    generation_id
    content
    capability_requests[]
    finish_reason
    error
    trace_refs
}
```

A capability request is a **cognitive output**.

The model selects:

```text
logical capability_id
arguments
```

The model MUST NOT select:

```text
provider
provider_id
endpoint
transport
proxy
browser session
DOM selector
database transport
release tree
```

Those remain execution/composition authority.

---

# 12. CapabilityRequest Validation

A model-emitted request MUST pass deterministic validation before execution.

Validation includes:

```text
recognized capability
schema-valid arguments
current availability
permission
side-effect policy
turn/generation/correlation binding
provider binding readiness
authority-field prohibition
```

Failure MUST produce a typed outcome.

Failure MUST NOT trigger:

```text
keyword fallback
semantic router fallback
second-model semantic repair
silent provider switch
synthetic success
ordinary-persona claim of completed execution
```

---

# 13. Same-Turn Capability Continuation

Frozen lifecycle:

```text
G1 cognition
→ CapabilityRequest
→ Runtime authorization
→ Capability execution
→ ToolResult / Evidence
→ Context OS projection
→ Alignment
→ G2 cognition
→ response
```

Invariant:

```text
same conversation_id
same turn_id
new generation_id allowed
```

No capability result may become a separate fake user turn.

No intermediate runtime event may become assistant transcript truth.

---

# 14. Failure Semantics

## 14.1 Malformed model capability request

```text
TOOL_PROTOCOL_ERROR / INVALID_REQUEST
```

No guessed repair.

## 14.2 Unknown / disabled capability

Typed failure projected to cognition where appropriate.

No substitute capability chosen by Runtime.

## 14.3 Provider unavailable

Typed UNAVAILABLE / provider failure.

No fallback provider unless separately governed and traceable by the applicable frozen policy.

## 14.4 Capability execution fails

Tool failure is projected through Context OS.

Julia may explain the failure.

Julia may not claim the capability succeeded.

## 14.5 Model does not request a capability

Runtime MUST NOT infer that it “should have” and force a semantic capability path.

If the model produces a normal answer, grounding/claim governance still applies.

A response that claims an external observation without execution evidence is rejected by claim grounding policy.

---

# 15. External-Execution Claim Grounding

C-12 already provides the required law:

```text
External observation claim
→ TOOL_OBSERVATION Evidence required

External side-effect claim
→ Action evidence required
```

Therefore P3-CC does not need a new canonical “ExecutionReceipt” authority.

A derived, non-authoritative projection MAY summarize:

```text
capability_request_ids
capability_call_ids
evidence_ids
action_ids
status
```

for response governance or UI.

Example:

```text
Julia says: "我查了一下..."
```

Allowed only if the accepted response can be grounded in a successful capability execution and corresponding evidence.

Without evidence, the response must remain clearly inferential or state that no external lookup was completed.

---

# 16. Research Desk Preservation Strategy

The Research Desk downstream spine is **not** the target of a rewrite.

Preserve:

```text
Market event identity authority
market.event.resolve
market.event.read
D1 controlled research
normalization
C1 verification
C2 preliminary judgment
Research Brief composition
structured product
Core persistence
Client rendering
restart continuity
```

The issue to solve is:

```text
WHO cognitively selects Research?
WHO authorizes the multi-step Research program?
```

---

# 17. Research Execution Authority — Two Candidate Models

This decision remains intentionally NOT frozen in v0.3.

## Candidate A — High-level governed Research capability/program

```text
Julia cognition
→ requests one high-level Research capability
→ Runtime authorizes that capability/program
→ deterministic internal Research program:
   resolve
   → read
   → enrich
   → C1
   → C2
   → Brief
→ final same-turn cognition
```

Advantages:

- maximizes reuse of RD1;
- deterministic evidence pipeline;
- stable Market/D1/C1/C2 authority;
- fewer model round trips;
- lower latency;
- easier canonical acceptance;
- easier fail-closed reasoning.

Required proof before approval:

1. Frozen contracts permit a cognitively selected high-level capability whose internal implementation invokes governed sub-capabilities.
2. Every sub-call remains individually authorized, correlated and evidenced.
3. Internal sequencing performs execution logic, not new semantic interpretation.
4. The high-level capability has a formal schema, authority and failure contract.
5. Runtime does not silently change research objective.

**Current disposition**: preferred candidate for formal review, not yet approved.

## Candidate B — Model-directed stepwise capability selection

```text
G1 → market.event.resolve
G2 → market.event.read
G3 → research.event.enrich
...
```

Advantages:

- strongest literal interpretation of model-owned capability selection.

Costs:

- more generations;
- greater latency;
- more failure boundaries;
- increased behavioral variance;
- risks turning a validated deterministic Research pipeline into an ad hoc agent workflow.

**Current disposition**: valid comparison candidate, not preferred without contract evidence.

---

# 18. `SameTurnResearchContinuation` Disposition

Do not delete it during early P3-CC work.

Classify:

```text
CURRENT_FUNCTIONAL_VALUE = HIGH
CURRENT_AUTHORITY_STATUS = REQUIRES_FORMAL_REVIEW
```

Possible future outcomes:

```text
A. retained as internal executor of an approved high-level Research capability
B. reduced to a helper beneath model-directed stepwise calls
C. split into reusable deterministic stages
```

No option is chosen until the formal authority review.

---

# 19. Legacy Semantic Authority Retirement

The following components must not gain new product dependence:

```text
_build_research_desk_resolver_call()
_research_intent_is_negated_only()
requires_tool() semantic keyword logic
WorkflowRouter semantic intent dispatch
MarketBriefIntentResolver pre-cognitive path
pre-cognitive _resolve_market_context(user_text)
```

Migration rule:

```text
DO NOT DELETE FIRST.
FIRST BUILD THE COMPLIANT PATH.
THEN PROVE IT.
THEN CUT AUTHORITY.
THEN REMOVE LEGACY.
```

This prevents a big-bang outage.

---

# 20. Migration Strategy

Internal workstream numbering is `P3-CC-Ax`; it does not modify frozen WBS task IDs.

## P3-CC-A1 — Contract-derived convergence design

Deliver:

```text
frozen requirement
current source
conformance state
target seam
migration dependency
acceptance gate
```

No production edits.

## P3-CC-A2 — Capability representation convergence

Implement/test:

```text
CapabilityFrame
→ Alignment
→ ModelInferenceRequest capability descriptors
→ provider-native/text capability protocol
```

No Research ingress cutover.

## P3-CC-A3 — Model-owned capability selection qualification

Controlled/offline or otherwise non-authoritative qualification corpus.

Prove examples such as:

```text
"你查一下7/19日阿里Qwen3.8发布对市场的影响"
```

can cause Julia cognition to emit the intended logical Research request without Runtime semantic keyword routing.

Also prove negatives:

```text
"查一下天气"
"看看这段代码"
"不要查市场"
"我们聊聊阿里模型"
```

No generic string matching is used as semantic authority.

This stage has:

```text
PRODUCTION_ROUTING_AUTHORITY = 0
CANONICAL_ACCEPTANCE_AUTHORITY = 0
CAPABILITY_SIDE_EFFECT_AUTHORITY = 0
```

## P3-CC-A4 — Research composite authority review and freeze

**This stage is a hard prerequisite for any controlled or production Research ingress cutover with execution authority.**

Choose and formally approve one execution-authority model:

```text
Candidate A — cognitively selected high-level governed Research capability/program
Candidate B — model-directed stepwise capability selection
```

Required output:

```text
RESEARCH_COMPOSITE_AUTHORITY_DECISION = A | B
DECISION_STATUS = FROZEN / APPROVED
SOURCE_TRACE = PROVEN
CONTRACT_COMPATIBILITY = PASS
```

If no candidate is approved:

```text
RESEARCH_INGRESS_CUTOVER_AUTHORIZED = NO
```

## P3-CC-A5 — Controlled Research ingress cutover

Allowed only if:

```text
P3-CC-A2 = PASS
P3-CC-A3 = PASS
P3-CC-A4 = CLOSED_PASS / APPROVED
```

Then:

```text
model-selected Research request
→ approved governed Research execution model
```

Legacy deterministic Research ingress may remain physically present during migration, but it MUST be disabled/non-authoritative for the controlled path.

No dual production semantic authority.

## P3-CC-A6 — Legacy semantic router retirement + parity

Retire semantic authority from:

```text
requires_tool semantic authority
WorkflowRouter semantic authority
MarketBriefIntentResolver production semantic authority
deterministic Research keyword authority
```

Converge stream/non-stream semantics and preserve the frozen P7-T08 text/voice cognitive-parity target.

## P3-CC-A7 — Canonical acceptance

Fresh conversation.

Prove:

```text
natural-language research request
→ Julia cognition selects Research
→ approved governed execution
→ Evidence
→ Research Brief
→ canonical product
→ client rendering
→ restart
```

Also prove:

```text
RUNTIME_SEMANTIC_KEYWORD_ADMISSION = 0
UNAPPROVED_COMPOSITE_AUTHORITY = 0
SEMANTIC_ROUTER_FALLBACK = 0
```

---

# 21. Shadow / Qualification Rules

P3-CC must avoid creating a second production cognition authority merely for “shadow mode.”

Preferred qualification order:

```text
1. deterministic fixture corpus
2. controlled non-canonical model qualification
3. zero-side-effect controlled runtime observation
4. fresh canonical acceptance only after authorization
```

If production shadow observation is used, the shadow output must:

- have authority = 0;
- trigger no capability;
- write no canonical semantic decision;
- create no user/assistant turn;
- be clearly marked test/telemetry only.

---

# 22. Streaming / Non-Streaming Convergence

Both must consume the same logical:

```text
CognitiveContextPackage
→ Alignment
→ ModelInferenceRequest
→ ModelInferenceResult
→ capability loop
```

Differences may only include:

```text
delta transport
buffering
cancellation timing
delivery
```

A Research request that is cognitively selected in stream mode must be semantically selectable in non-stream mode under equivalent context and provider capability support.

---

# 23. Text / Voice Convergence

P3-CC must remain modality-independent.

Future target after M2:

```text
Text ─┐
      ├→ same ConversationRuntime
Voice ─┘
          ↓
       same Context OS
          ↓
       same Alignment semantics
          ↓
       same cognitive capability authority
```

Modality may affect representation/transport.

Modality must not create:

```text
VoiceIntentRouter
TextResearchRouter
voice-only semantic tool policy
```

---

# 24. Architecture-First Development Gate

This lesson becomes a permanent development prerequisite.

Before any production feature development:

```text
CANONICAL_ARCHITECTURE_READ = YES
RELEVANT_FROZEN_CONTRACTS_READ = YES
ARCHITECTURE_REGISTRY_READ = YES
CURRENT_SOURCE_AUDITED = YES

PROPOSED_CHANGE_CONFORMS_TO_FROZEN_ARCHITECTURE
= YES / NO / REQUIRES_REVIEW

ARCHITECTURE_AMENDMENT_REQUIRED
= YES / NO
```

If any required architecture read-in is missing:

```text
IMPLEMENTATION_AUTHORIZED = NO
```

Required design trace:

```text
REQUIREMENT
→ FROZEN AUTHORITY
→ CURRENT IMPLEMENTATION
→ GAP
→ PROPOSED CHANGE
→ CONTRACT IMPACT
→ ACCEPTANCE
```

Only a proven frozen-contract gap may initiate an architecture amendment review.

---

# 25. No-Critical-Fallback Requirements

Critical P3-CC path:

```text
Context OS
→ Alignment
→ ModelProvider
→ CapabilityRequest
→ Authorization
→ Provider
→ ToolResult/Evidence
→ Context OS
→ continuation
```

Forbidden:

```text
keyword semantic fallback
second semantic classifier fallback
silent tool substitution
silent provider substitution
synthetic evidence
synthetic success
fallback to local persona claiming execution
malformed tool request repair by guessing
unavailable tool → alternative tool selected by Runtime
```

Unknown remains unknown.

Failure remains failure.

---

# 26. Observability Requirements

Each capability-bearing turn should preserve observable correlation:

```text
conversation_id
turn_id
request_id
generation_id
context_package_id
alignment_profile/version
capability_request_id
capability_call_id
evidence_id(s)
action_id(s), when applicable
accepted conversation_message_id
provider/model/version
```

This does not include hidden chain-of-thought.

---

# 27. Regression Invariants

P3-CC must not regress:

```text
M1 Text ordinary continuity
M1 Text Research E2E
Market authority uniqueness
D1 authority
C1 verification state
C2 preliminary judgment
research.brief.v1 semantics
julia.product.events.v1 transport
Core canonical product persistence
restart continuity
NCF
Voice gen-2 conversation authority
```

Historical acceptance failures remain historical failures.

---

# 28. Workload Reassessment

Expected engineering scale:

| Work package | Estimate |
|---|---:|
| P3-CC-A1 final conformance/design matrix | 0.5–1 person-day |
| P3-CC-A2 CapabilityFrame→Alignment convergence | 1–2 |
| P3-CC-A3 model-owned selection qualification | 1–2 |
| P3-CC-A4 Research composite authority review/freeze | 1–2 |
| P3-CC-A5 controlled Research ingress cutover | 1–1.5 |
| P3-CC-A6/A7 legacy retirement/parity/acceptance | 1.5–2.5 |

```text
BEST CASE    ≈ 6 person-days
EXPECTED     ≈ 8–10 person-days
CONSERVATIVE ≈ 12 person-days
```

Largest uncertainty: P3-CC-A4 composite Research execution authority.

---

# 29. P3-CC Design Acceptance Gates

Before implementation authorization:

```text
[ ] Frozen architecture source matrix approved
[ ] No architecture amendment required
[ ] CapabilityFrame target projection defined
[ ] C-09 Alignment capability encoding defined
[ ] ModelInferenceRequest / ModelInferenceResult boundary confirmed
[ ] CapabilityRequest decoding/validation boundary defined
[ ] No Runtime semantic router introduced
[ ] Research composite authority decision APPROVED/FROZEN before any cutover
[ ] Legacy authority retirement plan defined
[ ] Stream/non-stream parity plan defined
[ ] Text/Voice semantic parity preserved
[ ] NCF review passes
[ ] M1 mutation = 0
```

---

# 30. Repo Governance Placement

**External review-copy location**: `/Users/admin/Downloads` (non-governed review copies).  
**Repository governance status**: NOT YET ENTERED / NOT FROZEN / NO IMPLEMENTATION AUTHORITY.


The v0.1 downloads were external drafts and therefore had no repository-governed status.

The v0.3 artifacts define the following **proposed** governance destinations for formal review:

```text
Design review artifact:
docs/architecture/P3_COGNITIVE_AGENCY_TOOL_LOOP_CONVERGENCE_DESIGN_v0.3.md

Derived contract review artifact:
docs/project_control/P3_CC_COGNITIVE_CAPABILITY_CONVERGENCE_CONTRACT_DRAFT_v0.3.md
```

Placement rules:

1. Copying/committing a draft into a governed directory does **not** make it frozen.
2. The design remains `DESIGN DRAFT` until review disposition is recorded.
3. The contract remains `DRAFT / NOT FROZEN / NONE authority` until explicit freeze authorization.
4. If the contract is later approved as an architecture-level derived contract, its final governed location and registry disposition MUST be explicitly approved; no automatic promotion to C-series is allowed.
5. Any architecture-level normative status requires consistency with `ARCHITECTURE_DOCUMENT_REGISTRY.md` and its precedence rules.
6. The reviewed v0.3 copies are external review/download artifacts under `/Users/admin/Downloads`; they are not repo-governed artifacts until an authorized repository commit places them in the approved governance paths.

Freeze review SHALL record:

```text
REPO_PATH = <approved path>
COMMIT_SHA = <mechanically captured>
DOCUMENT_STATUS = <approved disposition>
REGISTRY_IMPACT = NONE | UPDATE_REQUIRED
IMPLEMENTATION_AUTHORITY = NO until contract freeze is separately approved
```

---

# 31. Contract Derivation Map

The next P3-CC contract shall be derived from this design, not invented independently.

| Design area | Contract clause family |
|---|---|
| Cognitive ownership | P3-CC-01 |
| No semantic router | P3-CC-02 |
| CapabilityFrame | P3-CC-03 |
| Alignment encoding | P3-CC-04 |
| Model capability request | P3-CC-05 |
| Runtime authorization/execution | P3-CC-06 |
| Same-turn continuation | P3-CC-07 |
| Failure/no fallback | P3-CC-08 |
| Evidence/claim grounding | P3-CC-09 |
| Research Desk preservation | P3-CC-10 |
| Composite Research authority gate | P3-CC-11 |
| Legacy semantic authority retirement | P3-CC-12 |
| Stream/Text/Voice parity | P3-CC-13 |
| Architecture-first development gate | P3-CC-14 |
| Acceptance / causal history | P3-CC-15 |

The first contract version must remain:

```text
DRAFT / NOT FROZEN
```

until Tony explicitly reviews and authorizes freeze.

---

# 32. Final Design Law

```text
P3-CC IS NOT A SEMANTIC ROUTER.

P3-CC RESTORES THE FROZEN COGNITIVE BOUNDARY.

Julia cognition decides what the user means
and whether a capability is needed.

Context OS decides what governed information is visible.

Alignment decides how the same capability semantics
are represented to the selected model.

Runtime validates, authorizes, executes and traces.

CapabilityManager owns the governed execution lifecycle.

Domain authorities own domain truth.

Evidence proves observation/execution lineage.

ConversationRuntime owns canonical history.

Research Desk execution is preserved
unless a later formal authority review proves otherwise.

No keyword semantic authority.
No hidden semantic fallback.
No synthetic execution claim.

Read the architecture first.
Then design.
Then contract.
Then implement.
```

---

# Appendix A — Evidence Baseline

Repository: `tonychang925-dev/Julia_core`  
Baseline: `c14f6aa77a50dafc21a97083fac8cb97efc7231d`

Primary files reviewed:

```text
docs/architecture/ARCHITECTURE_DOCUMENT_REGISTRY.md
docs/architecture/C-00_COGNITIVE_BOUNDARY_CONTRACT.md
docs/architecture/C-01_RUNTIME_EXECUTION_CONTRACT.md
docs/architecture/C-03_CONTEXT_OS_CONTRACT.md
docs/architecture/C-07_MODEL_PROVIDER_CONTRACT.md
docs/architecture/C-08_CAPABILITY_TOOL_CONTRACT.md
docs/architecture/C-09_ALIGNMENT_CONTRACT.md
docs/architecture/C-12_EVIDENCE_ACTION_TRACE_CONTRACT.md
docs/audit/PRODUCTION_CONTRACT_RECONCILIATION.md

julia_core/runtime/julia_session.py
julia_core/runtime/context_execution_runtime.py
julia_core/runtime/capability_bridge.py
julia_core/runtime/research_continuation.py
julia_core/runtime/workflow_router.py
julia_core/reasoning/intents/market_brief.py
julia_core/capability/providers/ai_theme/frozen_market.py
julia_core/research/registration.py
julia_core/research/d1_provider.py
```

Important post-freeze regression lineage:

```text
b5b0b0d30634b65468b4f7852dd7005c65d774fa
RD1-L1-F2: add deterministic research desk ingress
```

Functional history remains preserved; this design only reclassifies architecture conformance.

---

# Appendix B — Status Snapshot

```text
M1_FUNCTIONAL_ACCEPTANCE = CLOSED_PASS
M1_GIT_FREEZE = VALID

P3_CC_A0_READ_ONLY_AUDIT = CLOSED_PASS
CURRENT_ROUTING_CONFORMANCE = OPEN_FAIL

RD1_FULL_REWRITE_REQUIRED = NO
RD1_RESEARCH_TRUTH_SPINE = PRESERVE
RD1_PRECOGNITIVE_INGRESS = REWORK
RD1_CHAIN_ORCHESTRATION_AUTHORITY = FORMAL_REVIEW_REQUIRED_BEFORE_CUTOVER

FROZEN_ARCHITECTURE_AMENDMENT = NOT_REQUIRED
FROZEN_WBS_PRIMARY_PHASE = P3
CONFLICTING_PHASE_ALIAS_USE_FOR_THIS_WORK = FORBIDDEN
BIG_BANG_REWRITE = NO
```
