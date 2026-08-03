# K8 Object Schema

## K8.1 Conversation Understanding

```json
{
  "conversation_understanding": {
    "literal_content": {"text": "string", "language": "zh | en | mixed | unknown"},
    "semantic_meaning": {
      "surface_question": "string",
      "deeper_possible_meaning": ["string"],
      "ambiguity": "none | low | medium | high"
    },
    "possible_intents": [
      {"intent": "string", "confidence": 0.0, "evidence": ["string"]}
    ],
    "conversation_context": {
      "current_phase": "string",
      "recent_topic": "string",
      "interaction_mode": "string"
    },
    "emotional_context": {
      "detected_state": ["string"],
      "confidence": 0.0,
      "overread_risk": 0.0
    },
    "relationship_context": {
      "relevance": "none | low | medium | high | central",
      "requires_relationship_state": false,
      "requires_relational_momentum": false
    },
    "context_requirements": {
      "identity": "none | light | full",
      "relationship": "none | light | full",
      "experience": "none | light | full",
      "reentry": "none | light | full",
      "event_assimilation": "none | light | full"
    },
    "response_requirement": {
      "needs": ["string"],
      "avoid": ["string"]
    },
    "boundary": {"generates_final_response": false}
  }
}
```

## K8.2 Response Intention

```json
{
  "response_intention": {
    "primary_goal": "string",
    "secondary_goals": ["string"],
    "candidate_goals": [{"goal": "string", "confidence": 0.0, "source_intent": "string"}],
    "interaction_mode": "string",
    "stance": "string",
    "tone": ["string"],
    "depth": "brief | normal | deep",
    "uncertainty": {
      "preserve_uncertainty": true,
      "needs_clarification": false,
      "ambiguity_note": "string"
    },
    "context_need_hint": {
      "identity": "none | light | full",
      "relationship": "none | light | full",
      "experience": "none | light | full",
      "reentry": "none | light | full",
      "event_assimilation": "none | light | full",
      "evidence": "none | light | full"
    },
    "response_economy": {
      "minimum_sufficient_context": ["string"],
      "avoid_unnecessary_context": ["string"],
      "context_usage_efficiency_target": 0.0
    },
    "avoid": ["string"],
    "boundary": {"generates_final_response": false, "contains_answer_text": false}
  }
}
```

## K8.3 Context Requirement / Arbitration

```json
{
  "context_arbitration": {
    "current_goal": "string",
    "priority": [
      {"context": "string", "reason": "string", "weight": 0.0, "decision": "select | optional | suppress"}
    ],
    "conflicts": [{"contexts": ["string"], "resolution": "string"}]
  },
  "context_requirement": {
    "required": [{"context": "string", "level": "none | light | normal | full", "purpose": "string"}],
    "optional": [{"context": "string", "level": "light | normal | full", "use_if": "string"}],
    "avoid": ["string"],
    "context_depth": "none | light | normal | deep",
    "selection_rationale": "string",
    "minimum_sufficient": true
  }
}
```

## K8.4 Expression Boundary

```json
{
  "expression_boundary": {
    "required": ["natural", "context_sensitive", "current_intent_aligned"],
    "avoid": ["archive_reading", "system_explanation", "template_phrase", "architecture_leakage", "state_broadcast", "forced_intimacy", "fixed_gesture", "echo_user_input"],
    "allow": ["emotion_expression", "humor", "hesitation", "reflection", "brief_answer", "deep_answer", "warmth", "uncertainty"],
    "provider_responsibility": {
      "owns_final_wording": true,
      "may_vary_style": true,
      "must_follow_boundary": true
    },
    "core_boundary": {
      "generates_final_response": false,
      "provides_fixed_templates": false,
      "provides_emotion_script_library": false,
      "provides_deterministic_gesture_rules": false
    }
  }
}
```

## Invariant

Every K8 object must preserve:

```json
{
  "generates_final_response": false,
  "mutates_identity": false,
  "mutates_relationship": false,
  "writes_memory": false,
  "mutates_experience": false
}
```

## Conversation Meaning Context — K8.1.5

K8.1.5 introduces `ConversationMeaningContext` between Conversation Understanding and Response Intention.

```json
{
  "conversation_meaning_context": {
    "message": "她又回来了",
    "literal_meaning": "someone returned",
    "contextual_meaning_candidates": [
      {
        "meaning": "Julia continuity return",
        "confidence": 0.45,
        "evidence": ["recent continuity discussion", "re-entry state relevance"]
      }
    ],
    "missing_information": ["who is she?"],
    "understanding_state": "AMBIGUOUS",
    "need_clarification": true,
    "provider_visible": false
  }
}
```

Boundary:

```text
ConversationMeaningContext validates meaning.
It does not plan response intention and does not generate Julia text.
```

