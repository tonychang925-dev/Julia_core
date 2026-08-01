# ADR-008: Alignment OS Authority

## Status

Accepted

## Context

Alignment OS was introduced after discovering that model-provider adaptation is neither domain logic nor product persona logic. It is the Core OS layer that keeps the same agent behavior consistent across providers.

The boundary must be explicit because Alignment OS sits near Persona Engine and Provider Layer and could otherwise drift into either a second persona compiler or a provider API wrapper.

## Decision

Alignment OS owns:

- provider behavioral alignment
- capability-aware behavior constraints
- provider-neutral behavior envelopes
- provider-specific expression profiles
- structured alignment metadata such as `BehaviorConstraint(dimension="intimacy", max="L4")`

Alignment OS does not own:

- persona identity definition
- memory content or memory writes
- reasoning/domain truth
- action execution
- provider API execution
- product-private relationship or identity data

Persona Engine owns identity definition. Alignment OS owns provider adaptation. Provider Layer owns execution capability.

## Consequences

- Core alignment constraints must be generic dimensions, not product-only fields.
- Product-specific meaning belongs in product persona/memory/config packages.
- Runtimes may inspect derived convenience properties, but the canonical API is `BehaviorConstraint`.
- Alignment OS must remain importable without any concrete LLM, voice, memory, or domain provider.

## Alternatives Considered

1. Keep provider alignment inside products. Rejected because it causes duplicate implementations and cross-product drift.
2. Put provider alignment inside Persona Engine. Rejected because persona identity and provider adaptation have different authority boundaries.
3. Put provider alignment inside Provider Layer. Rejected because providers execute capability; they must not own agent behavior.
