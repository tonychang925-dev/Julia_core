# D2 — RD1 V1 Research Composite Authority Decision — FINAL FREEZE CANDIDATE v0.5

**Task**: RD1-V1-P3CC-A6
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN. No implementation authority.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_RESEARCH_COMPOSITE_AUTHORITY_DECISION_FINAL_FREEZE_CANDIDATE_v0.4.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.5 closes A6 blockers B3 (data_sensitivity fail-closed admission), B4
> (metadata canonicalization construction-path closure) and B5
> (engineering.code_review wording). A5 B1/B2 decisions are NOT reopened.

---

## 1. Approved Semantics (preserved — NOT reopened)

```text
CANDIDATE_A = APPROVED DIRECTION (unchanged)
COMPOSITE_FORM = C-08 GOVERNED CAPABILITY
CAPABILITY_ID = research.run_brief
SEMANTIC_SELECTION_AUTHORITY = JULIA COGNITION
COMPOSITE_INTERNAL_BOUNDARY = resolve → read → enrich → C1
C2 = JULIA COGNITION AFTER ToolResult/Evidence re-entry
RESEARCH_BRIEF = derived product after C2
CAPABILITY_OBJECT_MODEL = OPTION A
SIDE_EFFECT_CLASS_DEFAULT = None / UNCLASSIFIED (undeclared ≠ READ_ONLY)
AVAILABILITY_MODEL = OPTION_C (conservative registration availability;
  health execution-time only)
RESEARCH_EVIDENCE_BUNDLE = UNCHANGED bounded C1 aggregate
  (julia_core/research/contracts.py)
ARCHITECTURE_AMENDMENT_REQUIRED = NO
```

C-08 frozen basis re-read: §4 CapabilityManifestEntry includes
`data_sensitivity` and `side_effect_class`; §6 authorization basis includes
data sensitivity and side-effect level; §7 side-effect classes. Therefore:

```text
UNDECLARED DATA SENSITIVITY
MUST NOT be treated as a complete executable manifest classification.
```

---

## 2. Blocker B3 — Data Sensitivity Fail-Closed Admission

### 2.1 Accepted default (unchanged)

```text
CapabilityDefinition.data_sensitivity
: str
= ""

"" = NOT_DECLARED sentinel
"" ≠ PUBLIC
"" ≠ LOW_RISK
"" ≠ authorization-safe classification
```

No new C-08 enum is invented (frozen architecture does not require one).

### 2.2 Exact manifest admission rule (replaces v0.4 §2.3)

```text
A production CapabilityDefinition is metadata-admitted to the model-visible
executable CapabilityManifestEntry[] path ONLY when:

  side_effect_class is not None
  AND
  data_sensitivity.strip() != ""

Otherwise → NON_ADMITTED, with a typed governed projection diagnostic.

Exact diagnostic reasons:
  unclassified_side_effect
  unclassified_data_sensitivity

If both fields are missing, BOTH reasons are preserved (deterministic
multi-reason representation: reasons = ["unclassified_side_effect",
"unclassified_data_sensitivity"]). Runtime never silently selects one.
```

```text
FAIL_CLOSED = YES
SILENT_ADMISSION = NO
PARALLEL_AUTHORITY = NO
SEMANTIC_FILTERING = NO  (governance metadata validation, not topic/intent filter)
```

---

## 3. Production Metadata Gate (extends A5 G5)

```text
G5 — CAPABILITY METADATA ADMISSION GATE

UNCLASSIFIED_SIDE_EFFECT_COUNT
= 0

UNCLASSIFIED_DATA_SENSITIVITY_COUNT
= 0

for every production-reachable CapabilityDefinition
in the controlled RD1 activation surface.
```

Defense in depth:

```text
activation gate (G5 counts = 0)
+
projection fail-closed (§2.2; a pre-activation unclassified definition cannot
  become an executable model-visible capability even transiently)
```

Other defaults preserved (NOT reopened): `output_schema={}` SAFE_EMPTY /
undeclared; `idempotency_support=NONE` SAFE_CONSERVATIVE / not retry-safe;
`latency_cost_hints={}` SAFE_EMPTY / informational; `side_effect_class=None`
UNCLASSIFIED; `data_sensitivity=""` NOT_DECLARED. Only side-effect and
sensitivity are mandatory production metadata admission classifications. Empty
`output_schema` is NOT an admission blocker.

---

## 4. Blocker B4 — Metadata Canonicalization Construction-Path Closure

### 4.1 Mechanical construction-path re-verification (c14f6aa)

`CapabilityDefinition(...)` construction sites exist in exactly five source
files:

```text
julia_core/runtime/capability_bridge.py        (file.* local definitions)
julia_core/research/registration.py            (research.event.enrich)
julia_core/review/registration.py              (engineering.code_review)
julia_core/capability/providers/ai_theme/frozen_market.py   (market.* tuple + register copy)
julia_core/capability/providers/ai_theme/__init__.py        (legacy ai_theme spec list)
```

### 4.2 Chosen canonicalization model

```text
METADATA_CANONICALIZATION_MODEL
= COMPOSITION_ROOT_PRE_ACTIVATION_REREGISTRATION

Implementable entirely inside capability_bridge.py + capability/models.py
(+ read-only use of capability/registry.py). Verified against source:
RuntimeCapabilityBridge.initialize() performs ALL registrations and provider
binds, then constructs CapabilityManager at capability_bridge.py:436 and sets
_initialized=True at :442. The canonicalization + validation gate is inserted
between the last registration and the manager construction.

REGISTRATION_SOURCE_MUTATION_REQUIRED
= NO

research/registration.py
review/registration.py
frozen_market.py
ai_theme/__init__.py
= READ-ONLY / NO MUTATION
```

### 4.3 Exact initialization sequence (frozen)

```text
1. RuntimeCapabilityBridge.initialize() starts.

2. Existing registration helpers construct/register legacy-compatible
   CapabilityDefinition objects (unchanged source files).

3. BEFORE CapabilityManager construction (bridge.py:436),
   BEFORE _initialized=True,
   BEFORE any production CapabilityFrame can be built:

   the composition root canonicalizes EVERY production-reachable definition
   into its v0.5 explicit-metadata form, using a composition-root metadata
   table (CONSTRUCTION CONFIGURATION ONLY).

4. Canonicalization re-registers the final frozen CapabilityDefinition under
   the SAME capability_id in the SAME CapabilityRegistry
   (registry.register_definition idempotent-update).

5. Strict metadata validation runs:
   side_effect_class != None
   data_sensitivity.strip() != ""

6. If any production definition fails → initialization FAILS CLOSED.
   No manager activation. No executable manifest. No silent omission.

7. ONLY AFTER the gate passes: CapabilityManager is constructed and
   production initialization becomes active.
```

### 4.4 Canonicalization authority

```text
Composition-root metadata table/helper
= CONSTRUCTION CONFIGURATION ONLY (not consulted during execution)

Final registered CapabilityDefinition
= SINGLE CANONICAL RUNTIME SOURCE

CapabilityManifestEntry
MUST derive exclusively from the final registered CapabilityDefinition
+ existing governed availability/permission sources
```

Forbidden:

```text
second registry
second manifest authority
runtime mutable metadata overlay
parallel metadata truth consulted during execution
Alignment-owned metadata
model-authored metadata
```

### 4.5 Registry-admission wording correction (v0.4 fix)

v0.4 wording "explicit classification required before registry admission" is
replaced (too strong for the backward-compatible migration sequence, where
legacy construction may temporarily register an unclassified object inside an
unactivated composition). Exact law:

```text
Explicit safety metadata (side_effect_class, data_sensitivity) is mandatory
BEFORE PRODUCTION ACTIVATION and BEFORE MODEL-VISIBLE EXECUTABLE MANIFEST
ADMISSION.

Temporary pre-activation registry residence is permitted ONLY when:
  CapabilityManager not constructed/active
  CapabilityFrame cannot expose it
  strict canonicalization gate has not yet passed
  no execution path can consume it

Temporary residence is migration staging, NOT authority admission.
```

---

## 5. Canonical Production Metadata Table (A6 §14 — 17 rows, no blank sensitivity)

Every row: capability_id | side_effect_class | data_sensitivity |
idempotency_support | admin registration state | provider | permission_scope |
metadata canonicalization source.

| capability_id | side_effect | sensitivity | idempotency | admin state | provider | scope | canonicalization source |
|---|---|---|---|---|---|---|---|
| file.read | READ_ONLY | local_user_files | NONE | AVAILABLE | local | file.read | bridge composition-root table |
| file.search | READ_ONLY | local_user_files | NONE | AVAILABLE | local | file.read | bridge table |
| file.list | READ_ONLY | local_user_files | NONE | AVAILABLE | local | file.read | bridge table |
| market.event.resolve | READ_ONLY | market_observe | NONE | AVAILABLE (provider-first) | ai_theme_app | market.observe | bridge table |
| market.event.read | READ_ONLY | market_observe | NONE | same | ai_theme_app | market.observe | bridge table |
| market.snapshot.read | READ_ONLY | market_observe | NONE | same | ai_theme_app | market.observe | bridge table |
| market.alert.query | READ_ONLY | market_observe | NONE | same | ai_theme_app | market.observe | bridge table |
| market.intelligence.observe | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.decision.explain | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.stock.history | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.stock.auction | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.theme.constituents | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.theme.capital | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| market.regime.read | READ_ONLY | market_observe | NONE | legacy-list only; NOT-AVAILABLE | ai_theme_app | market.observe | bridge table |
| research.event.enrich | READ_ONLY | external_research_observation | NONE | REGISTERED until governed transition | research_enrichment | research.enrich | bridge table |
| engineering.code_review | EXTERNAL_SIDE_EFFECT | engineering_code_review | NONE | REGISTERED; provider unbound in Core | external_review | engineering.review.external | bridge table |
| research.run_brief | READ_ONLY | market_event_research | REQUEST_KEY | AVAILABLE ⇔ sub-caps AND | composite | research.run_brief | bridge table |

---

## 6. Blocker B5 — engineering.code_review Exact Boundary

Current source law (c14f6aa, review/registration.py + capability_bridge.py
`_resolve_tool_request` GOVERNED_INGRESS_REQUIRED):

```text
OPERATOR-TRIGGERED ONLY
+ trusted ReviewTransaction / Core-ledger token
+ guarded semantic ingress
```

No `model_invocable: bool` field is invented (no frozen amendment authorizes it).

v0.5 replaces ambiguous wording with the exact enforceable statement:

```text
A model-generated CapabilityRequest by itself is NEVER sufficient to authorize
or execute engineering.code_review.

Successful execution still requires the existing trusted ReviewTransaction /
Core-ledger token / guarded provider ingress.

P3-CC MUST NOT create any path that can mint, synthesize, bypass, or
substitute that authority.

Capability existence or manifest metadata never implies review-send authority.
```

---

## 7. Freeze Record

```text
RESEARCH_COMPOSITE_AUTHORITY_DECISION = A
COMPOSITE_FORM = C-08 GOVERNED CAPABILITY
COMPOSITE_CAPABILITY_ID = research.run_brief
SCHEMA_VERSION = 1.0
SEMANTIC_SELECTION_AUTHORITY = JULIA COGNITION
INTERNAL_EXECUTION_BOUNDARY = resolve → read → enrich → C1
C2_BOUNDARY = JULIA COGNITION AFTER TOOLRESULT REENTRY
AMBIGUITY_PATH = CONTEXT_OS → COGNITION
STREAM_NONSTREAM_AUTHORITY = IDENTICAL
CAPABILITY_OBJECT_MODEL = OPTION A

SIDE_EFFECT_ADMISSION_GATE = side_effect_class is not None
DATA_SENSITIVITY_ADMISSION_GATE = data_sensitivity.strip() != ""
NON_ADMITTED diagnostic reasons = unclassified_side_effect /
                                  unclassified_data_sensitivity (both preserved)

UNCLASSIFIED_SIDE_EFFECT_COUNT_REQUIRED = 0
UNCLASSIFIED_DATA_SENSITIVITY_COUNT_REQUIRED = 0

METADATA_CANONICALIZATION_MODEL
= COMPOSITION_ROOT_PRE_ACTIVATION_REREGISTRATION
CANONICALIZATION_OWNER = composition root (RuntimeCapabilityBridge.initialize)
CANONICALIZATION_OCCURS_BEFORE_MANAGER_ACTIVATION = YES
TEMPORARY_PREACTIVATION_REGISTRY_RESIDENCE = ALLOWED (migration staging only)
PREACTIVATION_EXECUTION_REACHABLE = NO
PREACTIVATION_MODEL_VISIBILITY = NO
REGISTRATION_SOURCE_MUTATION_REQUIRED = NO

ENGINEERING_CODE_REVIEW_BOUNDARY
= model request alone never authorizes/executes; trusted ReviewTransaction /
  ledger token / guarded ingress required; no mint/synthesize/bypass/substitute

AVAILABILITY_MODEL = OPTION_C
MARKET_STATUS_AFTER_LATE_BIND = REGISTERED
RESEARCH_EVIDENCE_BUNDLE = UNCHANGED (research/contracts.py)
ARCHITECTURE_AMENDMENT_REQUIRED = NO

STATUS = FINAL_FREEZE_CANDIDATE
CONTRACT_FREEZE = NO (pending MIRA_SIS + OWNER final mechanical freeze sign-off)
IMPLEMENTATION_AUTHORIZED = NO
```
