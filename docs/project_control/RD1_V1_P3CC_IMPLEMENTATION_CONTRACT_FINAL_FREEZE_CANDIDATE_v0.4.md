# D3 — RD1 V1 P3-CC Implementation Contract — FINAL FREEZE CANDIDATE v0.4

**Task**: RD1-V1-P3CC-A5
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_P3CC_IMPLEMENTATION_CONTRACT_FINAL_FREEZE_CANDIDATE_v0.3.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.4 implements the A5 deltas only: fail-closed metadata defaults,
> side-effect admission gate, availability lifecycle (OPTION_C), production
> definition inventory, exact allowed paths, new tests. All v0.3 ordering,
> ingress rule, dispositions, and boundaries are preserved.

---

## 0. Binding Fields (preserved)

```text
TASK_ID = RD1-V1-P3CC-IMPL (final id at Owner freeze)
REPO_FULL_NAME = tonychang925-dev/Julia_core
FREEZE_REVIEW_BRANCH = governance/p3-cc-freeze-review-v0.3
IMPLEMENTATION_TARGET_BRANCH = BLOCKED_PENDING_OWNER_AUTHORIZATION
IMPLEMENTATION_BASE_SHA = BLOCKED_PENDING_OWNER_FREEZE
```

---

## 1. Governance Gates (preserved) + A5 Metadata Gate

```text
G0 — D2 Research Composite Authority = FROZEN (research.run_brief, v0.4)
G1 — P3-CC contract = FROZEN / admitted as implementation authority
G2 — upstream frozen-contract compatibility recheck = PASS
G3 — Tony Owner implementation authorization = YES
G4 — exact implementation branch + base SHA bound

G5 — A5 metadata gate (NEW):
     UNCLASSIFIED_MANIFEST_COUNT = 0 for the controlled RD1 acceptance surface
     (every production-reachable definition has explicit side_effect_class;
      engineering.code_review = EXTERNAL_SIDE_EFFECT; no READ_ONLY default)

ONLY THEN: I1 — I11 (preserved ordering)
```

---

## 2. Top-Level Semantic Ingress Rule (preserved)

Model capability output is the sole semantic top-level ingress from ambiguous
natural-language cognition into capability selection, except frozen
deterministic protocol/UI infrastructure commands. After a governed composite
capability is cognitively selected, Runtime MAY deterministically construct the
exact internal sub-requests. Every internal request preserves CapabilityRequest
/ AuthorizationDecision / CapabilityCall / ToolResult / Evidence / Trace /
correlation. Composite internal boundary ends at C1.

---

## 3. Exact Implementation Fields and Defaults (A5)

New CapabilityDefinition fields and their exact defaults (fail-closed):

```text
output_schema:        dict[str, str]        = {}   # undeclared, not "correct"
side_effect_class:    SideEffectClass | None = None  # UNCLASSIFIED ≠ READ_ONLY
idempotency_support:  IdempotencySupport    = NONE # not retry-safe
latency_cost_hints:   dict[str, str]        = {}   # informational only
data_sensitivity:     str                   = ""   # NOT_DECLARED ≠ PUBLIC
```

New enums (capability/models.py):

```text
class SideEffectClass(str, Enum):
    READ_ONLY, REVERSIBLE_WRITE, IRREVERSIBLE_WRITE,
    EXTERNAL_SIDE_EFFECT, HIGH_IMPACT
    # EXACT C-08 §7 vocabulary; NO UNKNOWN member added

class IdempotencySupport(str, Enum):
    NONE = "none"
    REQUEST_KEY = "request_key"
```

Manifest admission rule (fail-closed):

```text
A CapabilityDefinition with side_effect_class is None is NOT admitted to the
model-visible executable CapabilityManifestEntry[] path. Projection emits an
explicit governed diagnostic (kind=capability_not_admitted,
reason=unclassified_side_effect). Never defaulted to READ_ONLY.
```

---

## 4. Production Definition Classification Inventory (A5 §25 — frozen)

Authoritative migration table (also in D2 v0.4 §4). Registration paths must
carry these explicit classifications at implementation (G5 gate):

```text
file.read / file.search / file.list
  side_effect=READ_ONLY  sensitivity=local_user_files  idempotency=NONE
  output_schema={}       source=capability_bridge.initialize (status AVAILABLE)

market.event.resolve / market.event.read / market.snapshot.read /
market.alert.query
  side_effect=READ_ONLY  sensitivity=market_observe  idempotency=NONE
  output_schema={}       source=frozen_market / ai_theme registration
                         (AVAILABLE in provider-first composition)

market.intelligence.observe / market.decision.explain / market.stock.history /
market.stock.auction / market.theme.constituents / market.theme.capital /
market.regime.read   [legacy ai_theme spec list]
  side_effect=READ_ONLY (intrinsic read)  sensitivity=market_observe
  idempotency=NONE
  derived availability = NOT-AVAILABLE under the frozen Market provider
  (not in _OPERATIONS_BY_CAPABILITY); canonical composition registers only the
  executable frozen surface as AVAILABLE

research.event.enrich
  side_effect=READ_ONLY  sensitivity=external_research_observation
  idempotency=NONE       (controlled D1; single-flight; composite dedupes)
  source=research/registration.py (status REGISTERED until governed
  transition; provider bound in bridge.initialize)

engineering.code_review
  side_effect=EXTERNAL_SIDE_EFFECT  sensitivity=engineering_code_review
  idempotency=NONE  source=review/registration.py (REGISTERED; provider unbound
  in Core; manual/explicit ingress only; NEVER model-invocable)

research.run_brief   [NEW composite]
  side_effect=READ_ONLY (explicit)  sensitivity=market_event_research
  idempotency=REQUEST_KEY  availability = AND over sub-capabilities (§5)
```

No generic "all legacy definitions default READ_ONLY".

---

## 5. Availability Lifecycle Implementation Contract (A5)

```text
MODEL = OPTION_C (conservative registration availability)

manifest availability source
= CapabilityDefinition.status (administrative; immutable registration field)

bound-state conjunct (defensive, read-only)
= CapabilityFrame build also verifies the definition's provider namespace is
  bound in CapabilityManager provider state before projecting AVAILABLE

execution readiness
= unchanged Runtime/CapabilityManager per-execution gate
  (provider resolution + provider.health(); typed UNAVAILABLE on failure)

governed transition mechanism
= explicit re-registration through the single registry
  (registry.register_definition update) by the composition root;
  required after late provider bind if the definition set must become AVAILABLE

health
= execution-time observation only; never projected; no health cache created

MARKET_STATUS_AFTER_LATE_BIND = REGISTERED (unchanged until governed
transition re-registers AVAILABLE)

derivation owner
= CapabilityFrame build (context_execution_runtime.py): reads registry
  definition.status + manager bound-provider state (read-only);
  DERIVED RUNTIME STATE, single lineage
```

```text
UNKNOWN HEALTH ≠ AVAILABLE
UNBOUND PROVIDER ≠ AVAILABLE
DISABLED DEFINITION ≠ AVAILABLE
REGISTERED (un-transitioned) ≠ AVAILABLE
composite research.run_brief AVAILABLE ⇔ AND over sub-capabilities (§6 D2)
```

---

## 6. Exact Allowed Paths (updated for A5)

Previous v0.3 matrix is preserved; A5 additions/changes below. **No new file
outside this set is required.**

| Required change | Exact authorized path |
| --------------- | --------------------- |
| manifest model + enums (SideEffectClass, IdempotencySupport) + CapabilityDefinition new defaults (side_effect_class=None etc.) | `julia_core/capability/models.py` |
| production definition explicit classifications + registration-status discipline (register only executable AVAILABLE surface; re-registration transition API) | `julia_core/runtime/capability_bridge.py` |
| manifest derivation + admission diagnostic (unclassified → non-admitted) | `julia_core/capability/registry.py` |
| permission rule (research.run_brief scope) | `julia_core/capability/policy.py` |
| availability projection (status + bound conjunct; composite AND) | `julia_core/runtime/context_execution_runtime.py` |
| Alignment capability encoding | `julia_core/alignment_os/capability_encoding.py` **[NEW]** |
| ResearchEvidenceBundle model | `julia_core/research/contracts.py` |
| composite executor (resolve→read→enrich→C1; REQUEST_KEY dedupe; ambiguity trigger) | `julia_core/runtime/research_continuation.py` |
| session continuation / F1 removal / parity | `julia_core/runtime/julia_session.py` |
| requires_tool semantic retirement | `julia_core/runtime/capability_bridge.py` |
| WorkflowRouter fencing | `julia_core/runtime/workflow_router.py` |
| MarketBriefIntentResolver fencing | `julia_core/reasoning/intents/market_brief.py` |

```text
MANAGER_PY_REQUIRED
= NO

Proof: availability projection needs only (a) registry definition.status and
(b) CapabilityManager provider-bound state, both READ-only at frame build
(manager.providers is already publicly readable and used by the composition
identity checks). Health stays inside execute_typed (unchanged). No manager.py
mutation is required by the OPTION_C lifecycle.
```

Forbidden paths (preserved): Market provider implementation/source pins, D1
provider transport, Assistant/Client/Voice, database data/migrations,
model/provider configuration, trading logic, generic workflow engine,
`julia_core/capability/manager.py` (read-only), `julia_core/research/judgment.py`
(C2 semantics), existing alignment_os modules (unchanged).

---

## 7. Dispositions Preserved (unchanged from v0.3)

`tool_manifest()` = legacy, no production caller, deprecated/removed after
governed Alignment encoding exists; not restored as a C-03 bypass.
`requires_tool()` = semantic authority removed; production_callers = 0.
WorkflowRouter/MarketBriefIntentResolver/MarketBriefPipeline = no pre-cognitive
semantic authority. SameTurnResearchContinuation = FUNCTIONAL SPINE REUSE,
refactor class boundary (ends at C1; C2/brief to session-level continuation).
C2 = Julia model cognition. Research Brief = deterministic product formatting
from C2 (research.brief.v1), never capability observation truth.

Rollback boundary: immutable git commit boundary; FLAG_AUTHORITY_MODE mutually
exclusive; DUAL_SEMANTIC_AUTHORITY = 0; FALLBACK_TO_LEGACY_ROUTER = 0;
no new-path failure routed to old F1/requires_tool/WorkflowRouter.

---

## 8. Required New Tests (A5 §24 — exact)

```text
tests/runtime/test_p3cc_manifest_fail_closed_metadata.py
tests/runtime/test_p3cc_capability_availability_projection.py
tests/runtime/test_p3cc_capability_definition_inventory.py
```

Required assertions (each must hold):

```text
unclassified side_effect → never READ_ONLY
unclassified side_effect → cannot silently become executable model-visible
                           capability (non-admission diagnostic emitted)
explicit research.run_brief → READ_ONLY
unbound provider → not AVAILABLE
late-bound Market provider → availability follows the frozen v0.4 lifecycle
                             exactly (status REGISTERED until governed
                             re-registration transition)
provider health/readiness unknown → not falsely AVAILABLE (no health cache)
DISABLED → never AVAILABLE
composite availability → conservative AND over required sub-capabilities
engineering.code_review → EXTERNAL_SIDE_EFFECT (never READ_ONLY default)
legacy non-executable ai_theme specs → not advertised AVAILABLE
```

Also carried from v0.3: alignment encoding, model-owned research ingress,
stream/non-stream parity, research ambiguity continuation,
requires_tool_no_production_callers, manifest derivation.

---

## 9. Acceptance Evidence / NCF

Acceptance captures per P3-CC v0.3 §18 plus A5 fields: capability manifest
digest incl. explicit side_effect_class per definition, availability projection
state per definition, UNCLASSIFIED_MANIFEST_COUNT = 0, late-bind lifecycle
trace, composite availability AND evaluation.

```text
CRITICAL_PATH = YES
PERMISSIVE_METADATA_DEFAULT = 0
FALSE_AVAILABLE_CAPABILITY = 0
LEGACY_AUTHORITY_FALLBACK = 0
DUAL_AUTHORITY = 0
SYNTHETIC_AVAILABILITY = 0
SYNTHETIC_SUCCESS = 0
FAIL_CLOSED = YES
```

NCF static gate re-run at every implementation step; P0/P1 → REJECT.

---

## 10. Historical Invariants (preserved)

M1_FUNCTIONAL_ACCEPTANCE = CLOSED_PASS. RD1_FUNCTIONAL_SPINE = KEEP. Market /
D1 / C1 / C2 semantics, Conversation persistence, Client rendering unchanged.
Voice out of scope. History not rewritten.

---

## 11. Implementation Contract Status

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
