# Context OS Runtime Integration Plan v1.0

> Phase: A2.2 — Context OS Runtime Integration Contract Design  
> Status: Contract Draft  
> Date: 2026-07-31  
> Baseline: `phase-a2.1.5-core-independence-complete`

## 1. Objective

A2.2 defines how the independent Julia Core Context OS is integrated into Julia Runtime lifecycle.

A2.1 proved:

```text
Context OS can exist independently.
```

A2.1.5 proved:

```text
Context OS does not require any Domain Provider.
```

A2.2 defines:

```text
How Julia Runtime owns and operates Context OS as core infrastructure.
```

A2.2 is contract design only.

It does not:

- integrate a Domain Provider;
- integrate Memory retrieval;
- integrate Identity data;
- integrate LLM calls;
- build prompt rendering;
- connect UI;
- connect Voice;
- migrate full legacy `runtime/context_os/`.

## 2. Architecture Position

Target relationship:

```text
Julia Runtime
        │
        ▼
Context OS Lifecycle
        │
        ▼
Provider Boundary
        │
        ▼
(no domain required)
```

Context OS becomes runtime infrastructure, not a domain capability.

The success criterion is not intelligence expansion. The success criterion is lifecycle ownership without domain contamination.

## 3. Runtime Ownership

### 3.1 Julia Runtime Owns Runtime Lifecycle

Julia Runtime owns:

- startup;
- shutdown;
- dependency injection;
- provider registry injection;
- session management;
- resource lifecycle;
- runtime error envelope;
- runtime observability hooks.

Julia Runtime does not own:

- `ContextBlock` semantic content;
- domain fact selection;
- memory persistence;
- domain reasoning;
- final answer generation.

### 3.2 Context OS Owns Context Lifecycle

Context OS owns:

- `ContextRequest` validation;
- context planning;
- provider-boundary resolution;
- `ContextBlock` lifecycle;
- context expiration;
- context result construction;
- context-level error classification.

Context OS does not own:

- runtime process lifecycle;
- session storage backend;
- provider implementation lifecycle;
- domain truth;
- Memory lifecycle;
- Identity lifecycle.

## 4. Session Lifecycle Contract

A2.2 defines minimal runtime session states.

```text
CREATED
   ↓
ACTIVE
   ↓
CONTEXT_REQUESTED
   ↓
CONTEXT_RESOLVED
   ↓
COMPLETED
   ↓
EXPIRED
```

### 4.1 Session Creation

Session creation does not create a dedicated Context OS instance.

Recommended ownership:

```text
Runtime owns one ContextRuntime / Context OS service.
Sessions reference ContextRuntime.
```

Reason:

- avoids one Context OS per session;
- keeps provider registry centralized;
- allows consistent lifecycle and shutdown behavior;
- keeps Context OS as runtime infrastructure.

### 4.2 Session Context Flow

```text
Session input
   ↓
ContextRequest
   ↓
ContextRuntime.resolve(request)
   ↓
ContextResult
   ↓
Session consumes result
```

Session may hold references to context result ids or selected blocks for the current turn, but must not persist them as Memory.

## 5. Context Lifecycle Contract

Context lifecycle:

```text
ContextRequest
        ↓
Planner
        ↓
Resolver
        ↓
ContextBlock candidates
        ↓
ContextResult
        ↓
Consumed
        ↓
Expired
```

### 5.1 ContextRequest

`ContextRequest` expresses need.

It is not a financial query, memory query, prompt, or final answer request.

### 5.2 ContextBlock

`ContextBlock` is short-lived context candidate material.

It may be:

- selected;
- excluded;
- consumed;
- expired;
- refreshed by future requests.

It must not silently become:

- Memory;
- prompt instruction;
- final answer;
- domain judgment.

### 5.3 ContextResult

A minimal runtime context result should contain:

```python
@dataclass(frozen=True, slots=True)
class ContextResult:
    request_id: str
    selected_blocks: tuple[ContextBlock, ...]
    errors: tuple[ContextError, ...]
    status: str  # resolved / partial / empty / failed
```

A2.2 implementation may keep this minimal. Full budget/provenance/quality integration may come later.

## 6. Dependency Injection Boundary

Context OS must not locate databases, domain providers, memory stores, or identity data by itself.

Correct:

```text
Julia Runtime
    ↓
Provider Registry
    ↓
ContextRuntime(provider_registry=registry)
```

Forbidden:

```text
Context OS
    ↓
import financial provider directly
```

Forbidden:

```text
Context OS
    ↓
open memory files directly
```

Forbidden:

```text
Context OS
    ↓
read identity private data directly
```

### 6.1 Provider Registry

A2.2 may define a minimal provider registry, but it must remain generic.

It may know:

- provider domain id;
- provider availability;
- provider protocol.

It must not know:

- financial rules;
- stock logic;
- medical rules;
- coding heuristics.

## 7. Error Handling

A2.2 must define non-crashing context error behavior.

### 7.1 Provider Unavailable

If no provider is registered for a requested domain:

```text
ContextResult.status = empty or partial
ContextError.code = provider_unavailable
```

Context OS must not crash.

### 7.2 Invalid Request

Invalid request examples:

- missing task intent;
- missing intent;
- invalid budget;
- malformed constraints.

Expected behavior:

```text
InvalidContextRequest
```

or structured `ContextError`.

### 7.3 Context Expired

Expired blocks must not be silently used.

Expected behavior:

```text
ContextExpired
```

or excluded block with expiration reason.

### 7.4 Provider Error

Provider exceptions must be contained at provider boundary.

Expected behavior:

```text
ContextResult.status = partial or failed
ContextError.code = provider_error
```

Provider errors must not mutate Runtime, Memory, or Identity state.

## 8. Shutdown Behavior

Runtime shutdown order:

```text
1. Stop accepting new sessions
2. Stop accepting new context requests
3. Mark active context results as expiring / expired
4. Release provider registry references
5. Shutdown ContextRuntime
6. Complete runtime shutdown
```

Forbidden:

```text
force kill context state without lifecycle transition
```

Context OS shutdown should be idempotent.

## 9. Regression Gates

A2.2 must inherit A2.1.5 regression gates.

Required:

```bash
.venv/bin/python -m pytest -q tests/test_a215_core_independence.py
```

A2.2 implementation must add Runtime Integration tests while preserving:

- no domain dependency;
- no private data dependency;
- provider interface as only extension point;
- ContextBlock not Memory;
- financial provider not required.

## 10. Acceptance Targets

- [ ] **A2.2-AT-01 Runtime initializes Context OS**: Runtime can create a ContextRuntime / Context OS service.
- [ ] **A2.2-AT-02 Runtime does not change Context OS ownership**: Runtime owns process/session lifecycle; Context OS owns context lifecycle.
- [ ] **A2.2-AT-03 Session lifecycle drives context lifecycle**: session can create request, resolve context, consume result, complete/expire.
- [ ] **A2.2-AT-04 ContextBlock lifecycle is explicit**: block can be selected, consumed, expired, and must not become Memory.
- [ ] **A2.2-AT-05 Providers are injected**: provider registry is injected by runtime; Context OS does not self-discover domain providers.
- [ ] **A2.2-AT-06 No Domain dependency**: `runtime/core` must not reference financial/stock/market/theme/ai_theme_app.
- [ ] **A2.2-AT-07 No Memory retrieval**: Context OS runtime integration must not read memory content.
- [ ] **A2.2-AT-08 No Identity data**: Context OS runtime integration must not read private identity data.
- [ ] **A2.2-AT-09 A2.1.5 regression gate passes**: `tests/test_a215_core_independence.py` remains mandatory.
- [ ] **A2.2-AT-10 Runtime shutdown releases context lifecycle**: shutdown stops new requests, expires active context, releases providers, and is idempotent.

## 11. Explicit Non-Goals

A2.2 must not introduce:

- Financial Provider;
- stock / market / theme logic;
- Memory retrieval;
- Identity private data;
- LLM;
- prompt builder;
- UI;
- Voice;
- vector database;
- embedding;
- full legacy Context OS migration.

## 12. Recommended A2.2 Implementation Shape

If approved, A2.2 implementation should remain minimal:

```text
runtime/core/context_os/runtime.py
runtime/core/context_os/result.py
runtime/core/context_os/errors.py
runtime/core/providers/registry.py
runtime/core/session.py or runtime/core/runtime.py
```

Tests should be added first:

```text
tests/test_a22_context_os_runtime_integration.py
```

Implementation should not touch financial modules.

## 13. Required Validation for A2.2 Contract

A2.2 Contract is documentation-only.

Expected changed files:

```text
docs/architecture/Context_OS_Runtime_Integration_Plan_v1.0.md
```

No runtime behavior changes should occur in this contract phase.

## 14. Approval Notes

Decision:

```text
APPROVED WITH NOTES
```

Approved:

- Runtime owns runtime lifecycle;
- Context OS owns context lifecycle;
- session references ContextRuntime rather than creating one Context OS per session;
- dependency injection boundary;
- provider registry boundary;
- structured error handling;
- shutdown behavior;
- regression gates;
- documentation-only scope.

Notes:

1. **Runtime must not become a hidden Context Authority.**

   Runtime owns execution and lifecycle. It must not mutate `ContextBlock` content, reinterpret evidence, or decide domain truth.

   ```text
   Runtime owns execution.
   Context OS owns context.
   Domain Provider owns facts/evidence.
   ```

2. **Provider Registry is not Domain Router reasoning.**

   Provider Registry may perform provider lookup and availability coordination. It must not decide which domain answer is better, rank domain truth, or perform intelligent provider selection reasoning.

   ```text
   Provider Registry = lookup / lifecycle boundary
   Provider Registry ≠ reasoning engine
   ```

Recommended next phase:

```text
A2.2.1 — Runtime Integration Skeleton
```

Recommended minimal implementation shape:

```text
runtime/core/runtime/
  lifecycle.py
  session_manager.py
  context_runtime.py
```

A2.2.1 must continue to exclude Financial Provider, Memory, Identity, LLM, Prompt Builder, UI, and Voice.
