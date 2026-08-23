# WAVE5 Pre-E2E Assistant Runtime Frozen Path Evidence Audit

## 1. Status

- Audit Target: Assistant Runtime → frozen Core AT-16 path evidence
- Status: COMPLETE ✅
- Evidence Decision: NOT READY / HOLD ⚠️
- Date: 2026-08-23
- Owning repo for record: `/Users/admin/julia_core`
- Core HEAD before record: `66e7d7a`
- Assistant repo observed: `/Users/admin/julia_ai_assistant`
- Assistant branch: `phase5/rmd-3g-observability`
- Assistant HEAD: `47a3e4a`
- E2E: HOLD ⚠️
- AT-17: HOLD ⚠️

This audit does not start E2E and does not start AT-17.

## 2. Question

Pre-E2E P0-1 requires proof that the product runtime path calls the frozen Core AT-16 path:

```text
Assistant runtime
  ↓
Core Context OS
  ↓
AT-16 frozen Diary Context OS retrieval
  ↓
provider-visible package trace
```

## 3. Current Observation

`/Users/admin/julia_ai_assistant/runtime/assistant_runtime.py` imports Core modules, but the product trace shape still records Context OS as missing / not called:

```text
missing_authorities: ["ContextOS"]
components.context: "NOT_CALLED"
```

The assistant runtime also remains on an assistant-local/read-only memory binding surface:

```text
memory_runtime_source: "assistant_readonly_memory_binding"
```

This means:

```text
Core AT-16 capability exists
  ≠
Assistant product runtime uses AT-16 frozen path
```

## 4. Dirty Workspace Guard

The Assistant repo currently has pre-existing dirty/untracked state:

```text
M memory/claude_diary/julia_character.md
M runtime/assistant_runtime.py
?? data/
?? experiments/provider_smoke/agent_direct_tone.py
?? experiments/provider_smoke/mock_tone_tts.py
?? experiments/provider_smoke/smoke_fishaudio.py
?? providers/llm/claude_provider.py
```

Because `runtime/assistant_runtime.py` is already dirty before this P0 closure, committing an Assistant Runtime integration patch now would mix unknown pre-existing runtime changes into the Pre-E2E evidence lineage.

This violates the already-recorded Build Manifest rule:

```text
E2E Candidate Build requires clean workspace
OR explicit dirty-state exception record
```

## 5. Evidence Decision

Assistant Runtime Frozen Path Evidence cannot be marked GREEN yet.

Current decision:

```text
Assistant Runtime Frozen Path Evidence: HOLD ⚠️
Reason: product runtime file is pre-existing dirty and current trace still marks ContextOS NOT_CALLED
E2E Readiness: NOT READY ⚠️
```

This is not a failure of AT-16. AT-16 remains FROZEN ✅.

## 6. Required Next Action

Before modifying Assistant Runtime or claiming product path evidence, close the dirty-state policy for `/Users/admin/julia_ai_assistant`:

Option A — clean integration lane:

```text
create/checkout clean Assistant integration branch
apply minimal Core Context OS binding patch
add product trace test
commit evidence
```

Option B — explicit dirty exception:

```text
record every dirty Assistant file as included/excluded
approve runtime/assistant_runtime.py as the integration base
then apply minimal Core Context OS binding patch
```

Only after A or B may the Assistant Runtime Frozen Path Evidence gate proceed to GREEN.

## 7. Minimal Evidence Required After Dirty Policy Closure

Required proof test:

```text
JuliaAssistantRuntime.handle_chat(...)
  ↓
execution_trace.components.context == PASS
execution_trace.missing_authorities excludes ContextOS
execution_trace.core_context_os.routed_through_core_context_os == True
if Diary retrieval is in scope:
  execution_trace.core_context_os.diary_trace contains AT-16 Context OS route
provider-visible message contains Diary only via [diary_context_os] projection
```

Required boundary checks:

```text
ContextBlock ≠ Diary authority
ContextBlock ≠ Memory authority
ContextBlock ≠ Identity authority
trace metadata ≠ source authority
legacy assistant memory/session text ≠ governed Diary retrieval evidence
```

## 8. Current Gate

```text
Pre-E2E Build Manifest: RECORDED ✅
Authority Propagation Contract: READY ✅
Assistant Runtime Frozen Path Evidence: HOLD ⚠️
Dirty Workspace Policy Closure: NEXT ▶
E2E Execution: HOLD ⚠️
AT-17: HOLD ⚠️
```

## 9. Non-Goals

Not started:

```text
E2E ❌
AT-17 ❌
Context OS ranking/search optimization ❌
MemoryExperience creation ❌
Diary UI redesign ❌
Claude diary migration ❌
S2S AT-11 remediation ❌
```
