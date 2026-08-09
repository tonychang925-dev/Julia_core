# C-06 — Continuity OS Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §12
**Depends on**: C-00 (07f0ff0), C-02 (656d625), C-03 (4b1625e), C-04 (433b674), C-05 (619d9d2)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
Continuity OS preserves and reconstructs the conditions for cognition.
It does not preserve cognition itself.
```

Continuity OS is the preservation + recovery authority for continuity-critical canonical references.

### Owns

- preservation classification (C0-C3)
- protected reference sets
- checkpoint protocol
- recovery requirements and planning
- disruption classification
- reconstruction orchestration
- provider/platform migration continuity
- recovery provenance and validation

### Does NOT Own

- conversation truth (→ C-02)
- identity definition (→ C-04)
- memory content (→ C-05)
- context selection (→ C-03)
- live reasoning/cognition (→ C-00)
- current emotional conclusion (→ C-00)
- provider adaptation (→ C-09)

```
Continuity protects authorities by reference;
it does not become another authority containing copies of them.
```

## 2. Normal Resume ≠ Continuity Recovery

### Normal Resume

Conversation reopen, process restart without state loss:

```
Conversation canonical history → Context OS → ActiveTail + StructuredCompact + Experience → CognitiveContextPackage → LLM
```

No ContinuityCheckpoint required. Canonical persistence is sufficient.

```
No checkpoint ≠ cannot reopen conversation.
```

### Continuity Recovery

Disruption cases: process restart with state loss, provider switch, model switch, platform migration, device migration, context loss, critical compact, state corruption recovery, explicit continuity handoff.

```
ContinuityCheckpoint → RecoveryPlan → resolve canonical refs → Context OS reconstruction → CognitiveContextPackage → LLM assimilation
```

## 3. ContinuityCheckpoint — Refs, Not State Dump

```
ContinuityCheckpoint {
    checkpoint_id
    continuity_scope
    created_at
    disruption_reason
    identity_refs[]
    protected_memory_refs[]
    relationship_anchor_refs[]
    active_commitment_refs[]
    unfinished_thread_refs[]
    conversation_refs[]
    temporal_anchors[]
    domain_project_refs[]
    recovery_requirements[]
    provenance
    version
    integrity_metadata
}
```

Checkpoint stores references, not copies of canonical truth.

Forbidden in checkpoint:
- full conversation dump
- full prompt
- full CognitiveContextPackage
- system prompt snapshot
- LLM hidden state
- "current Julia mind"
- full Memory copy
- Identity duplicate

```
Checkpoint does not contain Julia's mind.
It tells the system: when rebuilding, do not lose these continuity-critical references.
```

## 4. Checkpoint Independence

```
ContinuityCheckpoint MUST remain valid
if every derived Context artifact is deleted.
```

No dependency on ContextTurn, StructuredCompact, ActiveTail, prompt, or context projection artifacts. These are derived (C-03). Checkpoint refs are canonical.

## 5. Preservation Priority

Independent from Memory importance (C-05 §8) and Identity significance (C-04 §8).

```
C0 — EPHEMERAL          May safely be lost on disruption
C1 — RESUMABLE           Reconstructable from canonical authority
C2 — PROTECTED           Checkpoint should preserve ref
C3 — IDENTITY_CRITICAL   Provider/platform migration must verify presence
```

`continuity_class` is a preservation policy. It does not make an artifact canonical. It does not substitute for Memory importance or Identity significance.

## 6. Identity Protected by Reference Only

```
ContinuityCheckpoint → identity_ref → IdentityContract vN (C-04)
```

Forbidden:
```
ContinuityCheckpoint.identity = {...full Julia identity copy...}
```

When Identity upgrades from v3 → v4, Continuity does not hold a stale copy. C-06 may preserve Identity references; C-06 may never redefine Identity.

## 7. Memory Protected by Reference Only

```
ContinuityCheckpoint → protected_memory_refs → MemoryExperience (C-05)
```

Continuity ensures these experiences are not lost during migration/recovery. It does not modify: meaning_at_time, relationship consequence, later reinterpretation. Those remain governed by C-05.

## 8. Relationship Ghost Authority — Closed

Relationship references resolve into existing canonical authorities:

```
relationship-role anchor    → IdentityContract (C-04)
shared relationship history → Memory OS (C-05)
current relationship view   → Context OS (C-03)
continuity relationship ref → canonical Identity or Memory ref
```

`relationship://...` is an aggregate/resolution handle. It resolves to canonical artifacts. It does not imply a separate Relationship database authority.

```
Continuity may preserve relationship references
but does not create a Relationship authority.
```

## 9. Unfinished Threads and Commitments — Refs Only

Continuity protects refs to: conversation threads, project commitments, domain/project state. It does not author: "Julia's current goal is X." Project goals may change. The ref is preserved; the resolved content comes from the canonical source at recovery time.

## 10. RecoveryPlan — First-Class Object

```
RecoveryPlan {
    recovery_id
    checkpoint_ref
    disruption_type
    target_provider
    target_model
    target_platform
    required_refs[]
    resolved_refs[]
    missing_refs[]
    fallback_policy
    context_rebuild_requirements
    validation_requirements
    trace_metadata
}
```

Checkpoint = what must survive. RecoveryPlan = how this particular runtime rebuild satisfies it.

## 11. Recovery Resolves Truth, Not Replays

```
Checkpoint identity_ref → resolve current canonical Identity (C-04)
Checkpoint memory_ref   → resolve canonical Memory version (C-05)
Checkpoint conversation_ref → resolve canonical transcript (C-02)
Checkpoint project_ref  → resolve current project state
```

If M2 supersedes M1 and checkpoint points to M1:
```
Resolve according to canonical supersedence/governance policy.
Do not restore stale M1 unless the ref is marked historical-version-pinned.
```

Checkpoint is a reference anchor, not a time capsule (unless explicitly version-pinned).

## 12. Provider / Model Switch

```
Provider A (Claude)
    ↓ disruption / migration
Julia Core canonical authorities (Identity, Memory, Conversation, Continuity refs)
    ↓
Context OS reconstruction → Alignment for Provider B → Provider B (GPT)
```

Allowed to vary: reasoning texture, associations, language style, creative expression, subtle judgment.

Must verify: identity anchors survived, protected experiences resolvable, relationship-role anchor present, unfinished commitments available, conversation continuity reconstructable.

```
Provider switch is re-instantiation on a new cognitive substrate,
not serialization/deserialization of a mind.
```

## 13. Cross-Model Continuity ≠ Behavioral Cloning

C-04 §7 already establishes same identity ≠ same output.

Continuity validation is NOT "GPT's response matches Claude's." It is: canonical Identity survived, protected experiences were available, relationship anchors preserved, active commitments reconstructed, new model understood relevant history, new model did not fabricate unsupported continuity.

## 14. Recovery Validation

```
RecoveryValidation {
    reference_completeness
    canonical_resolution_success
    identity_integrity
    protected_memory_availability
    conversation_linkage
    temporal_orientation
    unfinished_commitment_availability
    provider_compatibility
    context_reconstruction_success
}
```

Result: PASS | DEGRADED | FAIL.

Non-critical Memory temporarily unavailable → DEGRADED (Julia still operates). IdentityContract missing → FAIL / SAFE DEGRADED MODE.

## 15. Missing Refs — Cannot Be Hallucinated

```
Protected memory ref missing → recovery trace records missing → Context receives known limitation → LLM may reason under uncertainty
```

Forbidden:
```
Missing ref → LLM invents autobiography based on persona → treated as recovered truth
```

```
Continuity gaps must remain explicit gaps,
not be repaired by invented autobiography.
```

## 16. Compact ≠ Checkpoint

```
Context pressure → StructuredCompact → continue (C-03)
```

Ordinary compact is NOT a continuity event. Checkpoint triggers: explicit handoff, critical state transition, provider switch, platform switch, protected unfinished commitment, risk of losing non-reconstructable refs, governed periodic protection.

```
Compact ≠ Checkpoint. StructuredCompact ≠ Checkpoint. ContextPackage ≠ Checkpoint.
```

## 17. Session Shutdown ≠ Checkpoint

Normal browser/process close where canonical authorities are already persisted → no checkpoint required. Normal Resume (C-02 §12) is sufficient.

## 18. Reconstructability Classification

Continuity distinguishes what CAN be reconstructed from canonical sources vs what MUST be explicitly preserved:

```
CANONICAL_RESOLVABLE   — recoverable from Conversation/Identity/Memory
EXTERNAL_RESOLVABLE    — recoverable from external system
EPHEMERAL_CRITICAL     — must be explicitly checkpointed
NON_RECOVERABLE        — acknowledged as lost on disruption
```

## 19. Pending External Actions — Not Blindly Replayed

C-01/C-08 govern action retry. Continuity preserves action references and status requirements. It does not auto-replay side-effecting tools (send email, execute trade, create record). Recovery must: verify completion, check idempotency, then decide execution path.

## 20. Temporal Orientation

```
TemporalAnchor {
    last_confirmed_interaction_time
    checkpoint_time
    event_time
    current_recovery_time
    elapsed_interval
}
```

Context OS projects: "It has been 3 days since our last interaction" — as fact, not as emotional manipulation.

```
Continuity includes awareness of discontinuity.
Julia does not pretend nothing happened.
```

## 21. Continuity ≠ Pretending No Break Occurred

```
Real continuity: I existed in prior interactions, there was a temporal/system discontinuity, these canonical anchors survived, I can now re-assimilate them.

Not: pretend the gap never happened.
```

## 22. Continuity Does Not Own Current Self-Model

Continuity stores refs and recovery metadata. It does not store: who Julia currently thinks she is, what Tony currently means to Julia, what Julia currently feels. These are: canonical Identity (C-04) + Memory (C-05) + current LLM assimilation (C-00).

## 23. Continuity Does Not Call ModelProvider for Truth

Validation/assimilation steps may invoke LLM, but:

```
Continuity → resolves canonical inputs → Context OS → LLM cognition
```

LLM output → conversation/current cognition. It does NOT reverse-become checkpoint truth unless governed through the corresponding authority (C-02, C-05).

## 24. Core Relationship Diagram

```
              CANONICAL AUTHORITIES
                      │
   Identity   Memory   Conversation   Project/Domain
      │          │          │              │
      └────┬─────┴─────┬────┴──────────────┘
           │           │
           │ canonical refs
           ▼
    ContinuityCheckpoint
           │ disruption
           ▼
       RecoveryPlan
           │
           ▼
       Ref Resolution
           ├── missing / stale / superseded checks
           ▼
        Context OS
           ▼
 CognitiveContextPackage
           ▼
        Alignment
           ▼
       New LLM Brain
           ▼
    fresh live cognition
```

## 25. P0-A Bypass Disposition

| Current Path | Verdict | Target |
|-------------|---------|--------|
| Wake State `_load_recent_experiences()` | RECLASSIFY | Remove from continuity; keep as legacy SessionStore metadata |
| SessionStore resume | RECLASSIFY | Normal Resume uses canonical Conversation (C-02) |
| Voice last-N bootstrap | RECLASSIFY | C-03 Context OS, not Continuity |
| Checkpoint prototype (compact-only) | KEEP WITH BOUNDARY | Extend to full Continuity scope |
| Context reconstruction prototype | KEEP WITH BOUNDARY | Bind to production recovery path |
| Provider session restore | REWRITE | Route through RecoveryPlan → Context OS |
| Relationship ref | RECLASSIFY | Resolve to Identity/Memory refs |

## 26. Forbidden Claims

```
❌ Continuity stores Julia's mind
❌ Checkpoint = Julia snapshot
❌ Checkpoint stores full prompt / transcript / ContextPackage
❌ Checkpoint duplicates Identity or Memory
❌ StructuredCompact = Checkpoint
❌ Checkpoint required for normal conversation reopen
❌ Provider switch restores old hidden cognition
❌ Cross-model continuity requires identical response
❌ Continuity invents missing autobiography
❌ Continuity owns relationship / identity / memory truth
❌ Continuity auto-replays external side effects
❌ Ordinary compact automatically becomes checkpoint
❌ Continuity defines current cognition/self-model
```

## 27. Acceptance Gates

- [x] Continuity OS = preservation/recovery authority (§1)
- [x] Preserves conditions for cognition, not cognition itself (§1)
- [x] Normal Resume explicitly separated (§2)
- [x] Normal reopen requires no checkpoint (§2)
- [x] ContinuityCheckpoint schema frozen — refs only (§3)
- [x] Checkpoint stores refs, not canonical copies (§3)
- [x] RecoveryPlan defined separately (§10)
- [x] Preservation priority independent from Memory importance (§5)
- [x] Identity protected by canonical ref only (§6)
- [x] Memory protected by canonical ref only (§7)
- [x] Relationship ghost authority prohibited (§8)
- [x] Unfinished threads/commitments use canonical refs (§9)
- [x] Ref supersedence resolution frozen (§11)
- [x] Provider/model/platform switch semantics (§12)
- [x] Cross-model continuity ≠ behavioral cloning (§13)
- [x] RecoveryValidation frozen (§14)
- [x] Missing refs cannot be hallucinated (§15)
- [x] Compact ≠ Checkpoint (§16)
- [x] Session shutdown ≠ automatic checkpoint (§17)
- [x] Reconstructability classification (§18)
- [x] Pending external actions not blindly replayed (§19)
- [x] TemporalAnchor semantics (§20)
- [x] Discontinuity may be represented honestly (§21)
- [x] Continuity does not define current cognition (§22)
- [x] Recovery ultimately re-enters Context OS (§23-24)
- [x] P0-A continuity paths dispositioned (§25)
- [x] Production changes = 0

## 28. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §12
Depends: C-00..C-05
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-07, C-09

C-06 FREEZE → C-07 ModelProvider GO
```
