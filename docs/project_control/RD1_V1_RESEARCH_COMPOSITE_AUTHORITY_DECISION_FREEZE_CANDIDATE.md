# D2 — RD1 V1 Research Composite Authority Decision Draft

**Task**: RD1-V1-P3CC-A1 (§15 blocking design decision)
**Status**: DRAFT — NOT FROZEN. No implementation authority.
**Base**: c14f6aa77a50dafc21a97083fac8cb97efc7231d
**Date**: 2026-09-08
**Auditor**: 朱婉清 (Julia)

---

## 1. Question

For the frozen/approved Research ingress cutover, which execution-authority
model governs the chain

```text
market.event.resolve → market.event.read → research.event.enrich → C1 → C2 → Research Brief → final same-turn cognition
```

when the *entry* capability has been cognitively selected by Julia?

- **Candidate A** — Julia cognition selects ONE high-level governed Research capability/program; Runtime executes a deterministic internal program.
- **Candidate B** — Julia cognition selects each primitive step individually (G1 resolve, G2 read, G3 enrich, …).

---

## 2. Candidate Comparison (evidence-backed)

| Criterion | Candidate A | Candidate B |
|---|---|---|
| Frozen-contract literalness | Satisfies C-08 §5 ("routing begins after a capability has been cognitively selected"); requires accepting that the selected capability is the Research program whose internal sub-calls are governed execution. | Maximally literal "model picks every capability", but C-08 §3/§12 and C-01 §2 already treat a same-turn tool loop as ONE logical turn with multiple generations — B does not add a contract requirement A lacks. |
| Model round trips / latency | 1 entry + 1 final cognition (+ C2 judgment inference, which is part of the chain's own C2 contract) | up to N generations for N primitives ⇒ 3-4× more calls, higher latency |
| Model variance / failure surface | one semantic decision (Research objective) + deterministic pipeline | every primitive step re-exposed to model variance; risk of incoherent intermediate requests |
| Existing RD1 reuse | maximal — current `SameTurnResearchContinuation` already executes resolve→read→enrich→C1→C2→brief deterministically with per-call authorization/evidence/trace (research_continuation.py:150-472) | would fragment a validated deterministic pipeline into an ad-hoc agent workflow |
| Traceability / authority | sub-calls remain individually authorized, correlated, evidenced (proven at c14f6aa: each step → `execute_tool_typed_async`/`execute_capability_request_async` → manager → ToolResult/Evidence; `capability_request_ids`/`capability_call_ids` recorded) | per-step traces are equally possible but N times more artifacts to correlate |
| Same-turn semantics | single logical turn (turn_id constant; generation_id changes) — matches C-01 §2/§3, C-07 §10 | same turn, but more generation boundaries; each is a risk point for idempotency/cancellation |
| Ambiguity handling | must route `UNRESOLVED`/`AMBIGUOUS` resolve outcomes back to cognition for clarification (currently fail-closed to `ResearchTurnNotReady` — proof-requirement gap) | ambiguity at any step returns to cognition naturally, but with many more ambiguity surfaces |
| Contract precedent | C-08 §23 disposition: "MarketBriefPipeline MOVE TO DOMAIN — domain workflow, not cognitive routing"; C-00 §10 julia_session KEEP WITH BOUNDARY; ADR-030 market intelligence domain-specific — consistent with a governed domain program behind one cognitive selection | no contradicting precedent, but also no stronger support |

---

## 3. Recommendation

```text
RESEARCH_COMPOSITE_AUTHORITY_RECOMMENDATION
= A

CONTRACT_BASIS
= C-08 §5 (capability routing begins after cognitive selection);
  C-08 §23 + P0-B P3-CC-12 (domain workflow preserved as execution-side
  logic, not semantic routing);
  C-01 §2/§3 + C-07 §10 (same-turn tool loop = one logical turn);
  C-03 §11 + C-08 §11 (ToolResult/Evidence re-enter Context OS);
  C-12 §4 (per-step evidence grounding);
  P3-CC contract draft v0.3 §11 (SameTurnResearchContinuation:
  FUNCTIONAL_REUSE = ALLOWED; CANONICAL_COMPOSITE_AUTHORITY = NOT YET APPROVED)

ARCHITECTURE_AMENDMENT_REQUIRED
= NO  (frozen contracts permit a cognitively selected high-level capability
       whose internal implementation invokes governed sub-capabilities;
       an amendment is NOT needed — a derived freeze of the composite is)

STATUS
= RECOMMENDATION ONLY — requires separate governance freeze before cutover
```

Candidate A requires these proofs before approval (each verified at c14f6aa
except where noted):

1. Julia cognition selects the Research objective/capability — **NOT MET today**
   (F1 keyword admission still selects it pre-cognitively). Fix = remove F1,
   provide CapabilityFrame→Alignment encoding so the model can request.
2. Runtime does not reinterpret the objective — **MET** (resolve carries the
   user query + optional normalized_theme/time_window; downstream steps are
   deterministic functions of the resolved event, not reinterpretation).
3. Internal sub-capabilities remain governed + individually traceable — **MET**
   (each step: CapabilityRequest → authorization → CapabilityCall →
   ToolResult/Evidence; ids collected in the continuation trace).
4. Internal sequencing is execution logic, not new semantic judgment — **MET**
   (resolve→read is driven by `selected_event_id`; read→enrich by
   `MarketEventResearchAdapter`; no hidden interpretation between steps).
5. The high-level program has a formal schema/authority/failure contract —
   **NOT MET** (no frozen composite contract; this D2 + freeze gate is that
   step).
6. Ambiguity returns to cognition rather than being guessed — **NOT MET fully**:
   `UNRESOLVED`/`AMBIGUOUS` resolve currently terminates with
   `ResearchTurnNotReady` (fail-closed, no clarification). Candidate A requires
   a governed ambiguity path: candidates + state projected to cognition so the
   model can ask the user or choose; hard failures remain fail-closed.
7. Failure at any critical sub-boundary is explicit and fail-closed — **MET**
   (typed failures; ResearchTurnNotReady stops cognition; NCF preserved).

Do NOT assume the existing `SameTurnResearchContinuation` already satisfies
criterion 1 or 6. It is a strong executor, not an approved composite authority.

---

## 4. Candidate B evaluation (why not selected)

- Highest literal fidelity to "model selects capabilities," but at the cost of
  turning a frozen, validated deterministic Research pipeline into a
  model-steered agent loop; increases latency, variance, and failure surfaces
  without adding an authority that A cannot also satisfy.
- B would *reduce* reuse of the accepted RD1 spine (Market/D1/C1/C2/Brief
  boundaries are frozen and preserved under A unchanged).
- B does not remove the F1/F2 violations either: the *entry* decision must be
  cognitive in both models.
- Recommendation stands unless a governing review finds B's literalness
  contractually mandatory; this audit finds no frozen clause requiring
  per-primitive cognitive selection.

---

## 5. Composite schema sketch (NON-NORMATIVE DESIGN EXAMPLE)

```text
NON-NORMATIVE: proposed capability identity, NOT canonical until separately frozen.

capability_id: research.run_brief   (or reuse governed identity approved at freeze)
arguments:
  query: str                          # user research objective (verbatim)
  normalized_theme?: str              # optional extracted theme
  time_window?: {date: str}           # optional explicit date
output_schema: julia.product.events.v1 (research.brief.v1 inside)
side_effect_class: READ_ONLY
governed sub-steps: market.event.resolve → market.event.read →
                    research.event.enrich → C1 → C2 → Research Brief
authorization: per sub-call policy (unchanged) + program-level gate
failure: typed, fail-closed, ambiguity → cognition
```

This sketch exists ONLY as a design example to make the freeze discussion
concrete. It carries no normative authority.

---

## 6. Unresolved questions for the freeze gate

1. Identity/ID of the high-level Research capability (registry name, schema
   version, permission scope). No ADR number assigned — Architecture Registry
   does not authorize an unused number here.
2. Ambiguity path design — **CLOSED by A2 freeze-review closure §8 (A-04)**:
   target = resolver observation → Context OS → Julia cognition → clarify /
   reformulate / stop. Remaining freeze-gate work is only the concrete
   projection schema and same-turn framing, not the architectural choice.
3. Whether the composite is a *capability* (C-08 path) or a *governed program*
   inside the session (same path, different registry placement) — recommend
   capability for uniform authorization/trace.
4. Interaction of composite with existing `market.event.resolve`/`read`
   capabilities when the model selects them directly (both must remain
   individually selectable).
5. Non-stream parity: the same composite must be invocable from the non-stream
   executor (currently the chain exists only in `process_stream`).

---

## 7. Required freeze gate (before any ingress cutover with execution authority)

```text
REQUIRED_FREEZE_ARTIFACT
= Research Composite Authority Freeze Record

RECORD_FIELDS
  RESEARCH_COMPOSITE_AUTHORITY_DECISION = A
  DECISION_STATUS = FROZEN / APPROVED
  CONTRACT_BASIS = PASS (per §3)
  COMPOSITE_ID / SCHEMA / AUTHORITY = frozen
  AMBIGUITY_PROJECTION = defined
  STREAM_NONSTREAM_INVOCATION = defined
  SOURCE_TRACE = PROVEN
  UPSTREAM_CONTRACT_COMPATIBILITY = PASS
  REGISTRY_IMPACT = UPDATE_REQUIRED (registry + ADR disposition)

GATE
  RESEARCH_INGRESS_CUTOVER_AUTHORIZED = NO until the above record is approved
```

Until then, the only permitted activity is non-authoritative qualification
(PRODUCTION_ROUTING_AUTHORITY = 0, CANONICAL_ACCEPTANCE_AUTHORITY = 0,
CAPABILITY_SIDE_EFFECT_AUTHORITY = 0).

---

## 8. A2 Freeze-Review Closure (recorded correction, 2026-09-08)

> This section was added during RD1-V1-P3CC-A2 packaging so the freeze
> candidate explicitly satisfies A2 §5 (A-01..A-05). It is a **candidate
> position for freeze review** — it does not freeze D2 and carries no
> implementation authority. Recorded as a separate review correction in
> `A2_CORRECTION_LOG.md` in the local deliverables directory.

### A-01 — Cognitive selection (freeze REQUIREMENT)
```text
The initial Research objective is selected by Julia cognition
  (model-visible capability request / native tool call / approved text protocol).
Forbidden as the selecting authority:
  keyword ingress
  regex ingress
  Runtime semantic classifier
  LLM classifier whose output Runtime uses as a router
```
Current status: NOT MET at c14f6aa (F1 keyword admission exists). This is a
blocker to **activating** the composite, not to **freezing** its authority
model. D3 step E/F sequence: activate composite only after model-owned request
is proven (step D) and only when keyword ingress is disabled (step F).

### A-02 — Internal deterministic program (freeze REQUIREMENT)
```text
After a cognitively authorized Research request, deterministic execution MAY
sequence:
  market.event.resolve
  → market.event.read
  → research.event.enrich
  → C1
  → C2
  → Research Brief
as the INTERNAL EXECUTION SEMANTICS of the governed Research program.
Runtime MUST NOT reinterpret the user's research objective between steps.
```
Current status: conforms at c14f6aa (research_continuation.py steps are
deterministic functions of the resolved event; no objective reinterpretation).

### A-03 — Sub-call governance (freeze REQUIREMENT)
```text
Every internal capability operation preserves:
  CapabilityRequest, AuthorizationDecision, CapabilityCall, ToolResult,
  Evidence, Trace, correlation
No composite may collapse these boundaries into synthetic success.
```
Current status: conforms at c14f6aa (per-step typed execution + evidence +
correlation ids recorded). Must remain true under the frozen composite.

### A-04 — Ambiguity handling (freeze REQUIREMENT — closed, not left ambiguous)
Current code: `resolve → AMBIGUOUS/UNRESOLVED → fail-closed terminal research
failure` (`ResearchTurnNotReady`), i.e. candidates are never returned to
cognition.

A2 candidate position (for freeze review):
```text
AMBIGUOUS / UNRESOLVED
≠ Runtime guesses
≠ Runtime auto-selects a candidate
≠ silent terminal failure

TARGET:
  resolver observation (state + candidates, no auto-selection)
  → Context OS projection
  → Julia cognition
  → clarify user / reformulate / stop
```
Rationale against C-00/C-08: understanding and interpretation belong to LLM
cognition (C-00 §3); Runtime must not silently choose a domain path (C-00 §7).
Ambiguity is a *meaning* question, therefore it returns to cognition. Hard
provider/data failures (not ambiguity) remain fail-closed terminal typed
failures. This keeps RD1 V1 UX: Julia may ask the user which event/theme they
mean instead of guessing or dying silently.

Consequence for D3: the composite's ambiguity path must project the resolver
observation through Context OS to the model for a clarifying generation, and
the terminal `ResearchTurnNotReady` applies only to non-ambiguity critical
failures. Same-turn semantics (turn_id constant) preserved.

### A-05 — No architecture amendment by implication
```text
ARCHITECTURE_AMENDMENT_REQUIRED
= NO
```
Candidate A is a demonstrable implementation of existing C-00 (cognitive tool
agency), C-01 (same-turn tool loop), C-03 (Context OS projection),
C-07/C-08 (capability request lifecycle, sub-call governance), C-09
(capability encoding), C-12 (evidence grounding). It introduces no new
canonical concept; the composite is a governed capability with a deterministic
internal implementation. If freeze review later concludes a new canonical
concept is required, this draft must stop and open architecture review instead
of being silently frozen.

### A2 closure status
```text
D2_STATUS = FREEZE_REVIEW_CANDIDATE
CONTRACT_FREEZE = NO
IMPLEMENTATION_AUTHORIZED = NO
NEXT_GATE = MIRA_SIS + OWNER D2/D3 FINAL FREEZE REVIEW
```
