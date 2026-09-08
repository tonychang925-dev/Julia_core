# D3 — RD1 V1 P3-CC Implementation Contract — FINAL FREEZE CANDIDATE v0.6

**Task**: RD1-V1-P3CC-A7
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_P3CC_IMPLEMENTATION_CONTRACT_FINAL_FREEZE_CANDIDATE_v0.5.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.6 is a minimal mechanical consistency repair. It closes B6 (G5 ordering
> cycle) and B7 (two A6 tests absent from the complete allowed-path matrix).
> All D2 v0.5 semantics and all A6 closures (B3/B4/B5) are preserved unchanged.

---

## 0. Binding Fields

```text
TASK_ID = RD1-V1-P3CC-IMPL (final id at Owner freeze)
REPO_FULL_NAME = tonychang925-dev/Julia_core
FREEZE_REVIEW_BRANCH = governance/p3-cc-freeze-review-v0.3
IMPLEMENTATION_TARGET_BRANCH = BLOCKED_PENDING_OWNER_AUTHORIZATION
IMPLEMENTATION_BASE_SHA = BLOCKED_PENDING_OWNER_FREEZE
```

---

## 1. Gate Lifecycle — Three Phases, No Cycle (B6)

```text
PHASE A — PRE-IMPLEMENTATION GOVERNANCE

G0 — D2 Research Composite Authority frozen (research.run_brief, v0.5)
G1 — P3-CC implementation contract frozen
G2 — upstream frozen-contract compatibility PASS
G3 — Tony Owner implementation authorization YES
G4 — exact implementation branch + base SHA bound

ONLY AFTER G0–G4: implementation work may begin.
```

```text
PHASE B — IMPLEMENTATION / CONSTRUCTION

I1a — capability metadata model
      + composition-root metadata canonicalization
      + projection fail-closed implementation
      + required supporting implementation
```

```text
PHASE C — PRE-RUNTIME-ACTIVATION GATE

G5 — CAPABILITY METADATA ACTIVATION GATE
     UNCLASSIFIED_SIDE_EFFECT_COUNT = 0
     UNCLASSIFIED_DATA_SENSITIVITY_COUNT = 0
     canonicalization completed
     projection fail-closed proven
     no preactivation model visibility
     no preactivation execution reachability

Only after G5:
  I1b — CapabilityManager / runtime activation
  I2 — I11 (downstream acceptance execution)
```

```text
G0–G4
= governance authorization to IMPLEMENT

G5
= implementation/runtime admission gate to ACTIVATE
```

G5 is NOT "before any implementation"; it is NOT post-production
best-effort validation. It is a **pre-runtime-activation** admission gate,
located after canonicalization implementation (I1a) and before manager/runtime
activation (I1b).

```text
GATE_ORDER_CYCLE
= 0

G5_OCCURS_AFTER_CANONICALIZATION_IMPLEMENTATION = YES
G5_OCCURS_BEFORE_MANAGER_RUNTIME_ACTIVATION = YES
```

Single linear, non-circular sequence:

```text
G0 → G1 → G2 → G3 → G4 → I1a → G5 → I1b → I2 → … → I11
```

(Option B numbering adopted: I1 split into I1a / G5 / I1b.)

### Runtime sequence preserved (source anchor, unchanged)

```text
RuntimeCapabilityBridge.initialize()
  legacy-compatible registration
  → composition-root metadata canonicalization (insertion point)
  → strict metadata validation / G5
  → CapabilityManager(...) construction
  → _initialized = True
  → runtime activation
```

No source redesign.

---

## 2. Top-Level Semantic Ingress Rule (preserved)

Model capability output is the sole semantic top-level ingress from ambiguous
natural-language cognition into capability selection, except frozen
deterministic protocol/UI infrastructure commands. After a governed composite
capability is cognitively selected, Runtime MAY deterministically construct the
exact internal sub-requests. Every internal request preserves CapabilityRequest
/ AuthorizationDecision / CapabilityCall / ToolResult / Evidence / Trace /
correlation. Composite internal execution boundary ends at C1.

---

## 3. Metadata Fields, Defaults, Admission (B3 preserved)

```text
output_schema:        dict[str, str]         = {}    # undeclared (SAFE_EMPTY)
side_effect_class:    SideEffectClass | None = None  # UNCLASSIFIED ≠ READ_ONLY
idempotency_support:  IdempotencySupport     = NONE  # not retry-safe
latency_cost_hints:   dict[str, str]         = {}    # informational
data_sensitivity:     str                    = ""    # NOT_DECLARED ≠ PUBLIC
```

Admission rule (unchanged):

```text
metadata-admitted to model-visible executable CapabilityManifestEntry[] ⇔
  side_effect_class is not None
  AND data_sensitivity.strip() != ""

non-admitted → typed projection diagnostic preserving ALL missing reasons:
  unclassified_side_effect
  unclassified_data_sensitivity
```

---

## 4. Metadata Canonicalization (B4 preserved)

```text
METADATA_CANONICALIZATION_MODEL
= COMPOSITION_ROOT_PRE_ACTIVATION_REREGISTRATION

Owner = composition root (RuntimeCapabilityBridge.initialize)
Insertion point = after last registration, before CapabilityManager(...)
Source anchor = capability_bridge.py:436

REGISTRATION_SOURCE_MUTATION_REQUIRED = NO
  research/registration.py, review/registration.py, frozen_market.py,
  ai_theme/__init__.py → READ-ONLY / NO MUTATION

TEMPORARY_PREACTIVATION_REGISTRY_RESIDENCE = ALLOWED (migration staging only:
  manager not active, CapabilityFrame cannot expose, gate not passed, no
  execution path consumes it)
PREACTIVATION_EXECUTION_REACHABLE = NO
PREACTIVATION_MODEL_VISIBILITY = NO
```

After canonicalization, CapabilityManifestEntry derives exclusively from the
final registered CapabilityDefinition + governed availability/permission
sources. Forbidden: second registry, metadata overlay, parallel execution-time
metadata truth, Alignment-owned metadata, model-authored metadata.

---

## 5. engineering.code_review Boundary (B5 preserved)

```text
A model-generated CapabilityRequest alone NEVER authorizes or executes
engineering.code_review.

Trusted ReviewTransaction + Core-ledger token + guarded ingress remain
required.

P3-CC cannot mint/synthesize/bypass/substitute them.

Capability existence or manifest metadata never implies review-send authority.

No model_invocable field.
```

---

## 6. Exact Allowed Paths — COMPLETE MATRIX (single place, no `?`)

| Required behavior | Exact authorized path |
| ----------------- | --------------------- |
| manifest model (CapabilityManifestEntry) + enums (SideEffectClass, IdempotencySupport) + CapabilityDefinition new defaults | `julia_core/capability/models.py` |
| composition-root metadata table + canonicalization + G5 gate (before manager activation) + registration-status discipline | `julia_core/runtime/capability_bridge.py` |
| manifest derivation + metadata admission diagnostic | `julia_core/capability/registry.py` |
| permission rule (research.run_brief scope) | `julia_core/capability/policy.py` |
| availability projection (status + bound conjunct; composite AND) | `julia_core/runtime/context_execution_runtime.py` |
| Alignment capability encoding | `julia_core/alignment_os/capability_encoding.py` **[NEW]** |
| ResearchEvidenceBundle model | `julia_core/research/contracts.py` |
| composite executor (resolve→read→enrich→C1; REQUEST_KEY dedupe; ambiguity trigger) | `julia_core/runtime/research_continuation.py` |
| session continuation / F1 removal / stream-non-stream parity | `julia_core/runtime/julia_session.py` |
| requires_tool semantic retirement | `julia_core/runtime/capability_bridge.py` |
| WorkflowRouter fencing | `julia_core/runtime/workflow_router.py` |
| MarketBriefIntentResolver fencing | `julia_core/reasoning/intents/market_brief.py` |
| tests (complete authorized set — 11 files, B7) | `tests/runtime/test_p3cc_alignment_capability_encoding.py`, `test_p3cc_model_owned_research_ingress.py`, `test_p3cc_stream_nonstream_parity.py`, `test_p3cc_research_ambiguity_continuation.py`, `test_p3cc_requires_tool_no_production_callers.py`, `test_p3cc_manifest_derivation.py`, `test_p3cc_manifest_fail_closed_metadata.py`, `test_p3cc_capability_availability_projection.py`, `test_p3cc_capability_definition_inventory.py`, `test_p3cc_metadata_canonicalization_gate.py`, `test_p3cc_review_ingress_no_bypass.py` |

```text
EVERY REQUIRED IMPLEMENTATION FILE = IN EXACT_ALLOWED_PATHS
EVERY REQUIRED TEST FILE = IN EXACT_ALLOWED_PATHS
HIDDEN_REQUIRED_PATH_COUNT = 0

REQUIRED_TEST_COUNT = 11
AUTHORIZED_TEST_COUNT = 11
REQUIRED_BUT_UNAUTHORIZED_TEST_COUNT = 0
```

```text
MANAGER_PY_REQUIRED = NO (metadata/availability paths read registry + manager
  provider state read-only; canonicalization occurs before manager exists)
```

Forbidden paths (unchanged): Market provider implementation / source pins /
tree digest; D1 provider transport; Assistant/Client/Voice; database
data/migrations; model/provider configuration; trading logic; generic workflow
engine; `julia_core/capability/manager.py` (read-only);
`julia_core/research/judgment.py`; existing alignment_os modules (unchanged);
`research/registration.py`, `review/registration.py`, `frozen_market.py`,
`ai_theme/__init__.py` (read-only — no mutation required).

No required behavior depends on mutating a forbidden source.

---

## 7. Required Tests — Complete Assertion Set

A5/A6 assertions retained (see v0.5 §7): unclassified side-effect / blank
sensitivity → non-admitted + typed diagnostic; both missing → both reasons;
16 baseline definitions explicit; research.run_brief READ_ONLY /
market_event_research; engineering.code_review EXTERNAL_SIDE_EFFECT /
engineering_code_review; availability lifecycle (unbound → not AVAILABLE,
late-bind, health unknown → not AVAILABLE, DISABLED → never AVAILABLE,
composite AND); canonicalization-before-activation; review ingress no-bypass.

---

## 8. Acceptance Evidence / NCF

Acceptance captures P3-CC v0.3 §18 + metadata/sensitivity/availability +
canonicalization-before-activation trace + review ingress no-bypass proof.

```text
GATE_ORDER_CYCLE = 0
REQUIRED_BUT_UNAUTHORIZED_TEST_COUNT = 0
HIDDEN_REQUIRED_PATH_COUNT = 0
PERMISSIVE_METADATA_DEFAULT = 0
PREACTIVATION_METADATA_LEAK = 0
REVIEW_INGRESS_BYPASS = 0
DUAL_AUTHORITY = 0
SYNTHETIC_SUCCESS = 0
LEGACY_AUTHORITY_FALLBACK = 0
FAIL_CLOSED = YES
CRITICAL_PATH = YES
```

NCF static gate re-run at every implementation step; P0/P1 → REJECT.

---

## 9. Dispositions / Boundaries / Invariants (preserved)

tool_manifest() legacy → deprecated/removed after governed Alignment encoding;
requires_tool() semantic authority removed (production_callers = 0);
WorkflowRouter/MarketBriefIntentResolver no pre-cognitive authority;
SameTurnResearchContinuation refactor class boundary (ends at C1); C2 = Julia
cognition; Research Brief = derived product (research.brief.v1); rollback =
immutable git commit boundary, no legacy fallback; Market/D1/C1/C2/conversation
authorities unchanged; D2 v0.5 = FINAL_FREEZE_READY (unchanged); history not
rewritten.

---

## 10. Implementation Contract Status

```text
IMPLEMENTATION_CONTRACT_STATUS = FINAL_FREEZE_CANDIDATE
IMPLEMENTATION_AUTHORIZED = NO
IMPLEMENTATION_BASE_SHA = BLOCKED_PENDING_OWNER_FREEZE
IMPLEMENTATION_TARGET_BRANCH = BLOCKED_PENDING_OWNER_AUTHORIZATION
CONTRACT_FREEZE = NO (pending MIRA_SIS + OWNER final mechanical freeze sign-off)
NEXT_GATE = MIRA_SIS + OWNER FINAL MECHANICAL FREEZE SIGN-OFF
```
