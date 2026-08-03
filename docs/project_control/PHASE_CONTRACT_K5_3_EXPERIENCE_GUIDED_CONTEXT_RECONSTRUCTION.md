# Phase Contract — K5.3 Experience-guided Context Reconstruction

Status: COMPLETE / APPROVED

## Objective

Use governed Experience Artifact as a Context OS shaping factor.

K5.3 explicitly does not generate Julia responses from Experience. It reconstructs an `ExperienceContextBlock` that Provider may consume only through Context OS.

## Correct Flow

```text
User Input
    ↓
ExperienceContextReconstructor
    ↓
ExperienceContextCandidate
    ↓
ExperienceContextBlock
    ↓
Context OS
    ↓
Provider
```

## Implemented Components

```text
julia_core/experience/reconstruction.py
```

Objects:

```text
ExperienceRetrievalRequest
ExperienceContextCandidate
ExperienceContextReconstruction
ExperienceContextReconstructor
```

## Boundary

```json
{
  "experience_generates_response": false,
  "experience_mutates_identity": false,
  "experience_mutates_persona": false,
  "experience_writes_memory": false,
  "provider_reads_experience_artifact": false,
  "context_os_required": true
}
```

## Required Cases

- ER-001 Identity Question
- ER-002 Correction
- ER-003 Project Collaboration
- ER-004 Relationship Boundary

## Acceptance

- Identity-transfer question selects `identity_question`.
- Correction question selects `correction`.
- Project continuation selects `collaboration`.
- Relationship challenge selects `relationship_boundary`.
- Ordinary unrelated input has no high influence.
- Reconstruction output is a ContextBlock, not a response.
