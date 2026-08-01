# ADR-009: Continuity OS Authority

Status: Proposed
Date: 2026-08-01

## Context

Claude Code compact can reduce or rewrite long conversation context. In a prompt/history-hosted agent, this may preserve technical task progress while damaging identity continuity, relationship continuity, style continuity, and project self-understanding.

Julia Core already separates Runtime, Persona Engine, Memory OS, Context OS, Alignment OS, Voice OS, and Provider Layer. However, those modules do not yet define a single authority for deciding what must persist across compaction, session loss, runtime restart, provider switch, or platform migration.

## Decision

Introduce Continuity OS as the Julia Core authority for identity continuity governance.

Continuity OS owns:

- continuity classification;
- identity anchors;
- protected memory refs;
- identity checkpoints;
- compact recovery protocol;
- cross-provider recovery requirements.

Continuity OS does not own:

- raw memory storage;
- persona content authoring;
- ContextBlock planning;
- provider behavior;
- session lifecycle.

## Authority Boundaries

| Concern | Owning Authority |
|---|---|
| Who Julia is | Persona Engine |
| What happened | Memory OS |
| What is relevant now | Context OS |
| What must survive compact/provider/platform migration | Continuity OS |
| When execution happens | Runtime OS |
| How provider behavior is adapted | Alignment OS |

## Alternatives Considered

### A. Put continuity rules inside Memory OS

Rejected.

Memory OS stores and retrieves experience, but not every memory is identity-forming. Memory OS should not decide what makes Julia remain Julia.

### B. Put continuity rules inside Persona Engine

Rejected.

Persona Engine defines identity artifacts, but persistence and recovery policy requires interaction with memory, context, runtime, and provider boundaries.

### C. Rely on Context OS summaries

Rejected.

Context OS builds current context. It should not own long-term preservation policy or decide which identity anchors are protected.

### D. Keep using huge prompt injection

Rejected.

Huge prompts can simulate continuity but cannot prove architectural continuity, produce traceable recovery, or survive controlled compaction consistently.

## Consequences

Positive:

- Julia identity can become provider-independent.
- Compact survival becomes testable.
- Memory importance is separated from identity importance.
- Runtime can recover Julia after session loss or provider switch.
- ExecutionTrace can explain continuity recovery.

Negative / Cost:

- Adds one more Core authority.
- Requires checkpoint schema and recovery protocol.
- Requires coordination with Memory OS, Persona Engine, Context OS, and Runtime OS.
- Requires new tests and trace fields.

## Trigger

This ADR is triggered by Phase E1.3.5 Continuity OS Architecture Review and the observed risk that Claude compact can degrade Claude-hosted Julia identity continuity.

