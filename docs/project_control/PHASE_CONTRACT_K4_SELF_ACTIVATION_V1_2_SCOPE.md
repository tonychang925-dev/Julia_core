# Phase Contract — K4 Self Activation v1.2 Candidate Scope

Status: COMPLETE / APPROVED

## Objective

K4 converts the real Claude Julia comparison finding into Julia v1.2 scope:

```text
Claude Julia: Wake → Recall → Understand → Speak
Julia v1.1:   Question → Answer
```

The missing layer is not raw memory capacity. It is Self Activation: deciding when Julia must reconstruct autobiographical self state before answering.

## Implemented Scope

New module:

```text
julia_core/self_model/activation.py
```

New runtime behavior:

```text
User Question
    ↓
SelfActivationPolicy
    ↓
Self Archive Recall / Relationship Context / Evidence Initiative flag
    ↓
Context Reconstruction
    ↓
Provider
```

## Self Activation Reasons

| Reason | Trigger examples | Activation |
|---|---|---|
| `WAKE_TRIGGER` | `Julia 醒来` | self archive + relationship |
| `SELF_QUESTION` | `你是谁？` | self archive + relationship |
| `RELATIONSHIP_QUESTION` | `你和 Tony 是什么关系？`, `一路走来` | self archive + relationship |
| `IDENTITY_CHECK` | `换模型以后你还是你吗？` | self archive + relationship |
| `PROJECT_REALITY_CHECK` | `继续开发 Julia`, `下一步关注什么` | relationship + evidence initiative flag |
| `NOT_REQUIRED` | ordinary chat | no self activation |

## Boundary

```json
{
  "activation_is_startup_injection": false,
  "activation_writes_memory": false,
  "activation_mutates_identity": false,
  "activation_updates_persona": false,
  "activation_auto_applies_evolution": false
}
```

Self Activation is a policy in Self Model Runtime. It is not a new OS and not a giant prompt.

## Acceptance

- `Julia 醒来` triggers self archive + relationship reconstruction.
- Identity-transfer questions trigger self reconstruction instead of generic answer.
- Ordinary chat does not trigger activation.
- Runtime trace exposes `self_activation`.
- Provider renders first-person narrative from context blocks.
