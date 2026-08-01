# ADR-006: Provider Alignment Boundary

## Status

Accepted

## Context

Provider alignment was discovered in a product/history repository, but the problem is not domain-specific. Every agent product that uses multiple LLM providers needs a shared way to preserve behavior contracts across provider differences.

If each product implements its own provider alignment layer, Core users will duplicate policy, drift across products, and incorrectly treat prompts as agent identity.

## Decision

Julia Core adds `alignment_os` as a formal subsystem. Alignment OS owns provider-neutral contracts, provider-specific behavior profiles, profile resolution, and message adaptation helpers.

Product repositories consume Core Alignment OS. They may register product-specific profile overrides, but they must not fork the alignment architecture.

## Consequences

- `julia_ai_assistant` binds Julia persona to Core Alignment OS.
- `julia_agent` provider-alignment behavior becomes migration source / historical validation, not the architectural owner.
- Domain providers remain separate from model provider behavior alignment.
