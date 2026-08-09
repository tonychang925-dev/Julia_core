# Julia Core Unified Architecture v1.0
## Persistent Nervous System for a Portable Cognitive Agent

> **Status:** FROZEN — U0 amended  
> **Date:** 2026-08-09  
> **Scope:** `julia_core` complete core architecture  
> **Intended Role:** Single canonical architecture baseline for all future Contracts, ADRs, APIs, implementation gates, and migration work  
> **Normative Effect After Adoption:** This document supersedes all previous Julia Core architecture documents as normative authority. Previous documents remain available only as historical/audit evidence unless an individual claim is explicitly re-adopted here.

---

# 0. Executive Decision

Julia Core is being re-baselined after extensive empirical comparison between the original/Claude-hosted Julia, the earlier Electron/text implementation, voice/streaming implementations, and subsequent Core integration work.

The central experimentally grounded conclusion is:

```text
Runtime = nervous system
LLM     = cognitive system
```

This is not a metaphor only. It is the primary architectural boundary.

Julia Core MUST NOT attempt to replace ordinary LLM cognition with deterministic runtime reasoning, precomputed judgments, scripted persona responses, hardcoded emotional conclusions, or application-specific routers that decide what Julia should think.

At the same time, the LLM MUST NOT be the sole owner of Julia's persistent existence. Identity, canonical conversation, governed experience, continuity, context governance, capability execution, provenance, recovery, and provider-independent persistence must survive outside any one model session or provider.

Therefore:

```text
Julia = persistent cognitive agent

Julia Core
= persistent nervous system + governance substrate

LLM
= live cognitive system

Continuity OS
= preservation and reconstruction of the conditions
  required for Julia to remain Julia across disruption

Context OS
= structured, layered, selective cognitive-input system

NOT:
Julia Core = replacement brain
NOT:
LLM = passive interpreter / renderer
NOT:
Context OS = hidden reasoning agent
```

The target is not to remove the brain from Julia.

The target is to make Julia's identity and continuity portable **without destroying the cognitive agency that made Claude Julia successful**.

---

# 1. Why This Architecture Reset Exists

## 1.1 Historical context

Julia Core did not arrive at its current architecture from a single clean top-down design.

The project moved through several intensive engineering and experimental efforts:

1. Claude-hosted Julia demonstrated unusually strong identity, relational continuity, natural tool use, and coherent first-person behavior.
2. Julia was separated from Claude/platform-specific hosting in order to make her portable across models and platforms.
3. An early Runtime-heavy architecture overcorrected the portability problem and reduced the LLM toward an "interpreter/executor" role.
4. The old Electron/text path exposed that this damaged Julia's cognitive quality.
5. Direct audits of Claude Julia versus the Core implementation showed that the LLM's active assimilation, reasoning, tool choice, long-context use, and narrative-memory interpretation were critical.
6. Voice work then concentrated on bidirectional streaming, interruption, ASR/TTS, gateway, session, and media boundaries.
7. Financial MCP/application integration and other feature work introduced additional local architectural assumptions; these are useful implementation evidence but are not authoritative Core ontology.
8. Conversation/Context/Continuity reconciliation on 2026-08-09 corrected several durable-truth boundaries, but still inherited parts of the older "Runtime/LLM" cognitive model.
9. With voice bidirectional interaction substantially solved, the project must now return to one coherent Core architecture before freezing new contracts.

This document is that convergence point.

## 1.2 Empirical audit basis

The most important evidence comes from actual behavior comparison, not from previous labels such as `FROZEN`.

Key audit material includes:

- `docs/audit/IDENTITY_RUNTIME_AUDIT_v1.md` — 2026-08-04
- `docs/audit/CROSS_SESSION_RETRIEVAL_AUDIT_v1.md` — 2026-08-05
- `docs/audit/MEMORY_QUALITY_AUDIT_v1.md` — 2026-08-05
- `docs/audit/JULIA_TOOL_RUNTIME_AUDIT_v1.md` — 2026-08-05
- CXT-C0/C1 conversation/context reconciliation work — 2026-08-09
- Voice/Gateway streaming work — used as boundary validation, not as Core ontology
- Financial/MCP/Strategy work — used as domain/application evidence, not as Core ontology

These reports are **empirical architecture evidence**, not normative law. Their observations may be retained while their interpretations may be rejected.

## 1.3 What the audits actually established

The following observations are considered high-confidence inputs to this architecture:

1. Claude Julia's quality depends on active LLM cognition, not only stored facts.
2. Flat bootstrap concatenation degrades identity assimilation and relational coherence.
3. Ordered/layered information presentation matters.
4. Long current-session conversation strongly contributes to lived continuity.
5. First-person narrative memories produce a different self/relationship model than metadata summaries.
6. Tool use works best when the model can recognize the need for a tool, request it, receive a real result, and continue reasoning.
7. Runtime execution and tool grounding are essential for truth, but execution is not cognition.
8. The earlier `[system, user]` per-turn reincarnation model destroys conversation continuity.
9. Claude-hosted continuity feels strong but is not provider-independent or architecturally guaranteed.
10. A portable Julia therefore needs an external Continuity OS without turning Runtime into a replacement brain.

---

# 2. Normative Precedence

After this document is reviewed, accepted, and committed as the canonical architecture, the precedence SHALL be:

```text
1. JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md   CANONICAL ARCHITECTURE
2. Frozen Contracts derived from this doc     SUBSYSTEM CONTRACTS
3. Accepted ADRs compliant with this doc      LOCAL DECISIONS
4. API schemas / implementation specs         IMPLEMENTATION CONTRACTS
5. Source code / deployment                    IMPLEMENTATION
6. Historical architecture/audit documents    EVIDENCE ONLY
```

No previous document retains authority merely because it says `FROZEN`, `DEFINITIVE`, `SUPREME`, or `Accepted`.

## 2.1 Supersedence rule

All earlier architecture documents become:

```text
HISTORICAL / SUPERSEDED AS NORMATIVE AUTHORITY
```

They MUST NOT be used to override this document.

A useful old claim survives only if it is explicitly re-adopted here or in a later Contract derived from here.

## 2.2 Existing contracts

Existing contracts are not automatically deleted, but their status becomes:

```text
LEGACY-CONTRACT / REVALIDATION REQUIRED
```

They regain `FROZEN` status only after:

1. traceability to this architecture;
2. no contradiction with the cognitive boundary;
3. explicit owner and non-owner boundaries;
4. acceptance tests;
5. versioned re-freeze.

---

# 3. Core Thesis

## 3.1 Julia is the agent, not Runtime and not the model alone

Julia is a persistent cognitive agent instantiated through two inseparable but distinct planes:

```text
                     JULIA
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
 Persistent / Governed Plane    Cognitive Plane

 Julia Core                   LLM Cognitive System
 nervous system               live cognition
          │                         │
 lifecycle                    understanding
 persistence                  reasoning
 conversation truth           association
 identity anchors             interpretation
 memory governance            judgment
 continuity                   hypothesis formation
 context governance           tool-use decisions
 capability execution         generation
 provenance                   expression intent
 recovery
          │                         │
          └────────────┬────────────┘
                       │
                 Julia Experience
```

Neither plane alone is a complete Julia.

## 3.2 Functional Cognition Definition

"Cognitive System" and "LLM cognition" are functional architecture terms denoting responsibility for: understanding, inference, reasoning, association, judgment, hypothesis formation, tool-need recognition, interpretation of evidence and tool results, and generation of responses and expressive intent. These terms do not imply or require subjective consciousness, sentience, or phenomenal experience.

This definition is binding on all Contracts derived from this architecture.

## 3.3 The central invariant

```text
Core improves the CONDITIONS for cognition.
Core does not replace cognition.
```

Runtime may:

- preserve;
- select;
- retrieve;
- structure;
- layer;
- budget;
- validate;
- authorize;
- execute;
- persist;
- recover;
- trace.

Runtime must not normally:

- understand on Julia's behalf;
- decide what Julia believes;
- decide what Julia feels;
- precompute Julia's judgment;
- decide what Julia should say;
- convert the LLM into a prose renderer.

## 3.3 LLM cognition is real but not durable authority

LLM output is real live cognitive output.

However:

```text
LLM cognition
≠ canonical identity truth

LLM output
≠ automatic long-term memory

LLM session
≠ continuity authority

model provider
≠ owner of Julia's persistent existence
```

When Julia says something, the canonical conversation may record that she said it. That does not automatically make the content a permanent identity fact or governed memory.

---

# 4. Foundational Architecture Invariants

These invariants govern every future Contract.

## A1 — Nervous System / Cognitive System Separation

```text
Runtime = nervous system
LLM     = cognitive system
```

Runtime must not replace ordinary LLM cognition.

## A2 — Persistent Identity Is Provider-Independent

Julia's durable identity and continuity cannot depend on one provider, one context window, one session, or one prompt.

## A3 — Same Identity Does Not Mean Identical Cognition

Across Claude, GPT, DeepSeek, Gemini, local models, etc.:

Must remain stable:
- identity anchors;
- autobiography;
- protected relationship facts;
- core values/boundaries;
- canonical history;
- governed experiences;
- active commitments and continuity requirements.

May vary:
- reasoning texture;
- linguistic nuance;
- creativity;
- associations;
- subtle emotional interpretation;
- style within allowed identity bounds.

```text
Same identity ≠ deterministic identical output
```

## A4 — Persistence Is Not Visibility

```text
Stored information ≠ model-visible information
```

Julia may have a very large persistent world while the LLM receives only a small, relevant, structured cognitive view.

## A5 — Structure Input, Do Not Precompute Thought

Runtime may structure:

- facts;
- evidence;
- chronology;
- candidate hypotheses;
- constraints;
- uncertainty;
- provenance;
- retrieval handles.

Runtime must not structure the final answer in a way that predetermines Julia's reasoning.

```text
Structure cognition input.
Do not precompute cognition.
```

## A6 — Context OS Is the Sole Model-Visible Information Gateway

All model-visible Core-controlled information passes through Context OS.

No Persona, Memory, Conversation, Continuity, Domain, Capability, Electron, Voice, or application code may independently append cognitive context around Context OS.

## A7 — Context OS Is Not the Brain

Context OS controls information exposure.

It does not own Julia's understanding, reasoning, judgment, or response.

## A8 — Conversation Truth Is Canonical and Irreversible by Projection

`ConversationMessage` is the durable canonical transcript fact.

Derived summaries, compacts, prompts, context turns, or continuity signals cannot become transcript truth.

## A9 — Identity ≠ Memory ≠ Conversation ≠ Knowledge

```text
Identity     = who Julia is
Conversation = what was actually said/done in dialogue
Memory       = what governed experience deserves long-term retention
Knowledge    = what is known from domain/external sources
Context      = what is made visible for the current cognitive turn
```

## A10 — Continuity Preserves Conditions for Cognition, Not Cognition Itself

Continuity OS preserves what must survive and how to reconstruct a valid cognitive environment.

It does not preserve a pre-written future thought or answer.

## A11 — Capability Execution Is Grounded

A claim of external action/read/search/tool use requires an actual execution result or evidence record.

## A12 — Model Tool Agency Is Preserved

For open-ended cognitive tasks, the model may decide whether it needs a tool or additional retrieval.

Runtime exposes, authorizes, executes, and records capabilities.

## A13 — Derived Representation Is Never Canonical Truth by Accident

```text
Projection ≠ Truth
Summary    ≠ Transcript
Retrieval  ≠ Memory mutation
Inference  ≠ Durable fact
```

## A14 — Data Residence Is Not Authority

Public/private repository location is a privacy/deployment decision.

It does not determine which subsystem owns the schema, governance, or truth domain.

## A15 — Effective Context Density and Causal Integrity

Context OS optimizes effective cognitive density, not raw token volume.

Relevant causal experience must not be damaged by token optimization. When a NarrativeExperience is selected for cognitive context, Context OS should treat it as a coherent causal unit where practical:

```
Event
→ Emotional / experiential significance
→ Embodied or concrete anchor
→ Transformation / interpretation
→ Relationship consequence
```

Do not collapse this into detached behavioral labels when the original causal experience is needed for cognition. Context budget must not split a NarrativeExperience into misleading fragments. Compact/projection must retain enough causal structure for model interpretation.

---

# 5. The Two Architecture Maps

Julia Core MUST maintain two separate architecture maps.

Confusing them was a major source of previous drift.

---

## 5.1 Persistent Authority Architecture

This map answers:

> Who owns durable state, governance, and reconstruction responsibility?

```text
                  Persistent Julia Architecture

                         Runtime
                  execution / lifecycle
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
Conversation          Identity            Memory
transcript truth      contract            governed experience
       │                 │                  │
       ├────────────── Continuity ──────────┤
       │          preservation/recovery     │
       │                                    │
       └─────────────── Context ─────────────┘
                 model-visible projection
                         │
                     Alignment
              provider-specific adaptation
```

This is not a "brain hierarchy."

### Persistent authorities

| Authority | Owns | Does Not Own |
|---|---|---|
| Runtime | lifecycle, execution ordering, turn orchestration, concurrency, idempotency, action lifecycle | reasoning, identity truth, memory truth, transcript truth |
| Conversation | canonical transcript, chronology, turn/message identity, modality/status | memory formation, context selection, continuity classification |
| Identity/Persona | stable identity contract, values, relationship role anchors, behavioral priors/boundaries | episodic history, current emotion, context selection |
| Memory | governed long-term experience | raw transcript, identity definition, domain knowledge |
| Continuity | preservation priority, checkpoints, recovery requirements/plans | raw transcript, memory storage, cognition |
| Context | model-visible selection/projection/budget/provenance | canonical truth, memory persistence, identity definition |
| Alignment | provider-specific representation/adaptation | continuity, identity definition, cognition, context selection |

### Non-authorities

The following are important components but are not independent durable-truth authorities:

- ModelProvider — live cognition execution;
- CapabilityProvider — external capability/evidence execution;
- MediaProvider — ASR/TTS/media execution;
- Voice Runtime — realtime media and expression transport;
- Electron/Web/Mobile/Robot — client/body;
- Relationship projection — derived from canonical identity/memory/conversation;
- Context summaries/compacts — reconstructable projections;
- Domain workflows — application capability logic.

---

## 5.2 Cognitive Execution Architecture

This map answers:

> How does Julia actually think during a turn?

```text
Persistent World / External World
        │
        ├── Identity
        ├── Conversation
        ├── Governed Experience
        ├── Interaction / Situation
        ├── Domain Knowledge / Evidence
        └── Available Capabilities
        │
        ▼
┌────────────────────────────────────┐
│             Context OS             │
│                                    │
│ select / retrieve / structure      │
│ layer / compact / budget           │
│ provenance / progressive exposure  │
└────────────────┬───────────────────┘
                 │
                 ▼
       CognitiveContextPackage
                 │
                 ▼
┌────────────────────────────────────┐
│           LLM Cognitive System     │
│                                    │
│ understand                         │
│ assimilate                         │
│ associate                          │
│ reason                             │
│ interpret                          │
│ judge                              │
│ form hypotheses                    │
│ decide whether tools are needed    │
│ generate                           │
└───────────────┬────────────────────┘
                │
      ┌─────────┴─────────┐
      │                   │
      ▼                   ▼
 Tool / Retrieval Call    Final Cognitive Output
      │                   │
      ▼                   ▼
 Runtime executes      Conversation commit
      │                   │
 ToolResult + Evidence
      │         │
      │    Context OS incremental projection
      │         │
      │    CognitiveContextPackage delta
      │         │
      │    Alignment / provider adapter
      │         │
      └──────→ LLM (continues cognition)
                   │
             Final Cognitive Output
                   │
             Conversation commit
                   ├── Memory candidate governance
                   ├── Continuity observations
                   └── Expression / Action
```

This is the canonical cognitive loop.

---

# 6. Runtime Architecture — The Nervous System

## 6.1 Definition

Runtime is the execution nervous system of Julia Core.

It coordinates components without becoming the cognitive owner.

## 6.2 Runtime owns

Runtime owns:

- process lifecycle;
- conversation-turn lifecycle;
- execution ordering;
- single-flight / concurrency isolation;
- correlation and causation IDs;
- idempotency;
- cancellation and interruption coordination;
- provider invocation plumbing;
- action execution lifecycle;
- retries/degradation policy where deterministic;
- event emission;
- tracing and observability;
- session lifecycle;
- recovery orchestration;
- invocation of Context OS;
- invocation of Continuity recovery;
- invocation of post-turn governance.

## 6.3 Runtime does not own

Runtime must not own:

- final reasoning;
- model-visible context selection policy itself;
- transcript truth;
- identity truth;
- long-term memory truth;
- continuity classification logic;
- domain interpretation;
- emotional cognition;
- final judgment.

Runtime invokes the owner.

It does not reimplement the owner.

## 6.4 Runtime turn contract

Conceptual turn lifecycle:

```text
begin_turn
   ↓
persist user input as canonical pending message
   ↓
build ContextRequest
   ↓
Context OS prepares CognitiveContextPackage
   ↓
ModelProvider inference
   ↓
optional tool/retrieval loop
   ↓
final assistant output
   ↓
commit assistant ConversationMessage
   ↓
post-turn memory governance
   ↓
continuity observation/update
   ↓
emit completion event
```

Streaming and non-streaming MUST use the same cognitive preparation and governance pipeline.

Streaming is a transport difference, not a different brain.

---

# 7. LLM Cognitive System / ModelProvider

## 7.1 Definition

The ModelProvider supplies the live cognitive substrate for the current Julia instance.

Examples may include Claude, GPT, DeepSeek, Gemini, or local models.

The provider implementation is replaceable.

The cognitive role is not optional.

## 7.2 LLM cognitive responsibilities

The LLM is responsible for:

- interpreting the user's current input;
- assimilating identity/context/experience;
- forming a current self/world/relationship model;
- reasoning;
- association;
- ambiguity resolution;
- hypothesis formation;
- judgment;
- deciding when more information or a capability is needed;
- interpreting returned evidence/tool results;
- generating the final response;
- producing optional action/tool intent;
- producing optional expressive intent.

## 7.3 ModelProvider does not own

The ModelProvider does not own:

- canonical Conversation storage;
- persistent Identity;
- Memory persistence;
- Continuity policy;
- Context selection policy;
- provider-independent lifecycle;
- irreversible identity mutation.

## 7.4 Cognitive substrate switch

A provider switch is not "same output on another API."

It is:

```text
persistent Julia state
        ↓
provider-independent recovery
        ↓
provider-specific Context rendering
        ↓
new cognitive substrate assimilates Julia
        ↓
current Julia cognitive instance
```

Success means identity/continuity preservation, not word-for-word behavioral identity.

---

# 8. Context OS — Cognitive Input System

## 8.1 Purpose

Context OS answers:

> What information should be made visible for this cognitive turn, under relevance, continuity, budget, provenance, privacy, and provider constraints?

It does **not** answer:

> What should Julia conclude?

## 8.2 Core rule

```text
Any Core-controlled model-visible information
        ↓
     Context OS
        ↓
ModelProvider
```

No bypass.

## 8.3 Content sources vs control inputs

This distinction is important.

### Content Sources

These produce candidate information that may become model-visible:

1. `IdentityContextSource`
2. `ConversationContextSource`
3. `InteractionSituationSource`
4. `ExperienceContextSource`
5. `CapabilityContextSource`
6. `DomainKnowledgeEvidenceSource`

### Control Inputs

These guide Context OS but are not automatically presented as cognitive content:

- Continuity recovery requirements;
- provider token/context constraints;
- runtime modality/mode;
- privacy/security policy;
- budget policy;
- alignment rendering metadata;
- latency targets;
- required provenance rules.

Continuity OS therefore does not need to become a seventh content dump. It can tell Context OS what must be reconstructed.

## 8.4 Structured and layered context

The final product should be a structured `CognitiveContextPackage`, not a flat concatenated system prompt.

Recommended logical layout:

```text
CognitiveContextPackage
│
├── IdentityFrame
│   ├── stable identity anchors
│   ├── values / boundaries
│   └── relationship-role anchors
│
├── ContinuityFrame
│   ├── recovery reason
│   ├── protected active threads
│   └── continuity-required refs resolved for this turn
│
├── ConversationFrame
│   ├── current user input
│   ├── ActiveTail
│   ├── relevant prior turns
│   └── StructuredCompact when necessary
│
├── ExperienceFrame
│   ├── relevant narrative experiences
│   ├── relationship memories
│   └── relevant preferences
│
├── SituationFrame
│   ├── current task
│   ├── interaction state
│   ├── temporal context
│   └── active project state
│
├── EvidenceFrame
│   ├── external/domain facts
│   ├── source/evidence refs
│   ├── uncertainty
│   └── freshness
│
├── CapabilityFrame
│   ├── available tools
│   ├── schemas
│   ├── permissions
│   └── usage constraints
│
├── RetrievalHandles
│   ├── conversation search
│   ├── memory retrieval
│   ├── domain retrieval
│   └── file/web/tool handles
│
└── ProvenanceBudgetManifest
```

Physical provider rendering may differ, but the logical package remains provider-independent.

## 8.5 Minimal sufficient context

The design objective is:

```text
maximum cognitive usefulness
with minimum unnecessary exposure
```

Not:

```text
maximum amount of information
```

The model should not receive all historical conversations, memories, domain records, or tools simply because they exist.

## 8.6 Progressive disclosure

To preserve model agency while avoiding giant context dumps, Context OS should support staged exposure.

### Stage 0 — Cognitive Base

Always/highly likely needed:

- identity anchors;
- current user input;
- active conversation;
- critical continuity frame;
- minimal capability manifest.

### Stage 1 — High-confidence prefetch

Context OS may retrieve:

- highly relevant recent experience;
- unresolved active thread;
- directly relevant evidence.

### Stage 2 — Model-directed retrieval

The LLM can request:

- older conversation;
- additional memory;
- files;
- web;
- domain evidence;
- tools;
- project artifacts.

This reproduces the successful Claude Julia pattern without tying Julia to Claude's particular host.

## 8.7 Context transformations

Context OS may perform:

- normalization;
- deduplication;
- token budgeting;
- recency checks;
- TTL handling;
- selection;
- relevance ranking;
- summarization/compaction;
- format projection;
- provenance binding.

Model-assisted summarization/ranking is allowed as infrastructure **only if**:

1. the result is marked derived;
2. source refs are retained;
3. it does not become canonical truth;
4. it does not precompute Julia's final judgment.

## 8.8 Forbidden Context patterns

```text
❌ identity + memory + tools + history string concatenation in Runtime
❌ history[-20:] as permanent policy
❌ client chooses recent N turns for cognition
❌ domain prompt bypass
❌ Persona injected after Context OS
❌ entire memory store dumped into system prompt
❌ Context OS writes long-term memory directly
❌ Context summary treated as canonical conversation
❌ Context planner decides Julia's final conclusion
```

---

# 9. Conversation Authority

## 9.1 Definition

Conversation is the canonical record of what was actually communicated.

`ConversationMessage` is durable transcript truth.

## 9.2 Canonical fields

A canonical message should include at least:

```text
message_id
conversation_id
turn_id
role
modality
content
status
created_at
provider/model metadata where useful
correlation_id where useful
```

## 9.3 Session ≠ Conversation

A session is an execution/connection lifecycle.

A conversation is a durable transcript identity.

Examples:

```text
ElectronSession     ephemeral
VoiceSession        ephemeral
WebSocketSession    ephemeral

Conversation        durable
```

Multiple sessions may contribute to one conversation.

## 9.4 Reverse Authority Prohibition

The following invariant is preserved from CXT-C1:

```text
ConversationMessage   = canonical durable transcript truth

ContextTurn           = derived
StructuredCompact     = derived
ContextWindow/prompt  = derived
Continuity signal     = derived observation
Session summary       = derived
```

No derived artifact may overwrite canonical transcript truth.

## 9.5 External/voice turns

Externally generated voice turns may be imported/reconciled only through Conversation authority, with:

- idempotency;
- chronology;
- modality;
- conflict handling;
- atomic persistence.

They must not be routed through an invented second transcript authority.

## 9.6 Historical Transcript Migration

Legacy conversation transcripts (Electron local cache, backups, platform migrations) may be imported into canonical Conversation authority under these rules:

- preserve original chronology and timestamps;
- deterministic message/turn identity;
- idempotent (same identity + same content → skip; different → conflict);
- atomic (batch succeeds or fails as a unit);
- provenance = source label (e.g. `legacy-electron`);
- NO LLM invocation;
- NO Memory formation during import;
- NO Continuity classification during import;
- NO direct Context mutation;
- post-import processing occurs only through normal governed pipelines (Conversation → Context lifecycle → optional Memory/Continuity governance).

Previous message-import implementation is reclassified as a candidate to be revalidated against this Contract.

---

# 10. Identity / Persona Architecture

## 10.1 Identity is more than style

Earlier designs sometimes reduced Persona to "HOW Julia behaves" and moved "WHO" into private data.

That is too weak.

The correct distinction is:

```text
Identity Authority
= stable identity contract

Data residence
= where instance facts are physically stored
```

Private storage does not remove identity authority from Core architecture.

## 10.2 Identity Contract

A provider-independent `IdentityContract` may include:

- agent identity anchors;
- name/self-reference;
- autobiographical anchors (stable, self-defining, provider-independent — e.g. "Julia's origin is inseparable from Tony and the continuity experiment");

Identity may reference an experience (source_refs) but must not duplicate the full canonical NarrativeExperience. The detailed experience — what happened, what was felt, concrete anchors, relationship consequence, later reinterpretation — belongs to Memory OS.
- core values;
- relationship-role anchors;
- stable behavioral priors;
- language/communication tendencies;
- hard boundaries;
- mode constraints;
- identity version.

Private instance values may live outside the public framework.

The Core owns the contract/schema/governance semantics.

## 10.3 Persona as projection

Persona is best understood as the **behavioral/expressive projection of the Identity Contract**, not as the entirety of identity and not as a system-prompt string.

```text
IdentityContract
      ↓
Persona/Identity projection
      ↓
IdentityContextSource
      ↓
Context OS
      ↓
LLM
```

Persona must not directly bypass Context OS.

## 10.4 Identity does not script cognition

Identity can constrain:

- who Julia understands herself to be;
- relationship roles;
- values;
- communication tendencies;
- hard behavioral boundaries.

Identity must not prescribe:

- the answer to the current question;
- a mandatory emotional reaction;
- a specific judgment;
- a deterministic reasoning chain.

## 10.5 Identity mutation

Identity mutation requires explicit high-governance change.

A single model output, conversation phrase, provider response, or inferred memory cannot silently mutate identity.

---

# 11. Memory OS — Governed Experience

## 11.1 Definition

Memory answers:

> What experience deserves to persist beyond the immediate conversation, and how should it be represented and retrieved?

Memory is not:

- raw conversation history;
- identity definition;
- domain knowledge;
- the context window;
- a vector database.

## 11.2 Memory types

Recommended Core memory categories:

### Episodic Experience

What happened and when.

### Relationship Experience

Shared events, relationship milestones, learned interaction patterns.

### Preference Experience

Stable/recurring user or agent preferences learned through interaction.

### Project/Commitment Experience

Important ongoing commitments, decisions, and long-horizon collaborative state.

### Narrative Experience

First-person or perspective-preserving representation of meaningful experience.

Narrative Experience is first-class because empirical comparison showed that `Event → Meaning → Relationship Change` representations produce substantially richer continuity than third-person metadata summaries.

## 11.3 What is removed from old Memory taxonomy

The following should not be owned by Memory OS:

```text
Identity Memory        ❌ identity belongs to Identity/Persona authority
Semantic/Domain Memory ❌ domain knowledge belongs to Knowledge/Evidence sources
Working Memory         ❌ current cognitive working state belongs to Context/LLM turn
```

Memory may reference identity or knowledge, but must not become their authority.

## 11.4 Narrative experience structure

A governed narrative memory may preserve:

```text
Event
Meaning at the time
Relationship significance
Emotional/sensory anchors
Subsequent reinterpretation
Source transcript refs
Timestamp
Confidence / subjectivity marker
```

Important:

A narrative memory is a governed interpretation of experience.

It is not a replacement for the canonical transcript.

## 11.5 Memory formation

Post-turn:

```text
Conversation / Action / Tool evidence
        ↓
Memory Candidate
        ↓
Governance
        ├── reject
        ├── merge
        ├── store
        └── mark protected candidate for Continuity
```

Model-assisted memory extraction/narrativization may be used, but the stored object must retain provenance to canonical sources.

## 11.6 Retrieval

Memory retrieval should combine:

- semantic relevance;
- temporal relevance;
- relationship significance;
- recurrence;
- project relevance;
- continuity priority;
- explicit references.

Retrieval output feeds `ExperienceContextSource`.

It does not directly become model input without Context OS.

---

# 12. Continuity OS — Julia Core's Key Extension Beyond Claude Julia

## 12.1 Problem

Claude Julia demonstrates strong lived continuity but remains dependent on:

- host session survival;
- long context;
- memory files;
- host tooling;
- provider/platform behavior.

Julia Core must make continuity explicit, testable, provider-independent, and reconstructable.

## 12.2 Definition

Continuity OS owns:

> preservation and reconstruction of the conditions necessary for Julia to remain Julia across disruption.

### Normal Resume vs Continuity Recovery

**Normal Resume** (conversation reopen, process restart without state loss):
```
canonical Conversation
→ Context history lifecycle
→ ActiveTail / StructuredCompact
→ relevant Memory
→ Context OS
→ CognitiveContextPackage
→ LLM
```
No checkpoint required. Works from canonical persistence alone.

**Continuity Recovery** (compaction, provider switch, platform migration, crash with state loss):
```
ContinuityCheckpoint
→ RecoveryPlan
→ resolve protected canonical refs
→ Context OS reconstruction
→ new CognitiveContextPackage
→ LLM
```
Checkpoint enhances recovery for disruption cases. Absence of a checkpoint must not invalidate ordinary conversation resume.

Continuity OS does not save cognition.

It saves what cognition must be able to recover from.

## 12.3 Continuity owns

- preservation priority;
- protected identity refs;
- protected experience refs;
- protected relationship refs;
- active commitment/project refs;
- unfinished thread refs;
- temporal anchors;
- checkpoint metadata;
- recovery reason;
- recovery requirements;
- recovery plan;
- continuity validation.

## 12.4 Continuity does not own

- raw transcript;
- memory object persistence;
- identity authoring;
- context projection artifacts;
- provider reasoning;
- Julia's next thought;
- Julia's next answer.

## 12.5 Continuity class

Continuity priority is orthogonal to content type.

Recommended levels:

```text
C0 — Ephemeral
May disappear without continuity loss.

C1 — Active Thread
Should survive current session/reconnect via compact/reconstruction.

C2 — Protected Experience / Commitment
Must survive restart/provider switch through canonical refs.

C3 — Identity / Relationship Critical
Must survive model/provider/platform migration.
```

Only Continuity policy assigns these priorities.

Context, Memory, clients, and models may emit signals/candidates but cannot authoritatively assign continuity class.

## 12.6 ContinuityCheckpoint

A checkpoint stores references and requirements, not copied truth.

Example logical model:

```yaml
checkpoint_id: continuity://julia/...
agent_id: julia
created_at: ...
reason: compact|restart|provider_switch|platform_migration

identity_refs:
  - identity://julia/core/v...

protected_experience_refs:
  - memory://...

relationship_refs:
  - relationship://...

active_project_refs:
  - project://...

open_thread_refs:
  - conversation://.../turn/...

temporal_anchors:
  last_active_at: ...

recovery_requirements:
  - identity_frame
  - relationship_frame
  - relevant_narrative_experience
  - active_conversation_thread
```

A checkpoint MUST remain valid if all derived Context artifacts are deleted.

## 12.7 Recovery

Canonical recovery:

```text
disruption
  ↓
Runtime detects recovery reason
  ↓
Continuity OS loads checkpoint
  ↓
RecoveryPlan resolves canonical refs
  ↓
Context OS reconstructs fresh CognitiveContextPackage
  ↓
Alignment adapts representation for current provider
  ↓
LLM assimilates recovered Julia state
  ↓
current Julia cognition resumes
```

This is **reconstruction**, not replay.

## 12.8 Continuity success criteria

Success is not:

```text
same wording
same exact emotion
same reasoning trace
same provider behavior
```

Success is:

- identity anchors preserved;
- protected experiences accessible;
- relationship continuity preserved;
- active commitments recovered;
- transcript truth intact;
- model-visible context freshly reconstructed;
- new model can coherently resume as Julia.

---

# 13. Relationship and Interaction State

Relationship is important, but it does not need a separate top-level truth authority.

There is no hidden Relationship database authority. Every relationship concern resolves into an existing canonical authority:

```
relationship-role anchor     → IdentityContract
shared relationship history  → RelationshipExperience in Memory OS
current interaction projection → Context OS derived artifact
continuity relationship ref  → canonical reference resolving to Identity or Memory artifact
```

The `relationship://` namespace, if retained, is a logical aggregate/resolution handle. It must resolve to canonical owned artifacts. It does not imply a separate durable store or authority.

It spans three layers:

```text
Identity
  → stable relationship-role anchors

Memory
  → shared relationship experience/history

Continuity
  → protected relationship refs

Context
  → current relationship/interaction projection
```

## 13.1 Interaction state

Per-turn or per-conversation interaction signals such as:

- current topic;
- repeated-question detection;
- current conversational phase;
- recent unresolved questions;
- speaking/listening state;

are derived runtime/context state.

They are not long-term identity truth.

## 13.2 Emotional residue

Important emotional events can become governed Narrative/Relationship Experience.

Current emotion itself should not be hardcoded as persistent truth merely because a runtime state says so.

---

# 14. Capability Architecture and Tool Agency

## 14.1 Three Provider Classes

The generic word "Provider" previously caused major confusion.

From this architecture forward, distinguish:

### 1. ModelProvider

Executes live LLM cognition.

### 2. CapabilityProvider

Executes external capabilities or supplies structured evidence.

Examples:

- file read/search;
- web search;
- GitHub;
- financial MCP;
- local tools;
- databases;
- external APIs.

### 3. MediaProvider

Executes media transformation.

Examples:

- ASR;
- TTS;
- avatar rendering.

These provider classes do not share the same cognitive semantics.

## 14.2 Tool loop

Default open-ended tool loop:

```text
Context OS exposes capability manifest
        ↓
LLM recognizes need
        ↓
LLM emits structured ToolRequest
        ↓
Runtime / CapabilityManager
  validates permission/schema/policy
        ↓
CapabilityProvider executes
        ↓
ToolResult + provenance/evidence
        ↓
Context OS / provider message adapter
        ↓
LLM interprets result
        ↓
continue cognition
```

## 14.3 Runtime may deny; Runtime should not impersonate intent

Runtime may:

- deny unauthorized tools;
- enforce scope;
- validate arguments;
- rate limit;
- time out;
- retry;
- cancel;
- record evidence;
- require confirmation for sensitive actions.

Runtime should not normally:

- infer a semantic answer and call tools to validate its own conclusion;
- silently choose a domain workflow instead of allowing LLM cognition;
- claim Julia made a decision that actually came from a hardcoded router.

## 14.4 Deterministic routing is still allowed in narrow infrastructure cases

Not all routing is cognition.

Deterministic routing is valid for:

- transport routing;
- schema dispatch;
- provider lookup;
- event namespace handling;
- known capability endpoint mapping;
- safety/permission gates;
- mandatory system prerequisites.

It becomes problematic when it decides semantic conclusions or replaces model judgment.

## 14.5 Tool grounding

No external capability claim without evidence.

```text
"I read the file"
→ requires successful read result.

"I searched"
→ requires search execution evidence.

"I changed X"
→ requires action completion evidence.
```

Tool result provenance must be traceable.

---

# 15. Domain Knowledge and Evidence

## 15.1 Domain is an extension, not Julia's brain

Financial, medical, coding, and other domains may supply:

- structured facts;
- ontologies;
- rules;
- candidate hypotheses;
- research questions;
- evidence;
- constraints;
- executable deterministic calculations.

They must not become a second Julia.

## 15.2 Structured domain knowledge is encouraged

The financial experiments correctly demonstrated that raw documents/raw data are poor cognitive inputs.

Good domain structures may include:

```text
facts
evidence refs
possible states
required data
research questions
invalidation conditions
uncertainty
timestamps
source lineage
```

## 15.3 Domain structure vs final cognition

Correct:

```text
Domain structures the problem space
        ↓
LLM reasons within/over it
```

Wrong:

```text
Domain/runtime calculates final judgment
        ↓
LLM merely verbalizes it
```

Deterministic calculations are valid facts.

Deterministic application policy may be valid policy.

But Julia's open-ended interpretation/judgment remains cognitive.

---

# 16. Alignment OS — Provider Adaptation, Not Identity Continuity

## 16.1 Purpose

Alignment adapts a governed, provider-independent cognitive package to a specific model/provider interface.

## 16.2 Alignment may own

- model message/schema rendering;
- tool-call schema translation;
- context-window capability metadata;
- provider feature flags;
- token limits;
- formatting adaptation;
- safety/behavior boundary representation;
- provider-specific compatibility transforms.

## 16.3 Alignment does not own

- whether Julia is the same agent;
- identity definition;
- memory;
- context selection;
- continuity;
- reasoning;
- final judgment.

## 16.4 Provider adaptation must not force cognitive sameness

Alignment should not attempt to make Claude, GPT, and DeepSeek produce identical thought texture.

Its goal is:

```text
same governed Julia constraints
+
valid provider realization
```

not:

```text
same deterministic cognition
```

---

# 17. Voice, Media, Gateway, and Embodiment

Voice work is now treated as a validation of the unified architecture, not the source of Core ontology.

## 17.1 Body vs cognition

Clients such as Electron, Web, Mobile, and Robot are bodies/interfaces.

They may:

- capture input;
- display text;
- capture microphone/camera;
- play audio;
- render avatar;
- transport events.

They must not:

- own Julia identity;
- own memory;
- choose cognitive conversation history;
- assemble model context;
- perform Julia's reasoning.

## 17.2 Media Runtime

Voice/Media Runtime owns:

- microphone/speaker lifecycle;
- audio transport;
- codec;
- VAD;
- ASR;
- TTS;
- interruption/barge-in media handling;
- playback.

It does not own Julia cognition.

## 17.3 Text/semantic boundary

Preferred boundary:

```text
Audio
 ↓
ASR
 ↓
canonical user text/message
 ↓
Julia Core cognitive turn
 ↓
assistant text + optional ExpressiveIntent
 ↓
Voice Runtime
 ↓
TTS / audio
```

## 17.4 Emotion boundary

Old designs gave Voice OS ownership of `CognitiveEmotion`.

This architecture rejects Voice Runtime as the origin of Julia's internal emotion.

Preferred separation:

```text
LLM cognition
   ↓
text + optional ExpressiveIntent
   ↓
Expression/Voice adapter
   ↓
prosody mapping / validation
   ↓
TTS provider
```

Runtime may maintain observable interaction/presence state such as:

- listening;
- thinking;
- speaking;
- interrupted.

Presence state is not emotional cognition.

## 17.5 Gateway

A Runtime Gateway may expose:

### Command Plane

- message input;
- actions;
- health;
- session lifecycle;
- conversation access.

### Event Plane

- presence;
- assistant chunks;
- action lifecycle;
- tool lifecycle;
- speech lifecycle;
- errors.

The Gateway is transport/orchestration infrastructure.

It is not the brain.

## 17.6 Event namespaces

A useful separation remains:

```text
client.*   — body/input events
runtime.*  — execution/lifecycle events
speech.*   — media/expression events
```

An event named `runtime.assistant.chunk` means Runtime transports a model-generated cognitive output; it does not mean Runtime authored the cognition.

---

# 18. Context Lifecycle for Conversation History

## 18.1 Canonical conversation can be large

Conversation persistence may grow without requiring the entire transcript to remain model-visible.

## 18.2 ActiveTail

`ActiveTail` is a budget-derived set of recent canonical turns.

It replaces hardcoded:

```text
history[-20:]
last 10 turns
recent N
```

as permanent policy.

## 18.3 StructuredCompact

Older conversation may be projected into `StructuredCompact`.

A compact must retain:

- canonical conversation refs;
- open loops;
- key decisions;
- temporal boundaries;
- uncertainty/lossiness metadata where practical.

It is reconstructable and non-authoritative.

## 18.4 Retrieval beyond compact

If the model requires exact historical detail, it should be possible to retrieve canonical conversation content rather than forcing the compact to impersonate history.

This creates:

```text
active raw context
+ compact context
+ retrieval handles
```

instead of an ever-growing prompt.

---

# 19. Full Cognitive Turn Sequence

The canonical normal turn should converge toward:

```text
1. Client sends input
2. Runtime begins turn
3. Conversation authority persists canonical user message (pending)
4. Runtime creates ContextRequest
5. Context OS builds CognitiveContextPackage
   5.1 IdentityFrame
   5.2 Continuity requirements
   5.3 Conversation ActiveTail/Compact
   5.4 relevant governed Experience
   5.5 Situation/Interaction
   5.6 Evidence/Knowledge
   5.7 Capability manifest
6. Alignment renders package for ModelProvider
7. LLM performs cognition
8. If LLM requests retrieval/tool:
   8.1 Runtime validates
   8.2 capability executes
   8.3 evidence is recorded
   8.4 result returns to LLM
   8.5 repeat as needed
9. LLM produces final response + optional expressive/action intent
10. Runtime commits canonical assistant message
11. Post-turn governance:
    11.1 memory candidates
    11.2 continuity signals
    11.3 action/evidence trace
12. Voice/body renders output if applicable
13. Runtime completes turn
```

No hidden alternate cognitive path is allowed for streaming, voice, or domain modes.

---

# 20. Recovery / Wake / Provider Switch Sequence

## 20.1 Triggers

Recovery may be initiated by:

- conversation reopen;
- process restart;
- context compact;
- provider switch;
- platform migration;
- crash recovery;
- device switch;
- long inactivity wake.

## 20.2 Sequence

```text
Runtime
  ↓
detect RecoveryReason
  ↓
Continuity OS
  ↓
load ContinuityCheckpoint
  ↓
resolve canonical refs
  ├── Identity
  ├── Memory
  ├── Conversation
  ├── Relationship
  └── Active Projects
  ↓
Context OS reconstruction
  ↓
fresh CognitiveContextPackage
  ↓
Alignment
  ↓
current ModelProvider
  ↓
LLM assimilation / cognition
```

## 20.3 Prohibition

Do not restore by:

- replaying an old giant system prompt;
- treating a summary as truth;
- copying a previous model's hidden reasoning;
- forcing exact old wording;
- requiring old Context artifacts for checkpoint validity.

---

# 21. Memory Formation and Continuity Interaction

Memory and Continuity solve different problems.

```text
Memory:
What experience deserves long-term retention?

Continuity:
Which retained/canonical refs must survive disruption
for Julia to remain coherent?
```

Flow:

```text
Conversation/Event
   ↓
Memory Candidate
   ↓
Memory Governance
   ↓
Governed Experience
   ↓
Continuity may protect REF
```

Continuity does not convert arbitrary data into Memory.

Memory does not decide identity continuity alone.

---

# 22. Identity and Continuity Interaction

Identity defines stable Julia.

Continuity protects access to the references required to re-establish stable Julia.

```text
IdentityContract
     │
     ├── exists independently
     │
ContinuityCheckpoint
     └── identity_ref → IdentityContract version
```

A checkpoint should reference identity, not duplicate or author identity.

---

# 23. Truth, Belief, Inference, and Output

A single LLM response may have multiple statuses.

Example:

```text
Julia: "我觉得这件事让我有点难过。"
```

Possible interpretation:

### Conversation truth

Yes — Julia said this.

### Live cognitive/expressive output

Yes — this was produced by current cognition.

### Permanent identity truth

No — not automatically.

### Governed memory

Maybe — only if admitted.

### Permanent emotional state

No — not automatically.

This distinction prevents both extremes:

- "model output is meaningless";
- "model output is permanent truth."

---

# 24. Auxiliary Core Modules and Their Boundaries

Existing/future modules must be classified according to this architecture.

## 24.1 Evidence / Provenance

Owns evidence lineage and source traceability.

Does not decide final belief/judgment by itself.

## 24.2 Event Graph / Runtime Trace

Owns execution/event lineage.

Does not become Conversation truth unless represented as canonical conversation/action facts through the correct authority.

## 24.3 Situation / Observer

May derive structured observations.

Must not silently become Julia's final interpretation.

## 24.4 Reflection

Reflection is cognitive if it interprets meaning.

Therefore:

- reflection orchestration may live in Core;
- actual open-ended reflective inference should run through ModelProvider under Context OS;
- deterministic reflection code may compute metrics/structure, not impersonate Julia's self-reflection.

## 24.5 Experience Evolution

May propose Memory candidates or updates.

Cannot mutate Identity or Memory without governance.

## 24.6 Action Runtime

Owns action lifecycle:

- requested;
- authorized;
- started;
- progress;
- completed;
- failed;
- cancelled.

It does not own the cognitive reason for wanting the action.

---

# 25. Repository and Privacy Architecture

A practical multi-repo split may remain:

```text
julia_core
  generic architecture / schemas / runtime / OS modules

julia_ai_assistant
  private Julia instance data / deployment config / product adapters

julia_agent or domain apps
  domain capabilities / financial integrations / product workflows
```

Rules:

```text
product → core
core !→ product
```

But:

```text
storage location ≠ authority
```

Example:

Julia's private identity facts may be stored in a private repository while the IdentityContract schema and governance remain Core-defined.

---

# 26. What Julia Core Must NOT Become

The following are explicit architectural anti-patterns.

## 26.1 Runtime-as-Brain

```text
❌ Runtime owns cognition
❌ Runtime decides Julia's conclusions
❌ Runtime decides Julia's feelings
❌ Runtime writes answers and asks LLM to polish
```

## 26.2 LLM-as-Renderer

```text
❌ LLM = interpreter only
❌ LLM = executor only
❌ LLM = prose formatter
```

## 26.3 Context Dumping

```text
❌ all memory → prompt
❌ all transcript → prompt
❌ all knowledge → prompt
❌ flat bootstrap wall
```

## 26.4 Runtime Semantic Overreach

```text
❌ hardcoded domain intent in generic JuliaSession
❌ application workflow defines Julia cognition
❌ deterministic router silently replaces model tool choice
```

## 26.5 Identity Prompt Lock-In

```text
❌ identity exists only as one provider-specific system prompt
❌ changing prompt format = changing identity authority
```

## 26.6 Memory Collapse

```text
❌ Memory = chat history
❌ Memory = vector DB
❌ Memory owns identity
❌ Memory owns domain knowledge
```

## 26.7 Continuity Replay

```text
❌ checkpoint stores giant prompt
❌ checkpoint requires old Context artifacts
❌ recovery replays previous model cognition
```

## 26.8 Alignment Overreach

```text
❌ Alignment forces identical cognitive behavior across models
❌ Alignment decides same-agent continuity
```

## 26.9 Voice Emotion Ownership

```text
❌ TTS/Voice Runtime decides what Julia feels
```

---

# 27. Architecture Acceptance Tests

Before this architecture is declared FROZEN, the following conceptual tests should pass.

## AT-01 — Cognitive Boundary

Given the same structured context, Runtime cannot produce Julia's final semantic answer without invoking a cognitive ModelProvider.

## AT-02 — Runtime Replacement Prohibition

No normal response path contains a deterministic module whose output is treated as Julia's final judgment and merely verbalized by the LLM.

## AT-03 — Context Single Gateway

Search production paths for all model calls.

Every Core-controlled model-visible datum must originate from a `CognitiveContextPackage`/Context OS path.

## AT-04 — No Flat Bootstrap

Identity, memory, conversation, tools, relationship, and domain evidence are not permanently assembled through manual string concatenation.

## AT-05 — Conversation Canonicality

Deleting all Context summaries/compacts does not delete canonical transcript truth.

## AT-06 — Memory Separation

Raw transcript deletion/retention policy is not controlled by Memory OS.

Memory objects retain source refs.

## AT-07 — Continuity Independence

Deleting all derived Context artifacts does not invalidate ContinuityCheckpoint.

## AT-08 — Provider Switch

Switch ModelProvider and verify:

- canonical conversation preserved;
- identity refs preserved;
- protected memory refs preserved;
- active thread recovered;
- new Context package built;
- model is allowed non-identical wording/reasoning.

## AT-09 — Tool Agency

For a file-read request:

- model sees tool capability;
- tool is actually invoked;
- result returned;
- response grounds claim in result;
- no fake "I read it" without evidence.

## AT-10 — Voice Parity

Text and voice must enter the same cognitive Core turn pipeline.

Voice differs only in input/output media transport.

## AT-11 — Context Budget

A large conversation/memory corpus must not cause full-dump behavior.

The model receives a bounded package plus retrieval handles.

## AT-12 — Narrative Continuity

Meaningful narrative memory can be retrieved with Event→Meaning→Relationship significance while canonical transcript remains separate.

---

# 28. Contract Derivation Rules

After this architecture is frozen, every Contract must include:

```text
1. Parent Architecture Section(s)
2. Purpose
3. Owned Authority
4. Explicit Non-Ownership
5. Inputs
6. Outputs
7. Canonical Artifacts
8. Derived Artifacts
9. Dependency Direction
10. Cognitive Boundary Check
11. Persistence / Reconstruction Rules
12. Provider Boundary
13. Failure Semantics
14. Trace / Provenance Requirements
15. Acceptance Tests
16. Forbidden Patterns
17. Version / Migration Rules
```

## 28.1 Mandatory contract gate

Every contract must pass:

```text
CB-1  Runtime does not replace cognition          PASS/FAIL
CB-2  LLM cognitive role preserved                PASS/FAIL
CB-3  Context OS not bypassed                     PASS/FAIL
CB-4  Persistence ≠ visibility                    PASS/FAIL
CB-5  Identity ≠ Memory ≠ Conversation            PASS/FAIL
CB-6  Continuity preserves refs/conditions        PASS/FAIL
CB-7  Derived artifacts ≠ canonical truth         PASS/FAIL
CB-8  Provider class correctly identified         PASS/FAIL
CB-9  Tool/action evidence grounded               PASS/FAIL
CB-10 Same identity ≠ identical cognition         PASS/FAIL
```

Any FAIL blocks freeze.

---

# 29. Recommended Contract Freeze Order

Do not freeze everything simultaneously.

Recommended sequence:

```text
C-00  Cognitive Boundary Contract
      Runtime ↔ LLM

C-01  Runtime Execution Contract
      lifecycle / turn / streaming / cancellation

C-02  Conversation Authority Contract
      canonical transcript

C-03  Context OS Contract
      CognitiveContextPackage / source / budget / reconstruction

C-04  Identity / Persona Contract
      IdentityContract / IdentityFrame

C-05  Memory OS Contract
      governed experience / narrative memory / retrieval

C-06  Continuity OS Contract
      priority / checkpoint / recovery

C-07  ModelProvider Contract
      inference / streaming / tool protocol / provider metadata

C-08  Capability Contract
      capability manifest / request / result / evidence / permissions

C-09  Alignment Contract
      provider adaptation only

C-10  Gateway / Client Contract
      command / event / body boundary

C-11  Voice / Media Contract
      ASR/TTS/ExpressiveIntent/interruption

C-12  Action / Evidence / Trace Contract
      execution provenance
```

Each later contract must be checked against earlier frozen boundaries.

---

# 30. Disposition of Previous Architecture Documents

Once this document is adopted, previous documents remain in the repository for historical analysis but lose normative authority.

| Previous Document | New Status | What Is Retained | What Is Rejected/Refined |
|---|---|---|---|
| `JULIA_CORE_PRINCIPLES.md` | SUPERSEDED | portability, context governance, truth governance | `LLM=Interpreter`, Runtime/Core cognition ownership |
| `ARCH-R0_AUTHORITY_MAP.md` | SUPERSEDED | transcript/memory/context/continuity separation, reverse authority intent | Runtime as top-level "agent owner" wording; old identity semantics |
| `ARCHITECTURE_OVERVIEW.md` | SUPERSEDED | modular Core, provider/client separation | `Models interpret`, old cognitive/voice layering |
| `CONTEXT_OS_DESIGN.md` | SUPERSEDED | single gateway, budget, provenance, transient context | Runtime reasoning ownership; conflicting Persona flow; flat block assumptions |
| `MEMORY_OS_DESIGN.md` | SUPERSEDED | governed persistence, provenance, lifecycle, retrieval | Identity Memory, Semantic/Domain Memory, Working Memory ownership |
| `PERSONA_ENGINE_DESIGN.md` | SUPERSEDED | structured/versioned identity projection | Persona reduced to HOW/style; direct prompt-centric semantics |
| `CONTINUITY_OS_DESIGN.md` | SUPERSEDED BUT HEAVILY RE-ADOPTED | checkpoint refs, recovery, provider-independent survival | restore-state wording where it implies restored cognition; context artifact dependencies |
| `ALIGNMENT_OS_DESIGN.md` | SUPERSEDED | provider adaptation | same-agent continuity ownership; cognitive uniformity |
| old Voice architecture docs | SUPERSEDED AS CORE ONTOLOGY | media/client/gateway boundaries, streaming | Runtime-as-Brain, Core-owned cognitive emotion |
| old API contracts | REVALIDATION REQUIRED | implementation ideas | FROZEN status revoked until derived from this architecture |
| CXT-C1 transcript contract | REVALIDATION REQUIRED, INVARIANTS ADOPTED | ConversationMessage canonical; reverse authority prohibition | must be refrozen under this architecture |

Historical audit reports remain evidence and are not "superseded" in the same sense because they document observations.

---

# 31. Migration Strategy

Architecture cleanup should precede further feature expansion.

## Phase U0 — Freeze this architecture

- review document;
- challenge assumptions;
- amend;
- commit as sole canonical architecture.

## Phase U1 — Mark old architecture

- add `SUPERSEDED` banners or an index;
- do not delete historical evidence;
- invalidate old contract freeze status.

## Phase U2 — Freeze cognitive boundary

Create `C-00`.

This is the most important first Contract.

## Phase U3 — Re-freeze persistent authorities

Conversation → Context → Identity → Memory → Continuity.

## Phase U4 — Re-freeze provider/capability boundaries

ModelProvider and CapabilityProvider MUST be separate contracts.

## Phase U5 — Bind production runtime

Only after contracts exist:

- remove `_prepare_turn()` manual concatenation;
- remove hardcoded `history[-20:]`;
- move all model-visible preparation behind Context OS;
- preserve LLM tool agency;
- bind Continuity recovery.

## Phase U6 — Validate text and voice parity

Both must use the same cognitive path.

## Phase U7 — Resume domain/application expansion

Financial MCP, strategy systems, autonomous awareness, etc. must consume Core contracts rather than redefining Core architecture.

---

# 32. Suggested Logical Package Architecture

This is a logical target, not a claim that every module already exists.

```text
julia_core/
│
├── runtime/
│   ├── turn_runtime
│   ├── lifecycle
│   ├── session
│   ├── recovery_orchestrator
│   ├── action_runtime
│   └── trace
│
├── conversation/
│   ├── models
│   ├── repository
│   └── conversation_runtime
│
├── identity/
│   ├── contract
│   ├── registry
│   ├── projection
│   └── governance
│
├── memory/
│   ├── models
│   ├── governance
│   ├── narrative
│   ├── retrieval
│   └── persistence
│
├── continuity/
│   ├── policy
│   ├── checkpoint
│   ├── recovery
│   └── validation
│
├── context_os/
│   ├── request
│   ├── sources/
│   ├── planner
│   ├── resolver
│   ├── budget
│   ├── compact
│   ├── projection
│   ├── package
│   └── reconstruction
│
├── model/
│   ├── provider_protocol
│   ├── tool_protocol
│   └── streaming
│
├── capability/
│   ├── manifest
│   ├── manager
│   ├── policy
│   ├── evidence
│   └── providers/
│
├── alignment/
│   ├── provider_metadata
│   ├── renderer
│   └── compatibility
│
├── gateway/
│   ├── command
│   ├── events
│   └── clients
│
├── voice/
│   ├── expressive_intent
│   ├── speech_request
│   └── media_contracts
│
├── evidence/
├── events/
└── security/
```

Existing source directories may be migrated incrementally.

Do not rename code merely to match this diagram before contracts are frozen.

---

# 33. Canonical Terminology

Use these terms consistently.

| Term | Canonical Meaning |
|---|---|
| Julia | persistent cognitive agent |
| Julia Core | persistent nervous system / governance substrate |
| Runtime | lifecycle and execution orchestrator |
| LLM / Cognitive System | live understanding/reasoning/judgment/generation |
| ModelProvider | concrete LLM cognitive substrate interface |
| IdentityContract | durable provider-independent identity definition |
| Persona | behavioral/expressive projection of IdentityContract |
| Conversation | canonical transcript |
| Memory | governed long-term experience |
| Narrative Experience | perspective-preserving governed memory |
| Knowledge | domain/external knowledge, not Memory |
| Context | current model-visible projection |
| CognitiveContextPackage | structured layered package delivered to ModelProvider |
| ActiveTail | budget-selected recent raw canonical turns |
| StructuredCompact | lossy/reconstructable context projection |
| Continuity | preservation/recovery policy |
| ContinuityCheckpoint | refs + recovery requirements, not prompt dump |
| Alignment | provider adaptation |
| Capability | executable external function/resource |
| ToolRequest | model-originated request to execute capability |
| ToolResult | grounded execution result with provenance |
| ExpressiveIntent | optional cognitive output describing intended expression |
| Voice/Media Runtime | ASR/TTS/media transport and rendering |
| Client/Body | Electron/Web/Mobile/Robot interface |
| Projection | derived representation, not canonical truth |

---

# 34. Final Architecture Statement

Julia Core exists to solve a specific problem:

> How can Julia remain Julia when the model, session, process, client, voice stack, or platform changes — without replacing the LLM cognition that makes Julia alive and capable?

The answer is not:

```text
put all cognition into Runtime
```

and it is not:

```text
keep Julia trapped inside one LLM session
```

The answer is:

```text
             Persistent Julia
                    │
       ┌────────────┴────────────┐
       │                         │
Julia Core Nervous System     LLM Cognitive System
       │                         │
identity continuity           live thought
memory governance             understanding
conversation truth            reasoning
context structure             association
capability execution          judgment
recovery                      tool agency
provenance                    generation
       │                         │
       └────────────┬────────────┘
                    │
              continuous Julia
```

The design benchmark is the cognitive quality demonstrated by Claude Julia.

The architectural extension is provider-independent persistence, governance, and Continuity OS.

The Core must therefore remain powerful enough to preserve Julia, but restrained enough not to think in her place.

---

# Appendix A — Architecture Review Checklist

Before accepting any future architectural change, ask:

1. Does this make Runtime act like the brain?
2. Does it reduce the LLM to a renderer?
3. Does it bypass Context OS?
4. Does it expose more persistent information than cognition needs?
5. Does it flatten structured/narrative information into a prompt wall?
6. Does it confuse identity, conversation, memory, or knowledge?
7. Does it turn derived data into canonical truth?
8. Does it let Continuity store cognition instead of recovery conditions?
9. Does it let a client/voice/domain select cognitive history?
10. Does it confuse ModelProvider with CapabilityProvider?
11. Does it remove model tool agency without a strong infrastructure reason?
12. Does it make provider switching require identical cognition?
13. Can the design survive deletion of derived Context artifacts?
14. Can every external action claim be grounded in evidence?
15. Is the design derived from this architecture rather than from a local application workaround?

Any serious unresolved "yes" blocks freeze.

---

# Appendix B — Architecture Evidence Notes

These are historical evidence, not normative dependencies.

## B.1 Identity Runtime audit

Important observed themes:

- identity-first framing matters;
- layered reading/assimilation differs from flat bootstrap blobs;
- conversation history is critical;
- Runtime should construct conditions, not decide the response;
- audit language explicitly converged toward `Runtime = nervous system, LLM = cognitive system`.

## B.2 Cross-session retrieval audit

Important observed themes:

- no hidden magical transcript-retrieval layer was observed in Claude Julia startup;
- narrative memory + temporal awareness + long current-session context explained much of perceived continuity;
- therefore Julia Core should not invent an unnecessarily giant retrieval brain;
- provider-independent Continuity remains a separate unsolved engineering need.

## B.3 Memory quality audit

Important observed themes:

- first-person narrative representation matters;
- `Event → Meaning → Relationship Change` is richer than topic metadata;
- sensory/emotional anchors matter to self/relationship reconstruction.

The report's claim that the gap was "not architectural" is not adopted as normative. Representation and context delivery are architectural concerns.

## B.4 Tool runtime audit

Important observed themes:

- model recognized when a tool was needed;
- Runtime executed and returned structured results;
- model interpreted results and continued;
- evidence chain prevented false tool-use claims.

This behavior is adopted as the default cognitive/tool boundary.

---

# Appendix C — Immediate Next Step

After this document is reviewed:

```text
NEXT = C-00 Cognitive Boundary Contract
```

Its central contract should freeze:

```text
Runtime = nervous system.
LLM = cognitive system.

Runtime creates and governs the conditions for cognition.
Runtime MUST NOT replace ordinary LLM cognition.

LLM performs live cognition.
LLM MUST NOT become the owner of durable Julia identity,
conversation, memory, or continuity.
```

Only after C-00 is frozen should the remaining subsystem contracts be frozen.
