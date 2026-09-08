# D3 — RD1 V1 P3-CC Implementation Contract — FINAL FREEZE CANDIDATE v0.5

**Task**: RD1-V1-P3CC-A6
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN — NO IMPLEMENTATION AUTHORITY.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_P3CC_IMPLEMENTATION_CONTRACT_FINAL_FREEZE_CANDIDATE_v0.4.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.5 closes A6 deltas: data_sensitivity admission gate, pre-activation
> metadata canonicalization, complete one-place allowed-path matrix, and the
> engineering.code_review boundary statement.

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

## 1. Governance Gates (before ANY implementation)

```text
G0 — D2 Research Composite Authority = FROZEN (research.run_brief, v0.5)
G1 — P3-CC contract = FROZEN / admitted as implementation authority
G2 — upstream frozen-contract compatibility recheck = PASS
G3 — Tony Owner implementation authorization = YES
G4 — exact implementation branch + base SHA bound

G5 — CAPABILITY METADATA ADMISSION GATE (extends A5)
     UNCLASSIFIED_SIDE_EFFECT_COUNT = 0
     UNCLASSIFIED_DATA_SENSITIVITY_COUNT = 0
     for every production-reachable CapabilityDefinition in the controlled
     RD1 activation surface (defense in depth: activation gate + projection
     fail-closed)

ONLY THEN: I1 — I11 (preserved ordering; I1 now includes metadata
canonicalization before manager activation per §4)
```

---

## 2. Top-Level Semantic Ingress Rule (preserved)

Model capability output is the sole semantic top-level ingress from ambiguous
natural-language cognition into capability selection, except frozen
deterministic protocol/UI infrastructure commands. After a governed composite
capability is cognitively selected, Runtime MAY deterministically construct the
exact internal sub-requests. Composite internal execution boundary ends at C1.

---

## 3. Exact Implementation Fields and Defaults (fail-closed)

```text
output_schema:        dict[str, str]         = {}    # undeclared (SAFE_EMPTY)
side_effect_class:    SideEffectClass | None = None  # UNCLASSIFIED ≠ READ_ONLY
idempotency_support:  IdempotencySupport     = NONE  # not retry-safe
latency_cost_hints:   dict[str, str]         = {}    # informational
data_sensitivity:     str                    = ""    # NOT_DECLARED ≠ PUBLIC
```

Enums: `SideEffectClass` = exact C-08 §7 five members (no UNKNOWN);
`IdempotencySupport` = {NONE, REQUEST_KEY}.

Manifest metadata admission rule:

```text
metadata-admitted to model-visible executable CapabilityManifestEntry[] ⇔
  side_effect_class is not None
  AND data_sensitivity.strip() != ""

non-admitted → typed projection diagnostic with ALL missing reasons:
  unclassified_side_effect
  unclassified_data_sensitivity
```

Only side-effect and sensitivity are mandatory admission classifications.
Empty output_schema/latency hints are not admission blockers.

---

## 4. Metadata Canonicalization (B4) — Frozen Implementation Contract

```text
METADATA_CANONICALIZATION_MODEL
= COMPOSITION_ROOT_PRE_ACTIVATION_REREGISTRATION
```

Source-verified placement: `RuntimeCapabilityBridge.initialize()` completes all
registrations and provider binds, then constructs CapabilityManager at
capability_bridge.py:436. The canonicalization + validation gate is inserted
between the last registration and line 436.

Sequence:

```text
1. initialize() starts.
2. Existing registration helpers construct/register legacy-compatible
   CapabilityDefinition objects (those source files are NOT modified).
3. BEFORE CapabilityManager construction, BEFORE _initialized=True, BEFORE any
   production CapabilityFrame: composition root canonicalizes EVERY
   production-reachable definition into explicit-metadata form from the
   composition-root metadata table (construction configuration only).
4. Canonicalization re-registers the final frozen CapabilityDefinition under
   the SAME capability_id in the SAME CapabilityRegistry (idempotent update).
5. Strict validation: side_effect_class != None AND
   data_sensitivity.strip() != "".
6. Any failure → initialization FAILS CLOSED (no manager, no executable
   manifest, no silent omission).
7. Only then: CapabilityManager constructed; production initialization active.
```

```text
CANONICALIZATION_OWNER = composition root (RuntimeCapabilityBridge.initialize)
REGISTRATION_SOURCE_MUTATION_REQUIRED = NO
  research/registration.py, review/registration.py, frozen_market.py,
  ai_theme/__init__.py  →  READ-ONLY / NO MUTATION
TEMPORARY_PREACTIVATION_REGISTRY_RESIDENCE = ALLOWED (migration staging ONLY:
  manager not active, CapabilityFrame cannot expose, gate not passed, no
  execution path consumes it)
PREACTIVATION_EXECUTION_REACHABLE = NO
PREACTIVATION_MODEL_VISIBILITY = NO
```

After canonicalization, `CapabilityManifestEntry` derives exclusively from the
final registered CapabilityDefinition + governed availability/permission
sources. Forbidden: second registry, metadata overlay, parallel execution-time
metadata truth, Alignment-owned metadata, model-authored metadata.

---

## 5. Engineering.code_review Boundary (B5)

```text
A model-generated CapabilityRequest by itself is NEVER sufficient to authorize
or execute engineering.code_review.

Successful execution still requires the existing trusted ReviewTransaction /
Core-ledger token / guarded provider ingress.

P3-CC MUST NOT create any path that can mint, synthesize, bypass, or
substitute that authority.

Capability existence or manifest metadata never implies review-send authority.

No model_invocable bool field is introduced.
```

---

## 6. Exact Allowed Paths — COMPLETE MATRIX (single place, no `?`)

| Required behavior | Exact authorized path |
| ----------------- | --------------------- |
| manifest model (CapabilityManifestEntry) + enums (SideEffectClass, IdempotencySupport) + CapabilityDefinition new defaults | `julia_core/capability/models.py` |
| composition-root metadata table + canonicalization + G5 gate (before manager activation) + registration-status discipline | `julia_core/runtime/capability_bridge.py` |
| manifest derivation + metadata admission diagnostic (non-admitted reasons) | `julia_core/capability/registry.py` |
| permission rule (research.run_brief scope) | `julia_core/capability/policy.py` |
| availability projection (status + bound conjunct; composite AND) | `julia_core/runtime/context_execution_runtime.py` |
| Alignment capability encoding | `julia_core/alignment_os/capability_encoding.py` **[NEW]** |
| ResearchEvidenceBundle model | `julia_core/research/contracts.py` |
| composite executor (resolve→read→enrich→C1; REQUEST_KEY dedupe; ambiguity trigger) | `julia_core/runtime/research_continuation.py` |
| session continuation / F1 removal / stream-non-stream parity | `julia_core/runtime/julia_session.py` |
| requires_tool semantic retirement | `julia_core/runtime/capability_bridge.py` |
| WorkflowRouter fencing | `julia_core/runtime/workflow_router.py` |
| MarketBriefIntentResolver fencing | `julia_core/reasoning/intents/market_brief.py` |
| tests | `tests/runtime/test_p3cc_alignment_capability_encoding.py`, `test_p3cc_model_owned_research_ingress.py`, `test_p3cc_stream_nonstream_parity.py`, `test_p3cc_research_ambiguity_continuation.py`, `test_p3cc_requires_tool_no_production_callers.py`, `test_p3cc_manifest_derivation.py`, `test_p3cc_manifest_fail_closed_metadata.py`, `test_p3cc_capability_availability_projection.py`, `test_p3cc_capability_definition_inventory.py` |

```text
MANAGER_PY_REQUIRED = NO (availability/metadata paths read registry + manager
  provider state read-only; canonicalization occurs before manager exists)
```

Forbidden paths (unchanged, confirmed): Market provider implementation /
source pins / tree digest; D1 provider transport; Assistant/Client/Voice;
database data/migrations; model/provider configuration; trading logic; generic
workflow engine; `julia_core/capability/manager.py` (read-only);
`julia_core/research/judgment.py`; existing alignment_os modules (unchanged);
`research/registration.py`, `review/registration.py`, `frozen_market.py`,
`ai_theme/__init__.py` (read-only — no mutation required by §4).

No required behavior depends on mutating a forbidden source.

---

## 7. Required Tests (A6 §16 — exact assertions)

A5 tests preserved. A6 adds/extends:

```text
tests/runtime/test_p3cc_manifest_fail_closed_metadata.py
  data_sensitivity == ""            → non-admitted
  data_sensitivity == ""            → typed capability_not_admitted diagnostic
  explicit side_effect + blank sensitivity → FAIL CLOSED
  explicit sensitivity + side_effect None  → FAIL CLOSED
  both missing → both reasons preserved (deterministic multi-reason)

tests/runtime/test_p3cc_capability_definition_inventory.py
  all 16 baseline definitions → explicit side_effect + sensitivity
  research.run_brief → READ_ONLY / market_event_research
  engineering.code_review → EXTERNAL_SIDE_EFFECT / engineering_code_review

NEW:
tests/runtime/test_p3cc_metadata_canonicalization_gate.py
  UNCLASSIFIED_SIDE_EFFECT_COUNT = 0 before activation
  UNCLASSIFIED_DATA_SENSITIVITY_COUNT = 0 before activation
  canonicalization completes before CapabilityManager activation
  canonicalization failure → no manager activation, no executable CapabilityFrame

NEW:
tests/runtime/test_p3cc_review_ingress_no_bypass.py
  ordinary model-generated engineering.code_review request
  → cannot bypass trusted review ingress (GOVERNED_INGRESS_REQUIRED preserved)
```

Availability tests unchanged (unbound → not AVAILABLE; late-bind lifecycle;
health unknown → not AVAILABLE; DISABLED → never AVAILABLE; composite AND).

---

## 8. Acceptance Evidence / NCF

Acceptance captures P3-CC v0.3 §18 + A5 fields + A6: per-definition
side_effect_class + data_sensitivity (no blanks), G5 counts = 0,
canonicalization-before-activation trace, code_review ingress no-bypass proof.

```text
CRITICAL_PATH = YES
PERMISSIVE_METADATA_DEFAULT = 0
UNCLASSIFIED_SIDE_EFFECT_AT_ACTIVATION = 0
UNCLASSIFIED_DATA_SENSITIVITY_AT_ACTIVATION = 0
PREACTIVATION_METADATA_LEAK = 0
FALSE_AVAILABLE_CAPABILITY = 0
SYNTHETIC_AVAILABILITY = 0
LEGACY_AUTHORITY_FALLBACK = 0
REVIEW_INGRESS_BYPASS = 0
DUAL_AUTHORITY = 0
SYNTHETIC_SUCCESS = 0
FAIL_CLOSED = YES
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
authorities unchanged; history not rewritten.

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
