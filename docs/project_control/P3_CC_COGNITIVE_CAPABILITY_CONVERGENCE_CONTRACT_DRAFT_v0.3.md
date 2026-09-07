# P3-CC — Cognitive Agency / Tool Loop Convergence — Cognitive Capability Convergence Contract Draft v0.3

**Status**: DRAFT — NOT FROZEN  
**Normative authority**: NONE until explicitly reviewed and frozen  
**Derived from**: P3-CC Cognitive Agency / Tool Loop Convergence — Cognitive Capability Convergence Design v0.2  
**Upstream authority**: Existing Frozen Unified Architecture + C-00/C-01/C-03/C-07/C-08/C-09/C-12  
**Baseline Core**: `c14f6aa77a50dafc21a97083fac8cb97efc7231d`  
**Primary frozen WBS phase**: `P3 — Cognitive Agency / Tool Loop Convergence`  
**Cross-phase dependencies**: P2 / P6 / P7 / P8  
**Proposed repo review path**: `docs/project_control/P3_CC_COGNITIVE_CAPABILITY_CONVERGENCE_CONTRACT_DRAFT_v0.3.md`  
**Current file authority**: external/download review copy only  
**Purpose**: Bind P3 cognitive/tool-loop convergence implementation to already-frozen Julia Core cognitive/capability architecture without amending it.

---

# 0. Contract Status Law

This document is a **derived convergence contract draft**.

It SHALL NOT:

- supersede the Unified Architecture;
- supersede any Frozen C-series contract;
- retroactively rewrite M1 or RD1 history;
- authorize production code changes by itself;
- create a new canonical architecture layer.

If a clause conflicts with an upstream Frozen contract:

```text
UPSTREAM FROZEN CONTRACT WINS
P3-CC CLAUSE = INVALID
```

Freeze requires explicit Tony approval after architecture review.

---

# 1. Frozen WBS Namespace Binding

This contract is bound to the frozen WBS namespace:

```text
P3 = Cognitive Agency / Tool Loop Convergence
The existing frozen Identity / Memory Convergence phase remains unchanged and is out of scope.
```

Therefore:

```text
P3-CC = derived contract family inside frozen P3
      ≠ new project phase
      ≠ replacement for P3-T01..T09
```

Primary frozen task coverage:

```text
P3-T01 ModelProvider tool-call normalization
P3-T02 Permission gate
P3-T03 Capability execution
P3-T04 ToolResult evidence
P3-T05 Context incremental reinjection
P3-T06 Model continuation
P3-T07 Remove broad Runtime semantic tool routers
P3-T08 Preserve explicit infrastructure routing exceptions
P3-T09 Grounding tests
```

Cross-phase dependencies include P2-T07/P2-T14, P6-T05, P7-T08 and P8 retirement work.

This contract SHALL NOT redefine the frozen WBS phase boundaries or exit criteria.

---

# P3-CC-01 — Cognitive Selection Authority

```text
Semantic interpretation
Intent understanding
Tool-need recognition
Logical capability selection
```

SHALL belong to Julia cognition executed through the ModelProvider.

Runtime SHALL NOT semantically infer an ambiguous natural-language request and choose a capability/workflow on Julia's behalf.

Allowed Runtime decisions are structural/deterministic only.

Examples:

```text
explicit command ID
conversation_id
turn_id
modality
event type
permission state
capability availability
schema validation
transport state
```

---

# P3-CC-02 — No Pre-Cognitive Semantic Router

Production SHALL NOT introduce or retain as semantic authority:

```text
keyword intent router
regex intent router
classifier intent router
LLM classifier whose output is used by Runtime to choose capability
domain workflow router that interprets user meaning before Julia cognition
```

A classifier does not become compliant merely because it uses an LLM.

Test:

> If the decision requires understanding “what the user really means,” the decision belongs to cognition, not Runtime routing.

Explicit deterministic commands are outside this prohibition because the command itself already encodes the requested operation.

---

# P3-CC-03 — CapabilityFrame Contract

Context OS SHALL project a model-visible CapabilityFrame from canonical capability sources.

At minimum:

```text
capability_id
description
input_schema
```

CapabilityFrame:

```text
= derived projection
≠ execution authority
≠ semantic routing authority
```

Runtime/Context OS MUST NOT hide or include capabilities based on inferred user semantic intent.

Deterministic filtering MAY occur for:

```text
permission
availability
provider feature support
policy
side-effect restrictions
security
```

Every projected capability SHALL preserve provenance to its source definition/policy.

---

# P3-CC-04 — Alignment Capability Encoding

Alignment SHALL convert the same logical CapabilityFrame into the selected ModelProvider's supported representation.

Allowed:

```text
native function/tool schema
textual structured tool protocol
provider-specific escaping/encoding
unsupported-feature reporting
```

Forbidden:

```text
Alignment chooses whether tool is needed
Alignment chooses capability for Julia
Alignment injects semantic conclusion
Alignment hides capability because it infers user intent
Alignment selects domain/provider transport
```

Weak-model capability compensation is permitted.

Weak-model cognitive compensation by pre-solving user meaning is forbidden.

---

# P3-CC-05 — Model Capability Request

A capability request SHALL originate as observable cognitive output from a ModelInferenceResult, except for explicit deterministic commands allowed by C-00/C-08.

Logical form:

```text
CapabilityRequest {
    capability_id
    arguments
    turn_id
    generation_id
    correlation_id
}
```

The model MAY choose:

```text
logical capability
logical arguments
```

The model MUST NOT choose execution authority fields such as:

```text
provider
provider_id
endpoint
transport
proxy
browser_session_id
database transport
release identity
```

---

# P3-CC-06 — Runtime Admission and Execution

Runtime SHALL execute only after one of:

```text
A. cognitively selected CapabilityRequest
B. explicit deterministic command request
C. separately frozen system/lifecycle action explicitly allowed by upstream contract
```

Before execution Runtime SHALL deterministically validate:

```text
capability exists
arguments conform to schema
permission
availability
side-effect policy
turn/generation/correlation identity
provider binding readiness
forbidden authority fields absent
```

Execution SHALL proceed through the governed CapabilityManager lifecycle.

---

# P3-CC-07 — Same-Turn Continuation

Capability use SHALL remain within one logical turn:

```text
generation G1
→ capability request
→ execution
→ ToolResult/Evidence
→ Context OS projection
→ Alignment
→ generation G2
→ final response
```

Invariant:

```text
conversation_id unchanged
turn_id unchanged
generation_id may change
```

Tool results SHALL NOT be converted into fake user turns.

Runtime progress events SHALL NOT become canonical assistant messages.

---

# P3-CC-08 — Fail-Closed / No Semantic Fallback

The critical cognitive/capability path MUST fail closed.

Forbidden:

```text
keyword semantic fallback
secondary semantic router fallback
silent capability substitution
silent provider substitution
guessed tool arguments
malformed tool-call repair by semantic guessing
synthetic ToolResult
synthetic Evidence
ordinary persona success after capability failure
```

Unknown stays UNKNOWN.

Unavailable stays UNAVAILABLE.

Failure stays FAILED.

Any provider/model fallback permitted elsewhere by frozen policy must remain explicit and fully traceable; P3-CC itself grants no fallback authority.

---

# P3-CC-09 — Evidence and External-Claim Grounding

External observation claims require C-12 evidence.

```text
"I checked / searched / read / found ..."
→ TOOL_OBSERVATION evidence required
```

External action claims require Action evidence.

A model inference alone SHALL NOT be upgraded into an observation.

No new canonical ExecutionReceipt is required.

A non-authoritative execution-attestation projection MAY summarize existing:

```text
capability_request_id
capability_call_id
evidence_id
action_id
status
```

for response governance/UI.

---

# P3-CC-10 — Research Desk Preservation

The following RD1 assets SHALL be preserved unless a later evidence-backed review proves a defect in their own authority boundary:

```text
Market event authority
market.event.resolve/read contracts
D1 controlled research
research normalization
C1 verification
C2 preliminary judgment
Research Brief
structured product transport
Core canonical product persistence
Client rendering
restart continuity
```

P3-CC SHALL NOT treat Research ingress conformance debt as evidence that the downstream Research truth spine must be rewritten.

---

# P3-CC-11 — Research Composite Authority Gate

Current `SameTurnResearchContinuation` SHALL be classified:

```text
FUNCTIONAL_REUSE = ALLOWED
CANONICAL_COMPOSITE_AUTHORITY = NOT YET APPROVED
```

Before **any controlled or production Research ingress cutover with execution authority**, architecture review MUST choose and freeze one model:

```text
A. cognitively selected high-level governed Research capability/program
B. model-directed stepwise capability selection
```

The only activity permitted before that decision is non-authoritative qualification with:

```text
PRODUCTION_ROUTING_AUTHORITY = 0
CANONICAL_ACCEPTANCE_AUTHORITY = 0
CAPABILITY_SIDE_EFFECT_AUTHORITY = 0
```

If Candidate A is approved, the high-level program MUST prove:

1. Julia cognition selects the research objective/capability.
2. Runtime does not reinterpret the objective.
3. Internal sub-capabilities remain governed and individually traceable.
4. Each sub-call preserves CapabilityRequest/Call/ToolResult/Evidence identity.
5. Internal sequencing is deterministic execution logic, not new semantic judgment.
6. Any ambiguity requiring meaning is returned to cognition rather than guessed.
7. Failure at any critical sub-boundary remains explicit and fail-closed.

No implementation may silently assume Candidate A is already frozen.

Hard gate:

```text
RESEARCH_COMPOSITE_AUTHORITY_DECISION = APPROVED/FROZEN

otherwise

RESEARCH_INGRESS_CUTOVER_AUTHORIZED = NO
```

---

# P3-CC-12 — Legacy Semantic Authority Retirement

The following SHALL be treated as migration debt and SHALL NOT gain new product responsibility:

```text
_build_research_desk_resolver_call()
_research_intent_is_negated_only()
requires_tool() semantic keyword detection
WorkflowRouter semantic dispatch
MarketBriefIntentResolver pre-cognitive path
pre-cognitive _resolve_market_context(user_text)
```

Retirement order:

```text
build compliant replacement
→ qualify
→ controlled cutover
→ prove single authority
→ retire legacy
```

Deletion-first big-bang migration is prohibited.

During migration there MUST NOT be two simultaneously authoritative semantic routers.

---

# P3-CC-13 — Stream / Non-Stream / Modality Parity

Streaming and non-streaming MUST share the same:

```text
Context OS semantics
Alignment semantics
capability availability semantics
model-owned capability selection semantics
authorization semantics
ToolResult projection semantics
completion semantics
```

Text and Voice MUST converge on the same cognitive/capability authority.

Forbidden:

```text
TextResearchRouter
VoiceIntentRouter
voice-only semantic tool policy
stream-only research cognition policy
```

Transport/media differences are allowed.

Semantic authority differences are not.

---

# P3-CC-14 — Architecture-First Development Gate

Before any production feature or critical-path refactor:

```text
CANONICAL_ARCHITECTURE_READ = YES
RELEVANT_FROZEN_CONTRACTS_READ = YES
ARCHITECTURE_REGISTRY_READ = YES
CURRENT_SOURCE_AUDITED = YES
```

The work item MUST record:

```text
REQUIREMENT
FROZEN_AUTHORITY
CURRENT_IMPLEMENTATION
CONFORMANCE_GAP
PROPOSED_CHANGE
CONTRACT_IMPACT
ACCEPTANCE_PLAN
```

It MUST also state:

```text
PROPOSED_CHANGE_CONFORMS_TO_FROZEN_ARCHITECTURE
= YES / NO / REQUIRES_REVIEW

ARCHITECTURE_AMENDMENT_REQUIRED
= YES / NO
```

If architecture read-in is incomplete:

```text
IMPLEMENTATION_AUTHORIZED = NO
```

If current implementation differs from frozen architecture:

```text
DO NOT assume architecture is wrong.
First classify implementation convergence debt.
```

Only a proven frozen-contract gap may open an architecture amendment review.

---

# P3-CC-15 — Acceptance and Causal History

P3-CC changes MUST NOT rewrite historical acceptance status.

M1 remains:

```text
M1_FUNCTIONAL_ACCEPTANCE = CLOSED_PASS
M1_GIT_FREEZE = VALID
```

Historical failures remain failures.

New P3-CC acceptance IDs SHALL be new causal events.

A P3-CC acceptance MUST use a fresh conversation where canonical turns are involved.

No acceptance may claim compliance merely because output quality is good.

It must prove the authority path.

---

# 16. Repo Governance / Freeze Entry

**External review-copy location**: `/Users/admin/Downloads` (non-governed review copy).  
**Repository governance status**: NOT YET ENTERED / NOT FROZEN / NO IMPLEMENTATION AUTHORITY.

This draft has no governed repository authority while it exists only as an external/download file.

Proposed formal review path:

```text
docs/project_control/P3_CC_COGNITIVE_CAPABILITY_CONVERGENCE_CONTRACT_DRAFT_v0.3.md
```

Entering that path is necessary for repo-governed review but is **not sufficient** for freeze.

Before freeze, the review must record:

```text
REPO_PATH = approved
COMMIT_SHA = mechanically captured
DOCUMENT_STATUS = DRAFT/REVIEW until explicit freeze
REGISTRY_IMPACT = NONE | UPDATE_REQUIRED
UPSTREAM_CONTRACT_COMPATIBILITY = PASS
RESEARCH_COMPOSITE_AUTHORITY_DECISION = APPROVED/FROZEN
IMPLEMENTATION_AUTHORITY = NO
```

If this document is later promoted from project-control draft to architecture-level derived contract, its final path and `ARCHITECTURE_DOCUMENT_REGISTRY.md` disposition must be explicitly approved. It SHALL NOT become a C-series contract by naming convention or file placement alone.

---

# 17. Implementation Gate Matrix

Before P3-CC production cutover:

```text
[ ] CapabilityFrame source/provenance proven
[ ] C-09 Alignment capability encoding proven
[ ] ModelInferenceResult capability request proven
[ ] provider/transport authority remains outside model
[ ] Runtime validation/authorization proven
[ ] ToolResult/Evidence C-03 re-entry proven
[ ] same-turn continuation proven
[ ] no semantic keyword fallback
[ ] no second semantic router
[ ] Research composite authority APPROVED/FROZEN BEFORE ingress cutover
[ ] legacy semantic routing disabled as authority
[ ] stream/non-stream parity proven
[ ] Text/Voice semantic contract preserved
[ ] external-execution claim grounding proven
[ ] NCF gate PASS
[ ] M1 mutation = 0
[ ] Frozen WBS phase namespace = P3
[ ] Repo-governed review path + commit SHA captured
```

---

# 18. Required P3-CC Acceptance Evidence

For a canonical natural-language research acceptance, capture:

```text
conversation_id
turn_id
user input bytes/digest

context_package_id
capability catalog/version or digest
alignment profile/version
provider/model/version

generation G1 id
model-emitted logical capability request
capability_request_id
authorization decision
capability_call_id

research sub-call identities
Market event identity
D1 provenance
C1 verification refs
C2 judgment_id
Research Brief id

ToolResult/evidence refs
generation G2 id
assistant message id
structured product digest

restart readback
```

Also prove:

```text
RUNTIME_SEMANTIC_KEYWORD_ADMISSION = 0
SEMANTIC_ROUTER_FALLBACK = 0
SYNTHETIC_SUCCESS = 0
CRITICAL_FALLBACK = 0
```

---

# 19. Contract Freeze Preconditions

This draft MUST NOT be frozen until:

```text
1. Tony reviews the design.
2. Upstream C-00/C-01/C-03/C-07/C-08/C-09/C-12 compatibility is rechecked.
3. Research Composite Authority Gate is resolved or explicitly left as a blocking clause.
4. No clause silently amends a frozen upstream contract.
5. Contract name/location in repository governance hierarchy is approved and the reviewed draft is committed at that governed path.
6. Acceptance criteria are judged executable and observable.
7. Research composite authority decision is approved/frozen before any ingress cutover authority.
8. Frozen WBS namespace mapping remains `P3`; no conflicting phase alias remains.
```

Until then:

```text
P3-CC_STATUS = DRAFT
P3-CC_NORMATIVE_AUTHORITY = NONE
PRODUCTION_CHANGE_AUTHORIZED_BY_THIS_DOCUMENT = NO
```

---

# 20. Final Contract Law

```text
Julia understands.
Runtime orchestrates.

Julia decides whether a capability is cognitively needed.
Runtime does not infer that decision from ambiguous language.

Context OS exposes governed capability information.
Alignment faithfully encodes it for the model.

The model selects logical capability and arguments.
The model does not select provider or transport.

Runtime validates, authorizes, executes and traces.
Tool results return through Context OS and Alignment.

External observation claims require evidence.

Research Desk truth machinery is preserved.
Its execution authority is formally reviewed, not guessed.

No semantic router.
No keyword authority.
No synthetic success.
No hidden fallback.

Architecture first.
Contract second.
Implementation third.
Acceptance last.
```
