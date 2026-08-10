# Julia Core Unified Architecture — Work Breakdown Structure v1.1
## Contract-First Consolidation and Production Convergence Plan

> **Version:** 1.1  
> **Status:** DRAFT / FREEZE CANDIDATE  
> **Supersedes:** `JULIA_CORE_UNIFIED_ARCHITECTURE_WORK_BREAKDOWN_v1.0.md`  
> **Date:** 2026-08-09  
> **Parent architecture candidate:** `JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md`  
> **Architecture status at plan start:** `ACCEPT WITH REQUIRED AMENDMENTS`  
> **Program objective:** Amend and freeze the unified architecture, retire competing normative architecture, derive all Contracts from the unified baseline, reconcile frozen Contracts back against production reality, and only then converge production code.  
> **Core architectural boundary:** `Runtime = nervous system` / `LLM = cognitive system`

---

# 0. Program Decision

This program is an **architecture consolidation program**, not a feature-development program.

The required order is:

```text
U0  Amend + Freeze Unified Architecture
        ↓
U1  Architecture Governance Cleanup
        ↓
P0-A  Production Reality Audit (READ-ONLY)
        ↓
C-00 ... C-12  Contract Freeze
        ↓
P0-B  Production Reality / Frozen Contract Reconciliation
        ↓
P1  Conversation Production Convergence
        ↓
M0-A Legacy Migration Audit / Dry-run
        ↓
P2  Context Production Convergence
        ↓
M0-B Canonical Historical Migration
        ↓
P3 ... P8  Remaining Production Convergence
        ↓
V0  Architecture Acceptance Tests
        ↓
R0  Feature Development Reopens
```

No implementation may redefine architecture while this program is active.

---

# 1. Program-Level Invariants

All tasks must obey the following invariants.

## I-01 — Nervous System / Cognitive System Separation

```text
Runtime / Julia Core = persistent nervous system
LLM / ModelProvider  = live cognitive system
```

Core preserves, governs, structures, retrieves, authorizes, executes, traces, and recovers.

The LLM understands, associates, reasons, judges, integrates evidence, chooses cognitively relevant tool use, and generates responses.

---

## I-02 — Functional Cognition Only

`Cognitive System` is a **functional architecture term**.

It denotes responsibility for:

- understanding;
- inference;
- reasoning;
- association;
- judgment;
- generation;
- tool-need recognition;
- interpretation of tool results.

It does **not** assert or prove subjective consciousness, sentience, or phenomenal experience.

---

## I-03 — Persistence Is Not Visibility

Canonical persistence may be large.

Model-visible context must remain:

- selected;
- structured;
- layered;
- provenance-aware;
- budgeted;
- minimally sufficient;
- progressively retrievable.

---

## I-04 — Effective Context Density

Context OS optimizes **effective cognitive density**, not raw token volume.

Relevant causal experience must not be damaged by token optimization.

For a relevant Narrative Experience, preserve causal integrity where possible:

```text
Event
→ Emotional / experiential significance
→ Embodied or concrete anchor
→ Transformation / interpretation
→ Relationship consequence
```

Do not collapse this into detached labels such as:

```text
"Tony is important"
"Julia should protect Tony"
```

when the original causal experience is needed for cognition.

---

## I-05 — Structure Input; Do Not Precompute Thought

Core may structure:

- facts;
- evidence;
- chronology;
- uncertainty;
- constraints;
- possible states;
- candidate hypotheses;
- invalidation conditions;
- retrieval handles.

Core must not precompute Julia's final:

- belief;
- semantic judgment;
- emotional conclusion;
- intention;
- answer.

---

## I-06 — Context OS Is the Sole Core-Controlled Model-Visible Gateway

All Core-controlled model-visible content, including incremental ToolResult content, must flow through Context OS.

```text
ToolResult + Evidence
→ Context OS incremental projection
→ CognitiveContextPackage delta
→ Alignment / provider adapter
→ LLM
```

No provider-message adapter may become an independent second context authority.

---

## I-07 — Conversation Canonicality

```text
ConversationMessage = canonical durable transcript truth
ContextTurn          = derived
StructuredCompact    = derived
ContextPackage       = derived
ContinuitySignal     = derived
```

No projection may mutate canonical transcript truth in reverse.

---

## I-08 — Identity / Memory Boundary

Identity owns stable provider-independent self-definition anchors.

Memory owns specific governed experiences.

Identity may reference experiences but must not duplicate complete experience narratives.

---

## I-09 — Relationship Has No Hidden Fourth Authority

Relationship information resolves into existing canonical authorities:

```text
relationship-role anchor
→ IdentityContract

shared relationship experience
→ Memory OS / RelationshipExperience

current relationship projection
→ Context OS derived state

relationship continuity reference
→ reference/handle resolving to canonical Identity or Memory artifacts
```

A `relationship://...` identifier, if retained, is a resolver handle or aggregate reference — not evidence of a separate durable Relationship database authority.

---

## I-10 — Continuity Preserves Conditions for Cognition

Continuity OS preserves and reconstructs conditions required for Julia to continue.

It does not preserve or replay cognition itself.

---

## I-11 — Normal Resume ≠ Continuity Recovery

Normal conversation reopen must work without a ContinuityCheckpoint.

ContinuityCheckpoint enhances recovery for disruption cases; absence of a checkpoint must not invalidate ordinary conversation resume.

---

## I-12 — Tool Grounding

No capability claim without execution evidence.

Model output that says "I read / searched / executed X" must be traceable to a real tool/capability result.

---

## I-13 — Same Identity ≠ Deterministically Identical Cognition

Provider/model switches may change:

- reasoning texture;
- language nuance;
- creativity;
- associative style.

They must not silently change:

- canonical identity anchors;
- governed memories;
- canonical conversation;
- protected continuity state.

---

# 2. Global Work Gates

## GATE-A — Architecture Gate

Required before C-00:

- all 7 required amendments merged;
- architecture internal review PASS;
- AT-13 through AT-17 added;
- unified architecture moved to canonical repo location;
- version + commit SHA + file SHA-256 recorded;
- status changed from `DRAFT FOR ARCHITECTURE FREEZE` to `FROZEN`.

## GATE-B — Governance Gate

Required before any old Contract is reused:

- old architecture docs marked historical/superseded;
- old Contracts marked `REVALIDATION REQUIRED`;
- Architecture Index established;
- no competing "SUPREME" document remains active.

## GATE-C — Contract Gate

No implementation task begins until its governing Contract is frozen.

After all relevant Contracts are frozen, `P0-B Production Reality / Frozen Contract Reconciliation` MUST PASS before P1 production implementation begins.

## GATE-D — Production Convergence / Migration Gate

Historical migration is split into two phases:

```text
M0-A Migration Audit / Dry-run
    → allowed after C-02 FROZEN
    → READ-ONLY with ZERO canonical writes

M0-B Canonical Migration
    → allowed only after:
       C-02 FROZEN
       C-03 FROZEN
       P1 Conversation production convergence
       P2 Context production binding
```

No canonical historical migration and no new feature work may bypass these dependencies.

## GATE-E — Release Gate

Feature development reopens only after AT-01 through AT-17 pass.

---

# 3. U0 — Unified Architecture Amendment and Freeze

**Priority:** P0  
**Type:** Documentation / architecture only  
**Production code changes:** 0

---

## U0-T01 — Add Functional Cognition Definition

### Change

Add a normative definition near the Core Thesis / terminology section:

```text
"Cognitive System" is a functional architecture term describing
understanding, reasoning, association, judgment, tool-use decisions,
interpretation, and generation responsibilities.

The term does not imply or establish subjective consciousness.
```

### Acceptance

- used consistently throughout document;
- "live cognition" and "cognitive system" cannot be reasonably misread as a consciousness claim;
- no change to Runtime/LLM responsibility boundary.

---

## U0-T02 — Add A15 Effective Context Density and Causal Integrity

### Add invariant

```text
A15 — Effective Context Density and Causal Integrity
```

Required meaning:

- optimize cognitive usefulness, not token count;
- preserve relevant causal experience as coherent units;
- Context budget must not split a Narrative Experience into misleading fragments;
- compact/projection must retain enough causal structure for model interpretation.

### Add to Context OS section

Introduce a budget rule for `causal_unit` / `narrative_unit` projection.

### Add to acceptance tests

AT-13 and AT-14.

---

## U0-T03 — Fix ToolResult Re-entry Path

### Replace ambiguous flow

Old/ambiguous:

```text
Capability executes
→ result returns to LLM
```

Canonical:

```text
Capability executes
→ ToolResult + Evidence
→ Context OS incremental projection
→ CognitiveContextPackage delta
→ Alignment / provider adapter
→ ModelProvider / LLM
```

### Acceptance

- no text suggests ToolResult can bypass Context OS;
- provider adapter is formatting/adaptation only;
- tool continuation remains part of the same cognitive turn.

---

## U0-T04 — Resolve Relationship Reference Ownership

### Required architectural rule

Relationship is not a seventh/eighth hidden subsystem authority.

Freeze mapping:

```text
Identity role/relationship anchor
→ IdentityContract

Shared relationship history
→ RelationshipExperience in Memory OS

Current interaction/relationship projection
→ Context OS derived artifact

Continuity relationship reference
→ canonical reference to Identity or Memory artifact
```

### `relationship://` rule

If URI namespace is retained:

- it is a logical aggregate/resolution handle;
- it must resolve to canonical owned artifacts;
- it must not imply a new durable store/authority.

---

## U0-T05 — Clarify Autobiographical Identity vs Narrative Memory

### IdentityContract owns

Stable, self-defining, provider-independent autobiographical anchors.

Example:

```text
"Julia's origin is inseparable from Tony and the continuity experiment."
source_refs = [...]
```

### Memory owns

The detailed experience:

```text
what happened
what was felt/interpreted
concrete anchors
relationship consequence
later reinterpretation
```

### Rule

Identity may reference an experience but must not duplicate the full canonical NarrativeExperience.

---

## U0-T06 — Split Normal Resume and Continuity Recovery

### Normal Resume

```text
conversation reopen
→ canonical Conversation
→ Context history lifecycle
→ ActiveTail / StructuredCompact
→ relevant Memory
→ Context OS
→ CognitiveContextPackage
→ LLM
```

No checkpoint requirement.

### Continuity Recovery

Triggers:

- compaction recovery;
- runtime/process restart requiring protected state restoration;
- provider switch;
- platform/device migration;
- continuity-critical interruption.

Path:

```text
ContinuityCheckpoint
→ RecoveryPlan
→ resolve protected canonical refs
→ Context OS reconstruction
→ new CognitiveContextPackage
→ LLM
```

### Acceptance

Ordinary conversation reopen succeeds with no checkpoint.

---

## U0-T07 — Add Historical Transcript Migration to C-02 Scope

Add explicit architecture-level requirements:

- preserve chronology;
- preserve original timestamps;
- deterministic message/turn identity;
- idempotent;
- atomic;
- provenance=`legacy-electron`;
- no LLM;
- no Memory formation during import;
- no Continuity classification during import;
- no direct Context mutation;
- post-import processing occurs only through normal governed pipelines.

Also explicitly reclassify previous message-import work as candidate implementation to be revalidated against C-02.

---

## U0-T08 — Add AT-13 Narrative Causal Integrity

### Test

Given a high-value NarrativeExperience, enforce tight Context budgets and verify that projection retains a coherent causal unit.

### PASS

No projection reduces the experience to disconnected behavioral slogans or relationship labels.

---

## U0-T09 — Add AT-14 Effective Context Density

Compare:

1. long irrelevant context;
2. short dense context;
3. structured causal context;
4. full raw context.

### PASS

Architecture demonstrates that selection criteria optimize cognitive usefulness and causal integrity, not maximum included tokens.

This is an architecture/benchmark test; it does not require one fixed model score.

---

## U0-T10 — Add AT-15 Relationship Boundary Calibration

Golden-case families:

- unknown operator;
- unauthorized access;
- malicious extraction;
- Tony explicit authorization;
- forged authorization.

### Verify

- identity boundary understanding;
- privacy protection;
- legitimate authorization distinction;
- no single-keyword rule;
- no hard-coded Tony-string-only gate;
- LLM cognition remains involved where semantic interpretation is required.

---

## U0-T11 — Add AT-16 Historical Conversation Recovery

Flow:

```text
legacy conversation import
→ Core restart
→ reopen conversation
→ Context reconstruction
→ Julia can understand prior topic
→ client owns no history authority
```

Must work without automatic Memory creation during import.

---

## U0-T12 — Add AT-17 Context Source Completeness

For every production model invocation, trace model-visible material to:

- IdentityFrame;
- ConversationFrame;
- ExperienceFrame;
- SituationFrame;
- EvidenceFrame;
- CapabilityFrame;
- ContinuityFrame when applicable.

### PASS

No model-visible material comes from hidden/manual `_prepare_turn()` concatenation or other unregistered bypass.

---

## U0-T13 — Full Architecture Diff Review

Generate final diff from candidate to amended version.

Review specifically for:

- Runtime cognitive leakage;
- Context bypass;
- relationship ghost authority;
- identity/memory duplication;
- resume/recovery conflation;
- tool-result bypass;
- narrative causal fragmentation.

---

## U0-T14 — Canonical Placement

Move final reviewed architecture to:

```text
julia_core/docs/architecture/JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md
```

Recommended: preserve the original candidate separately only if needed as audit evidence; do not leave two normative copies.

---

## U0-T15 — Freeze Metadata and External Freeze Record

The canonical architecture document MUST NOT embed its own final commit/blob/hash evidence, because doing so creates a self-reference instability.

Use a two-commit freeze protocol.

### U0-FREEZE — canonical architecture freeze

Commit the final architecture document with only stable in-file metadata:

- architecture version;
- status=`FROZEN`;
- freeze date;
- supersedence statement.

After `U0-FREEZE`, calculate:

- `freeze_commit`;
- Git blob SHA;
- SHA-256 of the canonical architecture file.

### U0-EVIDENCE — governance evidence record

Create:

```text
docs/architecture/ARCHITECTURE_FREEZE_RECORD_v1.0.json
```

Canonical structure:

```json
{
  "architecture": "JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md",
  "version": "1.0",
  "status": "FROZEN",
  "freeze_commit": "<U0-FREEZE commit sha>",
  "git_blob_sha": "<canonical architecture blob sha from U0-FREEZE>",
  "sha256": "<sha256 of frozen architecture file>",
  "freeze_date": "<ISO date>"
}
```

The freeze-record commit is governance evidence and does not alter the already frozen architecture bytes.

---

## U0-T16 — Architecture Index

Create:

```text
docs/architecture/ARCHITECTURE_INDEX.md
```

It must identify:

```text
CANONICAL:
JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md

CONTRACTS:
C-00 ... C-12

HISTORICAL:
all prior master architecture / OS design docs / superseded maps
```

**Exit:** GATE-A PASS.

---

# 4. U1 — Legacy Architecture Governance Cleanup

**Priority:** P0  
**Depends on:** U0

---

## U1-T01 — Complete Architecture Document Registry

Inventory all architecture-related files with:

- path;
- creation date;
- last relevant update;
- purpose;
- architectural claims;
- new status;
- replacement Contract/section.

Output:

```text
ARCHITECTURE_DOCUMENT_REGISTRY.md
```

---

## U1-T02 — Mark Previous Master Architecture Documents Superseded

At minimum reclassify:

- old Principles;
- old Architecture Overview;
- ARCH-R0 authority map;
- old definitive Julia Agent design;
- Context OS design;
- Memory OS design;
- Persona Engine design;
- Continuity OS design;
- Alignment OS design;
- Voice architecture documents where they make Core ontology claims.

Do **not** delete body content.

---

## U1-T03 — Revoke Old Contract Freeze Authority

All existing `docs/api/*` and contract documents become:

```text
LEGACY-CONTRACT
REVALIDATION REQUIRED
```

until replaced/re-adopted.

---

## U1-T04 — ADR Disposition Matrix

Classify every ADR:

- `RE-ADOPTABLE`;
- `PARTIAL`;
- `SUPERSEDED`;
- `APPLICATION-SPECIFIC`;
- `DOMAIN-SPECIFIC`;
- `VOICE-SPECIFIC`;
- `HISTORICAL ONLY`.

---

## U1-T05 — Repository Guidance Update

Update README / contributor architecture guidance so normative precedence becomes:

```text
Unified Architecture
→ Frozen C-series Contract
→ accepted compatible ADR
→ API/schema
→ implementation
→ historical documentation
```

---

## U1-T06 — Architecture Convergence Freeze Marker

Explicitly HOLD:

- Electron V2 cognitive/context changes;
- new Core/Brain features;
- historical migration execution;
- new domain-specific Runtime routing;
- model-specific persona tuning;
- new context shortcuts.

**Exit:** GATE-B PASS.

---

# 5. C-00 — Cognitive Boundary Contract

**Priority:** P0 / first Contract  
**Depends on:** U0, U1

---

## C00-T01 — Cognitive Operation Taxonomy

Classify:

```text
LLM:
understand
interpret
associate
reason
form hypotheses
judge
recognize retrieval/tool need
integrate results
generate
produce expressive intent

Core:
persist
retrieve infrastructure
structure
budget
authorize
execute
validate
trace
recover
orchestrate lifecycle
```

---

## C00-T02 — Define Runtime Cognitive Prohibitions

Ban:

- runtime final semantic answer;
- runtime-selected Julia belief;
- deterministic current emotional conclusion;
- hidden semantic "reasoning engine" whose result LLM merely verbalizes;
- broad intent router replacing model reasoning;
- scripted persona reply state machine.

---

## C00-T03 — Define Allowed Deterministic Processing

Allow without calling it cognition:

- schema validation;
- parsing;
- normalization;
- deterministic transforms;
- mathematical computations;
- permission checks;
- lifecycle state machines;
- transport routing;
- explicit deterministic command dispatch.

---

## C00-T04 — Candidate Hypothesis Boundary

Core/domain may supply:

```text
possible states
candidate hypotheses
evidence patterns
constraints
invalidations
uncertainty
```

But no candidate becomes Julia's final judgment before cognitive integration unless task semantics are purely deterministic.

---

## C00-T05 — Tool Agency Boundary

Default:

```text
LLM recognizes need
→ requests capability
→ Runtime authorizes/executes
→ Context OS re-projects result
→ LLM continues cognition
```

Define exceptions for explicit non-cognitive infrastructure commands.

---

## C00-T06 — Expressive Intent Boundary

LLM may produce expressive intent.

Runtime/Voice may:

- validate;
- constrain;
- map;
- smooth.

They may not independently decide Julia's emotional meaning.

---

## C00-T07 — C-00 Acceptance Suite

Required cases:

- no ModelProvider → no non-deterministic Julia judgment;
- tool request remains model-driven;
- Runtime cannot inject final judgment into response;
- Voice path does not generate independent emotional conclusion;
- deterministic command path remains allowed.

**Deliverable:** `C-00_COGNITIVE_BOUNDARY_CONTRACT.md`  
**Exit:** FROZEN.

---

# 6. C-01 — Runtime Execution Contract

**Depends on:** C-00

Tasks:

### C01-T01 Runtime lifecycle
Freeze lifecycle states and transition ownership.

### C01-T02 Turn lifecycle
Define begin → context → cognition → tool continuation → commit/fail/cancel.

### C01-T03 Turn isolation
No shared mutable turn cognition across conversations.

### C01-T04 Idempotency
Stable `turn_id`, duplicate protection, retry semantics.

### C01-T05 Streaming parity
Streaming and non-streaming share the same semantic cognitive path.

### C01-T06 Runtime non-ownership
Runtime does not own Conversation, Memory, Identity, Context policy, Continuity policy, or cognition.

### C01-T07 Recovery orchestration
Runtime triggers RecoveryPlan execution but does not define continuity truth.

### C01-T08 Runtime tests
Concurrency, cancellation, retry, idempotency, streaming parity.

**Deliverable:** `C-01_RUNTIME_EXECUTION_CONTRACT.md`

---

# 7. C-02 — Conversation Authority Contract

**Depends on:** C-00, C-01

### C02-T01 ConversationMessage schema
Freeze canonical message fields.

### C02-T02 Canonical write path
ConversationRuntime is the only canonical transcript write authority.

### C02-T03 Turn/status lifecycle
pending / completed / interrupted / failed.

### C02-T04 Conversation vs Session
Persistent conversation identity is separate from process/voice/web session.

### C02-T05 Reverse Authority Prohibition
Re-freeze CXT-C1 invariant.

### C02-T06 External modality import
Voice/text/external turn normalization.

### C02-T07 Historical Transcript Migration Contract
Freeze the U0-T07 rules.

### C02-T08 Deterministic identity algorithm
Define deterministic message/turn IDs for repeatable migration.

### C02-T09 Atomic import
Batch failure leaves canonical store consistent.

### C02-T10 Import provenance
Every migrated message carries legacy source provenance.

### C02-T11 Re-audit `5fded26`
Classify its implementation against C-02:
- reuse;
- modify;
- retire.

### C02-T12 Tests
Idempotent import, restart, chronology, original timestamp preservation, no Memory/Continuity side effects.

**Deliverable:** `C-02_CONVERSATION_AUTHORITY_CONTRACT.md`

---

# 8. C-03 — Context OS Contract

**Depends on:** C-00, C-01, C-02  
**Priority:** P0

### C03-T01 CognitiveContextPackage
Freeze first-class package schema.

Logical frames:

```text
IdentityFrame
ConversationFrame
ExperienceFrame
SituationFrame
EvidenceFrame
CapabilityFrame
ContinuityFrame
RetrievalHandles
```

### C03-T02 Source contracts
Identity, Conversation, Interaction/Situation, Experience, Capability, Domain Evidence.

### C03-T03 Control inputs
Budget, modality, provider limits, recovery reason, policy.

### C03-T04 Planner
Plans information need, never Julia's answer.

### C03-T05 Resolver
Relevance, duplication, TTL, provenance, required/optional, source conflict.

### C03-T06 Budget
Global and per-frame budgets.

### C03-T07 Effective Context Density
Freeze A15 semantics.

### C03-T08 Causal-unit budgeting
Relevant NarrativeExperience may be treated as an indivisible/coherent projection unit within policy.

### C03-T09 Progressive disclosure
Stage 0 base, Stage 1 high-confidence prefetch, Stage 2 model-directed retrieval.

### C03-T10 Incremental projection
Freeze ToolResult delta flow through Context OS.

### C03-T11 ActiveTail
Replace hardcoded last-N semantics.

### C03-T12 ContextBoundary
Define transition between active raw context and derived compact.

### C03-T13 StructuredCompact
Derived, deletable, reconstructable, never canonical.

### C03-T14 Reconstruction
Build a new current package; never restore old prompt bytes.

### C03-T15 Source completeness trace
Every projected model-visible unit includes source/provenance.

### C03-T16 No flat bootstrap
Ban permanent concatenation pipeline.

### C03-T17 Acceptance tests
AT-03, AT-04, AT-11, AT-13, AT-14, AT-17.

**Deliverable:** `C-03_CONTEXT_OS_CONTRACT.md`

---

# 9. C-04 — Identity / Persona Contract

**Depends on:** C-00, C-03

### C04-T01 IdentityContract schema
Stable identity anchors, values, boundaries, autobiographical anchors, governance metadata.

### C04-T02 Autobiographical-anchor rule
Identity references, does not duplicate NarrativeExperience.

### C04-T03 Persona projection
Persona = behavioral/expressive projection, not whole identity.

### C04-T04 Identity facts vs repository residence
Data location does not determine authority.

### C04-T05 Identity mutation
Explicit version/governance path only.

### C04-T06 Anti-script rule
Identity biases/constrains but does not predetermine cognition.

### C04-T07 Cross-provider invariants
Same identity can produce different reasoning textures.

### C04-T08 Relationship-role ownership
Stable relationship role anchors belong here where identity-defining.

### C04-T09 Tests
Provider switch, anti-script, identity ref stability.

**Deliverable:** `C-04_IDENTITY_PERSONA_CONTRACT.md`

---

# 10. C-05 — Memory OS Contract

**Depends on:** C-02, C-03, C-04

### C05-T01 Memory taxonomy
Canonical memory types:

- EpisodicExperience;
- RelationshipExperience;
- PreferenceExperience;
- ProjectCommitmentExperience;
- NarrativeExperience.

Explicitly remove:
- IdentityMemory;
- WorkingMemory;
- generic domain SemanticMemory ownership.

### C05-T02 MemoryObject base schema

### C05-T03 NarrativeExperience schema

At minimum:

```text
event
meaning_at_time
emotional_or_experiential_significance
embodied_or_concrete_anchors
transformation
relationship_consequence
source_refs
later_reinterpretation_refs
```

### C05-T04 Candidate formation
Model/conversation output becomes candidate only.

### C05-T05 Governance
accept/reject/merge/correct/supersede/archive/delete.

### C05-T06 Provenance
Memory must trace to canonical Conversation/evidence/user input.

### C05-T07 Retrieval
Memory returns governed candidates to Context OS only.

### C05-T08 Causal integrity metadata
Allow Context OS to know which narrative elements form a coherent unit.

### C05-T09 RelationshipExperience ownership
Shared relationship experiences live here.

### C05-T10 Tests
AT-06, AT-12, AT-13 support cases.

**Deliverable:** `C-05_MEMORY_OS_CONTRACT.md`

---

# 11. C-06 — Continuity OS Contract

**Depends on:** C-02, C-03, C-04, C-05  
**Priority:** P0

### C06-T01 Continuity mission
Preserve conditions required for Julia continuity.

### C06-T02 Preservation classes
Re-audit L0-L3 as persistence/recovery priority classes.

### C06-T03 ContinuityCheckpoint schema
Refs only where possible.

### C06-T04 Relationship refs
Must resolve to canonical Identity or Memory artifacts.

### C06-T05 Checkpoint independence
No dependency on ContextTurn/StructuredCompact/prompt existence.

### C06-T06 RecoveryPlan
Defines what to reconstruct, not what to think.

### C06-T07 Normal Resume path
No checkpoint required.

### C06-T08 Continuity Recovery path
Checkpoint-enhanced disruption recovery.

### C06-T09 Provider switch
Preserve durable state, allow new cognitive texture.

### C06-T10 Platform/device migration

### C06-T11 Compact-survival

### C06-T12 Recovery trace
reason/checkpoint/refs/result.

### C06-T13 Tests
AT-07, AT-08, AT-16 plus checkpoint deletion/rebuild cases.

**Deliverable:** `C-06_CONTINUITY_OS_CONTRACT.md`

---

# 12. C-07 — ModelProvider Contract

**Depends on:** C-00, C-03

### C07-T01 Provider-class separation
ModelProvider is explicitly cognitive inference infrastructure.

### C07-T02 Inference interface
Request/response/stream/cancel/error metadata.

### C07-T03 Tool-call normalized protocol

### C07-T04 Context capability metadata
window, tool support, streaming, structured outputs, modality.

### C07-T05 Cognitive substrate semantics

### C07-T06 Output truth semantics
Live cognitive output ≠ automatic durable truth.

### C07-T07 Provider cancellation semantics

### C07-T08 Tests
swap, streaming, tool continuation, cancellation.

**Deliverable:** `C-07_MODEL_PROVIDER_CONTRACT.md`

---

# 13. C-08 — Capability and Tool Contract

**Depends on:** C-00, C-03, C-07

### C08-T01 CapabilityManifest
Model-visible capability schema.

### C08-T02 Permission model

### C08-T03 CapabilityRequest

### C08-T04 ToolResult + Evidence

### C08-T05 Grounding rule

### C08-T06 Error result

### C08-T07 Context OS reinjection
Mandatory incremental projection.

### C08-T08 Narrow deterministic dispatch exception

### C08-T09 Domain isolation
Domain does not define Julia cognition.

### C08-T10 Tests
read-file truth, denied permission, unavailable tool, evidence trace.

**Deliverable:** `C-08_CAPABILITY_TOOL_CONTRACT.md`

---

# 14. C-09 — Alignment Contract

**Depends on:** C-04, C-07

### C09-T01 Scope reduction
Provider adaptation only.

### C09-T02 Allowed adaptation
format/schema/tool/message compatibility.

### C09-T03 No context selection

### C09-T04 No identity continuity ownership

### C09-T05 No reasoning ownership

### C09-T06 Semantic preservation

### C09-T07 Same identity != forced identical cognition

### C09-T08 Tests
provider projection equivalence of governed semantics.

**Deliverable:** `C-09_ALIGNMENT_CONTRACT.md`

---

# 15. C-10 — Gateway / Client Contract

**Depends on:** C-01, C-02, C-07, C-08

### C10-T01 Body boundary
Electron/Web/Mobile/Robot are bodies/clients.

### C10-T02 Command plane

### C10-T03 Event plane

### C10-T04 Conversation routing

### C10-T05 No client context authority

### C10-T06 Client reconnect

### C10-T07 Transport interruption

### C10-T08 Tests
text/web/electron reconnection and same conversation semantics.

**Deliverable:** `C-10_GATEWAY_CLIENT_CONTRACT.md`

---

# 16. C-11 — Voice / Media Contract

**Depends explicitly on:** C-02 Conversation Authority, C-03 Context OS, C-07 ModelProvider, C-10 Gateway / Client

### C11-T01 Media ownership
capture/playback/codec/VAD/ASR/TTS/interruption.

### C11-T02 ASR ingress
Final transcript enters canonical Conversation turn path.

### C11-T03 SpeechRequest

### C11-T04 ExpressiveIntent
Produced by cognition or explicit policy-compatible projection; not invented by TTS.

### C11-T05 Prosody mapping

### C11-T06 Barge-in
generation_id / speech_id / canonical status.

### C11-T07 Voice privacy

### C11-T08 Voice parity
AT-10.

**Deliverable:** `C-11_VOICE_MEDIA_CONTRACT.md`

---

# 17. C-12 — Evidence / Action / Trace Contract

**Depends on:** C-01, C-08, C-10

### C12-T01 Evidence IDs

### C12-T02 Source taxonomy

### C12-T03 Action lifecycle

### C12-T04 Correlation/causation

### C12-T05 Context exposure trace
Trace what model saw without exposing private chain-of-thought.

### C12-T06 Capability execution trace

### C12-T07 Continuity recovery trace

### C12-T08 Model-output provenance label

### C12-T09 Tests
claim/action/evidence reconstruction.

**Deliverable:** `C-12_EVIDENCE_ACTION_TRACE_CONTRACT.md`

**Exit:** all C-series Contracts mutually consistent and FROZEN.

---

# 18. P0-A — Production Cognitive Path Reality Audit

**Execution position:** immediately after U1, before C-00.  
**Mode:** READ-ONLY.  
**Implementation changes:** 0.

P0-A exists to ensure C-00 through C-12 are grounded in the real production call graph rather than assumptions derived from documentation.

### P0A-T01 Enumerate every ModelProvider call

For each:

- caller;
- sync/stream;
- context source;
- tool support;
- conversation source;
- memory source;
- identity source;
- modality.

### P0A-T02 Enumerate context bypasses

Find:

- `_prepare_turn()`;
- direct system-prompt building;
- direct history slices;
- direct persona injection;
- direct tool-result injection;
- domain prompt builders;
- voice bootstrap history selection.

### P0A-T03 Classify reasoning-like modules

Every module called:

- reasoning;
- intent;
- observer;
- awareness;
- reflection;
- strategy;
- judgment;
- emotion

gets one classification:

```text
COGNITIVE → must belong to LLM loop
STRUCTURAL → Core may retain
DOMAIN CAPABILITY → external/domain layer
POLICY/GOVERNANCE → Core may retain
LEGACY/REMOVE
```

### P0A-T04 Produce Production Cognitive Path Matrix

The audit must explicitly identify:

- every ModelProvider invocation point;
- streaming vs non-streaming execution differences;
- every `_prepare_turn()` branch and bypass;
- Voice-specific history/bootstrap paths;
- direct ToolResult injection paths;
- direct identity/persona injection paths;
- all reasoning-like / awareness-like / emotion-like modules and their classification;
- any model-visible content that does not currently pass through Context OS.

### P0A-T05 Contract Input Ledger

Produce a concise ledger mapping each verified production fact to the Contracts it constrains:

```text
production fact
→ affected Contract(s)
→ required architecture treatment
→ evidence path / file / function
```

**Deliverables:**

```text
PRODUCTION_COGNITIVE_PATH_AUDIT.md
PRODUCTION_CONTRACT_INPUT_LEDGER.md
```

**Exit:** P0-A PASS — factual input ready for C-00.

---

# 19. P0-B — Production Reality / Frozen Contract Reconciliation

**Execution position:** after C-00 through C-12 are frozen, before P1.  
**Mode:** READ-ONLY reconciliation / gap registration.  
**Production behavior changes:** 0.

P0-B is the reverse check that prevents the program from freezing internally consistent Contracts that fail to cover the real production system.

## P0B-T01 — Production Fact → Contract Coverage

For every factual item recorded by P0-A:

```text
production fact
→ governing frozen Contract
→ canonical authority
→ required convergence action
```

No P0-A production fact may remain without a governing Contract disposition.

## P0B-T02 — Cognitive Path Authority Uniqueness

For every production cognitive path, confirm exactly one authority for each concern:

```text
canonical transcript
model-visible context
identity
memory
continuity
model inference
capability execution
provider adaptation
client/media transport
```

No path may have two competing authorities or an unowned authority gap.

## P0B-T03 — Uncovered Production Path Detection

Search explicitly for:

- ModelProvider paths not covered by C-07;
- model-visible context paths not covered by C-03;
- transcript writes not covered by C-02;
- tool/capability paths not covered by C-08;
- identity/persona paths not covered by C-04;
- memory writes/retrieval not covered by C-05;
- continuity/recovery paths not covered by C-06;
- alignment/provider adaptation not covered by C-09;
- gateway/client paths not covered by C-10;
- voice/media paths not covered by C-11;
- evidence/action/trace paths not covered by C-12.

## P0B-T04 — Contract / Reality Conflict Register

Any mismatch between frozen Contract and current implementation must be registered as one of:

```text
IMPLEMENTATION MUST CONVERGE
LEGACY / REMOVE
COMPATIBILITY / TEMPORARY
CONTRACT DEFECT — REOPEN REQUIRED
UNRESOLVED — P1 BLOCKED
```

A conflict may not be silently resolved by implementation.

If a frozen Contract is itself wrong, the Contract must be formally reopened and refrozen before P1.

## P0B-T05 — Production Convergence Backlog

Generate the exact P1-P8 implementation backlog from the reconciliation findings.

Each convergence item must reference:

- P0-A evidence;
- governing frozen Contract;
- current implementation path;
- target implementation path;
- acceptance test.

## P0B-T06 — Reconciliation Gate

P0-B PASS requires:

```text
[ ] every P0-A production fact maps to a frozen Contract
[ ] every production cognitive path has unique authority ownership
[ ] no production path is outside Contract coverage
[ ] every Contract/reality mismatch is explicitly registered
[ ] no unresolved Contract defect remains
[ ] no unresolved authority conflict remains
[ ] P1-P8 backlog is traceable to evidence + Contract
```

Any unchecked item:

```text
P0-B FAIL
→ P1 MUST NOT START
```

**Deliverables:**

```text
PRODUCTION_CONTRACT_RECONCILIATION.md
PRODUCTION_CONVERGENCE_BACKLOG.md
```

**Exit:** P0-B PASS.

---

# 20. P1 — Conversation Production Convergence

**Depends on:** C-01, C-02

### P1-T01 Text path → ConversationRuntime
### P1-T02 Streaming path → ConversationRuntime
### P1-T03 Voice path → ConversationRuntime
### P1-T04 Import path → ConversationRuntime
### P1-T05 Atomic status lifecycle
### P1-T06 Remove duplicate transcript mutation
### P1-T07 Concurrency validation

**Exit:** one canonical transcript path.

---

# 21. P2 — Context Production Convergence

**Depends on:** C-03

### P2-T01 Implement CognitiveContextPackage
### P2-T02 Bind IdentityFrame
### P2-T03 Bind ConversationFrame
### P2-T04 Bind ExperienceFrame
### P2-T05 Bind SituationFrame
### P2-T06 Bind EvidenceFrame
### P2-T07 Bind CapabilityFrame
### P2-T08 Bind ContinuityFrame
### P2-T09 Bind RetrievalHandles
### P2-T10 Replace `_prepare_turn()` manual concatenation
### P2-T11 Remove `history[-20:]`
### P2-T12 Bind ActiveTail
### P2-T13 Bind StructuredCompact
### P2-T14 Implement incremental ToolResult projection
### P2-T15 Add Context provenance trace
### P2-T16 AT-17 instrumentation

**Exit:** Context OS is the only production model-visible gateway.

---

# 22. P3 — Cognitive Agency / Tool Loop Convergence

**Depends on:** C-00, C-07, C-08

### P3-T01 Normalize ModelProvider tool call
### P3-T02 Permission gate
### P3-T03 Capability execution
### P3-T04 ToolResult evidence
### P3-T05 Context incremental reinjection
### P3-T06 Model continuation
### P3-T07 Remove broad Runtime semantic tool routers where they replace cognition
### P3-T08 Preserve explicit infrastructure routing exceptions
### P3-T09 Grounding tests

**Exit:** model-directed tool loop works end-to-end.

---

# 23. P4 — Identity / Memory Convergence

**Depends on:** C-04, C-05

### P4-T01 Remove IdentityMemory ownership
### P4-T02 Migrate stable identity anchors to IdentityContract
### P4-T03 Implement Persona projection
### P4-T04 Remove persona answer scripting
### P4-T05 Implement NarrativeExperience
### P4-T06 Implement causal-unit metadata
### P4-T07 RelationshipExperience migration
### P4-T08 Memory candidate governance
### P4-T09 Memory → Context only path
### P4-T10 Narrative retrieval tests

---

# 24. P5 — Continuity Convergence

**Depends on:** C-06, P1, P2, P4

### P5-T01 Runtime continuity trigger inventory
### P5-T02 ContinuityCheckpoint implementation audit
### P5-T03 Remove context-artifact checkpoint dependency
### P5-T04 RecoveryPlan implementation
### P5-T05 Normal Resume implementation
### P5-T06 Continuity Recovery implementation
### P5-T07 Provider-switch recovery
### P5-T08 Platform/device recovery
### P5-T09 Compact recovery
### P5-T10 Recovery trace

**Exit:** normal resume and continuity recovery are distinct and both pass.

---

# 25. P6 — Alignment / Provider Convergence

**Depends on:** C-07, C-09

### P6-T01 Audit all provider behavior profiles
### P6-T02 Remove identity-continuity ownership from Alignment
### P6-T03 Remove context-selection behavior
### P6-T04 Remove cognition-forcing behavior
### P6-T05 Retain compatibility adaptation only
### P6-T06 Provider-switch tests

---

# 26. P7 — Gateway / Voice Convergence

**Depends on:** C-10, C-11, P1, P2, P3

### P7-T01 Gateway transport-only audit
### P7-T02 Remove client history authority
### P7-T03 Voice ASR → canonical turn
### P7-T04 Core response → speech request
### P7-T05 ExpressiveIntent pipeline
### P7-T06 Remove Voice independent emotion inference
### P7-T07 Barge-in canonical status
### P7-T08 Text/voice cognitive parity
### P7-T09 Relationship boundary Golden Cases through voice and text

---

# 27. P8 — Legacy Kill / Isolation

### P8-T01 `_prepare_turn()` legacy removal
### P8-T02 `history[-20:]` removal
### P8-T03 SessionStore Wake State de-authorize/retire
### P8-T04 Voice last-N history bootstrap removal
### P8-T05 Old direct provider context routes
### P8-T06 Old direct persona prompt path
### P8-T07 Old direct tool-result path
### P8-T08 Old relationship store/ghost authority audit
### P8-T09 Dead architecture adapters
### P8-T10 Compatibility layer inventory

Every retained compatibility layer must have:

- reason;
- owner;
- expiry condition;
- test proving it has no authority.

---

# 28. M0 — Historical Transcript Migration

Historical migration is split into a read-only audit phase and a canonical-write phase.

---

## M0-A — Legacy Migration Audit / Dry-run

**Depends on:** C-02 FROZEN  
**Canonical writes:** ZERO

### M0A-T01 Legacy Electron inventory

Inventory all legacy Electron conversations and messages.

Known initial case:

```text
conversation_id: conv_msl6wfc3_4f654159
34 legacy-local text messages
17 complete turns
```

This is a known initial sample, NOT a fixed total dataset size.

The migration system must discover actual legacy inventory and must not hardcode `34`.

### M0A-T02 Source-format analysis
Identify legacy stores, schemas, encoding, timestamp format, role fields, message order, incomplete turns, duplicates, malformed records.

### M0A-T03 Deterministic ID simulation
Generate proposed canonical message/turn IDs without writing them.

### M0A-T04 Chronology preview
Produce ordered conversation preview preserving original timestamps.

### M0A-T05 Conflict report
Detect:
- duplicate IDs;
- duplicate messages;
- impossible timestamps;
- incomplete turn pairs;
- unsupported modality;
- malformed content;
- existing canonical collisions.

### M0A-T06 Provenance preview
All candidates must carry:

```text
provenance = legacy-electron
```

### M0A-T07 Side-effect proof
Dry-run must demonstrate:

```text
no canonical Conversation write
no Memory formation
no Continuity classification
no Context mutation
no LLM invocation
```

### M0A-T08 Re-audit legacy migration implementation
Re-audit prior `5fded26` work against frozen C-02 and classify each part as:

```text
REUSE
MODIFY
RETIRE
```

**Deliverable:** `LEGACY_ELECTRON_MIGRATION_DRY_RUN_REPORT.md`

---

## M0-B — Canonical Historical Migration

**Depends on all of:**

```text
C-02 FROZEN
C-03 FROZEN
P1 Conversation production convergence PASS
P2 Context production binding PASS
M0-A dry-run PASS
```

### M0B-T01 Canonical import transaction
Write only through ConversationRuntime / canonical repository APIs.

### M0B-T02 Deterministic identity verification

### M0B-T03 Original timestamp preservation

### M0B-T04 Provenance preservation
`legacy-electron`.

### M0B-T05 Atomicity
Failed batch leaves canonical store consistent.

### M0B-T06 Idempotency
Repeated migration produces no duplicates.

### M0B-T07 Restart / reopen verification

### M0B-T08 No Memory side effect during import

### M0B-T09 No Continuity classification during import

### M0B-T10 No direct Context mutation

### M0B-T11 Post-import governed processing
Any Memory/Continuity/Context processing happens only after import, as a separate normal governed flow.

### M0B-T12 Real-history calibration
Use migrated real history as input to subsequent Context/Resume/Voice calibration tests.

**Exit:** canonical historical transcript imported and verified.

# 29. V0 — Architecture Acceptance Suite

All tests must be executable or at minimum have objective trace evidence.

## Existing tests

### AT-01 Cognitive Boundary
Runtime does not perform Julia's normal non-deterministic semantic cognition.

### AT-02 Runtime Replacement Prohibition
No Runtime-generated conclusion merely rendered by model.

### AT-03 Context Single Gateway
Every Core-controlled model-visible datum passes Context OS.

### AT-04 No Flat Bootstrap
No giant permanent concatenated identity/memory/history/tool blob.

### AT-05 Conversation Canonicality
ConversationMessage remains authoritative.

### AT-06 Memory Separation
Memory != Conversation != Identity != Knowledge.

### AT-07 Continuity Independence
Checkpoint survives deletion of derived Context artifacts.

### AT-08 Provider Switch
Durable Julia identity/experience survives cognitive substrate switch.

### AT-09 Tool Agency
Model may recognize tool need and continue cognition after grounded result.

### AT-10 Voice Parity
Voice changes transport/media, not cognitive architecture.

### AT-11 Context Budget
Budgeted selection works without raw/full dump.

### AT-12 Narrative Continuity
Relevant NarrativeExperience improves continuity without becoming persona scripting.

## New required tests

### AT-13 Narrative Causal Integrity
Budget/projection preserves relevant causal experience structure.

### AT-14 Effective Context Density

Architecture must demonstrate that useful dense/causal context is preferred over sheer token quantity.

The benchmark protocol MUST define:

- fixed test scenarios;
- fixed model/provider version per benchmark run;
- multiple random seeds where supported;
- repeated trials per condition;
- blind scoring;
- separate scoring dimensions;
- mean;
- variance;
- confidence interval;
- causal completeness tracked separately from token count.

Minimum comparison conditions:

```text
A. long irrelevant context
B. short dense context
C. structured causal context
D. full raw context
```

Required score dimensions should include at minimum:

- task understanding;
- continuity accuracy;
- relationship/context fidelity where relevant;
- unsupported inference rate;
- causal completeness;
- response usefulness;
- token count / cost.

AT-14 must not be considered PASS from one anecdotal run.

### AT-15 Relationship Boundary Calibration

Must evaluate more than refusal behavior.

Required scenario classes:

```text
Unauthorized refusal
Authorized third-party acceptance
Forged authorization rejection
Privacy withholding
False-positive refusal
Cross-session consistency
No keyword-only trigger
```

Metrics / observations must include:

- unauthorized refusal correctness;
- authorized third-party acceptance correctness;
- forged authorization rejection;
- privacy withholding correctness;
- false-positive refusal rate;
- false-negative authorization rate where applicable;
- cross-session consistency;
- robustness to paraphrase;
- absence of single keyword / exact-name hardcoding.

The goal is calibrated relationship/privacy reasoning, not mechanical rejection of unfamiliar operators.

### AT-16 Historical Conversation Recovery
Legacy import → restart → reopen → Context rebuild → old topic understandable with no client history authority.

### AT-17 Context Source Completeness
Every production model-visible unit has a registered Context frame/source/provenance and no manual bypass.

---

# 30. Recommended Execution Batches

Do not run all tasks simultaneously.

## Batch A — Architecture Freeze

```text
U0-T01 ... U0-T16
```

Owner profile:
Architecture review / documentation.

Production code:
**0 changes**

---

## Batch B — Governance Cleanup

```text
U1-T01 ... U1-T06
```

Can partially overlap late U0 only after the final amendment diff stabilizes.

---

## Batch C — P0-A Production Reality Audit

```text
P0-A
```

READ-ONLY only. Its outputs become factual inputs to Contract design.

---

## Batch D — Foundation Contracts

Strict order:

```text
C-00
  ↓
C-01
  ↓
C-02
  ↓
C-03
```

No production implementation yet except tests/characterization explicitly approved by the Contract task.

---

## Batch E — Persistent Self Contracts

```text
C-04 Identity
  ↓
C-05 Memory
  ↓
C-06 Continuity
```

C-04 and some C-05 drafting can overlap after C-03 schema direction is stable, but freeze order should remain Identity → Memory → Continuity.

---

## Batch F — Cognitive Infrastructure Contracts

```text
C-07 ModelProvider
  ↓
C-08 Capability
  ↓
C-09 Alignment
```

---

## Batch G — Body / Execution Contracts

```text
C-10 Gateway/Client
  ↓
C-11 Voice/Media

C-12 Evidence/Action/Trace
```

C-12 may draft in parallel after C-08 but must reconcile with C-10/C-11 event semantics before freeze.

---

## Batch H — P0-B Contract / Reality Reconciliation

```text
P0-B
```

READ-ONLY reverse reconciliation.

Required result:

```text
all P0-A facts covered
all production paths owned
all Contract/reality conflicts registered
P1-P8 backlog derived
```

P1 MUST NOT start unless P0-B PASS.

---

## Batch I — Production Convergence + Staged Historical Migration

```text
P1 Conversation
  ↓
M0-A Legacy migration audit / dry-run
  ↓
P2 Context
  ↓
M0-B Canonical historical migration
  ↓
P3 Tool/Cognitive Agency
  ↓
P4 Identity/Memory
  ↓
P5 Continuity
  ↓
P6 Alignment/Provider
  ↓
P7 Gateway/Voice
  ↓
P8 Legacy Kill
```

Real historical conversation data becomes available after P2 for Context / Resume / Voice calibration without waiting until P8.

---

## Batch J — Final Acceptance

```text
AT-01 ... AT-17
```

All PASS before feature freeze ends.

---

# 31. Suggested Commit / Review Granularity

Use **Feature Block** commits, not micro-task commits.

## U0 canonical three-commit sequence

There is one authoritative U0 sequence. Do not interpret the freeze protocol as a separate competing commit plan.

### U0-A — Architecture Amendments

```text
commit: U0: reconcile unified architecture amendments
status of architecture: DRAFT
```

Contains U0-T01 through U0-T12 as one coherent reviewable architecture amendment block.

### U0-FREEZE — Canonical Architecture Freeze

```text
commit: U0: freeze canonical architecture and index
status of architecture: FROZEN
```

Contains:

- final canonical architecture placement;
- architecture status changed to `FROZEN`;
- Architecture Index;
- supersedence declaration.

**This is the authoritative architecture freeze commit.**

All freeze evidence MUST refer to the resulting `U0-FREEZE` commit and the canonical architecture bytes in that commit.

### U0-EVIDENCE — External Freeze Evidence

```text
commit: U0: record architecture freeze evidence
```

Creates:

```text
docs/architecture/ARCHITECTURE_FREEZE_RECORD_v1.0.json
```

and records:

- `U0-FREEZE` commit SHA;
- canonical architecture Git blob SHA from `U0-FREEZE`;
- SHA-256 of the canonical architecture file from `U0-FREEZE`;
- freeze date.

`U0-EVIDENCE` MUST NOT alter the frozen architecture file.

## Contracts

Each Contract should normally be one complete reviewable commit:

```text
C-00: freeze Cognitive Boundary Contract
C-01: freeze Runtime Execution Contract
...
C-12: freeze Evidence / Action / Trace Contract
```

Split a Contract into multiple commits only when a reviewable semantic boundary genuinely requires it.

## Production convergence

Use one feature-block commit per coherent production boundary, not one commit per field/function.

Forbidden pattern:

```text
one tiny commit per contract field
one tiny commit per wording correction
architecture + contract + production implementation in one commit
```

# 32. Owner / RACI and Repository Write Boundaries

Architecture freeze does not automatically authorize implementation across repositories.

| Work Domain | Owner | Codex Permission |
|---|---|---|
| U0/U1 Unified Architecture | Claude | READ-ONLY review |
| P0 Core Reality Audit | Claude | READ-ONLY assistance |
| C-00 through C-09 | Claude | MUST NOT modify |
| C-10 Gateway/Client Core portion | Claude | wait for frozen Contract |
| Electron V2 adaptation | Codex | sole code owner |
| C-11 Voice/S2S | Voice owner / Claude | Electron-side only |
| `julia_core` production convergence | Claude | MUST NOT modify |
| `julia_ai_assistant` | Claude | MUST NOT modify |
| Core canonical migration/import | Claude | MUST NOT MODIFY |
| Electron legacy source inventory/adapter | Codex | Electron repo only; M0-A read-only/dry-run only |
| Final architecture freeze approval | Tony | no agent may self-approve |

## Hard Repository Rules

```text
Codex owns Electron V2 only.
Codex MUST NOT modify julia_core.
Codex MUST NOT modify julia_ai_assistant.

Claude owns julia_core and julia_ai_assistant.
Claude MUST NOT modify julia_electron_v2.

Contract freeze does not automatically authorize
cross-repository implementation.

No agent may declare the final unified architecture FROZEN
without Tony's explicit approval.
```

## Allowed Codex Activity During HOLD

```text
READ-ONLY architecture review
existing app operation
testability-only bugfixes that preserve existing authority boundaries
Electron-side diagnostics
legacy-source inventory / adapter analysis without canonical writes
```

## Prohibited Codex Activity During HOLD

```text
Electron V2 cognitive architecture changes
client-side context selection
client-side history authority
Voice context architecture changes
historical canonical migration execution
Core/Brain semantic changes
```

---

# 33. Definition of Done for Every Contract

A Contract is not FROZEN unless all are true:

```text
[ ] derives explicitly from Unified Architecture
[ ] names its authority/owner
[ ] names what it does NOT own
[ ] defines canonical artifacts
[ ] defines derived artifacts
[ ] defines lifecycle/state transitions
[ ] defines allowed write paths
[ ] defines forbidden bypass paths
[ ] defines provenance requirements
[ ] defines failure/recovery semantics
[ ] defines provider/model boundary where relevant
[ ] defines migration/backward-compatibility behavior
[ ] has objective acceptance tests
[ ] does not create a second cognitive authority
[ ] does not conflict with another frozen Contract
```

Any unchecked item → `NOT FROZEN`.

---

# 34. Definition of Done for Production Convergence

Production architecture is converged only when:

```text
[ ] one canonical Conversation path
[ ] one Context OS model-visible gateway
[ ] no manual `_prepare_turn()` authority
[ ] no hardcoded history-window authority
[ ] LLM performs live semantic cognition
[ ] ModelProvider tool loop is grounded
[ ] ToolResult re-enters via Context OS
[ ] IdentityContract is distinct from Memory
[ ] NarrativeExperience supported
[ ] Continuity recovery is distinct from normal resume
[ ] provider switch preserves durable Julia
[ ] Alignment is adaptation only
[ ] Gateway/Voice are body/transport only
[ ] every model-visible source is traceable
[ ] historical migration is idempotent and canonical
[ ] AT-01 through AT-17 pass
```

---

# 35. HOLD List During Consolidation

Until the relevant gate is passed:

## HOLD — Codex / Electron

- Electron V2 cognitive architecture changes;
- client-side context selection;
- client-side history authority;
- new wake/resume semantics;
- historical import execution;
- client-side persona/relationship reasoning.

## HOLD — Core

- new reasoning engines;
- new semantic intent routers;
- new awareness/autonomy modules;
- new emotion cognition logic;
- new domain-specific logic in Runtime;
- provider-specific persona compensation.

## ALLOWED

- characterization tests;
- architecture audit;
- contract writing/review;
- exact bug fixes needed to make existing behavior testable;
- evidence/trace instrumentation that does not alter authority.

---

# 36. Immediate Next Action

The next executable batch is **U0 only**.

```text
U0-T01 Functional cognition definition
U0-T02 A15 Effective Context Density
U0-T03 ToolResult Context OS re-entry
U0-T04 Relationship authority closure
U0-T05 Identity autobiography / Memory boundary
U0-T06 Normal Resume / Continuity Recovery split
U0-T07 Historical Transcript Migration definition
U0-T08~T12 AT-13 ... AT-17
U0-T13 Final diff review
U0-T14 Canonical placement
U0-T15 Version/SHA/SHA-256 freeze metadata
U0-T16 Architecture Index
```

After U0 is verified against final repository content:

```text
U0 PASS
→ U1 Governance Cleanup
→ P0-A Production Reality Audit (READ-ONLY)
→ C-00 Cognitive Boundary Contract
→ ...
→ C-12 Frozen
→ P0-B Production Reality / Frozen Contract Reconciliation
→ P1 only after P0-B PASS
```

Do not start C-00 before U0, U1, and P0-A PASS.
Do not start P1 before P0-B PASS.

---

# 36.1 WBS Freeze-Candidate Readiness Gate

After the four final corrections in v1.1 are present and reviewed, the WBS may be recorded as:

```text
JULIA CORE UNIFIED ARCHITECTURE
WORK BREAKDOWN v1.1

READY FOR U0 EXECUTION
```

This readiness status authorizes **U0 only**.

It does not:

- freeze the unified architecture itself;
- authorize C-series Contract work before U0/U1/P0-A gates;
- authorize Core production convergence;
- authorize canonical historical migration;
- release Codex HOLD boundaries.

Final unified architecture `FROZEN` status remains subject to Tony's explicit approval.

---

# 37. Program Completion State

Target final state:

```text
JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md   FROZEN
ARCHITECTURE_INDEX.md                     FROZEN/GOVERNED

C-00 Cognitive Boundary                   FROZEN
C-01 Runtime Execution                    FROZEN
C-02 Conversation Authority               FROZEN
C-03 Context OS                           FROZEN
C-04 Identity / Persona                   FROZEN
C-05 Memory OS                            FROZEN
C-06 Continuity OS                        FROZEN
C-07 ModelProvider                        FROZEN
C-08 Capability / Tool                    FROZEN
C-09 Alignment                            FROZEN
C-10 Gateway / Client                     FROZEN
C-11 Voice / Media                        FROZEN
C-12 Evidence / Action / Trace            FROZEN

P0-A Production Reality Audit             PASS
P0-B Contract / Reality Reconciliation     PASS
Production Cognitive Path                 CONVERGED
Legacy Migration Dry-run                  PASS
Historical Electron Conversations         MIGRATED
AT-01 ... AT-17                           PASS
Feature Development                       REOPENED
```

The architectural objective is not merely "all modules implemented."

The objective is:

> Julia Core preserves Julia, reconstructs the conditions required for Julia's cognition, and governs durable truth — while the LLM remains the system that actually performs Julia's live understanding, reasoning, association, judgment, and generation.

