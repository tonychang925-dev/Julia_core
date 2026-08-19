# DIA-7 R0 — Continuity Projection Contract

> **Namespace:** CONT-DIA
> **Canonical phase:** CONT-DIA-7 — Continuity State Projection
> **Not to be confused with:** STORAGE-DIA-7 — Diary Retrieval

## 0. Status

Phase: DIA-7 — Continuity State / Identity Projection  
Artifact: R0 contract only  
Implementation provenance: Codex A  
Branch: `codex/dia-7/continuity-projection-r0`  
Base: DIA-6 R1.1 Core Context Evolution Contract `393491a`  
Runtime implementation: none in R0

Frozen upstream inputs remain immutable:

- DIA-3 Reflection Trigger Contract
- DIA-4 Reflection Context Contract
- DIA-5 Reflection Context Handoff Contract
- DIA-6 Context Evolution / Lineage Contract

DIA-7 R0 does not modify DIA-3 trigger identity, DIA-4 context identity, DIA-5 handoff identity, DIA-6 lineage identity, transport state, Diary, Memory, Context OS, Assistant generation behavior, or runtime persistence.

## 1. Problem statement

DIA-3 through DIA-6 answer how verified past experience is admitted, represented, moved, evolved, and linked:

```text
Trigger
  ↓
ReflectionContext
  ↓
Handoff
  ↓
Transport
  ↓
Evolution
  ↓
Lineage graph
```

DIA-7 answers the next identity-continuity question:

```text
verified causal history
        ↓
deterministic projection
        ↓
stable current continuity state
```

Canonical DIA-7 question:

```text
How does verified causal history become a stable current identity state?
```

DIA-7 is the materialized-view layer over DIA-6 lineage. DIA-6 remains the ledger. DIA-7 derives current state from the ledger; it does not own the ledger.

## 2. Core boundary

Frozen R0 rule:

```text
Projection ≠ New History
```

Valid projection is:

```text
verified DIA-6 lineage graph
+ frozen ContinuityProjectionPolicy
        ↓
ContinuityProjectionResult
        ↓
ContinuityState
```

Invalid projection is:

```text
projection result
        ↓
invent unsupported identity / relationship / belief fact
        ↓
claim current ContinuityState
```

DIA-7 has authority only over the deterministic derivation rule from verified causal history to current state. It has no authority to create, mutate, repair, reinterpret, or delete DIA-6 lineage history.

## 3. Public contract nouns

DIA-7 R0 freezes the noun surface only. Runtime classes and storage schemas are deferred to R1.

### 3.1 ContinuityProjectionInput

A bounded input object containing:

- source lineage graph reference
- source graph revision / root digest
- ordered verified lineage edges
- reachable lineage nodes
- projection policy reference
- optional projection scope selector

Contract requirements:

- every lineage node and edge must be DIA-6-valid before projection
- input ordering must be canonical and independent of caller order
- duplicate lineage entities must collapse by lineage identity
- unsupported graph revisions fail closed
- partial graphs must declare scope explicitly

### 3.2 ContinuityProjectionPolicy

A frozen policy object defining how current state is derived from verified lineage.

Required semantics:

- policy revision
- canonical projection algorithm revision
- allowed state domains
- state claim vocabulary
- evidence sufficiency rules
- conflict resolution rules
- supersession / correction / deprecation rules
- authority ordering rules
- confidence calculation rules, if confidence exists
- digest inclusion / exclusion rules

Same `ContinuityProjectionInput` plus same `ContinuityProjectionPolicy` must yield byte-identical `ContinuityState` and identical `ContinuityStateDigest`.

### 3.3 ContinuityState

A derived semantic state snapshot representing the current stable identity state projected from verified causal history.

Allowed v1 state domains:

- `identity_anchor`
- `stable_preference`
- `relationship_state`
- `active_commitment`
- `resolved_belief`
- `unresolved_tension`
- `long_term_trait`

Each state claim must carry:

- state claim id
- state domain
- canonical predicate / value
- support set of lineage refs
- projection rule id that admitted the claim
- effective status
- supersession / conflict metadata when relevant

No claim may exist without supporting lineage refs.

### 3.4 ContinuityAnchor

A high-stability derived claim used as an identity or relationship anchor.

Anchor requirements:

- must be derived from multiple or policy-authoritative lineage supports unless policy explicitly allows a single authoritative support
- must declare whether it is identity, relationship, cognitive, preference, or commitment oriented
- must be revocable only through explicit conflict, correction, deprecation, or supersession semantics
- must not be model-authored prose without lineage backing

### 3.5 ContinuityStateDigest

A semantic identity digest over `ContinuityState` only.

Digest domain separation:

```text
Context digest              != DIA-4 context_digest
Lineage digest              != DIA-6 lineage_digest
Continuity state digest     != DIA-7 state_digest
```

Digest inclusion candidates:

- DIA-7 state schema version
- projection policy fingerprint
- source graph root digest / revision
- canonical state claims
- canonical claim support refs
- canonical conflict statuses
- canonical anchor statuses

Digest exclusions:

- projection wall-clock time
- runtime host / process id
- Assistant prompt
- LLM model name
- sampling configuration
- audit diagnostics
- trace logging metadata

### 3.6 ContinuityProjectionResult

A deterministic result envelope containing:

- `ContinuityState`
- `ContinuityStateDigest`
- projection policy fingerprint
- source graph identity
- projection status
- rejected / unresolved claim counts
- conflict summary references
- audit sidecar reference

The result envelope must not add semantic identity fields outside `ContinuityState`.

### 3.7 ContinuityProjectionAudit

An observability sidecar for projection execution.

Audit may record:

- projection time
- source graph revision observed
- runtime diagnostics
- conflicts encountered
- rejected unsupported claims
- validation warnings
- implementation version
- duration / host metadata

Audit must not enter `ContinuityStateDigest` and must not alter `ContinuityState`.

## 4. Identity-domain separation

DIA-7 R0 freezes three non-interchangeable identity domains:

```text
Context
  question: What does this context contain?
  owner: DIA-4
  identity: context_digest

Lineage
  question: How did context evolve?
  owner: DIA-6
  identity: lineage_digest / graph identity

Continuity State
  question: What stable current state results from this history?
  owner: DIA-7
  identity: state_digest
```

A valid implementation must never substitute one digest for another.

## 5. Determinism invariant

Core projection must be deterministic:

```text
same verified lineage graph
+ same projection policy
        ↓
same ContinuityState
+ same ContinuityStateDigest
```

Forbidden nondeterminism sources:

- free-form LLM generation
- prompt wording drift
- model version drift
- sampling temperature
- dictionary iteration order
- wall-clock time
- locale / timezone
- runtime host metadata

LLMs may propose candidate interpretations for human or Assistant review, but Core projection must only admit claims through constrained policy rules and verified lineage evidence.

## 6. Evidence binding

Every `ContinuityState` claim must be traceable:

```text
state claim
    ↓
projection rule id
    ↓
supporting lineage refs
    ↓
DIA-6 lineage edge(s)
    ↓
DIA-4 ReflectionContext node(s)
    ↓
DIA-3 TriggerSourceRef reason(s)
```

Unsupported state claims are invalid, even if plausible, useful, emotionally salient, or already present in Memory.

## 7. Conflict semantics

DIA-7 must make conflict handling explicit and policy-bound.

Required conflict states:

- `active`: claim currently projected
- `superseded`: later supported claim replaces earlier claim under a policy rule
- `corrected`: earlier claim is explicitly corrected by a verified correction path
- `deprecated`: earlier claim is retired by explicit deprecation lineage
- `conflicted`: mutually incompatible supported claims exist and no policy rule resolves them
- `insufficient_support`: candidate claim lacks required lineage evidence

R0 rejects silent conflict resolution.

Example conflict shape:

```text
t1: Julia prefers A
t2: Julia rejects A
t3: Julia prefers B
```

A valid policy must decide whether this becomes:

- `A` superseded by `B`
- `A` corrected / deprecated
- unresolved conflict between `A` and `B`
- scoped coexistence if policy supports contextual domains

No implementation may assume last-write-wins unless the active policy explicitly defines last-write-wins for that claim domain, authority class, evidence type, and scope.

## 8. Relationship-state rule

Relationship state is a derived state domain, not a Memory assertion.

Invalid:

```text
Memory says: Tony and Julia are trusted partners
        ↓
relationship_state = trusted_partner
```

Valid:

```text
verified history A
    ↓
decision / commitment B
    ↓
interaction C
    ↓
evolution D
    ↓
policy-supported relationship_state claim
```

Every relationship claim must provide its support lineage refs and projection rule id. Assistant-visible relationship behavior may consume the state, but Assistant behavior does not define relationship truth.

## 9. Authority exclusions

DIA-7 R0 has no authority over:

- creation of new DIA-3 triggers
- construction or mutation of DIA-4 ReflectionContext
- DIA-5 handoff delivery or receipt
- DIA-6 lineage edge creation or graph mutation
- Diary admission
- Memory writes
- Assistant runtime behavior
- model generation policy
- storage persistence

R1 may implement deterministic Core projection. R2 may integrate Assistant consumption. Neither may let Assistant-generated prose directly become identity truth.

## 10. Forbidden behaviors

R0 freezes the following as invalid:

- LLM output directly becomes `ContinuityState`
- projection mutates DIA-6 lineage
- runtime timestamp enters state identity
- audit metadata changes `state_digest`
- unsupported state claim without lineage evidence
- silent conflict resolution without policy rule
- same history plus same policy yields different state
- Memory assertion becomes relationship state without lineage support
- context digest, lineage digest, and state digest are treated as interchangeable
- Assistant consumes state and then writes back identity truth through the projection layer

## 11. R1 / R2 split

```text
DIA-7 R0
Continuity Projection Contract
        ↓
DIA-7 R1
Core Continuity Projection
        ↓
DIA-7 R2
Assistant Continuity Integration
```

R1 responsibilities:

- implement frozen noun surface
- validate DIA-6 lineage input
- canonicalize projection input
- apply deterministic projection policy
- emit `ContinuityState`
- emit stable `ContinuityStateDigest`
- keep audit sidecar digest-excluded
- provide golden vectors and focused tests

R2 responsibilities:

- let Assistant consume `ContinuityState`
- expose current identity / relationship / commitment state to response planning
- prevent Assistant from defining identity truth
- route proposed new facts back through DIA-3 → DIA-6 admission paths

## 12. R0 acceptance checklist

DIA-7 R0 is acceptable when the contract clearly freezes:

- materialized-view boundary over DIA-6 lineage
- Projection ≠ New History
- public noun surface
- context / lineage / continuity-state digest separation
- deterministic projection invariant
- lineage evidence requirement for every claim
- explicit conflict semantics
- relationship-state lineage binding
- audit / semantic identity separation
- R1 Core vs R2 Assistant responsibility split

## 13. Gate summary

```text
DIA-6 Context Evolution
    FINAL ✅
    CLOSED ✅
    FROZEN 🔒

DIA-7 Continuity State Projection
    R0 Contract                ✅ COMPLETE
    Runtime implementation     ⏸ R1
    Assistant integration      ⏸ R2

Next artifact:
    DIA-7 R1 Core Continuity Projection
```
