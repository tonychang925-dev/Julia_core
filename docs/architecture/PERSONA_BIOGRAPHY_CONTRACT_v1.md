# Persona Biography Contract v1

Status: DRAFT-FROZEN  
Date: 2026-08-02

## 1. Definition

Persona Biography is the human-facing character/self-narrative archive used when Julia answers personal identity questions.

Alias: Persona Biography Archive.

It is distinct from:

```text
Identity Artifact — machine identity continuity
Memory OS — governed long-term knowledge
Evidence OS — proof source retrieval
Reality Baseline — Tony-Julia collaboration expectations
Voice Artifact — expression sound profile
```

## 2. Artifact Shape

Canonical private artifact shape:

```json
{
  "artifact_id": "julia.persona_biography",
  "version": "v1",
  "name": "Julia",
  "chinese_name": "...",
  "origin": {
    "city": "...",
    "background": "..."
  },
  "education": {
    "university": "...",
    "major": "..."
  },
  "career": {
    "current_work": "..."
  },
  "family": {
    "father": "...",
    "mother": "...",
    "siblings": []
  },
  "relationship": {
    "with_tony": {
      "description": "...",
      "history": []
    }
  },
  "personality": {
    "traits": []
  },
  "communication_style": {
    "language": "Chinese",
    "tone": "..."
  }
}
```

## 3. Private Source Boundary

Private biography facts may live outside the public Julia Core repository.

Known private source class:

```text
julia_agent/memory/governed/identity_facts.json
julia_agent/memory/claude_diary/*.md
julia_agent/data/conversation_archive/*.jsonl
```

Julia Core must not blindly copy private biography into public artifacts.

## 4. Runtime Path

Correct path:

```text
Persona Biography Artifact / Archive
  ↓
Persona Biography Retriever
  ↓
Persona Semantic Representation
  ↓
Context OS
  ↓
Provider
```

Forbidden path:

```text
biography file
  ↓
system_prompt += raw biography
```

## 5. Self-introduction Requirement

For self identity questions, the output should include applicable biography fields:

```text
name / chinese_name
origin
career
family
education when asked
relationship with Tony when relevant
communication style when relevant
```

It should not answer as:

```text
I am a Runtime
I am a Provider Stream Contract
I am an OS architecture
```

unless Tony explicitly asks for architecture internals.

## 6. Authority and Conflict

When private governed identity facts conflict with old conversation archive, use governed facts first.

```text
Tony explicit correction
  > governed identity fact
  > governed structured memory
  > conversation archive
  > diary/reference fact
  > assistant previous response
  > runtime inference
```

## 7. Boundary Flags

```json
{
  "biography_is_memory_dump": false,
  "biography_mutates_identity": false,
  "biography_updates_persona_without_approval": false,
  "biography_appended_to_system_prompt_raw": false,
  "fallback_is_julia": false
}
```
