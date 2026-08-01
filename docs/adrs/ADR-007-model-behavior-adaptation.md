# ADR-007: Model Behavior Adaptation

## Status

Accepted

## Context

Different LLM providers express the same behavior contract differently. Some providers require stronger identity anchoring; others require warmer constrained expression. This must not cause the agent to become a different persona.

## Decision

Alignment OS resolves an `AlignmentProfile` from `(provider, persona, mode)`. The profile contains:

- a provider-neutral `AlignmentContract`
- a provider-specific `ProviderBehaviorProfile`
- structured behavior-boundary metadata such as `BehaviorConstraint(dimension="intimacy", max="L4")`

The adapter may append these sections to provider messages, but the authoritative object is the structured profile, not the rendered prompt text.

## Consequences

- Runtime observes contract/profile IDs, strategy, and ceilings.
- Provider output remains inference output only.
- Persona and memory remain separate from provider-specific alignment rules.
