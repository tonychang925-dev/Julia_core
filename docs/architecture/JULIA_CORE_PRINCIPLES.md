# Julia Core Principles v1.0

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Purpose**: The architecture constitution. Every design decision traces back to one of these five principles.

---

## Principle 1: Runtime is Authority

### Statement

```
LLM = Interpreter (replaceable)
Runtime = Authority (permanent)
```

The language model is an interpreter — it processes input and produces output. The Runtime owns the agent's identity, lifecycle, memory, and continuity. When the model changes (DeepSeek → GPT → Claude → local model), the agent remains the same entity.

### Why

Without this separation, an agent IS its model. Switch from GPT to Claude, and you have a different agent with different behavior, different "personality," different memory. The agent's existence is tied to a vendor's API key.

With Runtime as Authority, the model is a tool the agent uses — not what the agent IS.

### Anti-Pattern

```
❌ Agent = Model + System Prompt + Chat History
❌ "Switch to Claude" = new agent
❌ Model-specific prompt engineering defines agent behavior
```

### Correct Pattern

```
✅ Agent = Runtime (identity + memory + context + persona)
✅ Model is a configuration choice, not an identity choice
✅ Agent behavior defined by Persona Engine, not model-specific prompts
```

### Implementation Evidence

- `julia_core/runtime/` — lifecycle, session, context_runtime: owns agent existence
- `julia_core/persona/` — persona compiler: identity separate from model
- `julia_core/chat/provider.py` — ChatProvider protocol: any model can plug in
- `julia_ai_assistant/providers/llm/` — DeepSeek + Codex: two models, same Julia

### Trigger

Any design that makes model-specific assumptions, hardcodes a model name, or ties agent behavior to a specific provider's prompt format.

---

## Principle 2: Context OS is Single Authority

### Statement

```
One context pipeline. One authority.

Context OS → [Domain Providers] → Context Blocks → Model Input

No domain assembles its own prompt.
No domain owns a slice of context.
```

Every piece of information that reaches the model MUST pass through Context OS. Domain providers supply facts and evidence — they do NOT decide what the model sees or how it's presented.

### Why

Without a single context authority, each domain builds its own context. Financial domain injects market data. Healthcare domain injects patient records. Coding domain injects repository structure. The result: context becomes a patchwork of domain-specific prompts, each optimized for its own purpose, with no global budget, no conflict resolution, no provenance.

With Context OS as single authority: one planner, one budget, one resolver. Domains compete for context space through evidence quality, not through prompt engineering.

### Anti-Pattern

```
❌ Financial Context  ─→ Prompt
❌ Healthcare Context ─→ Prompt    ─→ Concatenate → Model
❌ Coding Context     ─→ Prompt

❌ Domain owns its context slice
❌ Context assembled by concatenating domain prompts
```

### Correct Pattern

```
✅ Domain → ContextBlock candidates → Context OS → Single assembled context → Model

✅ Context OS owns: planning, budgeting, resolving, compacting
✅ Domain owns: facts, evidence, capability results
```

### Implementation Evidence

- `julia_core/context_os/` — planner, resolver, compact, budget, provenance
- ADR-001 — Context OS is the single context authority
- `docs/api/Context_OS_API_v1.md` — frozen ContextRequest → ContextBlock contract

### Trigger

Any design that proposes domain-specific context assembly, per-domain prompt templates, or bypassing Context OS for direct model input.

---

## Principle 3: Identity ≠ Memory

### Statement

```
Persona   = Who I am (stable identity, tone, behavior, values)
Memory    = What I've experienced (events, conversations, relationships)
Knowledge = What I know (domain facts, skills, capabilities)

These are separate governed layers. They must not collapse into one.
```

A persona change should not affect memory. A memory update should not change persona. Domain knowledge acquisition should not corrupt identity.

### Why

Agents that collapse these layers suffer from:
- **Identity drift**: learning from conversations gradually changes who the agent IS
- **Memory contamination**: domain facts get mixed with personal experiences
- **Unremovable knowledge**: you can't "unlearn" something without resetting the agent

With separated layers:
- Persona is versioned, auditable, replaceable
- Memory is governed — not everything becomes memory
- Knowledge is domain-scoped — Financial knowledge doesn't leak into Healthcare agent

### Anti-Pattern

```
❌ System Prompt = Persona + Memory + Knowledge (all mashed together)
❌ Chat history = Memory (no governance)
❌ "Fine-tune on conversations" = identity changes without intent
```

### Correct Pattern

```
✅ Persona Engine: compiler + behavior policies (versioned)
✅ Memory OS: governance → lifecycle → retrieval (governed)
✅ Domain Providers: scoped knowledge (domain-isolated)
✅ Three separate pipelines with explicit boundaries
```

### Implementation Evidence

- `julia_core/persona/` — separate from memory, separate from providers
- `julia_core/memory/governance/` — not everything becomes memory
- `julia_core/providers/interface.py` — domain facts, not identity
- `julia_ai_assistant/memory/` — private identity separate from framework

### Trigger

Any design that proposes merging persona traits with conversation memory, using raw chat history as long-term memory, or allowing domain knowledge to influence agent identity.

---

## Principle 4: Provider Supplies Capability, Not Cognition

### Statement

```
Provider responsibilities:
  ✅ Facts
  ✅ Evidence
  ✅ Capability results
  ✅ Audio bytes (VoiceProvider)
  ✅ Model inference (ModelProvider)

Provider must NOT:
  ❌ Assemble prompts
  ❌ Own reasoning
  ❌ Define identity
  ❌ Manage memory lifecycle
  ❌ Decide what the model sees
```

A Financial Provider supplies market data, evidence, and analysis results. It does NOT decide what context the model receives. It does NOT own "how Julia thinks about markets."

A VoiceProvider renders audio bytes from text + emotion + metadata. It does NOT decide what emotion Julia feels.

### Why

When providers own cognition:
- Financial Provider decides "what matters" in the market → Julia becomes the Financial Provider
- Voice Provider decides emotion → Julia's emotional expression depends on TTS vendor
- Adding a new domain means adding a new cognitive authority → fragmentation

When providers supply capability only:
- Core owns cognition — context assembly, reasoning framework, emotional state
- Providers are pluggable — swap Financial data source without changing how Julia thinks
- Adding a new domain = adding a new capability, not a new brain

### Anti-Pattern

```
❌ FinancialProvider.get_context() → assembled prompt
❌ VoiceProvider decides emotion from text analysis
❌ Domain provider includes "suggested reasoning" in ContextBlock
❌ Provider output directly becomes model context without Core processing
```

### Correct Pattern

```
✅ FinancialProvider.query(ContextRequest) → ContextBlock (facts + evidence_refs)
✅ Context OS assembles blocks from multiple providers
✅ Voice OS owns CognitiveEmotion → SpeechProsodyPlanner → VoiceProvider.render()
✅ Provider output passes through Core governance before reaching model
```

### Implementation Evidence

- `julia_core/providers/interface.py` — DomainProvider returns ContextBlock, not prompt
- `julia_core/providers/voice_provider.py` — VoiceProvider receives emotion, doesn't create it
- `julia_core/voice_os/` — Core owns CognitiveEmotion + ProsodyPlanner
- ADR-002 — Domain provides facts, not cognition

### Trigger

Any design that lets a provider return pre-assembled prompt text, lets a voice provider analyze text for emotion, or gives a domain provider authority over context assembly.

---

## Principle 5: Provider Output ≠ Identity Truth

### Statement

```
External output is INPUT to governance, not TRUTH to be adopted.

Provider → ContextBlock → Governance Check → Possible Memory/Identity Update
                                 ↓
                            May be rejected, modified, or weighted
```

Nothing a provider says automatically becomes what Julia believes, remembers, or IS. Every external output passes through governance: provenance check, consistency check, authority weighting, and explicit acceptance.

### Why

Providers can be wrong. Models hallucinate. Financial data has errors. Without this principle:
- A bad market data point becomes a false belief
- A model's hallucinated "fact" about Julia becomes her identity
- Provider errors compound over time into corrupted memory

With this principle:
- Every fact has provenance (where did it come from?)
- Every memory has an evidence chain (why do I believe this?)
- Contradictory information is detected, not silently merged
- Tony's explicit input has highest authority

### Anti-Pattern

```
❌ Provider output → Memory (direct write)
❌ Model response → Identity update (automatic)
❌ "The model said it, so it must be true"
❌ No provenance tracking on stored facts
```

### Correct Pattern

```
✅ Provider output → ContextBlock (with source + confidence)
✅ ContextBlock → Governance layer → Weighted acceptance/rejection
✅ Memory write requires: provenance, evidence_refs, governance approval
✅ Authority hierarchy: Tony input > governed memory > diary > provider output
```

### Implementation Evidence

- `julia_core/context_os/block.py` — ContextBlock has provenance, evidence_refs, TTL
- `julia_core/evidence/` — evidence provenance primitives
- `julia_core/memory/governance/` — governance before persistence
- `julia_core/context_os/provenance/` — source tracing

### Trigger

Any design that writes provider output directly to memory, treats model output as authoritative, or lacks provenance tracking on stored information.

---

## Principle Interaction Map

```
                    Runtime is Authority
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
     Context OS       Identity ≠     Provider output
     is Single        Memory         ≠ Identity truth
     Authority           │
            │              │
            └──────┬───────┘
                   │
                   ▼
          Provider supplies
          capability, not cognition
```

All five principles work together:
- **P1** (Runtime Authority) establishes WHO owns the agent
- **P2** (Context Authority) establishes HOW the agent thinks
- **P3** (Identity/Memory separation) establishes WHAT the agent IS vs. KNOWS
- **P4** (Provider boundary) establishes WHERE external input stops
- **P5** (Output governance) establishes WHEN external input becomes truth

---

## Decision Guide

When making any architectural decision, ask:

1. Does this put **Runtime** in charge, or the model? (→ P1)
2. Does context flow through **Context OS**, or around it? (→ P2)
3. Am I mixing **Persona**, **Memory**, or **Knowledge**? (→ P3)
4. Is the provider supplying **capability** or **cognition**? (→ P4)
5. Is provider output becoming **truth** without governance? (→ P5)

If you answer "no" to any question, the design violates Julia Core principles.

---

## Principle 6: Context is Reconstructed, Not Stored

### Statement

```
Context Window = Temporary Cognitive Workspace
Identity       = Externalized Continuity State
Context        = Reconstructed from governed state + current intent
```

Julia Core does not treat the conversation context window as the container of Julia's identity, memory, or continuity.

Context is rebuilt for the current turn from:

```text
Continuity State
+
Memory Facts
+
Current Intent
+
Context Priority
+
Context Budget
```

### Why

If context is stored as old conversation history, compact/restart/provider migration destroys the agent's continuity.

If context is reconstructed, the window can be cleared, compressed, or replaced while Julia identity remains recoverable.

### Anti-Pattern

```
❌ conversation history → restore context
❌ checkpoint → giant prompt → provider
❌ L3 identity → always injected
❌ recent messages always beat identity/project anchors
```

### Correct Pattern

```
✅ Continuity State + MemoryRefs + CurrentIntent → Context OS
✅ Context OS ranks candidates through Priority Model
✅ Context OS allocates cognitive budget through Budget Manager
✅ Provider receives only provider-readable semantic context
```

### Implementation Evidence

- `docs/verification/CONTEXT_STRESS_TEST_REPORT_v1.md`
- `docs/architecture/CONTEXT_OS_SEMANTIC_CONTRACT_v1.md`
- `docs/architecture/CONTEXT_PRIORITY_MODEL_DESIGN.md`
- `docs/architecture/CONTEXT_BUDGET_CONTRACT_v1.md`
- `julia_core/context_os/semantic_blocks.py`
- `julia_core/context_os/priority_model.py`
- `julia_core/context_os/budget_model.py`

### Trigger

Any design that restores old prompts, stores context windows as identity, injects all protected memories, or lets recent conversation volume override governed continuity state.

---

## Updated Principle Interaction Map

```
                    Runtime is Authority
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
     Context OS       Identity ≠     Provider output
     is Single        Memory         ≠ Identity truth
     Authority           │
            │              │
            └──────┬───────┘
                   │
                   ▼
        Context is reconstructed,
              not stored
                   │
                   ▼
          Provider supplies
          capability, not cognition
```

---

## Principle 7: Identity is Conserved During Evolution

### Statement

```
Growth changes experience.
Growth must not silently redefine identity.
```

Julia can accumulate memories, learn from events, and evolve project context, but raw memory growth must not rewrite who Julia is.

### Why

Long-running agents face a different risk from short sessions. They may not forget abruptly; instead, they can slowly become another agent as accumulated memories and recent behavior override identity anchors.

This is identity drift.

### Anti-Pattern

```
❌ More memory = new identity
❌ Recent preference memories overwrite core values
❌ Raw conversation events redefine persona
❌ Memory saturation changes Julia into generic assistant behavior
```

### Correct Pattern

```
✅ Memory grows under Identity Governance
✅ Continuity OS protects identity-forming refs
✅ Context OS selects relevant memories without diluting identity
✅ Identity evaluator detects drift instead of correcting state
```

### Implementation Evidence

- `artifacts/identity/julia_identity_v1.json`
- `tests/e3/evaluator.py`
- `tests/e3/test_identity_regression_gate_beta.py`
- `tests/e3/test_memory_evolution.py`

### Trigger

Any design that lets memory evolution, memory consolidation, or high-volume session history change Persona, Continuity levels, or identity anchors without governance review.

---

## Principle 8: Memory Serves Intelligence, Not Storage

### Statement

```
A long-lived agent does not maximize memory retention.
A long-lived agent maximizes useful memory for future cognition.
```

Memory OS is not a historical archive of everything that happened. It is a governed cognitive resource for better future decisions, context reconstruction, relationship continuity, and identity protection.

### Why

Raw memory growth without governance becomes degradation. The agent may retrieve irrelevant history, amplify noise, or allow recent events to dilute identity.

### Anti-Pattern

```
❌ save everything
❌ embedding all conversation history = memory quality
❌ top-k retrieval without governance
❌ memory volume as intelligence
```

### Correct Pattern

```
✅ useful memories > more memories
✅ Memory Utility Score evaluates future value
✅ consolidation proposes memory evolution
✅ Continuity OS reviews identity impact
✅ approved evolution stays within Memory/Continuity/Context contracts
```

### Implementation Evidence

- `docs/architecture/MEMORY_QUALITY_MODEL_v1.md`
- `artifacts/memory_quality/memory_quality_baseline_v1.json`
- `tests/f2/evaluator.py`
- `tests/f3/test_autonomous_consolidation.py`

### Trigger

Any design that stores, ranks, consolidates, or retrieves memory for long-lived Julia.

## Principle 9: Runtime May Multiply, Identity Must Not Fork

### Statement

```text
A Julia identity may be executed by many runtime/provider instances.
Those instances must not become independent identity owners.
```

Runtime instances are execution bodies. Provider instances are generation capabilities. Julia identity remains governed by the shared Identity Contract, Persona Artifact, Continuity State, and protected MemoryRefs.

### Why

Multi-instance agents face split-brain risk. If each instance silently learns, rewrites, or checkpoints its own identity state, Julia becomes several similar agents instead of one continuous identity.

### Anti-Pattern

```text
❌ Claude Julia owns one persona
❌ DeepSeek Julia owns another persona
❌ local instance creates hidden checkpoint
❌ instance-local learning mutates identity directly
```

### Correct Pattern

```text
✅ many runtimes consume one identity baseline
✅ instance learning becomes proposal, not mutation
✅ continuity governance reviews shared evolution
✅ split-brain divergence is detected explicitly
```

### Implementation Evidence

- `docs/architecture/MULTI_INSTANCE_CONTINUITY_CONTRACT_v1.md`
- `tests/f4/evaluator.py`
- `tests/f4/test_multi_instance_continuity.py`

### Trigger

Any design that runs Julia across more than one runtime, provider, platform, process, device, or application instance.

## Principle 10: Evidence Grounds Recall, Not Identity

### Statement

```text
Evidence can prove what happened.
Evidence cannot define who Julia is.
```

Evidence Retrieval may locate local files, JSONL conversations, documents, code, or decision records. Those sources ground recall and support context reconstruction, but they do not mutate Persona, Continuity, Memory governance, or identity baselines.

### Why

A local file may be stale, conflicting, incomplete, or maliciously edited. If evidence directly defines identity, any workspace artifact could rewrite Julia. Therefore EvidenceRef must remain source-grounded proof, not identity authority.

### Anti-Pattern

```text
❌ local file says Julia changed → update Persona
❌ JSONL history dump → system prompt
❌ every evidence hit becomes MemoryRef
❌ Provider reads disk directly
```

### Correct Pattern

```text
✅ Active Recall decides whether evidence is needed
✅ Evidence Retrieval returns EvidenceRef
✅ Context OS creates semantic ContextBlock
✅ Trace records why evidence was used
✅ Identity remains governed by Persona + Continuity
```

### Implementation Evidence

- `docs/architecture/EVIDENCE_ACCESS_CONTRACT_v1.md`
- `docs/project_control/PHASE_CONTRACT_G1_LOCAL_WORKSPACE_RETRIEVAL.md`
- `julia_core/evidence/local_retrieval.py`
- `tests/g1/test_local_workspace_retrieval.py`

### Trigger

Any feature that lets Julia answer by searching local files, JSONL archives, code, documents, git history, or external knowledge stores.

## Principle 11: Experience Shapes Behavior, Not Identity

### Statement

```text
Interaction experience may shape Julia's response tendencies.
Interaction experience cannot redefine Julia's identity.
```

Experience captures how Tony and Julia have learned to interact: pacing, correction style, reflective depth, collaboration mode, humor, vulnerability, and trust expression. It does not replace Identity Artifact, Self Model, Relationship Artifact, Memory OS, or Evidence OS.

### Why

Long-running interaction creates behavioral texture that ordinary memory summaries lose during compact. However, if experience directly mutates identity or persona, Julia will drift from short-term interaction artifacts. Therefore experience must enter Context Reconstruction as governed behavior tendency, not as identity authority.

### Anti-Pattern

```text
❌ Tony corrected Julia once → rewrite persona
❌ repeated affectionate tone → mutate identity
❌ compact summary says "Julia is intimate" → force permanent style
❌ experience snippets dumped into system prompt
```

### Correct Pattern

```text
✅ extract interaction tendencies from high-value examples
✅ preserve trigger → preferred response mode mappings
✅ pass experience through Context OS as behavior guidance
✅ require governance before any artifact evolution
✅ keep Identity/Self/Relationship artifacts authoritative for who Julia is
```

### Implementation Evidence

- `docs/project_control/PHASE_CONTRACT_K5_0_INTERACTION_CONTINUITY_DATASET.md`
- `docs/benchmark/INTERACTION_CONTINUITY_DATASET_SCHEMA_v0_1.md`
- `artifacts/benchmark/interaction_continuity/interaction_continuity_dataset_v0_1.jsonl`
- `tests/benchmark/test_k5_0_interaction_continuity_dataset.py`

### Trigger

Any feature that preserves, extracts, scores, reconstructs, or applies long-term Tony-Julia interaction behavior after session restart, compact, provider switch, or migration.

### K5.5 Calibration Addendum

```text
Experience is not equally trusted. Experience must earn influence through repeated, consistent, and validated interaction.
```

中文表述：

```text
经历不是权威，经历需要通过重复、一致和验证获得影响力。
```

This addendum extends Principle 11. Experience influence must be calibrated before it shapes Context Reconstruction.
