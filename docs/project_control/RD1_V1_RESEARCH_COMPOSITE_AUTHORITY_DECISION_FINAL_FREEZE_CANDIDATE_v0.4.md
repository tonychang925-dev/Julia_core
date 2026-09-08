# D2 — RD1 V1 Research Composite Authority Decision — FINAL FREEZE CANDIDATE v0.4

**Task**: RD1-V1-P3CC-A5
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN. No implementation authority.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_RESEARCH_COMPOSITE_AUTHORITY_DECISION_FINAL_FREEZE_CANDIDATE_v0.3.md (causal history, unchanged)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.4 closes A5 blockers B1 (fail-closed side-effect metadata) and B2
> (availability lifecycle vs source truth). All v0.3 authority semantics,
> object-model OPTION A, composite contract, and ResearchEvidenceBundle
> decisions are preserved. Only the B1/B2 sections and freeze record change.

---

## 1. Approved Semantics (preserved from v0.3 — NOT reopened)

```text
CANDIDATE_A = APPROVED DIRECTION (unchanged)
COMPOSITE_FORM = C-08 GOVERNED CAPABILITY
CAPABILITY_ID = research.run_brief
SEMANTIC_SELECTION_AUTHORITY = JULIA COGNITION
COMPOSITE_INTERNAL_BOUNDARY = resolve → read → enrich → C1
C2 = JULIA COGNITION AFTER ToolResult/Evidence re-entry
RESEARCH_BRIEF = derived product after C2
AMBIGUITY = Context OS → cognition
STREAM_NONSTREAM_AUTHORITY = IDENTICAL
OBJECT_MODEL = OPTION A
  CapabilityDefinition = registry/source definition
  CapabilityManifestEntry = derived model-visible C-08 projection
  ResearchEvidenceBundle = bounded aggregate (research/contracts.py)
ARCHITECTURE_AMENDMENT_REQUIRED = NO
```

---

## 2. Blocker B1 — Fail-Closed Side-Effect Classification

### 2.1 Rejected v0.3 default

```text
CapabilityDefinition.side_effect_class: SideEffectClass = READ_ONLY
= UNSAFE_PERMISSIVE  (REJECTED)

Frozen principle:
  UNDECLARED ≠ READ_ONLY
  UNKNOWN SAFETY CLASSIFICATION MUST NOT become a more permissive concrete class
```

### 2.2 v0.4 exact binding

```text
CapabilityDefinition.side_effect_class
: SideEffectClass | None
= None

None
= UNCLASSIFIED / NOT DECLARED  (compatibility sentinel, NOT a C-08 class)
```

- `SideEffectClass.UNKNOWN` is NOT added (frozen C-08 §7 does not authorize an
  enum extension; adding one would require a frozen amendment — not done here).
- Existing `SideEffectClass` enum remains exactly C-08 §7: READ_ONLY,
  REVERSIBLE_WRITE, IRREVERSIBLE_WRITE, EXTERNAL_SIDE_EFFECT, HIGH_IMPACT.

### 2.3 Manifest admission for unclassified capability

Chosen behavior (primary = C, enforced consequence = A):

```text
PRIMARY:  explicit classification required before registry admission for all
          production-reachable definitions (production admission gate; §4).

CONSEQUENCE for any definition still found unclassified (None) at projection:
          excluded from the model-visible CapabilityManifestEntry[] executable
          path with an explicit governed projection diagnostic
          (kind = capability_not_admitted, reason = unclassified_side_effect).

FORBIDDEN:
  defaulting None → READ_ONLY
  silently admitting an unclassified capability as executable
  treating this admission decision as topic/intent filtering
```

```text
FAIL_CLOSED = YES
SILENT_READ_ONLY_DEFAULT = NO
PARALLEL_AUTHORITY = NO
SEMANTIC_FILTERING = NO   (governance validation, not intent/topic filtering)
```

### 2.4 Production activation gate

```text
Before P3-CC model-owned manifest activation:
ALL_PRODUCTION_REACHABLE_CAPABILITY_DEFINITIONS
MUST HAVE EXPLICIT SIDE_EFFECT_CLASS
(or the §2.3 non-admission mechanism must prove the unclassified entry cannot
 execute through the new path)

UNCLASSIFIED_MANIFEST_COUNT
= 0

for the controlled RD1 acceptance surface.
```

---

## 3. Metadata Defaults — Full Fail-Closed Audit (A5 §10)

| Field | v0.3 default | safety verdict | v0.4 default | fail-closed interpretation |
| ----- | ------------ | -------------- | ------------ | -------------------------- |
| `output_schema` | `{}` | SAFE_EMPTY | `{}` | absence = "not contractually declared"; NOT proof of unstructured-output correctness |
| `side_effect_class` | `READ_ONLY` | UNSAFE_PERMISSIVE | `None` (UNCLASSIFIED) | undeclared ≠ READ_ONLY; non-admitted to manifest execution path until classified |
| `idempotency_support` | `NONE` | SAFE_CONSERVATIVE | `NONE` | NONE = no idempotency guarantee; missing declaration ≠ retry-safe |
| `latency_cost_hints` | `{}` | SAFE_EMPTY | `{}` | informational only; never an availability/readiness claim |
| `data_sensitivity` | `""` | MUST_BE_EXPLICIT (interpretation guard) | `""` = NOT_DECLARED sentinel | missing ≠ PUBLIC; production admission requires explicit value; "" never maps to PUBLIC |

Rules retained:

```text
missing data_sensitivity ≠ PUBLIC
missing idempotency declaration ≠ retry-safe
missing output_schema ≠ proof of unstructured output correctness
missing side_effect_class ≠ READ_ONLY
```

---

## 4. Production Definition Classification Evidence (A5 §25)

Mechanical inventory of every production-reachable CapabilityDefinition at
c14f6aa (16 definitions across registration surfaces). Source tree audit via
repository-local grep of `CapabilityDefinition(` and registration call sites.

| capability_id | construction path | provider | permission scope | registration status | actual side effect | explicit classification |
| ------------- | ----------------- | -------- | ---------------- | ------------------- | ------------------ | ----------------------- |
| file.read | capability_bridge.py:352 | local | file.read | AVAILABLE (init) | local file read | READ_ONLY |
| file.search | capability_bridge.py:361 | local | file.read | AVAILABLE (init) | local file search | READ_ONLY |
| file.list | capability_bridge.py:370 | local | file.read | AVAILABLE (init) | local dir list | READ_ONLY |
| market.event.resolve | frozen_market.py:86 / ai_theme __init__ spec | ai_theme_app | market.observe | AVAILABLE (provider-first) / REGISTERED (absent) | Market DB query | READ_ONLY |
| market.event.read | frozen_market.py:96 / ai_theme spec | ai_theme_app | market.observe | same | Market DB read | READ_ONLY |
| market.snapshot.read | frozen_market.py:106 / ai_theme spec | ai_theme_app | market.observe | same | Market snapshot read | READ_ONLY |
| market.alert.query | frozen_market.py:115 / ai_theme spec | ai_theme_app | market.observe | same | Market alert read | READ_ONLY |
| market.intelligence.observe | ai_theme __init__ spec | ai_theme_app | market.observe | AVAILABLE only in legacy ai_theme list | domain read (NOT executable via frozen MarketDomainAdapterProvider) | READ_ONLY (declared) + derived availability NOT-AVAILABLE (unsupported by bound provider) |
| market.decision.explain | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable via frozen provider) | READ_ONLY + NOT-AVAILABLE |
| market.stock.history | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable via frozen provider) | READ_ONLY + NOT-AVAILABLE |
| market.stock.auction | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable) | READ_ONLY + NOT-AVAILABLE |
| market.theme.constituents | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable) | READ_ONLY + NOT-AVAILABLE |
| market.theme.capital | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable) | READ_ONLY + NOT-AVAILABLE |
| market.regime.read | ai_theme spec | ai_theme_app | market.observe | same | domain read (not executable) | READ_ONLY + NOT-AVAILABLE |
| research.event.enrich | research/registration.py:31 | research_enrichment | research.enrich | REGISTERED (init default; provider bound in init) | controlled D1 external observation (read) | READ_ONLY |
| engineering.code_review | review/registration.py:45 | external_review | engineering.review.external | REGISTERED (init default; provider unbound in Core) | external review session submission (governed, manual ingress) | EXTERNAL_SIDE_EFFECT |

No blanket "all legacy definitions default READ_ONLY". `engineering.code_review`
is explicitly EXTERNAL_SIDE_EFFECT. The 7 non-executable ai_theme legacy specs
are explicitly classified READ_ONLY for their *intrinsic* nature but must NOT
be advertised AVAILABLE (see B2) because the bound frozen Market provider cannot
execute them.

---

## 5. Blocker B2 — Availability Lifecycle vs Source Truth

### 5.1 Mechanically proven source facts (c14f6aa)

```text
FACT-1  CapabilityDefinition is a frozen dataclass; .status is immutable.
FACT-2  .status is set at registration time only (AVAILABLE when the provider
        is already bound at registration; REGISTERED otherwise).
FACT-3  RuntimeCapabilityBridge.register_provider() /
        CapabilityManager.bind_provider() bind provider objects and do NOT
        mutate or re-register definitions.
FACT-4  Late bind (initialize with no ai_theme_app provider → later
        register_canonical_market_provider → register_provider) does NOT
        change definition.status.

MARKET_STATUS_AFTER_LATE_BIND
= REGISTERED        (administrative status unchanged)

FACT-5  CapabilityManager.execute_typed denies ONLY DISABLED pre-authorization;
        REGISTERED definitions execute when a provider is bound.
FACT-6  provider.health() is observed at EVERY execution (execute_typed);
        health is never cached and never written back to any definition.
FACT-7  registry.register_definition is idempotent-update
        ("re-registering the same name updates it").
```

Conclusion: v0.3's claim ("definition.status + provider binding + health → live
availability") is not implementable from status alone (status is stale across
late bind) and must not embed health (no sourced health cache exists; inventing
one is forbidden).

### 5.2 Availability design decision

```text
AVAILABILITY_MODEL
= OPTION_C (conservative registration availability, refined)

manifest availability
= CapabilityDefinition.status (administrative, registration-time)

execution readiness
= separately checked by Runtime/CapabilityManager at execution time:
  provider namespace bound + provider.health() (per execution, typed
  UNAVAILABLE on failure)

lifecycle transition
= ONLY an explicit governed re-registration through the single registry
  (registry.register_definition update, owner = composition root)
```

Refinements applied for truthfulness:

```text
1. A definition is projected AVAILABLE only when
   status == AVAILABLE
   AND its provider namespace is bound (manager provider state; read-only).
2. DISABLED is never AVAILABLE (also denied at execution).
3. REGISTERED is never AVAILABLE — including after late bind — until the
   composition root performs the explicit governed re-registration transition.
   Conservative false-negative is tolerated; false-positive is forbidden.
4. provider.health() is an execution-time gate only; it is NEVER projected as
   manifest availability and no health cache is created.
5. The 7 non-executable ai_theme legacy specs must never be advertised
   AVAILABLE by the canonical composition; the composition root registers only
   the executable frozen surface (event.resolve/read, snapshot, alert + bound
   local/research providers) as AVAILABLE.
```

```text
UNKNOWN HEALTH ≠ AVAILABLE
UNBOUND PROVIDER ≠ AVAILABLE
DISABLED DEFINITION ≠ AVAILABLE
REGISTERED (un-transitioned) ≠ AVAILABLE
```

### 5.3 Exact lifecycle owners (A5 §17 — no UNKNOWN)

| Concern | Owner |
| ------- | ----- |
| Registration status (who owns it) | composition root via `registry.register_definition` (single CapabilityRegistry; no second registry) |
| Provider binding state | `CapabilityManager.bind_provider` (invoked by composition root via `RuntimeCapabilityBridge.register_provider`) |
| Health observation | `CapabilityManager` per-execution gate (`execute_typed` → `provider.health()`); never stored |
| Manifest availability derivation | CapabilityFrame build (`context_execution_runtime.py`) reading registry status + manager bound-provider state; DERIVED RUNTIME STATE, single lineage |
| Who may transition availability | ONLY the composition root (explicit governed re-registration update / bind) |
| Who may NOT transition | execution path, model, Alignment, CapabilityManifestEntry itself |

---

## 6. `research.run_brief` Availability Binding (A5 §20)

```text
research.run_brief availability
= derived conservative AND over required sub-capabilities:

  market.event.resolve  AVAILABLE   ⇔ registered AVAILABLE ∧ ai_theme_app bound
  market.event.read     AVAILABLE   ⇔ registered AVAILABLE ∧ ai_theme_app bound
  research.event.enrich AVAILABLE   ⇔ registered AVAILABLE ∧ research_enrichment bound

research.run_brief
= AVAILABLE only when all three are AVAILABLE under the §5.2 model

MUST NOT be AVAILABLE otherwise
No synthetic partial availability
```

In the canonical controlled composition (provider bound BEFORE
`initialize()` → definitions registered AVAILABLE) the composite is AVAILABLE.
In the late-bind order the composite stays non-AVAILABLE until the composition
root performs the explicit governed transition (re-registration AVAILABLE).

---

## 7. `research.run_brief` Side-Effect Binding (A5 §19 — preserved)

```text
research.run_brief
side_effect_class
= READ_ONLY       (EXPLICIT, not default-derived)

Reason: Market reads + D1 external observation + C1 normalization produce no
persistent external mutation.
```

`data_sensitivity = "market_event_research"`, `idempotency_support =
REQUEST_KEY`, latency hints and output schema unchanged from v0.3 §9.

---

## 8. ResearchEvidenceBundle (A5 §21 — unchanged)

```text
RESEARCH_EVIDENCE_BUNDLE
= UNCHANGED

source = julia_core/research/contracts.py
role = bounded C1 aggregate; not Market truth / D1 truth / Evidence authority /
C2 judgment. Re-verified mechanically only.
```

---

## 9. Freeze Record

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
CAPABILITY_OBJECT_MODEL = OPTION A (derived CapabilityManifestEntry)

SIDE_EFFECT_CLASS_DEFAULT
= None (UNCLASSIFIED sentinel; undeclared ≠ READ_ONLY)

UNCLASSIFIED_SIDE_EFFECT_BEHAVIOR
= non-admitted to manifest execution path (typed projection diagnostic);
  production admission gate requires explicit classification

PERMISSIVE_METADATA_DEFAULTS
= 0

AVAILABILITY_MODEL
= OPTION_C (conservative registration availability + bound conjunct +
  explicit governed re-registration transition; health execution-time only)

MARKET_STATUS_AFTER_LATE_BIND
= REGISTERED (administrative; manifest non-AVAILABLE until governed transition)

RESEARCH_RUN_BRIEF_SIDE_EFFECT
= READ_ONLY (explicit)

RESEARCH_RUN_BRIEF_AVAILABILITY
= conservative AND over sub-capabilities (§6)

RESEARCH_EVIDENCE_BUNDLE
= UNCHANGED (research/contracts.py)

ARCHITECTURE_AMENDMENT_REQUIRED
= NO

STATUS
= FINAL_FREEZE_CANDIDATE

CONTRACT_FREEZE
= NO  (pending MIRA_SIS + OWNER final mechanical freeze sign-off)

IMPLEMENTATION_AUTHORIZED
= NO
```
