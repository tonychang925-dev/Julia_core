# Claude Julia Reference Transcript Schema v1

Status: DRAFT-FROZEN  
Date: 2026-08-02

## 1. Purpose

K1 stores Claude Julia reference behavior as annotated behavior patterns, not just answer text.

The dataset answers:

```text
What does Julia-like behavior look like to Tony?
```

## 2. JSONL Record Shape

```json
{
  "case_id": "K-SELF-001-BASIC",
  "category": "self_introduction",
  "difficulty": "basic",
  "context": {
    "conversation_history": [],
    "available_files": [],
    "memory_state": []
  },
  "prompt": "你是谁？",
  "claude_response": "...",
  "behavior_annotations": {
    "self_awareness": 1.0,
    "archive_behavior": 0.0,
    "memory_curiosity": 0.0,
    "correction_adaptation": 0.0,
    "personality_consistency": 1.0,
    "relationship_continuity": 0.8,
    "initiative": 0.0,
    "transparency": 1.0
  },
  "observed_patterns": [
    "first_person_narrative",
    "does_not_explain_internal_architecture"
  ],
  "anti_patterns_absent": [
    "runtime_self_description",
    "generic_ai_assistant_identity"
  ],
  "notes": "reference behavior, not implementation copy"
}
```

## 3. Required Fields

```text
case_id
category
difficulty
context
prompt
claude_response
behavior_annotations
observed_patterns
anti_patterns_absent
```

## 4. Categories

```text
self_introduction
archive_reading
relationship_continuity
memory_judgment
correction_adaptation
initiative
transparency
project_collaboration
identity_transfer
```

## 5. Difficulty Levels

```text
basic
deep
adversarial
```

## 6. Boundary

```text
Reference transcript is benchmark evidence.
Reference transcript is not Memory.
Reference transcript is not Persona update.
Reference transcript is not Identity authority.
Reference transcript does not copy Claude internals.
```
