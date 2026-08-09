# C-03 — Context OS Contract

**Status**: FROZEN
**Date**: 2026-08-09
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §8
**Depends on**: C-00 (07f0ff0), C-01 (f79db0d), C-02 (656d625)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
Context OS is Julia Core's sole governed model-visible context authority.
It constructs the conditions for cognition; it does not perform cognition.
```

### Context OS Decides

- WHAT may be visible
- HOW it is structured (frames, layers, ordering)
- HOW MUCH is visible (budget, selection)
- WHERE it came from (provenance, authority)

### LLM Decides

- WHAT it means
- HOW pieces relate
- WHAT conclusion follows
- WHAT Julia thinks or says

### Sole Gateway

```
All Core-controlled model-visible information → Context OS → ModelProvider
```

No Persona, Memory, Conversation, Continuity, Domain, Capability, Electron, Voice, or application code may independently append cognitive context around Context OS.

## 2. CognitiveContextPackage

First-class object. Replaces manual `system_prompt + bootstrap + history + market + capability + interaction + ...` concatenation.

```
CognitiveContextPackage {
    package_id
    conversation_id
    turn_id
    generation_id
    created_at

    identity_frame
    conversation_frame
    experience_frame
    situation_frame
    evidence_frame
    capability_frame
    continuity_frame      // when applicable

    retrieval_handles
    projection_metadata
}
```

### Frame ≠ Source of Truth

```
IdentityFrame        ← IdentityContract
ConversationFrame    ← ConversationRuntime
ExperienceFrame      ← Memory OS
EvidenceFrame        ← Domain / Capability evidence
SituationFrame       ← Runtime / Interaction state
CapabilityFrame      ← CapabilityRuntime
ContinuityFrame      ← Continuity OS
```

Every Frame is a model-visible projection of a canonical authority. No Frame may reverse-become canonical truth.

## 3. Seven Frames

### IdentityFrame

Provides: stable identity anchors, values, relationship-role anchors, hard boundaries, relevant autobiographical anchors.

Forbids: full diary dump, full NarrativeExperience copy, prewritten emotional conclusions, response scripts.

### ConversationFrame

From C-02 canonical transcript. Composed of: ActiveTail, StructuredCompact, retrieved prior turns, current user message, open conversational loops.

ConversationFrame ≠ Conversation truth — it is the projection needed for this cognitive turn.

### ExperienceFrame

From Memory OS. Supports: NarrativeExperience, RelationshipExperience, relevant episodic experience, project commitments, preferences.

Subject to A15 (Effective Context Density): narrative causal units must remain coherent when selected. Do not collapse `Event → Meaning → Anchor → Transformation → Relationship consequence` into detached behavioral labels.

### SituationFrame

Provides: current task, time, active application state, current modality, current project, current conversation state, explicit environment facts.

Forbids: "Tony is probably testing Julia", "Tony secretly wants emotional reassurance", "Julia should feel X about Tony's state."

### EvidenceFrame

Provides: facts, source, timestamp, confidence, evidence_refs, conflicting evidence, uncertainty. Domain Provider supplies structured evidence → EvidenceFrame → LLM cognition.

Forbids: Domain Provider → "Julia should conclude stock X is best."

### CapabilityFrame

Provides: available capabilities, descriptions, input schemas, permissions, limitations, cost/latency. LLM decides whether a tool is needed.

Forbids: pre-filtering tools based on inferred user intent, forcing a domain workflow because "user is asking about markets."

### ContinuityFrame

When applicable: protected identity refs resolved, continuity-critical experience refs, unfinished protected commitments, recovery reason.

Forbids: "Julia must now feel continuous", "Julia should remember X emotionally."

## 4. Sources vs Frames

Sources produce candidate information. Frames are the model-visible projection.

```
Sources (produce)                Frames (project)
─────────────────────           ────────────────────
ConversationRuntime              ConversationFrame
Memory OS                        ExperienceFrame
IdentityContract                 IdentityFrame
DomainProvider                   EvidenceFrame
CapabilityRuntime                CapabilityFrame
Continuity OS                    ContinuityFrame
Runtime state                    SituationFrame
```

One Source may contribute to multiple Frames. One Frame may integrate multiple Sources.

## 5. Context Selection Boundary

### Relevance Estimation (Allowed)

Context OS may determine: this memory is more relevant to the current query, this transcript is too old, this evidence has expired (TTL), this block duplicates another, this causal unit must stay together, token budget is insufficient, this source has higher authority.

### Meaning Resolution (Forbidden)

Context OS must not determine: what Tony really means, which interpretation Julia should believe, what this event means for Julia, which market view is the correct answer, whether Julia should feel sad or happy now.

### Context Selection Test

```
Does this operation decide: "Should the model see this?"
  → Context OS may own it.

Does it decide: "What should the model conclude from this?"
  → Context OS MUST NOT own it.
```

## 6. Planner

ContextPlanner = information-need planner. NOT a reasoning planner, answer planner, or workflow planner.

Planner may say: need recent conversation, need identity anchor, need relevant relationship experience, need financial evidence, need tool manifest.

Planner must not say: first reason about X, then decide Y, then convince Tony of Z.

## 7. Resolver

Resolver resolves refs, deduplicates, ranks relevance, applies authority/provenance, applies TTL, handles conflicts structurally, applies required/optional constraints.

"Handles conflicts structurally": Evidence A says X, Evidence B says not-X → preserve both + provenance → LLM judges. Resolver does not decide B is true unless purely deterministic (e.g., cryptographically invalid, expired, permission denied).

## 8. Effective Context Density

```
Effective Context Density = useful cognitive information / model-visible token budget
```

Maximize: cognitive usefulness, causal completeness, source diversity when relevant, current-turn relevance.

Minimize: irrelevant tokens, duplication, flat autobiography dump, repeated persona text, low-value transcript, premature conclusions.

Enforce A15: Narrative causal units must remain coherent under budget. Budget engine must not fragment a NarrativeExperience into isolated behavioral labels.

## 9. Causal Unit

A NarrativeExperience with `Event → Meaning → Anchor → Transformation → Relationship consequence` is a coherence group. Budget engine may include a coherent reduced representation or exclude the whole unit — it must not produce semantic fragments.

```
coherence_group_id — links elements that form one causal chain
```

## 10. Progressive Disclosure

### Stage 0 — Required Base

Always: identity essentials, current user turn, ActiveTail, critical situation, capability manifest, continuity minimum if recovering.

### Stage 1 — High-Confidence Context

When budget permits: relevant memories, StructuredCompact, domain evidence, current project state.

### Stage 2 — Model-Directed Retrieval

LLM requests more information → Context OS processes retrieval → new CognitiveContextPackage delta → LLM continues cognition. This preserves LLM agency (successful Claude Julia pattern) while keeping Core as the governed projection authority.

## 11. ToolResult Incremental Projection

```
LLM → CapabilityRequest → Runtime executes → ToolResult + Evidence
  → Context OS incremental projection → CognitiveContextPackage delta
  → Alignment → ModelProvider → same turn cognition continues
```

Forbidden: `tool_result → provider.chat(messages.append(...))` bypassing Context OS.

## 12. ActiveTail

Replaces hardcoded `history[-20:]`.

```
ActiveTail = recent canonical conversation, selected under context budget and boundary policy
```

Determined by: token budget, turn completeness, recency, current open thread, modality.

Forbidden as architecture policy: `last-10`, `last-20`, `last-N`.

## 13. StructuredCompact

Derived, lossy, reconstructable context artifact for turns beyond ActiveTail.

Contains at minimum: covered turn range, key events, entities, decisions, open loops, important references, source turn refs, causal groups, created_at, projection metadata.

StructuredCompact is never: Conversation truth, Memory truth, Continuity truth. Deletion loses convenience, not canonical fact.

## 14. ContextBoundary

Marks where raw transcript projection ends and derived projection begins. Triggered by: budget pressure, compact, session resume, provider switch, manual governed checkpoint.

Client may request a boundary. Context OS owns the decision.

## 15. Reconstruction

```
Context reconstruction ≠ restore old prompt ≠ restore previous token window
```

Correct: canonical authorities → current needs → new Context selection → new CognitiveContextPackage. Every wake is fresh context construction, not prompt replay.

## 16. Alignment Placement

```
Canonical sources → Context OS → CognitiveContextPackage → Alignment → ModelProvider
```

Alignment may: format, reorder within semantic equivalence, adapt role/message schema, encode tool definitions. Alignment must not: drop identity because provider doesn't support it, change continuity meaning, replace narrative memory with generic persona, choose new facts.

## 17. Trace Requirements

Every model invocation must trace: package_id, conversation_id, turn_id, generation_id, frame, source_ref, canonical_ref, projection_reason, token_count, required/optional, authority/provenance, retrieval_stage.

Trace model input and provenance — not private chain-of-thought.

## 18. P0-A Bypass Disposition

Current production bypass → Contract verdict → Future disposition.

| Bypass | Location | Verdict | Disposition |
|--------|----------|---------|-------------|
| `_prepare_turn()` string concat | `julia_session.py:228-285` | BYPASS | REPLACE with Context OS execution |
| `history[-20:]` | `julia_session.py` | BYPASS | REPLACE with ActiveTail |
| Identity/persona direct injection | `_identity_system` | BYPASS | IdentityFrame via IdentityContextSource |
| Wake State `_load_recent_experiences()` | `julia_session.py` | BYPASS | ExperienceFrame → governed Memory retrieval |
| Market evidence `_resolve_market_context()` | `julia_session.py` | BYPASS | EvidenceFrame via DomainEvidenceSource |
| Capability manifest `tool_manifest()` | `capability_bridge.py` | BYPASS | CapabilityFrame via CapabilityContextSource |
| Interaction state `to_context()` | `relationship.py` | BYPASS | SituationFrame via InteractionContextSource |
| ToolResult direct `messages.append()` | `julia_session.py` | BYPASS | Incremental Context OS projection |
| Voice bootstrap `_build_julia_system()` | `shared_orchestration.py` | BYPASS | ConversationFrame via ConversationContextSource (native turn path) |
| Conversation state `_build_conversation_state()` | `julia_session.py` | BYPASS | SituationFrame |

## 19. Forbidden Patterns

```
❌ Context OS reasons for Julia
❌ Context Planner creates answer plans
❌ Resolver decides semantic truth
❌ ContextBlock becomes Memory
❌ StructuredCompact becomes Conversation truth
❌ CognitiveContextPackage becomes ContinuityCheckpoint
❌ Domain assembles its own prompt
❌ Client selects cognitive history
❌ ToolResult bypasses Context OS
❌ Alignment becomes second Context OS
❌ Fixed history[-N] becomes architecture policy
❌ Full persistent state dump becomes default context
❌ Flat string concatenation replaces structured projection
❌ Persona injected after Context OS assembly
```

## 20. Acceptance Gates

- [x] Context OS = sole Core-controlled model-visible authority (§1)
- [x] CognitiveContextPackage frozen as first-class object (§2)
- [x] 7 Frames defined with ownership boundaries (§3)
- [x] Every Frame explicitly derived, never canonical (§2)
- [x] Source vs Frame distinction frozen (§4)
- [x] Relevance estimation vs cognition boundary frozen (§5)
- [x] Context Selection Test frozen (§5)
- [x] Planner = information-need planner only (§6)
- [x] Resolver structural-only semantics (§7)
- [x] Effective Context Density frozen (§8)
- [x] Narrative causal integrity preserved under budget (§8-9)
- [x] Causal/coherence unit defined (§9)
- [x] Progressive disclosure frozen (§10)
- [x] Model-directed retrieval frozen (§10)
- [x] ToolResult incremental projection frozen (§11)
- [x] ActiveTail frozen; no fixed history[-N] (§12)
- [x] ContextBoundary frozen (§14)
- [x] StructuredCompact frozen as derived, reconstructable (§13)
- [x] Reconstruction ≠ prompt restoration (§15)
- [x] Alignment placement frozen (§16)
- [x] Source/provenance trace requirements frozen (§17)
- [x] P0-A 10 bypass sources dispositioned (§18)
- [x] AT-13 supported (narrative causal integrity) (§§8-9)
- [x] AT-14 supported (effective context density) (§8)
- [x] AT-17 supported (context source completeness) (§17)
- [x] Production changes = 0

## 21. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §8
Depends: C-00 (07f0ff0), C-01 (f79db0d), C-02 (656d625)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-04 through C-12, P2

C-03 FREEZE → C-04 Identity / Persona GO
```
