# D2 — RD1 V1 Research Composite Authority Decision — FINAL FREEZE CANDIDATE v0.2

**Task**: RD1-V1-P3CC-A3
**Status**: FINAL_FREEZE_CANDIDATE — NOT FROZEN. No implementation authority.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Governance branch**: governance/p3-cc-freeze-review-v0.3
**Supersedes**: RD1_V1_RESEARCH_COMPOSITE_AUTHORITY_DECISION_FREEZE_CANDIDATE.md (v0.1, preserved as causal history)
**Date**: 2026-09-08
**Author**: 朱婉清 (Julia)

> v0.2 applies the A3 constitutional correction: the composite internal
> execution boundary ends at C1. C2 is Julia cognition after ToolResult
> re-entry. C2 inside capability execution is forbidden.

---

## 1. Constitutional Correction (A3 §4)

### 1.1 Corrected target shape

```text
Julia cognition
        ↓
cognitively selects governed Research capability (research.run_brief)
        ↓
Runtime validates / authorizes
        ↓
Research composite executor
        ↓
market.event.resolve
        ↓
market.event.read
        ↓
research.event.enrich
        ↓
C1 evidence normalization / verification-state production
        ↓
ToolResult + Evidence
        ↓
C-03 Context OS
        ↓
C-09 Alignment
        ↓
Julia cognition resumes
        ↓
C2 preliminary judgment            (JULIA COGNITION)
        ↓
Research Brief composition         (derived product after C2)
        ↓
final Julia continuation
```

### 1.2 Frozen invariants

```text
RESEARCH_COMPOSITE_INTERNAL_EXECUTION_BOUNDARY
= resolve → read → enrich → C1

C2
= JULIA COGNITION

RESEARCH_BRIEF
= PRODUCT / DERIVED OUTPUT AFTER C2

C2_INSIDE_CAPABILITY_EXECUTION
= FORBIDDEN
```

### 1.3 Governing-law basis (exact frozen clauses)

- C-00 §3 — LLM owns judgment, interpretation of evidence, tool-need recognition; C-00 §7 — ToolResult + Evidence → Context OS incremental projection → LLM continues cognition.
- C-01 §2 — `TOOL_REQUESTED → TOOL_EXECUTING → TOOL_RESULT_PROJECTED → COGNITION_RUNNING` is the same logical turn.
- C-03 §11 — ToolResult incremental projection; forbidden direct append.
- C-07 §9/§10 — tool call is a cognitive output; tool continuation = same turn, `generation_id` increments.
- C-08 §1 — "LLM chooses whether cognition requires a capability. Runtime authorizes and executes. LLM interprets the result." §5 — routing begins after cognitive selection. §16 — domain signals are evidence, not Julia's conclusion.
- C-09 §2/§12 — Alignment encodes representation, never decides which capability the user needs.

Capability execution therefore MUST NOT contain Julia cognitive judgment (C2) as
executor semantics. C1 is deterministic evidence normalization /
verification-state production (Core-allowed deterministic processing, C-00 §4);
C2 is a model inference that occurs only after the composite ToolResult/Evidence
has re-entered through Context OS.

---

## 2. Composite Form — C-08 Governed Capability (D2-R1)

```text
COMPOSITE_FORM
= C-08 GOVERNED CAPABILITY

SEMANTIC_SELECTION_AUTHORITY
= JULIA COGNITION

EXECUTION_AUTHORITY
= RUNTIME / CAPABILITY MANAGER

INTERNAL SUB-CALLS
= CONTRACT-DEFINED DETERMINISTIC EXECUTION
```

No second canonical ontology called `ResearchProgram`. If implementation uses an
internal executor/program class, that is implementation structure only; canonical
authority remains C-08 capability semantics (CapabilityDefinition /
CapabilityRequest / AuthorizationDecision / CapabilityCall / ToolResult /
Evidence / Trace).

---

## 3. Exact Composite Contract (D2-R2)

Registry collision check at c14f6aa: `research.run_brief` does not exist in any
registered capability set (file.*, market.*, research.event.enrich,
engineering.code_review). The identity is free to freeze.

```text
capability_id
= research.run_brief

schema_version
= 1.0

description
= Execute the governed RD1 research evidence spine for one cognitively
  selected research objective: resolve the Market event, read canonical
  Market observation, run controlled D1 external enrichment, and produce C1
  normalized verification-state evidence. Returns a ResearchEvidenceBundle.
  Does NOT produce C2 judgment or a Research Brief (those follow in Julia
  cognition after ToolResult re-entry).

layer
= INTELLIGENCE            (consistent with market.event.resolve/read)

provider
= composite (runtime-managed internal executor over bound sub-providers;
  not a transport provider)

permission_scope
= research.run_brief      (new scope; registration required at implementation)

side_effect_class
= READ_ONLY

availability semantics
= AVAILABLE only when every governed sub-capability is registered and its
  provider bound; otherwise typed UNAVAILABLE. No partial synthetic success.

adapter
= composite_executor (contract-defined deterministic internal program)

input_schema
  query: str                    # original user research objective or governed
                                # normalized equivalent (see §4)
  normalized_theme?: str        # optional; suppliers restricted (see §4)
  time_window?: {date?: str, start?: str, end?: str}

output_schema
= ResearchEvidenceBundle (see §5; structured evidence result only)

ambiguity_result_schema
= resolver observation projection: state ∈ {RESOLVED, UNRESOLVED, AMBIGUOUS},
  candidates[] with provenance, selected_event_id present only when RESOLVED.
  AMBIGUOUS/UNRESOLVED payloads are observations returned through Context OS,
  never auto-selections (see §6).

failure semantics
= typed, fail-closed (UNKNOWN / DISABLED / UNAVAILABLE / INVALID_REQUEST /
  AUTHORIZATION_DENIED / PROVIDER_FAILURE / RESEARCH_NOT_READY). Ambiguity is
  NOT a failure; it is an observation routed to cognition. Hard provider/data
  errors remain typed terminal failures.

sub-capability list (each remains individually governed + authorized)
  market.event.resolve      (Market authority, scope market.observe)
  market.event.read         (Market authority, scope market.observe)
  research.event.enrich     (D1 controlled research, existing scope)

evidence requirements
  each sub-call produces ToolResult + Evidence with capability_request_id,
  capability_call_id, evidence_refs, correlation_id (C-12 §2/§4); the bundle
  aggregates evidence_refs; no synthetic Evidence.

trace requirements
  composite capability_request_id + per-sub-call capability_call_ids +
  evidence_ids + correlation graph (C-12 §8) preserved end to end.
```

Research Brief and C2 judgment are deliberately absent from this contract's
output — they are post-tool cognitive/product artifacts (§9).

---

## 4. Input Contract (D2-R3)

```text
ResearchCompositeRequest {
    query: str
    normalized_theme?: str
    time_window?: {
        date?: str
        start?: str
        end?: str
    }
}
```

Rules:

- `query` = the original user research objective, or a governed normalized
  equivalent. Runtime MUST NOT reinterpret the user's semantic objective.
- `normalized_theme` may be supplied only by: (a) Julia cognition (model output
  as part of the capability request), or (b) an explicit structural artifact
  from a governed upstream step (e.g. a prior resolve/read result in the same
  logical turn). Runtime keyword semantic inference is forbidden as a supplier.
- `time_window` is an explicit, structurally parsed date window (deterministic
  parsing of an explicit user-provided date expression is allowed; semantic
  guessing is not).
- Semantic ownership: the model chooses the logical objective and arguments;
  Runtime validates schema, permission, availability, and forbidden-authority
  fields (C-08 §6, P3-CC-05).

---

## 5. Output Boundary — ResearchEvidenceBundle (D2-R4)

The composite capability output is a structured research evidence result, NOT a
C2 judgment and NOT a final Research Brief.

```text
ResearchEvidenceBundle {
    resolved_event          # Market-owned canonical event (market.event.read)
    theme_relations         # Market-owned canonical relations
    normalized_external_research  # D1 external observation, normalized (C1)
    verification_state      # C1 verification-state production
    evidence_refs[]         # aggregated evidence ids
    provenance              # sub-call ids, source refs, timestamps
}
```

Exact schema derives from existing Market / D1 / C1 artifacts
(`research_continuation.py` `_project_market_read_payload`,
`ResearchEvidenceNormalizer.normalize_provider_outcome`, C1 verification
state). No parallel truth objects are invented where existing canonical objects
suffice. The bundle is suitable as:

```text
ToolResult.structured_output + Evidence
→ C-03 Context OS projection
→ C-09 Alignment
→ Julia cognition
```

---

## 6. Ambiguity Path (D2-R5)

Final invariant (no conflicting wording remains):

```text
AMBIGUOUS / UNRESOLVED
→ resolver observation (state + candidates, provenance intact, no selection)
→ Context OS
→ Julia cognition
→ clarify user / reformulate / stop
```

Forbidden:

```text
Runtime guesses
Runtime auto-selects a candidate
silent candidate selection
semantic ranking hidden inside Runtime
silent terminal failure for mere ambiguity
model "choosing" an ambiguous resolver candidate inside capability execution
```

Hard provider/data errors remain typed fail-closed failures (UNKNOWN /
UNAVAILABLE / PROVIDER_FAILURE / RESEARCH_NOT_READY); ambiguity is not in that
class. Same-turn semantics are preserved (turn_id constant); the clarifying
exchange is ordinary cognition, not a second composite invocation.

---

## 7. Direct Primitive Capability Interaction (D2-R6)

```text
market.event.resolve
market.event.read
research.event.enrich
```
remain individually valid C-08 capabilities. The composite does not revoke or
shadow them.

- Choosing composite (`research.run_brief`) vs a primitive is a cognitive/model
  choice based on CapabilityManifest semantics.
- Runtime MUST NOT substitute one for another (no silent capability
  substitution, C-08).
- The composite's deterministic internal sub-calls are contract-defined
  execution (identical capability ids), not the model choosing primitives
  inside a composite.

---

## 8. Stream / Non-Stream Authority (D2-R7)

```text
Research composite authority
= modality/transport independent

process_stream
and
non-stream runtime

MUST enter the same logical capability lifecycle (C-01 §4, C-07 §8).
```

Only output transport differs. The same research.run_brief lifecycle
(select → authorize → composite evidence execution → ToolResult/Evidence →
Context OS → C2 → Brief → continuation) is reachable from both executors.

---

## 9. C2 and Research Brief Boundaries (A3 §14-§15)

### 9.1 C2

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

Existing `form_preliminary_research_judgment()` is model cognition (a
`provider.chat` inference over the C1-normalized evidence package); the
implementation may rewire its context/Alignment path but MUST NOT convert C2 to
deterministic Runtime logic.

### 9.2 Research Brief

Source basis: the accepted RD1 chain composes the Brief in the caller/product
hook (`research_product_hook(judgment, validated_market)` →
`research.brief.v1`), i.e. **deterministic product formatting from the C2
judgment plus evidence**, assembled at the product layer and persisted as a
canonical structured product (conversation_runtime A2-R1). Julia's final
conversational explanation is model continuation over the projected brief.

```text
RESEARCH_BRIEF_COMPOSITION
= A — deterministic product formatting from C2 judgment
  (product-layer owned; contract_version research.brief.v1;
   trace.judgment_id binding enforced)

RESEARCH_BRIEF
MUST NOT become capability observation truth.

Market/D1/C1 evidence and Julia C2 judgment remain distinguishable
  inside the brief (evidence_refs + judgment_id + trace preserved).
```

---

## 10. SameTurnResearchContinuation Disposition (A3 §13)

```text
SameTurnResearchContinuation
= FUNCTIONAL SPINE REUSE

RESPONSIBILITY_BOUNDARY (target)
ALLOWED:
  composite evidence execution orchestration (resolve → read → enrich → C1)
  same-turn lifecycle
  per-step capability calls (individually authorized/evidenced/traced)
  ambiguity projection trigger (AMBIGUOUS/UNRESOLVED → Context OS → cognition)
  C1 output delivery (ResearchEvidenceBundle)

FORBIDDEN as capability-internal semantics:
  C2 cognitive judgment ownership
  final Julia meaning interpretation
```

Current source physically invokes C2 inside `SameTurnResearchContinuation.run()`
(`form_preliminary_research_judgment`, research_continuation.py:340). The
implementation MUST **refactor the class boundary** so the composite executor
ends at C1 delivery, and C2/brief continuation orchestration moves to the
session-level post-tool cognitive continuation (julia_session /
ConversationRuntime), which already owns the same-turn provider continuation.
D3 binds this choice; it is not left to coding-agent interpretation.

---

## 11. Candidate Freeze Record (A3 §23)

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

ARCHITECTURE_AMENDMENT_REQUIRED
= NO

STATUS
= FINAL_FREEZE_CANDIDATE

CONTRACT_FREEZE
= NO  (pending MIRA_SIS + OWNER sign-off)

IMPLEMENTATION_AUTHORIZED
= NO
```
