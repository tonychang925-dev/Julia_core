# C-05 — Memory OS Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §11
**Depends on**: C-00 (07f0ff0), C-02 (656d625), C-03 (4b1625e), C-04 (433b674)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
Memory OS governs durable experience.
It does not own transcript truth, identity, current context, continuity, or live cognition.
```

### Five Boundaries

```
Conversation = what actually happened
Memory       = what governed experience deserves durable retention

Identity     = who Julia persistently is
Memory       = what Julia has experienced

Context      = what Julia may see now
Memory       = one canonical source Context may retrieve from

Continuity   = what must survive disruption
Memory       = durable experience Continuity may protect by reference

LLM          = interprets experience
Memory OS    = governs whether that interpretation becomes durable memory
```

## 2. MemoryExperience — Canonical Durable Artifact

```
MemoryExperience {
    memory_id
    memory_type            // Episodic, Relationship, Preference, ProjectCommitment, Narrative
    version
    subject
    event_time             // when the experience occurred (NOT memory creation time)
    time_range             // optional span
    source_refs[]          // canonical Conversation, user statement, evidence
    provenance             // origin label, governance trail
    content                // the governed content
    meaning_at_time        // what it meant when experienced (optional)
    confidence             // epistemic status
    coherence_group_id     // links causal elements
    identity_anchor_refs   // if identity-defining (points to C-04)
    created_at             // when memory was formed (≠ event_time)
    governance_status      // ACCEPTED | REJECTED | SUPERSEDED | RETRACTED
    supersedes             // previous version if applicable
    metadata
}
```

`event_time` is the canonical event time. `created_at` is the memory formation time. These must not be confused.

## 3. Five Canonical Experience Types

### EpisodicExperience

What happened and when. Involved entities. Source refs. Relevant consequences. Not every conversation turn is an Episode.

### RelationshipExperience

Shared event, interaction meaning, relationship consequence. Does not own relationship role definition (→ C-04 Identity). Stores the experience of the relationship.

### PreferenceExperience

Stable recurring preferences learned through interaction. Distinguished from one-time task instructions (→ Context) or transient requests.

### ProjectCommitmentExperience

Important decisions, commitments, milestones, unfinished obligations, agreed directions. Current working project state may live in domain/project sources. Memory stores the experience of commitment.

### NarrativeExperience

The core continuity-quality memory type. Preserves causal chain:

```
Event → MeaningAtTime → Emotional/Experiential Significance
  → Concrete/Embodied Anchors → Transformation → Relationship Consequence
  → Source References → LaterReinterpretations[]
```

Narrative causal integrity is a durable property (A15). Memory stores the causal structure; Context OS protects it under budget.

## 4. meaning_at_time ≠ Eternal Truth

```
Original experience → MeaningAtTime (preserved)
Later cognition → LaterReinterpretation (appended)
```

New interpretation does not overwrite the original experience. Julia can grow; the past is not rewritten.

## 5. Memory ≠ Transcript Summary

Memory formation is not generic summarization. StructuredCompact (C-03) helps locate candidate experiences. Compact ≠ Memory — different lifecycles, different authority.

## 6. MemoryCandidate Lifecycle

```
Conversation / Event / LLM cognition
        ↓
MemoryCandidate
        ↓
Memory Governance
        ↓
ACCEPTED | REJECTED | SUPERSEDED | RETRACTED
```

LLM output is not automatically durable memory. Governance is required.

### Who Produces Candidates?

Candidates containing semantic interpretation (meaning, relationship significance, transformation, emotional significance) must originate from live LLM cognition, explicit user statement, or governed memory reinterpretation — not from deterministic Runtime rules.

```
Memory OS governs meaning-bearing artifacts; it does not manufacture their meaning.
```

Memory OS may: schema validation, source validation, provenance, deduplication, retention policy, versioning, conflict registration, permission/privacy rules.

Memory OS must not decide: "this meant Tony finally trusted Julia" — unless that meaning comes from provenance-tracked cognitive output or user statement.

## 7. Memory Promotion Test

A candidate seeking entry into durable Memory must satisfy:

1. Is this more than transient conversation content?
2. Is it likely useful beyond the current turn/session?
3. Does it represent an experience, preference, commitment, or relationship change?
4. Is its source traceable?
5. Is its semantic meaning supported by source/cognitive provenance?
6. Would storing it create harmful duplication?
7. Does it belong to Identity instead? (→ C-04)
8. Does it belong to a domain/project source instead?
9. Is retention permitted?

Important ≠ identity-forming. Many important experiences stay in Memory without entering Identity.

## 8. Importance ≠ Identity ≠ Continuity

Three separate dimensions:

```
memory_importance           → retrieval priority (C-05)
identity-forming significance → Identity promotion test (C-04)
continuity preservation       → survival priority (C-06)
```

No single importance score determines all three. Memory does not auto-promote to Identity. Memory does not auto-assign Continuity priority.

## 9. Removed Types

### IdentityMemory — REMOVED

Stable self-defining truth → IdentityContract (C-04). Supporting experience → MemoryExperience with source_ref to Identity. No duplicate authority.

### WorkingMemory — REMOVED

Current turn state, temporary observations, active Context blocks → Runtime / Context. Not durable Memory.

### Broad SemanticMemory — SCONTRACTED

Domain knowledge, world facts, documentation → Domain/Knowledge Providers, Evidence. Julia Memory stores personally experienced knowledge only. Julia Core is not a duplicate world knowledge base.

## 10. Version / Supersedence

Accepted Memory is versioned. In-place overwrite is forbidden. Correction path: M1 accepted → new evidence → M2 supersedes/corrects M1. Why changed, source refs, and time are preserved.

## 11. Fact / Interpretation Distinction

```
observed_fact       — what was verifiably observed
reported_fact       — what was reported by a source
interpretation      — what it was understood to mean
inference           — what was concluded from it
subjective_meaning  — what it meant to Julia personally
```

This prevents Memory from becoming a false-fact factory.

## 12. Retrieval ≠ Visibility

```
Memory retrieval → Context OS → ExperienceFrame → CognitiveContextPackage → LLM
```

Retrieved memory is not automatically visible. Context OS (C-03) retains final model-visible authority. No direct Memory → ModelProvider path. No direct `provider.messages.append(memory)` bypass.

## 13. No Auto-Memory During Historical Import

C-02 §8 already prohibits LLM/Memory/Continuity/Context side effects during import. C-05 inherits this. Historical conversation import → canonical facts only. Memory formation occurs through normal governed process after import completes.

## 14. Retention and Forgetting

Durable does not mean permanent. Allowed: retention policy, privacy deletion, user correction, legal/data policy, duplicate consolidation, low-value expiration.

Experiences important to Julia's identity/relationship continuity (C-04, C-06) must not be silently deleted by a generic TTL. `retention_class` defined here; survival priority governed by C-06.

## 15. P0-A Bypass Disposition

| Current Path | Verdict | Target |
|-------------|---------|--------|
| SessionStore Wake State summaries | RECLASSIFY | Remove from cognition; keep as legacy metadata |
| SessionRecorder diary writes | KEEP WITH BOUNDARY | Route through Memory governance |
| SessionSummarizer LLM summaries | KEEP WITH BOUNDARY | Classify as MemoryCandidate; require governance |
| Direct memory file loading (BOOTSTRAP) | RECLASSIFY | Separate Identity anchors (C-04) from Memory retrieval (C-05) |
| Auto-memory from every turn | REMOVE | Never was governance; candidate formation must be explicit |
| IdentityMemory concept | RECLASSIFY | → IdentityContract source_refs (C-04) |
| WorkingMemory concept | RECLASSIFY | → Runtime/Context turn state (C-01/C-03) |

## 16. Core Object Relationships

```
Canonical Conversation
        │ evidence/source
        ▼
   LLM cognition
        │ optional memory candidate
        ▼
  MemoryCandidate
        │
        ▼
 Memory Governance
        │ ACCEPTED
        ▼
 Accepted MemoryExperience
        │
        ├── source_ref → IdentityContract (C-04)
        │                 anchor only, never duplicate
        │
        ├── protected_ref → ContinuityCheckpoint (C-06)
        │                   protection by reference
        │
        ▼
    Memory retrieval
        │
        ▼
     Context OS → ExperienceFrame → LLM
```

No paths exist for: Memory → ModelProvider direct, Memory → Identity overwrite, Memory → Conversation rewrite.

## 17. Forbidden Claims

```
❌ Every conversation becomes Memory
❌ Summary = Memory
❌ Memory = transcript
❌ Memory = Identity
❌ IdentityMemory as duplicate authority
❌ WorkingMemory as durable Memory type
❌ Memory owns world/domain knowledge
❌ Memory decides current Context visibility
❌ Memory writes directly to ModelProvider
❌ Memory automatically promotes to Identity
❌ Importance score determines Identity
❌ Importance score determines Continuity
❌ Later interpretation overwrites original experience
❌ Historical import creates memory automatically
❌ Runtime rules manufacture emotional/relationship meaning
```

## 18. Acceptance Gates

- [x] Memory OS = governed durable experience authority (§1)
- [x] Memory ≠ Conversation (§1)
- [x] Memory ≠ Identity (§1, §9)
- [x] Memory ≠ Context (§1, §12)
- [x] Memory ≠ Continuity (§1)
- [x] MemoryExperience canonical schema frozen (§2)
- [x] Five canonical experience types frozen (§3)
- [x] NarrativeExperience causal structure frozen (§3)
- [x] meaning_at_time + later reinterpretation model (§4)
- [x] Fact / interpretation distinction frozen (§11)
- [x] MemoryCandidate lifecycle frozen (§6)
- [x] Semantic candidate generation respects C-00 (§6)
- [x] Memory Governance responsibilities frozen (§6)
- [x] Memory Promotion Test frozen (§7)
- [x] Importance ≠ identity significance (§8)
- [x] Importance ≠ continuity priority (§8)
- [x] IdentityMemory removed/reclassified (§9)
- [x] WorkingMemory removed/reclassified (§9)
- [x] Broad SemanticMemory contracted to personal experience (§9)
- [x] Version/supersedence semantics frozen (§10)
- [x] Retrieval must re-enter Context OS (§12)
- [x] No direct Memory → ModelProvider path (§12)
- [x] Retention/privacy boundary frozen (§14)
- [x] Historical migration side-effect prohibition (§13)
- [x] P0-A memory-related paths dispositioned (§15)
- [x] AT-13 Narrative Causal Integrity supported (§3)
- [x] Production changes = 0

## 19. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §11
Depends: C-00 (07f0ff0), C-02 (656d625), C-03 (4b1625e), C-04 (433b674)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-06

C-05 FREEZE → C-06 Continuity OS GO
```
