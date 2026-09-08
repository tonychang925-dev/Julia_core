# D3 — RD1 V1 P3-CC Implementation Contract — FINAL FREEZE CANDIDATE v0.3

**Task**: RD1-V1-P3CC-A4
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_P3CC_IMPLEMENTATION_CONTRACT_FINAL_FREEZE_CANDIDATE_v0.2.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.3 binds the A4 object model: CapabilityManifestEntry (OPTION A),
> ResearchEvidenceBundle location, and the exact implementation object graph.
> All v0.2 governance ordering, ingress rule, and boundary dispositions are
> preserved.

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

A governance review branch is not an implementation branch.

---

## 1. Governance Gates — BEFORE Any Implementation (preserved from v0.2)

```text
G0 — D2 Research Composite Authority = FROZEN (research.run_brief, v0.3)
G1 — P3-CC contract = FROZEN / explicitly admitted as implementation authority
G2 — upstream frozen-contract compatibility recheck = PASS
G3 — Tony Owner implementation authorization = YES
G4 — exact implementation branch + base SHA bound

ONLY THEN:
I1 — CapabilityFrame → Alignment implementation
I2 — ModelProvider capability encoding
I3 — model-owned logical CapabilityRequest production
I4 — non-authoritative qualification
I5 — activate model-owned Research composite ingress
I6 — retire deterministic F1 keyword ingress
I7 — retire semantic requires_tool / retry coercion
I8 — retire WorkflowRouter / MarketBriefIntentResolver semantic authority
I9 — stream/non-stream convergence
I10 — C2 Context OS / Alignment conformance
I11 — controlled canonical acceptance
```

No implementation step precedes G0-G4. Object-model work (CapabilityManifestEntry,
ResearchEvidenceBundle, registry/policy registration) is part of I1 and is
likewise gated.

---

## 2. Top-Level Semantic Ingress Rule (preserved)

```text
Model capability output is the sole semantic top-level ingress from ambiguous
natural-language cognition into capability selection, except frozen
deterministic protocol/UI infrastructure commands (C-00 §6 / C-08 §5).

After a governed composite capability (research.run_brief) has been
cognitively selected, Runtime MAY deterministically construct the exact
internal sub-capability requests defined by the frozen composite contract:
market.event.resolve → market.event.read → research.event.enrich.
```

Every internal request preserves CapabilityRequest / AuthorizationDecision /
CapabilityCall / ToolResult / Evidence / Trace / correlation. Composite
internal execution boundary ends at C1.

---

## 3. Object-Graph Bindings (A4 §25 — exact target object graph)

```text
CapabilityDefinition                 (capability/models.py — registry source truth)
        +
PermissionPolicy                    (capability/policy.py — authorization)
        +
Provider / Runtime Availability     (registry status + provider binding)
        ↓
CapabilityManifestEntry[]            (capability/models.py — derived, OPTION A)
        ↓
CapabilityFrame                      (runtime/context_execution_runtime.py)
        ↓
C-03 Context OS
        ↓
C-09 Alignment                       (alignment_os/capability_encoding.py [NEW])
        ↓
ModelProvider

Model capability request
        ↓
CapabilityRequest
        ↓
Runtime / CapabilityManager
        ↓
research.run_brief composite executor (runtime/research_continuation.py)
        ↓
primitive governed calls: market.event.resolve → market.event.read
                         → research.event.enrich
        ↓
ResearchEvidenceBundle                (research/contracts.py)
        ↓
ToolResult + Evidence
        ↓
Context OS
        ↓
Julia C2 cognition
```

---

## 4. Exact Allowed Paths (A4 §24 matrix — no `?`)

Repository layout inspected at c14f6aa: `julia_core/alignment/` does not exist;
the C-09 Alignment package is `julia_core/alignment_os/`. The C1 research
contract module is `julia_core/research/contracts.py` (already defines
MarketEvent/MarketEventRelation/VerificationState/NormalizedResearchEnrichment).

| Required change | Exact authorized path |
| --------------- | --------------------- |
| manifest model (CapabilityManifestEntry) | `julia_core/capability/models.py` |
| manifest enums (SideEffectClass, IdempotencySupport) | `julia_core/capability/models.py` |
| CapabilityDefinition NEW declarative fields (output_schema, side_effect_class, idempotency_support, latency_cost_hints, data_sensitivity) | `julia_core/capability/models.py` |
| registry derivation (definitions → CapabilityManifestEntry assembly) | `julia_core/capability/registry.py` |
| permission rule (research.run_brief scope, allow=TRUE) | `julia_core/capability/policy.py` |
| availability projection (status AND over sub-capabilities at frame build) | `julia_core/runtime/context_execution_runtime.py` |
| CapabilityFrame projection (structured manifest entries + availability) | `julia_core/runtime/context_execution_runtime.py` |
| Alignment capability encoding (manifest → native schema OR text protocol) | `julia_core/alignment_os/capability_encoding.py` **[NEW — authorized filename]** |
| ResearchEvidenceBundle model | `julia_core/research/contracts.py` |
| composite executor (research.run_brief; refactor SameTurn boundary to end at C1 + ambiguity trigger + REQUEST_KEY dedupe) | `julia_core/runtime/research_continuation.py` |
| session continuation (C2/brief after ToolResult re-entry; parity) | `julia_core/runtime/julia_session.py` |
| F1 keyword ingress removal | `julia_core/runtime/julia_session.py` |
| requires_tool semantic retirement + retry-coercion removal | `julia_core/runtime/capability_bridge.py` |
| WorkflowRouter fencing (minimal deletion/fencing of semantic authority) | `julia_core/runtime/workflow_router.py` |
| MarketBriefIntentResolver fencing | `julia_core/reasoning/intents/market_brief.py` |
| tests | `tests/runtime/test_p3cc_alignment_capability_encoding.py`, `tests/runtime/test_p3cc_model_owned_research_ingress.py`, `tests/runtime/test_p3cc_stream_nonstream_parity.py`, `tests/runtime/test_p3cc_research_ambiguity_continuation.py`, `tests/runtime/test_p3cc_requires_tool_no_production_callers.py`, `tests/runtime/test_p3cc_manifest_derivation.py` |

No implementation file required by this contract lies outside `allowed_paths`.
No authorized path is required by more than the changes listed in §3/§4.

---

## 5. Forbidden Paths (preserved)

```text
Market provider implementation / source pins / tree digest
D1 provider transport
Assistant / Client / Voice repos
database data and migrations
model/provider configuration
trading logic
generic workflow engine
legacy keyword-router enhancement (adding/expanding keyword or regex lists)
MarketBriefPipeline as a pre-cognitive router
julia_core/capability/manager.py            (no change required; read-only state)
julia_core/research/judgment.py             (C2 semantics unchanged)
julia_core/alignment_os/contracts.py / registry.py / resolver.py / adapter.py
                                            (persona/behavior alignment unchanged;
                                             only the NEW capability_encoding.py is added)
```

WorkflowRouter / MarketBriefIntentResolver are allowed ONLY for minimal
deletion/fencing of production semantic authority (§4); adding or expanding
semantic routing logic remains forbidden.

---

## 6. Forbidden Behavior (preserved + object-model additions)

```text
adding keyword lists / "查一下" / regex semantic inference
intent classifier / LLM-classifier-as-Runtime-router authority
deterministic ingress or requires_tool kept as semantic fallback
silent capability substitution (composite ↔ primitive)
provider/model fallback
synthetic ToolResult / Evidence / research success / availability
automatic ambiguous-event selection or hidden semantic ranking
C2 as capability-internal executor semantics
Research Brief as capability observation truth
generic workflow engine
RD1 V1 scope expansion
tool_manifest() restored as a direct system-prompt / C-03 bypass
new path failure silently routed to old F1 keyword ingress
a SECOND capability registry or SECOND manifest authority
a parallel permission authority
a second Evidence truth authority
model-visible capability list filtered by inferred user topic
```

---

## 7. `tool_manifest()` Final Disposition (preserved)

```text
tool_manifest() = legacy implementation; no proven production caller at
c14f6aa. Final disposition = B (deprecate/remove after equivalent governed
Alignment encoding exists), WITH A-permitted reuse of its logical
manifest-generation pieces inside julia_core/alignment_os/capability_encoding.py.
FORBIDDEN: restoring it as a direct Context OS / Alignment bypass.
```

---

## 8. `requires_tool()` Final Disposition (preserved)

```text
SEMANTIC_AUTHORITY = REMOVE FROM PRODUCTION
KEYWORD TOOL-NEED CLASSIFICATION = FORBIDDEN
production_callers = 0 (proved by test_p3cc_requires_tool_no_production_callers.py)
```

---

## 9. WorkflowRouter Final Disposition (preserved)

```text
WorkflowRouter / MarketBriefIntentResolver / MarketBriefPipeline
= NO PRE-COGNITIVE SEMANTIC AUTHORITY

Reusable domain execution logic may remain only semantically downstream of an
already cognitively selected capability.
```

---

## 10. SameTurnResearchContinuation Implementation Disposition (preserved)

```text
SameTurnResearchContinuation = FUNCTIONAL SPINE REUSE

TARGET: composite evidence executor — resolve → read → enrich → C1 —
producing ResearchEvidenceBundle; ambiguity projection trigger;
REQUEST_KEY dedupe. EXCLUDED: C2 judgment ownership and final Julia meaning
interpretation.

Binding choice: REFACTOR THE CLASS BOUNDARY — composite evidence execution
ends at C1 delivery; C2 + Research Brief orchestration moves to the
session-level post-tool cognitive continuation (julia_session.py).
```

---

## 11. C2 and Research Brief Boundaries (preserved)

C2 = Julia model cognition after ToolResult/Evidence re-entry via C-03/C-09.
`form_preliminary_research_judgment()` remains model cognition (its
context/Alignment path may be rewired at I10; it must never become
deterministic Runtime logic).

Research Brief = A — deterministic product formatting from C2 judgment +
evidence (product-layer owned, `research.brief.v1`, bound to judgment_id).
It MUST NOT become capability observation truth. Market/D1/C1 evidence and
Julia C2 judgment stay distinguishable.

---

## 12. Rollback Boundary (preserved)

```text
PRIMARY_ROLLBACK_BOUNDARY = immutable git commit boundary
FLAG_AUTHORITY_MODE = mutually exclusive
DUAL_SEMANTIC_AUTHORITY = 0
FALLBACK_TO_LEGACY_ROUTER = 0
FORBIDDEN: new path failure → silently route to old F1 keyword ingress or
requires_tool / WorkflowRouter semantic fallback
```

---

## 13. Qualification Corpus Lifecycle (preserved)

Research cases expect:

```text
model selects research.run_brief
→ Runtime composite evidence execution (resolve → read → enrich → C1)
→ ToolResult + Evidence (ResearchEvidenceBundle)
→ Context OS
→ Julia cognition (C2 preliminary judgment)
→ Research Brief (derived product)
→ final Julia continuation
```

AMBIGUOUS/UNRESOLVED → resolver observation → Context OS → cognition →
clarification/reformulation/stop. No hidden selection. Model-emits-no-capability
and ordinary-discussion cases expect no forced tool. Direct-primitive selection
remains valid with no substitution.

---

## 14. Acceptance Evidence + NCF

Acceptance captures per P3-CC contract v0.3 §18 (unchanged), plus manifest
binding evidence: capability catalog version (research.run_brief manifest
digest), alignment profile/version, ResearchEvidenceBundle bundle_contract id.

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

## 15. Historical Invariants (preserved)

M1_FUNCTIONAL_ACCEPTANCE = CLOSED_PASS (unchanged). RD1_FUNCTIONAL_SPINE =
KEEP. Market / D1 / C1 / C2 semantics, Conversation persistence, Client
rendering unchanged. Voice out of scope. History not rewritten.

---

## 16. Implementation Contract Status

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
= NO  (pending MIRA_SIS + OWNER final mechanical freeze sign-off)

NEXT_GATE
= MIRA_SIS + OWNER FINAL MECHANICAL FREEZE SIGN-OFF
```
