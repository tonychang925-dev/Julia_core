# ADR-010: Continuity Checkpoint Model

Status: Proposed
Date: 2026-08-01

## Context

Julia Core requires a provider-independent way to restore identity and continuity after context compaction, session loss, runtime restart, provider switch, or platform migration.

Saving a full conversation or large prompt is not acceptable because it preserves surface text rather than governed continuity state.

## Decision

Introduce ContinuityCheckpoint as a compact, provider-independent state artifact owned by Continuity OS.

A checkpoint stores refs, not raw conversation dumps:

- identity refs;
- protected memory refs;
- relationship refs;
- active project refs;
- continuity level mapping;
- recovery requirements.

## Consequences

Positive:

- Julia continuity becomes portable across providers.
- Compact recovery becomes testable.
- Identity state is separated from conversation history.
- Memory refs are protected without converting all memory into prompt text.

Negative:

- Requires checkpoint schema governance.
- Requires coordination with Memory OS and Persona Engine.
- Requires recovery tests.

## Rejected Alternatives

### Store full conversation transcript

Rejected because it recreates context-window dependence.

### Store a giant restored prompt

Rejected because it cannot prove governed continuity.

### Let Memory OS decide checkpoint contents alone

Rejected because Memory OS does not own identity continuity policy.

