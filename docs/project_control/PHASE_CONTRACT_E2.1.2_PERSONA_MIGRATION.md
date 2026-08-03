# Phase Contract — E2.1.2 Persona Migration

Status: COMPLETE
Phase Name: Persona Migration
Phase Code: E2.1.2
Decision: APPROVED
Implementation Status: COMPLETE
Parent Milestone: E2.1 Runtime Continuity Integration
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E2.1.1_RUNTIME_CONTINUITY_BINDING.md`
- `docs/project_control/PHASE_CONTRACT_E2.0.1_CORE_CONSUMPTION_REVIEW.md`
- `docs/adrs/ADR-015-persona-artifact-authority-boundary.md`
- `/Users/admin/julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md`

## 1. Objective

Migrate Julia AI Assistant persona consumption from legacy giant prompt construction to Core Persona Artifact consumption.

This phase decides whether Julia becomes:

```text
prompt persona
```

or:

```text
runtime persona artifact
```

## 2. Acceptance Targets

- [ ] Assistant consumes a Core-owned Persona Artifact.
- [ ] Trace records `persona.status=PASS` and `persona.artifact="julia.v1"` or equivalent stable artifact id.
- [ ] Assistant no longer injects startup memory into persona system prompt.
- [ ] Assistant persona path does not perform identity decision.
- [ ] Assistant persona path does not compile behavior/continuity rules from memory files.
- [ ] Persona Engine does not write Memory.
- [ ] Persona Engine does not create checkpoint.
- [ ] Persona Engine does not decide continuity level.
- [ ] Provider does not receive a giant persona prompt as identity source.

## 3. Required Commands

Expected new test:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_persona_migration
```

Regression baseline:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_runtime_continuity_binding tests.test_runtime_binding tests.test_provider_alignment
```

Core baseline:

```bash
cd julia_core && python3 -m unittest tests.test_runtime_continuity_hook tests.test_continuity_trace_integration tests.test_full_continuity_recovery
```

## 4. Deliverables

| Deliverable | Path |
|---|---|
| Persona migration implementation | `/Users/admin/julia_ai_assistant/adapters/persona_loader.py` or replacement adapter |
| Persona migration test | `/Users/admin/julia_ai_assistant/tests/test_persona_migration.py` |
| ADR | `docs/adrs/ADR-015-persona-artifact-authority-boundary.md` |
| Phase contract | `docs/project_control/PHASE_CONTRACT_E2.1.2_PERSONA_MIGRATION.md` |

## 5. Forbidden Patterns

E2.1.2 must remove or block:

```text
system_prompt += memory
load_startup_context() inside persona prompt
load_all_identity_memory()
persona_loader decides continuity level
persona_loader creates checkpoint
provider uses persona.system_prompt as identity source
```

## 6. Expected Trace Fragment

```json
{
  "persona": {
    "status": "PASS",
    "artifact": "julia.v1"
  },
  "continuity": {
    "checked": true
  }
}
```

Forbidden trace evidence:

```json
{
  "persona_prompt_length": 12000
}
```

## 7. Non-Goals

- No Memory migration.
- No Context OS integration beyond persona artifact trace.
- No Provider migration beyond preventing persona prompt ownership.
- No continuity checkpoint creation by Persona Engine.
- No live provider quality evaluation.

## 8. Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|---|---|---:|---|
| Persona remains giant prompt | P0 | High | Test forbids startup memory in persona prompt |
| Persona Engine gains continuity authority | P0 | Medium | ADR-015 forbids checkpoint/continuity level decision |
| Memory facts are compiled into persona | P0 | High | E2.1.3 owns Memory migration; E2.1.2 must not consume memory files |
| Provider still owns persona shaping | P1 | Medium | Trace must cite persona artifact, not prompt length |


## 9. Implementation Results

Implemented in Julia AI Assistant:

- `/Users/admin/julia_ai_assistant/adapters/persona/core_persona_adapter.py`
- `/Users/admin/julia_ai_assistant/adapters/persona/__init__.py`
- `/Users/admin/julia_ai_assistant/runtime/assistant_runtime.py`
- `/Users/admin/julia_ai_assistant/server.py`
- `/Users/admin/julia_ai_assistant/tests/test_persona_migration.py`

Validated behavior:

- Runtime consumes `CorePersonaArtifact` with artifact id `julia.v1`.
- Persona trace records `persona.status=PASS` and `persona.artifact=julia.v1`.
- Core persona shell has empty `system_prompt` and `runtime_context_only` load policy.
- New persona adapter does not import startup memory, legacy persona loader, provider, Core Continuity, Memory, Context OS, or Alignment OS.
- Persona adapter exposes no Memory or Continuity authority methods.
- Trace uses artifact evidence, not prompt length.
- Existing runtime continuity, runtime binding, and provider alignment tests still pass.

Legacy notes:

- `adapters/persona_loader.py` remains for old tests/backward compatibility but is no longer the default runtime/server persona entrypoint.
- Memory migration remains explicitly deferred to E2.1.3.

Result: PASS.
