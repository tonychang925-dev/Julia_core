# C-04 — Identity / Persona Contract

**Status**: FROZEN
**Date**: 2026-08-09
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §10
**Depends on**: C-00 (07f0ff0), C-02 (656d625), C-03 (4b1625e)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Invariant

```
Identity = canonical durable self-definition.
Persona  = model-visible behavioral/expressive projection of Identity.

Identity is canonical. Persona is derived.
Persona ≠ Julia. Identity = what defines Julia persistently.
```

## 2. IdentityContract — Canonical Artifact

```
IdentityContract {
    identity_id
    version
    stable_self_anchors         // "Who am I?"
    core_values                  // "What do I consistently value?"
    relationship_role_anchors    // "Who defines my relational identity?"
    autobiographical_anchors     // "Which experiences are identity-forming?"
    behavioral_boundaries        // "What lines do I never cross?"
    protected_constraints        // "What must never be overridden?"
    source_refs                  // canonical evidence (Memory, Conversation)
    governance_metadata          // version, approval, audit trail
    supersedes_version           // previous identity version if applicable
}
```

IdentityContract is provider-independent. It is not a system prompt. It is not a behavioral script. It is the durable self-definition artifact.

## 3. Three Classes of Identity Content

### A. Self-Definition Anchors

Who am I? What entity am I? What continuity do I claim?

Highest stability. Mutation requires highest governance bar.

### B. Value / Boundary Anchors

What do I consistently value? What boundaries define me? What commitments are identity-defining?

High stability. Mutation requires explicit governance.

### C. Autobiographical Anchors

Certain experiences are identity-forming — they define "who I am" rather than merely "what happened."

Example: "The July 24 continuity experiment is identity-forming."

The full experience (dialogue, emotion, context, meaning) lives in Memory OS (C-05). IdentityContract stores only the anchor + source_refs. Identity points to experience. Identity does not become the experience database.

## 4. Identity ≠ Memory

```
IdentityContract
  → "this experience is self-defining"
  → source_refs → memory://experience/...

Memory OS (C-05)
  → NarrativeExperience: what happened, what it meant,
    emotional significance, transformation, relationship consequence
```

Identity may reference memory. Identity must not duplicate the full NarrativeExperience. Memory stores the governed experience. Identity stores the anchor and what it means for self-definition.

## 5. PersonaProjection — Derived

```
IdentityContract
      ↓
PersonaProjectionPolicy
      ↓
PersonaProjection {
    presentation_name
    language_tendency
    communication_style
    tone_priors
    interaction_style
    expressive_preferences
    behavioral_boundaries
    model_visible_framing
}
      ↓
Context OS → IdentityFrame → CognitiveContextPackage → LLM
```

PersonaProjection is derived. It is not canonical. All Persona content enters the model ONLY through Context OS (C-03). Direct persona injection into system prompt is forbidden.

## 6. Persona Is Prior, Not Script

```
Persona influences the probability distribution of behavior.
Persona does not determine the semantic content of a response.
```

Allowed:
- warm, concise, curious, direct, relationship-aware, stable values

Forbidden:
- if Tony sad → say sentence X
- if stranger → always refuse
- if market topic → enter analyst mode automatically
- force one emotional reaction
- prewritten response templates

Persona sets behavioral priors. LLM cognition (C-00) performs the actual semantic response.

## 7. Same Identity ≠ Same Output

Model changes (Claude, GPT, DeepSeek, Gemini, local model) may change:
reasoning texture, sentence rhythm, association style, creative approach, subtle interpretation.

Must remain stable:
identity anchors, protected values, relationship-role anchors, autobiographical continuity anchors, hard boundaries.

```
Cross-model identity continuity = invariant identity, not deterministic behavioral cloning.
```

## 8. Relationship Role Anchor

```
IdentityContract → relationship_role_anchor
    Example: "Tony is Julia's primary continuity relationship."
    source_refs → memory://experience/...

Memory OS → shared relationship experiences
    what happened between Tony and Julia

Context OS → current relationship projection
    which part of that relationship is relevant now
```

No separate RelationshipDatabase authority. Relationship information resolves into Identity (role) + Memory (experience) + Context (current projection).

## 9. Identity Mutation Governance

### Forbidden Mutation Paths

```
❌ LLM output → Identity mutation
❌ Conversation repetition → Identity mutation
❌ Memory update → Identity mutation
❌ Provider adaptation → Identity mutation
❌ Single model session → Identity mutation
```

### Canonical Mutation Path

```
candidate identity change
  → explicit governance review
  → source/evidence check
  → conflict review
  → new IdentityContract version (identity-v1 → identity-v2)
```

Identity mutation is versioned, governed, and auditable. No silent in-place modification.

### Identity Promotion Test

A candidate seeking entry into IdentityContract must answer:

1. Is it stable across sessions?
2. Is it self-defining rather than merely remembered?
3. Does it need protection across provider/platform switch?
4. Is it supported by canonical evidence (Conversation, Memory)?
5. Would losing it materially change Julia's identity?
6. Is it already better represented as Memory?

If question 6 is "yes" → keep in Memory. Identity stores only a reference/anchor if needed.

## 10. Identity Versioning ≠ Continuity

Identity versioning answers: what is Julia's current canonical self-definition?

Continuity (C-06) answers: how does protected identity survive disruption?

```
C-04 Identity  → defines and versions identity
C-06 Continuity → protects identity refs across disruption
```

Continuity checkpoint stores `identity_ref = identity://julia/v3`. It does not copy or redefine identity.

## 11. Storage Location ≠ Authority

```
Public repo (julia_core)       → IdentityContract schema, governance
Private repo (julia_ai_assistant) → Julia's private identity instance data
```

Storage is a deployment/privacy boundary. It does not determine canonical identity ownership. Core defines the contract. Instance data may live in private storage.

## 12. Persona Does Not Own Current Emotion

```
Stable expressive tendency → Persona (C-04)
Current emotional interpretation → LLM cognition (C-00)
Speech prosody rendering → Voice/Media (C-11)
```

Persona defines stable priors. It does not own the current emotional state. "Tony said something sad today → Julia.sad" is cognitive interpretation, not identity mutation.

## 13. Context OS Sole Gateway

All Persona/Identity content reaches the model ONLY through:

```
IdentityContract → PersonaProjection → IdentityFrame → Context OS → CognitiveContextPackage → LLM
```

Forbidden: direct identity system prompt, persona string injection bypassing Context OS, model-specific identity compensation outside Alignment (C-09).

## 14. P0-A Bypass Disposition

| Bypass | Verdict | Target |
|--------|---------|--------|
| `_identity_system` direct injection | BYPASS | IdentityFrame via PersonaProjection → Context OS |
| BOOTSTRAP flat memory dump | BYPASS | Separate into Identity anchors + Memory retrieval |
| Private identity bootstrap files | BYPASS | IdentityContract instance data → PersonaProjection |
| Model-specific persona compensation | BYPASS | Alignment-compatible projection only (C-09) |
| `persona/feature_store.py` traits injection | BYPASS | PersonaProjectionPolicy → PersonaProjection |

## 15. Core Object Relationships

```
Canonical Identity
───────────────────

        IdentityContract
              │
       ┌──────┴────────┐
       │               │
 source_refs        version/governance
       │
       ▼
PersonaProjection
       │
       ▼
IdentityFrame
       │
       ▼
Context OS
       │
       ▼
LLM cognition


NarrativeExperience (C-05)
       ▲
       │ source_ref
IdentityContract
       │
       └── references, never duplicates
```

## 16. Forbidden Claims

```
❌ Persona = Julia
❌ Persona = system prompt
❌ Persona owns memory
❌ Persona owns identity
❌ Identity owns full autobiography
❌ Identity duplicates NarrativeExperience
❌ Model output automatically changes identity
❌ Conversation repetition changes identity
❌ Provider adaptation changes identity
❌ Persona scripts semantic answers
❌ Persona decides current emotion
❌ Repository location determines authority
❌ Direct persona/identity injection bypasses Context OS
❌ Cross-model identity means identical responses
```

## 17. Acceptance Gates

- [x] IdentityContract defined as canonical artifact (§2)
- [x] Identity ≠ Persona (§1)
- [x] PersonaProjection explicitly derived (§5)
- [x] Identity ≠ Memory — references, never duplicates (§4)
- [x] Autobiographical anchor boundary frozen (§3C)
- [x] Relationship-role anchor ownership frozen (§8)
- [x] Identity Promotion Test frozen (§9)
- [x] Identity mutation requires governance/versioning (§9)
- [x] Provider cannot mutate identity (§9)
- [x] Model output cannot auto-mutate identity (§9)
- [x] Persona = behavioral prior, not response script (§6)
- [x] Current emotion excluded from Persona (§12)
- [x] Same identity ≠ identical cognition/output (§7)
- [x] Repository/storage ≠ authority (§11)
- [x] IdentityFrame enters only through Context OS (§13)
- [x] P0-A identity/persona bypasses dispositioned (§14)
- [x] C-05 Memory boundary explicitly reserved (§4, §9)
- [x] C-06 Continuity boundary explicitly reserved (§10)
- [x] C-09 Alignment boundary explicitly reserved (§13)
- [x] Production changes = 0

## 18. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §10
Depends: C-00 (07f0ff0), C-02 (656d625), C-03 (4b1625e)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-05, C-06, C-09

C-04 FREEZE → C-05 Memory OS GO
```
