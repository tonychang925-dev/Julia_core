# D2 — RD1 V1 Research Composite Authority Decision — FINAL FREEZE CANDIDATE v0.3

**Task**: RD1-V1-P3CC-A4
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN. No implementation authority.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_RESEARCH_COMPOSITE_AUTHORITY_DECISION_FINAL_FREEZE_CANDIDATE_v0.2.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.3 adds the A4 object-binding closure: C-08 manifest object model,
> ResearchEvidenceBundle exact schema, and exact source binding. All approved
> v0.2 authority semantics are preserved unchanged (§1). Only the sections
> needed for object binding are added/refined (§2-§13).

---

## 1. Approved Authority Semantics (preserved from v0.2 — NOT reopened)

```text
CANDIDATE_A
= APPROVED DIRECTION (unchanged)

COMPOSITE_FORM
= C-08 GOVERNED CAPABILITY

COMPOSITE_CAPABILITY_ID
= research.run_brief

SEMANTIC_SELECTION_AUTHORITY
= JULIA COGNITION

INTERNAL_EXECUTION_BOUNDARY
= market.event.resolve → market.event.read → research.event.enrich → C1

C2
= JULIA COGNITION AFTER ToolResult/Evidence re-entry (C-03/C-09)

RESEARCH_BRIEF
= deterministic product formatting from C2 judgment + evidence
  (product-layer owned; research.brief.v1; MUST NOT become capability
   observation truth)

AMBIGUITY
= resolver observation → Context OS → Julia cognition →
  clarify user / reformulate / stop
  (no Runtime guess / auto-select / hidden ranking / silent terminal failure)

STREAM_NONSTREAM_AUTHORITY
= IDENTICAL

DIRECT PRIMITIVES
= remain individually valid C-08 capabilities; no silent substitution

ARCHITECTURE_AMENDMENT_REQUIRED
= NO
```

Governing contracts (exact clauses re-read at c14f6aa): C-03 §3/§4/§11,
C-07 §4/§7/§9, C-08 §1/§4/§5/§6/§7/§9/§11/§13/§16, C-09 §2/§12,
C-12 §2/§3/§4/§8. These bind this v0.3.

---

## 2. Capability Object-Model Decision (A4 §7)

```text
CAPABILITY_OBJECT_MODEL_DECISION
= OPTION A

OPTION A
= create a first-class CapabilityManifestEntry model,
  DERIVED from CapabilityDefinition + PermissionPolicy +
  provider/runtime availability state
```

### 2.1 Why not OPTION B (extend CapabilityDefinition to BE the manifest)

- C-03 §3/§4 and C-08 §4 require the model-visible manifest to be a governed
  **projection** distinct from registry truth ("Enters model via CapabilityFrame
  → Context OS → LLM. Not: tool registry → provider directly"). Collapsing
  definition and manifest into one object would make registry truth directly
  model-visible, exposing provider binding/adapter internals and blurring the
  Frame ≠ source-of-truth invariant.
- `CapabilityDefinition` today is a registration source object with
  `input_schema: dict[str,str]` (param → description), `provider`, `adapter`,
  `status`; the C-08 manifest concept additionally carries `output_schema`,
  `side_effect_class`, `idempotency_support`, `latency_cost_hints`,
  `data_sensitivity`, `permission_requirements`, `availability` — a different
  responsibility (what Julia is allowed to know) with different lifecycle
  (availability is live; static fields are frozen).

### 2.2 Why not OPTION C / OPTION D

- OPTION C (existing object satisfies C-08): false at c14f6aa — no manifest
  object exists; `CapabilityDefinition` lacks the C-08 manifest fields
  (verified: no `CapabilityManifestEntry`, no `SideEffectClass`, no
  `latency_cost_hints`/`data_sensitivity`/`idempotency_support`/`output_schema`
  anywhere in `julia_core/capability/` or `julia_core/alignment_os/`).
- OPTION D (architecture gap): not proven. C-08 §4 already defines the
  manifest concept; A is a faithful implementation, no amendment required.

### 2.3 Responsibility split (frozen)

```text
CapabilityDefinition
= registered logical capability source definition (what capability exists;
  registry truth; single canonical owner of declarative capability metadata)

CapabilityRegistry
= single registry of CapabilityDefinition objects (no second registry)

PermissionPolicy
= authorization owner (scope → AuthorizationDecision)

Provider / Runtime state
= availability / execution readiness owner

CapabilityManifestEntry
= DERIVED C-08 model-visible manifest projection (what Julia is allowed to
  know about a capability; stateless derivation; never canonical truth;
  never an execution registry; never a semantic router)

CapabilityFrame
= governed container of CapabilityManifestEntry[] inside Context OS

Alignment
= provider-specific encoding of CapabilityManifestEntry[]
```

---

## 3. CapabilityManifestEntry — Exact Schema (A4 §9)

New first-class frozen dataclass (module per §12). Exact types:

```text
@dataclass(frozen=True, slots=True)
class CapabilityManifestEntry:
    capability_id: str                      # = CapabilityDefinition.name
    description: str                        # = CapabilityDefinition.description
    input_schema: dict[str, str]            # param → description
                                            # (= CapabilityDefinition.input_schema)
    output_schema: dict[str, str]           # NEW declarative on CapabilityDefinition;
                                            # param/key → description of structured_output
    side_effect_class: SideEffectClass      # NEW enum (see §6)
    permission_requirements: tuple[str, ...]  # = (CapabilityDefinition.permission_scope,)
    idempotency_support: IdempotencySupport # NEW enum (see §8)
    latency_cost_hints: dict[str, str]      # NEW declarative; optional hints
                                            # (e.g. {"class": "read_snapshot"})
    data_sensitivity: str                   # NEW declarative classification
    availability: CapabilityStatus          # live-derived (see §5); enum value
    schema_version: str                     # = CapabilityDefinition.schema_version
    provenance: dict[str, str]              # {"source": "capability:registry",
                                            #  "definition_ref": <name>,
                                            #  "derived_at": <iso>}
```

Field-level rules:

- `input_schema`/`output_schema`: intentionally typed as `dict[str, str]`
  (key → description) to remain exactly compatible with the existing
  `CapabilityDefinition.input_schema` and the frozen Market/research contract
  conventions at c14f6aa. A structured JSON-Schema representation is NOT
  introduced by this freeze (would be a parallel schema); if later required it
  must be a separate governed evolution.
- `availability` is the ONLY non-frozen field; it is resolved at projection
  time (§5). It is never stored as registry truth.
- All other fields are frozen at registration and MUST NOT be mutated by
  Runtime during execution.
- `OPTIONAL` fields (empty default) are: `output_schema={}`,
  `latency_cost_hints={}`, `data_sensitivity=""`; WHY: not every capability
  declares them at c14f6aa; absence means "not declared", never "no
  side effect / not sensitive".
- `idempotency_support` default `NONE`; `side_effect_class` default
  `READ_ONLY` (safe fail-closed default for existing READ-only capabilities).

---

## 4. Manifest Derivation Authority Matrix (A4 §10 — no `?` remains)

| Manifest field          | Canonical source                                   | Derived by                       | May Runtime mutate? |
| ----------------------- | -------------------------------------------------- | -------------------------------- | ------------------- |
| capability_id           | CapabilityDefinition.name (registry registration)  | registry (identity pass-through) | NO                  |
| description             | CapabilityDefinition.description                    | registry (pass-through)          | NO                  |
| input_schema            | CapabilityDefinition.input_schema                   | registry (pass-through)          | NO                  |
| output_schema           | CapabilityDefinition.output_schema (NEW)            | registry (pass-through)          | NO                  |
| side_effect_class       | CapabilityDefinition.side_effect_class (NEW)        | registry (pass-through)          | NO                  |
| permission_requirements | CapabilityDefinition.permission_scope               | registry wraps scope             | NO (policy governed)|
| idempotency_support     | CapabilityDefinition.idempotency_support (NEW)      | registry (pass-through)          | NO                  |
| latency_cost_hints      | CapabilityDefinition.latency_cost_hints (NEW)       | registry (pass-through)          | NO                  |
| data_sensitivity        | CapabilityDefinition.data_sensitivity (NEW)         | registry (pass-through)          | NO                  |
| availability            | CapabilityDefinition.status + provider binding      | CapabilityFrame build (live)     | YES only via governed lifecycle (bind/health/operator); never arbitrary |

Static fields: single canonical source = the registered
`CapabilityDefinition` (which gains the NEW declarative fields
`output_schema`, `side_effect_class`, `idempotency_support`,
`latency_cost_hints`, `data_sensitivity`, each with the defaults in §3).
Availability: single canonical source = registry status maintained by the
governed composition root (provider bind → AVAILABLE; provider absent →
REGISTERED; health fail → DEGRADED; operator/policy → DISABLED).

No parallel registry, no parallel permission authority, no second Evidence
authority.

---

## 5. Availability Semantics (A4 §18)

```text
REGISTERED
= defined; provider not yet bound / not validated

AVAILABLE
= provider healthy and ready (composite: all governed sub-capabilities
  AVAILABLE and their providers bound)

DEGRADED
= provider unhealthy but may recover

DISABLED
= explicitly turned off (policy/operator)
```

- Manifest `availability` is the **enum `CapabilityStatus`** value (existing
  frozen enum at c14f6aa) — NOT a fabricated boolean, NOT a Runtime-authored
  record.
- Source: `CapabilityDefinition.status`, maintained ONLY by governed lifecycle
  events (composition root binds provider → AVAILABLE; health failure →
  DEGRADED; operator → DISABLED). Runtime never invents availability.
- For `research.run_brief` (composite, no single provider):
  `AVAILABLE ⇔ every governed sub-capability is AVAILABLE and its provider is
  bound`. Resolution is a deterministic AND over sub-capability statuses,
  computed at CapabilityFrame projection time from registry truth. If any
  sub-capability is REGISTERED/DEGRADED/DISABLED, manifest availability is the
  most restrictive state (DISABLED > DEGRADED > REGISTERED), never AVAILABLE.
- Execution-time enforcement stays fail-closed: any sub-call precheck failure
  (UNKNOWN/DISABLED/UNAVAILABLE) returns the typed outcome; no synthetic
  availability.

---

## 6. SideEffectClass Binding (A4 §19)

Current source has `SideEffectState` (execution-state enum: NONE/PLANNED/
SUCCEEDED/FAILED/UNKNOWN) but NO C-08 §7 side-effect **class** enum. A4 binds a
new first-class enum in `julia_core/capability/models.py`:

```text
class SideEffectClass(str, Enum):
    READ_ONLY           = "read_only"
    REVERSIBLE_WRITE    = "reversible_write"
    IRREVERSIBLE_WRITE  = "irreversible_write"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    HIGH_IMPACT         = "high_impact"
```

Exact C-08 §7 vocabulary. No free-text strings.

For `research.run_brief`:

```text
side_effect_class
= READ_ONLY
```

Note: READ_ONLY class with controlled D1 *external observation* (network read)
does not change the class; D1 returns observations, no external mutation.
Side-effect *state* (`SideEffectState`) on ToolResult remains the execution
record.

---

## 7. Permission Binding (A4 §20)

Current policy model (capability/policy.py): `PermissionRule` → `PermissionPolicy`
(`with_defaults`, `check(scope) → AuthorizationDecision`).

For `research.run_brief`:

```text
permission_scope
= research.run_brief

default policy rule
  allow = TRUE
  reason = read-only governed Research Desk evidence acquisition
```

- The scope is a NEW governed scope; rule registration is an implementation
  step (D3 allowed path `capability/policy.py`), added to
  `PermissionPolicy.with_defaults()`.
- No relationship/persona identity may affect permission (C-08 §6; identity
  role ≠ authorization).
- Sub-call authorization remains unchanged: each internal
  `market.event.resolve` / `market.event.read` / `research.event.enrich`
  request is separately checked against its own scope (`market.observe`,
  research enrichment scope). The composite scope gates entry; sub-call scopes
  gate each governed execution.

---

## 8. Idempotency Binding (A4 §21)

Research is READ_ONLY, but same-turn duplicate execution still matters: no
duplicate uncontrolled D1 external research execution for the same logical
request.

```text
idempotency_support (enum, new)
  NONE        = no idempotency guarantee
  REQUEST_KEY = duplicate same logical CapabilityRequest.idempotency_key
                → no duplicate uncontrolled external execution
```

For `research.run_brief`:

```text
idempotency_support
= REQUEST_KEY
```

Semantics (C-08 §13 / C-12 §6 compatible): the composite executor keys on the
CapabilityRequest `idempotency_key` (already a canonical CapabilityRequest
field). Same `turn_id` + same key + identical request → reuse the completed
ToolResult/Evidence of the prior attempt within the same logical turn; never
blindly re-execute a completed D1 research call with UNKNOWN side-effect state.
The controlled critical Research path keeps:

```text
RETRY
= 0
```

unless separately governed. No retry/fallback behavior is invented here.

---

## 9. `research.run_brief` — Complete Manifest Binding (A4 §11)

```text
capability_id            = research.run_brief
schema_version           = 1.0
layer                    = INTELLIGENCE
description              = Execute the governed RD1 research evidence spine for
                           one cognitively selected research objective:
                           resolve → read → enrich → C1. Returns a
                           ResearchEvidenceBundle. Does NOT produce C2 judgment
                           or a Research Brief.
permission_scope         = research.run_brief
side_effect_class        = READ_ONLY
idempotency_support      = REQUEST_KEY
data_sensitivity         = "market_event_research"     (market event + D1 external observation)
latency_cost_hints       = {"class": "composite_research", "sub_calls": "3"}
input_schema             = {"query": "original user research objective",
                            "normalized_theme": "optional governed theme (model or
                                                 explicit upstream artifact only)",
                            "time_window": "optional explicit date window"}
output_schema            = {"bundle_contract": "research.evidence_bundle.v1",
                            "resolved_event": "MarketEvent",
                            "theme_relations": "MarketEventRelation[]",
                            "normalized_external_research": "NormalizedResearchEnrichment",
                            "verification_state": "VerificationState + claim states",
                            "evidence_refs": "Evidence ids",
                            "provenance": "sub-call lineage"}
provider binding         = composite executor (deterministic internal program);
                           NO transport provider selection by the model
availability             = AVAILABLE ⇔ sub-capability availability AND (§5)
status registration      = governed composition root registers definition +
                           scope rule (D3 paths)
```

No field is left to implementation-agent interpretation.

---

## 10. ResearchEvidenceBundle — Exact Schema Closure (A4 §12)

Exact location (see §12): `julia_core/research/contracts.py` — the existing
"C1 Market-event research contracts" module that already canonically defines
`MarketEvent`, `MarketEventRelation`, `VerificationState`,
`NormalizedResearchEnrichment`, `SourceRecord` and "defines no final Julia
judgment and invokes no model". The bundle is a bounded aggregate referencing
those canonical objects.

```text
@dataclass(frozen=True, slots=True)
class ResearchEvidenceBundle:
    bundle_contract: str                 # "research.evidence_bundle.v1"
    schema_version: str                  # "1.0"
    resolved_event: MarketEvent          # Market canonical (frozen M0 payload)
    theme_relations: tuple[MarketEventRelation, ...]
    normalized_external_research: NormalizedResearchEnrichment
    verification_state: VerificationState
    claim_verification_states: dict[str, str]   # claim_id → VerificationState
    evidence_refs: tuple[str, ...]              # C-12 Evidence ids
    provenance: dict[str, Any]                  # sub-call lineage + trace
```

### Field matrix (no `?` remains)

| Field                        | Type | Required | Canonical source | Embedded or ref | Notes |
| ---------------------------- | ---- | -------- | ---------------- | --------------- | ----- |
| resolved_event               | `MarketEvent` (research/contracts.py) | required | Market (`market.event.read`) | embedded frozen projection; canonical ref via `event_id` + `source_trace_id` | canonical truth stays Market |
| theme_relations              | `tuple[MarketEventRelation, ...]` | required (may be empty) | Market (`market.event.read`) | embedded frozen projection; refs via source_trace_id | Market canonical |
| normalized_external_research | `NormalizedResearchEnrichment` | required | D1 external observation normalized by C1 | embedded C1 normalization; refs its `source_records` | raw D1 payload not re-embedded wholesale |
| verification_state           | `VerificationState` | required | C1 | embedded enum | C1 owns verification state |
| claim_verification_states    | `dict[str, str]` (claim_id → VerificationState) | required (may be empty) | C1 | embedded map | per-claim state (normalizer) |
| evidence_refs                | `tuple[str, ...]` | required (may be empty) | C-12 Evidence | **refs only** | no synthetic evidence |
| provenance                   | `dict[str, Any]` | required | C-12 / runtime trace | embedded | sub-call capability_request_id/capability_call_id/correlation_id/timestamps |

Versioning: `bundle_contract = research.evidence_bundle.v1`, `schema_version =
1.0`. Serialization: the bundle is a frozen dataclass; the composite
ToolResult carries a lossless serializable projection in
`structured_output` plus `evidence_refs`, while canonical truth remains in
Market / D1 / C1 / C-12 Evidence stores.

---

## 11. No Parallel Truth Object Rule (A4 §13)

```text
ResearchEvidenceBundle
≠ new Market truth
≠ new D1 truth
≠ new C1 truth
≠ new Evidence authority

Canonical authorities remain:
  Market, D1, C1, C-12 Evidence

ResearchEvidenceBundle
= bounded transport/projection aggregate referencing those canonical truths
```

Embedded values are frozen contract projections (MarketEvent/MarketEventRelation
are exact M0 payload projections; NormalizedResearchEnrichment is the C1
normalization artifact; VerificationState is C1-owned). Where embedded for
performance, canonical refs + provenance remain authoritative. Deleting a bundle
loses convenience, not truth.

---

## 12. CapabilityFrame and Alignment Binding (A4 §16-§17)

```text
CapabilityRegistry
+ Permission/availability metadata
        ↓
CapabilityManifestEntry[]      (derived per §4)
        ↓
CapabilityFrame               (context_execution_runtime.py)
        ↓
C-03 Context OS               (sole model-visible authority)
        ↓
C-09 Alignment                (alignment_os/capability_encoding.py)
        ↓
ModelProvider

CapabilityFrame
= model-visible governed capability metadata container
NOT a semantic intent router
NOT a provider execution registry
```

Alignment receives `CapabilityManifestEntry[]` and encodes to native tool schema
OR text structured capability protocol per `ProviderAdaptationProfile`.
Alignment MUST NOT infer user intent, filter by inferred topic, select
`research.run_brief`, or decide whether external research is needed.

---

## 13. Exact Source Binding (A4 §15)

```text
CAPABILITY_DEFINITION_SOURCE
= julia_core/capability/models.py
  (extend with NEW declarative fields: output_schema, side_effect_class,
   idempotency_support, latency_cost_hints, data_sensitivity)

CAPABILITY_MANIFEST_ENTRY_SOURCE
= julia_core/capability/models.py
  (+ new enums SideEffectClass, IdempotencySupport)

CAPABILITY_FRAME_SOURCE
= julia_core/runtime/context_execution_runtime.py

ALIGNMENT_SOURCE
= julia_core/alignment_os/capability_encoding.py  [NEW]

RESEARCH_EVIDENCE_BUNDLE_SOURCE
= julia_core/research/contracts.py

COMPOSITE_EXECUTOR_SOURCE
= julia_core/runtime/research_continuation.py

PERMISSION_SCOPE_RULE_SOURCE
= julia_core/capability/policy.py
```

---

## 14. Freeze Record

```text
RESEARCH_COMPOSITE_AUTHORITY_DECISION
= A

COMPOSITE_FORM
= C-08 GOVERNED CAPABILITY

COMPOSITE_CAPABILITY_ID
= research.run_brief

SCHEMA_VERSION
= 1.0

SEMANTIC_SELECTION_AUTHORITY
= JULIA COGNITION

INTERNAL_EXECUTION_BOUNDARY
= resolve → read → enrich → C1

C2_BOUNDARY
= JULIA COGNITION AFTER TOOLRESULT REENTRY

AMBIGUITY_PATH
= CONTEXT_OS → COGNITION

STREAM_NONSTREAM_AUTHORITY
= IDENTICAL

CAPABILITY_OBJECT_MODEL
= OPTION A (first-class derived CapabilityManifestEntry)

SIDE_EFFECT_CLASS
= READ_ONLY

PERMISSION_SCOPE
= research.run_brief (allow=TRUE, governed rule)

IDEMPOTENCY_SUPPORT
= REQUEST_KEY

RESEARCH_EVIDENCE_BUNDLE
= research.evidence_bundle.v1 aggregate (not a truth authority)

ARCHITECTURE_AMENDMENT_REQUIRED
= NO

STATUS
= FINAL_FREEZE_CANDIDATE

CONTRACT_FREEZE
= NO  (pending MIRA_SIS + OWNER final mechanical freeze sign-off)

IMPLEMENTATION_AUTHORIZED
= NO
```
