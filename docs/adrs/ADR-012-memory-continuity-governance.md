# ADR-012: Memory Continuity Governance

Status: Proposed
Date: 2026-08-01

## Context

Memory OS stores and retrieves facts or events. However, compact survival requires deciding which memory refs are identity-forming and must be protected across session loss, provider switch, platform migration, or context compaction.

If Memory OS directly promotes memories into identity continuity, Julia risks becoming memory-volume-driven instead of meaning-driven.

## Decision

Continuity OS owns memory continuity eligibility.

Memory OS may submit memory refs as candidates. Continuity OS classifies them and returns eligibility decisions and protected refs.

## Consequences

Positive:

- Memory remains storage/retrieval authority.
- Continuity remains preservation policy authority.
- Checkpoints remain refs-only.
- Ordinary memories do not automatically become identity.

Negative:

- Requires additional binding contracts.
- Requires tests to prevent memory promotion boundary violations.

## Rejected Alternatives

### Memory OS decides protected identity refs

Rejected because Memory OS does not own identity continuity policy.

### All high-importance memories become identity

Rejected because high importance does not always mean identity-forming.

### Context relevance controls persistence

Rejected because current relevance is not the same as cross-lifecycle preservation.
