# Phase Contract — E2.1.3 Memory Migration

Status: COMPLETE
Phase Name: Memory Migration
Phase Code: E2.1.3
Decision: APPROVED
Implementation Status: COMPLETE
Parent Milestone: E2.1 Runtime Continuity Integration
Risk Level: P0
Generated At: 2026-08-02
Source Documents:
- `docs/project_control/PHASE_CONTRACT_E2.1.2_PERSONA_MIGRATION.md`
- `docs/project_control/PHASE_CONTRACT_E2.0.1_CORE_CONSUMPTION_REVIEW.md`
- `docs/adrs/ADR-016-memory-os-authority-boundary.md`
- `/Users/admin/julia_ai_assistant/docs/verification/JULIA_AI_ASSISTANT_CORE_CONSUMPTION_REVIEW_v1.md`

## 1. Objective

Migrate Julia AI Assistant memory consumption from legacy memory-to-prompt paths to Core-governed memory refs.

This phase solves:

```text
Julia should not depend on chat history or raw memory prompt injection to exist.
```

## 2. Target Chain

```text
JuliaAssistantRuntime
  ↓
Julia Core Memory OS / MemoryRef adapter
  ↓
Memory Ref
  ↓
Continuity Governance
  ↓
Context Requirement
  ↓
Context Block
  ↓
Provider
```

## 3. Acceptance Targets

- [ ] `startup_memory.py` is no longer used by Runtime/Persona/Provider path.
- [ ] Memory trace records refs, not raw memory prompt text.
- [ ] Identity-forming memory goes through Core `MemoryGovernanceAdapter`.
- [ ] L3 identity memory is represented as `memory://...` protected ref.
- [ ] Ordinary memory does not become identity.
- [ ] Application runtime no longer owns memory retrieval policy as authority.
- [ ] Provider does not receive memory dump/system prompt as identity source.
- [ ] Trace contains `memory.status=PASS` and `memory.retrieved_refs=[...]` or equivalent.
- [ ] Trace does not contain `memory_prompt` / raw memory dump.

## 4. Required Commands

Expected new test:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_memory_migration
```

Regression baseline:

```bash
cd julia_ai_assistant && PYTHONPATH=/Users/admin:/Users/admin/julia_core:/Users/admin/julia_ai_assistant python3 -m unittest tests.test_persona_migration tests.test_runtime_continuity_binding tests.test_runtime_binding tests.test_provider_alignment
```

Core baseline:

```bash
cd julia_core && python3 -m unittest tests.test_memory_governance_adapter tests.test_full_continuity_recovery
```

## 5. Forbidden Patterns

```text
memory_text += system_prompt
startup_memory.py used by runtime/persona/provider
with open("memory/*.md") in runtime authority path
assistant_runtime.search_memory() as authority
memory creates checkpoint
memory decides continuity level
provider receives memory dump
```

## 6. Expected Trace Fragment

```json
{
  "continuity": {
    "checked": true
  },
  "persona": {
    "artifact": "julia.v1"
  },
  "memory": {
    "status": "PASS",
    "retrieved_refs": [
      "memory://event/julia-core-origin"
    ]
  },
  "context": {
    "status": "PASS"
  }
}
```

Forbidden trace evidence:

```json
{
  "memory_prompt": "...",
  "startup_prompt_memory_loaded": true
}
```

## 7. Non-Goals

- No new Persona migration.
- No provider migration beyond removing memory dump dependency.
- No live provider quality evaluation.
- No full compact survival real test yet.
- No product UI changes.

## 8. Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|---|---|---:|---|
| Memory remains hidden prompt | P0 | High | Test forbids startup memory and memory_prompt trace |
| App owns memory retrieval authority | P0 | High | Route identity candidates through Core governance |
| Memory mutates identity | P0 | Medium | ADR-016 forbids memory deciding L3/preservation |
| Provider still receives memory dump | P1 | Medium | Provider message tests must reject memory dump system message |


## 9. Implementation Results

Implemented in Julia AI Assistant:

- `/Users/admin/julia_ai_assistant/adapters/memory/core_memory_adapter.py`
- `/Users/admin/julia_ai_assistant/adapters/memory/__init__.py`
- `/Users/admin/julia_ai_assistant/adapters/startup_memory.py` legacy marking
- `/Users/admin/julia_ai_assistant/runtime/assistant_runtime.py`
- `/Users/admin/julia_ai_assistant/tests/test_memory_migration.py`
- `/Users/admin/julia_ai_assistant/tests/test_runtime_binding.py` refs-only expectation update

Validated behavior:

- Runtime uses `CoreMemoryAdapter` for refs-only memory consumption.
- Trace records `memory.status=PASS` and `memory.retrieved_refs`.
- Identity-forming memory ref `memory://event/julia-core-origin` is governed by Core `MemoryGovernanceAdapter` as `L3_IDENTITY` / checkpoint eligible.
- Provider receives no memory dump system message.
- `startup_prompt_memory_loaded=false`.
- `startup_memory.py` is marked `LEGACY COMPATIBILITY ONLY`.
- Runtime no longer calls `load_startup_context` / `load_startup_memory`.

Result: PASS.
