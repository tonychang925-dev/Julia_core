# WAVE5 Pre-E2E Dirty Workspace Policy Closure

## 1. Status

- Closure Target: Dirty Workspace Policy for Pre-E2E candidate
- Status: COMPLETE ✅
- Decision: Clean Assistant integration lane required ▶
- Date: 2026-08-23
- Owning repo: `/Users/admin/julia_core`
- Owning branch: `cm-r0-fix`
- Base HEAD: `4e009a3`
- E2E readiness: NOT READY ⚠️
- E2E execution: HOLD ⚠️
- AT-17: HOLD ⚠️

This record closes the policy question for dirty workspaces. It does not clean, revert, stash, or modify any dirty file.

## 2. Policy Rule

Authoritative E2E evidence requires:

```text
known repo + known branch + known commit + known workspace policy
```

Therefore:

```text
clean workspace
```

or:

```text
explicit dirty exception record
```

is mandatory before E2E can run.

## 3. Assistant Repo Observed State

Observed repo:

```text
/Users/admin/julia_ai_assistant
branch: phase5/rmd-3g-observability
HEAD: 47a3e4a
```

Observed dirty state:

| File / path | Status | Runtime impact | Pre-E2E decision |
| --- | --- | --- | --- |
| `runtime/assistant_runtime.py` | modified | HIGH — product runtime / provider path | EXCLUDE from E2E candidate until reviewed |
| `memory/claude_diary/julia_character.md` | modified | MEDIUM — legacy Claude diary / persona material | EXCLUDE from E2E candidate |
| `data/conversations.json` | untracked | MEDIUM — local conversation data | EXCLUDE from E2E candidate |
| `experiments/provider_smoke/agent_direct_tone.py` | untracked | LOW — experiment | EXCLUDE from E2E candidate |
| `experiments/provider_smoke/mock_tone_tts.py` | untracked | LOW — experiment | EXCLUDE from E2E candidate |
| `experiments/provider_smoke/smoke_fishaudio.py` | untracked | LOW — experiment | EXCLUDE from E2E candidate |
| `experiments/edge_tts_adapter_rejected/edge_tts_plugin.py` | untracked | LOW — rejected experiment | EXCLUDE from E2E candidate |
| `experiments/provider_smoke/smoke_elevenlabs_rest.py` | untracked | LOW — provider smoke experiment | EXCLUDE from E2E candidate |
| `providers/llm/claude_provider.py` | untracked | HIGH — provider runtime | EXCLUDE from E2E candidate |
| `providers/llm/deepseek_provider.py` | untracked | HIGH — provider runtime | EXCLUDE from E2E candidate unless already tracked in clean lane |
| `providers/voice/elevenlabs_provider.py` | untracked | HIGH — voice provider runtime | EXCLUDE from E2E candidate |
| `providers/voice/fish_audio_provider.py` | untracked | HIGH — voice provider runtime | EXCLUDE from E2E candidate |
| `providers/**/__pycache__/*` | untracked | NONE — generated cache | EXCLUDE from E2E candidate |

## 4. Runtime Dirty Diff Classification

`runtime/assistant_runtime.py` currently contains a pre-existing modified diff:

```text
31 insertions / 5 deletions
```

Observed purpose from diff:

```text
adds RuntimeCapabilityBridge
adds full cognitive tool loop
adds tool_calls trace
```

This is not the AT-16 Assistant → Core Context OS binding patch.

Pre-E2E decision:

```text
runtime/assistant_runtime.py dirty state must not be used as the base for AT-16 product trace evidence.
```

Reason:

```text
unknown prior runtime behavior change
  + new Context OS binding patch
  = unverifiable E2E lineage
```

## 5. Closure Decision

The dirty workspace policy is closed as follows:

```text
Preferred path: Clean Assistant integration branch ✅
Dirty exception path: NOT APPROVED for runtime/assistant_runtime.py ❌
```

A dirty exception is not accepted for the product runtime file because it directly affects the provider path and E2E authority trace.

## 6. Required Clean Assistant Integration Lane

Before Assistant Runtime Frozen Path Evidence can move from HOLD to GREEN:

```text
1. Create or checkout a clean Assistant integration branch from a known commit.
2. Ensure `git status --short` is clean or only contains explicitly approved evidence files.
3. Apply a minimal Assistant → Core Context OS binding patch.
4. Add a product trace test proving ContextOS PASS and frozen Core AT-16 route.
5. Commit the Assistant evidence in that clean lane.
6. Update Core Pre-E2E manifest with the new Assistant branch / commit.
```

Required proof shape:

```text
JuliaAssistantRuntime.handle_chat(...)
  ↓
execution_trace.components.context == PASS
execution_trace.missing_authorities excludes ContextOS
execution_trace.core_context_os.routed_through_core_context_os == True
if Diary retrieval is in scope:
  execution_trace.core_context_os.diary_trace[].routed_through_context_os == True
  provider-visible text contains Diary only via governed Context OS projection
```

## 7. Other Repo Dirty Policy

### Core

`/Users/admin/julia_core` has known pre-existing dirty/untracked state. AT-12 through AT-16 lineage artifacts have been committed independently.

E2E condition:

```text
Core E2E candidate must either run from committed HEAD or record explicit dirty exceptions.
```

### Voice-S2S

`/Users/admin/Julia-Voice-S2S` has known dirty/untracked doc state.

E2E condition:

```text
S2S can only be included under AT-11 deferred isolation and with dirty-state policy recorded.
```

### Electron

`/Users/admin/julia_electron_v2` showed no targeted dirty status for AT-10 files during Pre-E2E audit.

E2E condition:

```text
Electron E2E candidate must use AT-10 frozen commit/branch or a merge containing it.
```

## 8. Gate Update

```text
Dirty Workspace Policy Closure: COMPLETE ✅
Assistant Runtime Frozen Path Evidence: HOLD ⚠️
Next: Clean Assistant Integration Lineage ▶
E2E Readiness: NOT READY ⚠️
E2E Execution: HOLD ⚠️
AT-17: HOLD ⚠️
```

## 9. Non-Goals

Not performed by this closure:

```text
no file revert
no stash
no branch switch
no Assistant runtime patch
no E2E
no AT-17
no Context OS ranking/search optimization
no MemoryExperience creation
no Diary UI redesign
no Claude diary migration
no S2S AT-11 remediation
```
