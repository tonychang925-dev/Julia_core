# Phase Contract — K5.2 Governed Experience Artifact

Status: COMPLETE / APPROVED

## Objective

Convert K5.1 interaction patterns into a governed, versioned Experience State that can later be reconstructed into Context OS without becoming Memory, Persona, Identity, or prompt templates.

## Artifact

```text
artifacts/experience/julia_interaction_experience_v1.json
```

Core identity:

```json
{
  "artifact_id": "julia.interaction_experience",
  "version": "v1"
}
```

## What Experience Artifact Must Not Store

```text
❌ raw conversation
❌ persona facts
❌ relationship facts as authority
❌ fixed answer templates
❌ provider-specific prompts
```

## What It Stores

```text
trigger patterns
behavior tendencies
avoid modes
confidence
coverage/stability/transfer scores
supporting pattern refs
```

## Experience Scores

- Experience Coverage Score — whether key interaction types are covered.
- Experience Stability Score — consistency proxy across extracted patterns.
- Experience Transfer Score — expected provider-independent portability.
- Interaction Coherence Density — behavior texture reconstruction proxy.

## Context OS Interface

```text
Experience Artifact
    ↓
ExperienceContextBlock
    ↓
Context OS
    ↓
Provider
```

Provider does not read the artifact directly.

## Governance Boundary

```json
{
  "mutates_identity": false,
  "mutates_persona": false,
  "writes_memory": false,
  "stores_raw_chat": false,
  "stores_fixed_answer_templates": false,
  "provider_reads_artifact_directly": false,
  "requires_review": true
}
```

## Acceptance

- Pattern → Artifact conversion works.
- Artifact is versioned.
- Four experience dimensions exist.
- Governance boundary is explicit.
- Context block can be built for a query.
- Context block carries guidance, not raw conversation.
- Provider independence boundary is preserved.
