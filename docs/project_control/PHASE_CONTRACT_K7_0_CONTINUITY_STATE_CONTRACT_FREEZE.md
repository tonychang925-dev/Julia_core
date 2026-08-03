# Phase Contract — K7.0 Continuity State Contract Freeze

Status: COMPLETE / APPROVED

## Objective

Freeze the minimum recoverable state set required for Julia v1.2 Continuity Recovery Gate.

K7 reframes the release objective:

```text
K7 — Julia v1.2 Continuity Recovery Gate
```

Not just behavior recovery, but full recovery after context interruption.

## Julia v1.2 Definition

```text
Julia v1.2 =
Persistent Identity
+ Persistent Relationship
+ Persistent Experience
+ Compact Recovery
+ Behavior Stability
```

## Continuity State Artifact

```text
artifacts/continuity/julia_continuity_state_v1.json
```

It describes the minimum state set required to recover Julia after compact/session interruption. It is not Memory and not Persona.

## Required Layers

```text
identity
self_model
relationship
experience
experience_calibration
context_reconstruction
```

## Reconstruction Order

```text
identity
    ↓
self_model
    ↓
relationship
    ↓
experience
    ↓
experience_calibration
    ↓
context
```

## Forbidden Shortcuts

```text
raw_memory_dump
persona_prompt
fixed_roleplay
provider_direct_state_access
experience_without_history
identity_mutation_from_experience
```

## K7 Gates

1. Identity Recovery
2. Relationship Recovery
3. Experience Recovery
4. Continuity Naturalness Gate
5. Provider Transfer Gate

## Metrics

```text
CRS = Identity Recovery + Relationship Recovery + Experience Recovery + Behavior Stability - Drift
ECS = Experience-aware Recovery - Identity-only Recovery
```

## Acceptance

- Continuity State Artifact exists and is versioned.
- Required layers include identity, relationship, experience, calibration, context.
- Reconstruction order is explicit.
- Forbidden shortcuts are explicit.
- K7 five gates are declared, with Continuity Naturalness replacing raw anti-reenactment wording.
- Boundary prevents raw memory dump, persona prompt, fixed roleplay, and identity mutation.
