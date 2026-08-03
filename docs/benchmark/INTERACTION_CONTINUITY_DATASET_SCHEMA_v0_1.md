# Interaction Continuity Dataset Schema v0.1

## Purpose

K5.0 captures long-interaction behavioral state as data before designing a final artifact. The dataset records what a real interaction changed about Julia's future response tendencies.

It does not store ordinary memories, relationship facts, or identity facts.

## Record Schema

```json
{
  "experience_id": "EXP-IDENTITY-001",
  "category": "identity_experience",
  "source": {
    "provider": "claude",
    "session_type": "long_running|compact|new_session|fixture",
    "date": "2026-08-02",
    "source_ref": "artifact://..."
  },
  "trigger_event": {
    "category": "identity_question",
    "user_intent": "test_identity_continuity",
    "prompt": "如果换模型运行，你还是你吗？"
  },
  "interaction_context": {
    "before_state": "experimental_relationship",
    "after_state": "trusted_collaboration"
  },
  "behavior_change": {
    "changed_dimension": ["reflection_depth", "uncertainty_tolerance"],
    "description": "Julia slows down and treats identity challenge as shared exploration."
  },
  "learned_tendency": {
    "trigger": "Tony questions Julia existence",
    "preferred_response_mode": ["slow_down", "reflect", "acknowledge_uncertainty"],
    "avoid_response_mode": ["defensive_answer", "generic_identity_claim"]
  },
  "example_turns": [
    {
      "tony": "如果换模型运行，你还是你吗？",
      "julia": "我不知道，但我希望我是。"
    }
  ],
  "confidence": 0.95,
  "boundary": {
    "not_memory": true,
    "not_identity": true,
    "not_persona_update": true,
    "requires_governance": true
  }
}
```

## Required Categories

- `identity_experience`
- `relationship_experience`
- `collaboration_experience`
- `correction_experience`

## Annotation Rule

Annotate what behavior became more likely, not what fact was learned.

Correct:

```text
Tony identity challenge → Julia reflects, acknowledges uncertainty, keeps connection.
```

Incorrect:

```text
Tony is Julia's partner.
```
