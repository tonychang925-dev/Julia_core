# D3 — RD1 V1 P3-CC Implementation Contract — FINAL FREEZE CANDIDATE v0.2

**Task**: RD1-V1-P3CC-A3
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_P3CC_IMPLEMENTATION_CONTRACT_FREEZE_CANDIDATE_v0.1.md (preserved as causal history)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.2: governance gates moved BEFORE implementation; composite internal
> boundary ends at C1; exact paths; implementation branch separated from the
> governance review branch; rollback boundary made explicit.

---

## 0. Binding Fields

```text
TASK_ID
= RD1-V1-P3CC-IMPL (final id assigned at Owner freeze)

REPO_FULL_NAME
= tonychang925-dev/Julia_core

FREEZE_REVIEW_BRANCH
= governance/p3-cc-freeze-review-v0.3

IMPLEMENTATION_TARGET_BRANCH
= BLOCKED_PENDING_OWNER_AUTHORIZATION

IMPLEMENTATION_BASE_SHA
= BLOCKED_PENDING_OWNER_FREEZE
```

A governance review branch is not an implementation branch. Final delegation
replaces the two BLOCKED fields with exact values; until then
`IMPLEMENTATION_AUTHORIZED = NO`.

---

## 1. Governance Gates — BEFORE Any Implementation (A3 §7)

Architecture/contract freeze is NOT an implementation step. Required sequence:

```text
G0 — D2 Research Composite Authority = FROZEN
     (research.run_brief, C-08 governed capability, internal boundary
      resolve → read → enrich → C1; C2 = Julia cognition)

G1 — P3-CC contract = FROZEN / explicitly admitted as implementation authority
     (docs/project_control/P3_CC_COGNITIVE_CAPABILITY_CONVERGENCE_CONTRACT_DRAFT_v0.3.md)

G2 — upstream frozen-contract compatibility recheck = PASS
     (C-00/C-01/C-03/C-07/C-08/C-09/C-12)

G3 — Tony Owner implementation authorization = YES

G4 — exact implementation branch + base SHA bound (replace the two BLOCKED
     fields in §0)

ONLY THEN:
I1 — CapabilityFrame → Alignment implementation
I2 — ModelProvider capability encoding
I3 — model-owned logical CapabilityRequest production
I4 — non-authoritative qualification
I5 — activate model-owned Research composite ingress (research.run_brief)
I6 — retire deterministic F1 keyword ingress
I7 — retire semantic requires_tool / retry coercion
I8 — retire WorkflowRouter / MarketBriefIntentResolver semantic authority
I9 — stream/non-stream convergence
I10 — C2 Context OS / Alignment conformance
I11 — controlled canonical acceptance
```

The v0.1 contradiction (D2 freeze as step 4 inside migration) is removed. No
implementation step precedes G0–G4.

---

## 2. Top-Level Semantic Ingress Rule (A3 §8)

Replace the over-broad v0.1 statement. Corrected rule:

```text
Model capability output is the sole semantic top-level ingress
from ambiguous natural-language cognition into capability selection,
except frozen deterministic protocol/UI infrastructure commands
(C-00 §6 / C-08 §5 deterministic command exception).
```

Then, explicitly allowed:

```text
After a governed composite capability (research.run_brief) has been
cognitively selected, Runtime MAY deterministically construct the exact
internal sub-capability requests defined by the frozen composite contract:
market.event.resolve → market.event.read → research.event.enrich.
```

Every internal request still requires:

```text
CapabilityRequest
AuthorizationDecision
CapabilityCall
ToolResult
Evidence
Trace
correlation
```

No collapsed composite success artifact. The composite internal execution
boundary ends at C1 (see §10-§12); C2 and Research Brief occur after
ToolResult/Evidence re-entry through Context OS into Julia cognition.

---

## 3. Capability Responsibility Map (A3 §16)

```text
CapabilityRegistry
→ logical capability definitions (CapabilityDefinition; research.run_brief added)

Context OS / CapabilityFrame
→ governed model-visible logical manifest (context_execution_runtime.py)

Alignment
→ provider-specific representation (native tool/function schema OR
  text-based structured protocol); MUST NOT decide which capability the user
  needs

ModelProvider
→ provider invocation + capability output normalization
  (ModelInferenceResult.capability_requests[] / decoded text-protocol call)

Runtime
→ structural request validation / authorization / execution
  (manager lifecycle, typed outcomes)
```

---

## 4. Exact Allowed Paths (A3 §9)

Repository layout inspected at c14f6aa: `julia_core/alignment/` does not exist;
the C-09 Alignment package is `julia_core/alignment_os/` (adapter.py,
contracts.py, registry.py, resolver.py). Authorized paths below are derived from
that actual layout.

```text
julia_core/runtime/context_execution_runtime.py
  CapabilityFrame construction remains; remove pre-cognitive
  _resolve_market_context(user_text) market-intent prefetch decision

julia_core/runtime/julia_session.py
  remove F1 keyword admission (_build_research_desk_resolver_call +
  _research_intent_is_negated_only) from production authority;
  route research ingress through model-selected capability lifecycle;
  stream/non-stream parity; C2 schema via C-03/C-09

julia_core/runtime/capability_bridge.py
  remove requires_tool semantic authority (+ retry coercion trigger);
  keep detect_tool_call as structural text-protocol decoder;
  composite sub-request construction hooks

julia_core/runtime/research_continuation.py
  refactor SameTurnResearchContinuation boundary: composite evidence
  executor ends at C1 (ResearchEvidenceBundle) + ambiguity projection
  trigger; C2/brief orchestration moves to session-level continuation

julia_core/capability/registry.py
  register research.run_brief definition (schema per D2 v0.2 §3)

julia_core/capability/policy.py
  add research.run_brief permission scope rule (minimal, exact)

julia_core/alignment_os/capability_encoding.py        [NEW - authorized filename]
  CapabilityFrame → provider capability encoding (native schema OR text
  protocol per ProviderAdaptationProfile); no semantic intent authority

julia_core/runtime/workflow_router.py
  ALLOWED: minimal deletion/fencing of production semantic authority ONLY

julia_core/reasoning/intents/market_brief.py
  ALLOWED: minimal deletion/fencing of pre-cognitive semantic authority ONLY
  (MarketBriefIntentResolver)
```

### 4.1 Tests

Existing tests to keep green or update only during governed cutover:
`test_c1_rev2_cognitive_boundary.py`, `test_c1_rev2_sync_stream_authority.py`,
`test_l1_f2_deterministic_research_desk_ingress.py` (reclassified at I6 only),
`test_i1_streaming_capability_continuation.py`,
`test_i4_same_turn_research_orchestration.py`,
`test_r2_p3_2_3b_session_wiring.py`, `test_r2_p3_context_os_typed_projection.py`,
`test_c2_preliminary_research_judgment.py`.

Authorized new test filenames (actual tests/runtime/ convention):

```text
tests/runtime/test_p3cc_alignment_capability_encoding.py
tests/runtime/test_p3cc_model_owned_research_ingress.py
tests/runtime/test_p3cc_stream_nonstream_parity.py
tests/runtime/test_p3cc_research_ambiguity_continuation.py
tests/runtime/test_p3cc_requires_tool_no_production_callers.py
```

---

## 5. Forbidden Paths (A3 §10)

```text
Market provider implementation / source pins / tree digest
  (julia_core/capability/providers/ai_theme/frozen_market.py and pinned
   Market sources)
D1 provider transport (julia_core/research/d1_provider.py transport binding)
Assistant / Client / Voice repos
database data and migrations
model/provider configuration
trading logic (buy/sell/position/target price/execution)
generic workflow engine
legacy keyword-router enhancement (adding/expanding keyword or regex lists)
MarketBriefPipeline as a pre-cognitive router (execution-side domain logic may
  remain only semantically downstream of a cognitively selected capability)
```

WorkflowRouter / MarketBriefIntentResolver: they appear in §4 allowed paths for
**minimal deletion/fencing of production semantic authority** and remain
forbidden for **adding or expanding semantic routing logic**. The v0.1
contradiction is removed.

---

## 6. Forbidden Behavior (A3 §8 consolidated)

```text
adding "查一下" or any term to research_actions or any semantic keyword list
regex semantic inference as authority
intent classifier / LLM-classifier-as-Runtime-router authority
keeping deterministic ingress as fallback
keeping requires_tool as semantic fallback
silent capability substitution (composite ↔ primitive)
provider/model fallback
synthetic ToolResult / synthetic Evidence / synthetic research success
automatic ambiguous-event selection or hidden semantic ranking
C2 judgment as capability-internal executor semantics
Research Brief as capability observation truth
generic workflow engine
RD1 V1 scope expansion
restoring tool_manifest() as a direct system-prompt / C-03 bypass
new path failure silently routed to old F1 keyword ingress
```

---

## 7. `tool_manifest()` Final Disposition (A3 §17)

A1 finding preserved:

```text
tool_manifest()
= legacy implementation
= no proven production caller at c14f6aa
```

Disposition:

```text
tool_manifest() final disposition = B (deprecate/remove after the equivalent
  governed Alignment encoding exists), WITH A-permitted reuse:
  its logical manifest-generation pieces may be reused inside the governed
  Alignment path (julia_core/alignment_os/capability_encoding.py) as the
  source of the text-protocol representation for providers without native
  tools.

FORBIDDEN: restoring the old function as a direct system-prompt bypass of
  Context OS / Alignment.
```

---

## 8. `requires_tool()` Final Disposition (A3 §18)

```text
SEMANTIC_AUTHORITY
= REMOVE FROM PRODUCTION

KEYWORD TOOL-NEED CLASSIFICATION
= FORBIDDEN
```

If the function remains for legacy compatibility:

```text
production_callers
= 0
```

New test `test_p3cc_requires_tool_no_production_callers.py` must prove zero
production callers. No fallback use. The retry coercion
(`required_tool_call_missing` forced second pass) is retired with it.

---

## 9. WorkflowRouter Final Disposition (A3 §19)

```text
WorkflowRouter
= NO PRE-COGNITIVE SEMANTIC AUTHORITY

MarketBriefIntentResolver
= NO PRE-COGNITIVE SEMANTIC AUTHORITY

MarketBriefPipeline
= NO PRE-COGNITIVE SEMANTIC AUTHORITY
```

Reusable domain execution logic (context-block building, prediction-id
extraction, evidence assembly) may remain only semantically downstream of an
already cognitively selected capability. Minimal deletion/fencing edits are
authorized (§4); adding or expanding semantic routing logic is forbidden (§5-§6).

---

## 10. SameTurnResearchContinuation Implementation Disposition (A3 §13)

```text
SameTurnResearchContinuation
= FUNCTIONAL SPINE REUSE

TARGET RESPONSIBILITY
  composite evidence execution orchestration (resolve → read → enrich → C1)
  same-turn lifecycle
  per-step capability calls
  ambiguity projection trigger
  C1 output delivery (ResearchEvidenceBundle)

EXCLUDED
  C2 cognitive judgment ownership
  final Julia meaning interpretation
```

The current class physically invokes C2 inside `run()` (research_continuation.py
:340). The implementation contract **chooses: refactor the class boundary** —
separate the composite evidence executor (ends at C1 delivery + ambiguity
trigger) from the post-tool cognitive continuation (C2 + brief) that lives in
the session-level same-turn continuation. This is a binding choice, not a
coding-agent option.

---

## 11. C2 Boundary (A3 §14)

```text
C1
= evidence normalization / verification state

ToolResult + Evidence
→ C-03
→ C-09
→ ModelProvider

C2
= Julia model cognition
```

`form_preliminary_research_judgment()` must remain model cognition. The
implementation may rewire its context/Alignment path (C2 schema through
C-03/C-09, I10) but MUST NOT convert C2 to deterministic Runtime logic.

---

## 12. Research Brief Boundary (A3 §15)

Answer determined from accepted RD1 source/contract: Research Brief composition
is **A — deterministic product formatting from the C2 judgment** (assembled by
the caller/product hook as `research.brief.v1`, bound to `judgment_id`, then
persisted as a canonical structured product). Julia's final conversational
explanation is model continuation over the projected brief.

```text
RESEARCH_BRIEF
MUST NOT become capability observation truth.

Market/D1/C1 evidence and Julia C2 judgment remain distinguishable
  (evidence_refs + judgment_id + trace inside the brief).
```

---

## 13. Rollback Boundary (A3 §12)

```text
PRIMARY_ROLLBACK_BOUNDARY
= immutable git commit boundary
  (each migration step lands as its own commit on the implementation branch;
   rollback = revert to the last governed commit, never a live semantic switch)

IF FEATURE FLAGS ARE USED:
  FLAG_AUTHORITY_MODE = mutually exclusive
  DUAL_SEMANTIC_AUTHORITY = 0
  FALLBACK_TO_LEGACY_ROUTER = 0

FORBIDDEN:
  new path failure → silently route to old F1 keyword ingress
  new path failure → requires_tool / WorkflowRouter semantic fallback
```

---

## 14. Qualification Corpus Lifecycle (A3 §20)

A–N corpus retained from v0.1 with updated expected lifecycle for research
cases:

```text
model selects research.run_brief
→ Runtime composite evidence execution (resolve → read → enrich → C1)
→ ToolResult + Evidence (ResearchEvidenceBundle)
→ Context OS
→ Julia cognition (C2 preliminary judgment)
→ Research Brief (derived product)
→ final Julia continuation
```

not:

```text
capability internally produces Julia judgment
```

For `AMBIGUOUS`/`UNRESOLVED`:

```text
resolver result (observation, no selection)
→ Context OS
→ cognition
→ clarification / reformulation / stop
```

No hidden selection. Model-emits-no-capability (case K) and ordinary discussion
(case E/D) expect no forced tool. Direct-primitive cases (model chooses
`market.event.resolve` alone) remain valid with no substitution.

---

## 15. Acceptance Evidence + NCF (A3 §22)

Acceptance captures per P3-CC contract v0.3 §18: conversation_id, turn_id,
input digest, context_package_id, capability catalog version, alignment profile
version, provider/model/version, generation ids, model-emitted logical
capability request, authorization decision, capability ids/call ids, Market
event identity, D1 provenance, C1 refs, C2 judgment_id, Research Brief id,
evidence refs, assistant message id, product digest, restart readback.

NCF target:

```text
CRITICAL_PATH = YES
FALLBACK_INTRODUCED = NO
LEGACY_AUTHORITY_FALLBACK = NO
SYNTHETIC_SUCCESS = NO
MOCK_PRODUCTION_REACHABLE = NO
DUAL_SEMANTIC_AUTHORITY = NO
FAIL_CLOSED = YES
```

NCF static gate re-run at every implementation step; P0/P1 → REJECT.

---

## 16. Historical Invariants (A3 §21)

```text
M1_FUNCTIONAL_ACCEPTANCE = CLOSED_PASS          (unchanged)
RD1_FUNCTIONAL_SPINE = KEEP                     (unchanged)
Market authority = unchanged
D1 authority = unchanged
C1 semantics = unchanged
C2 semantics = unchanged
Conversation persistence = unchanged
Client rendering = unchanged
Voice = out of scope
```

Historical deterministic-ingress tests may be reclassified only during the
governed cutover (I6). History is not rewritten.

---

## 17. Implementation Contract Status (A3 §23)

```text
IMPLEMENTATION_CONTRACT_STATUS
= FINAL_FREEZE_CANDIDATE

IMPLEMENTATION_AUTHORIZED
= NO

IMPLEMENTATION_BASE_SHA
= BLOCKED_PENDING_OWNER_FREEZE

IMPLEMENTATION_TARGET_BRANCH
= BLOCKED_PENDING_OWNER_AUTHORIZATION

CONTRACT_FREEZE
= NO  (pending MIRA_SIS + OWNER final freeze sign-off)

NEXT_GATE
= MIRA_SIS + OWNER FINAL FREEZE SIGN-OFF
```
