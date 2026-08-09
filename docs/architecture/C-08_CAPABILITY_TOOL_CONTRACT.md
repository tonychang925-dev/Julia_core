# C-08 — Capability / Tool Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §14
**Depends on**: C-00 (07f0ff0), C-01 (f79db0d), C-03 (4b1625e), C-07 (248d42b)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Principle

```
LLM chooses whether cognition requires a capability.
Runtime authorizes and executes that capability.
LLM interprets the result.
```

```
Need recognition       → LLM (C-00)
Execution authority    → Runtime / Capability (C-01, C-08)
Meaning interpretation → LLM (C-00)
```

## 2. Full Cognitive Tool Loop

```
LLM cognition → CapabilityRequest
  → Runtime validates, authorizes, executes, records evidence
  → ToolResult + Evidence
  → Context OS incremental projection (C-03)
  → CognitiveContextPackageDelta
  → ModelProvider (C-07)
  → LLM continues cognition
```

## 3. CapabilityRequest

```
CapabilityRequest {
    capability_request_id
    turn_id, generation_id, correlation_id
    capability_id
    arguments
    requested_scope
    idempotency_key
    requested_at
    provenance
}
```

Rationale/context may be provided as metadata. Full hidden reasoning chain is NOT required as a mandatory field.

## 4. CapabilityManifest

```
CapabilityManifestEntry {
    capability_id
    description
    input_schema, output_schema
    side_effect_class       // READ_ONLY, REVERSIBLE_WRITE, IRREVERSIBLE_WRITE, EXTERNAL_SIDE_EFFECT, HIGH_IMPACT
    permission_requirements
    idempotency_support
    latency_cost_hints
    data_sensitivity
    availability
}
```

Enters model via CapabilityFrame → Context OS → LLM. Not: tool registry → provider directly (bypassing C-03).

## 5. Semantic Router — Prohibited

```
Capability routing begins after a capability has been cognitively selected, not before.
```

Allowed: `capability_id = "calendar.create_event"` → deterministic dispatch to CalendarExecutor.

Forbidden: user says "maybe talk to John tomorrow" → Runtime infers CREATE_CALENDAR_EVENT → auto-executes.

### Deterministic Command Exception

Explicit, unambiguous, non-semantic, protocol-defined commands: `/cancel`, `/stop`, `/reconnect`, healthcheck, transport reconnect, explicit UI action. These may enter deterministic infrastructure route without LLM cognition.

Test: "Does this path require interpreting what the user really means?" If yes → not a deterministic command.

## 6. Authorization

```
CapabilityRequest → AuthorizationDecision { ALLOW, DENY, REQUIRE_CONFIRMATION, REQUIRE_ELEVATION, UNAVAILABLE }
```

Basis: operator authorization, capability scope, data sensitivity, side-effect level, environment policy, explicit consent state.

Not based on: Runtime's interpretation of emotional intent, relationship closeness as access-control token (C-04 identity role ≠ authorization).

```
Authorization evaluates policy.
LLM evaluates semantic usefulness.
```

## 7. Side-Effect Classification

```
READ_ONLY            — no persistent change (search, read, query)
REVERSIBLE_WRITE     — can be undone (save draft, update field)
IRREVERSIBLE_WRITE   — cannot be undone (delete, overwrite)
EXTERNAL_SIDE_EFFECT — affects external systems (send email, post message)
HIGH_IMPACT          — significant consequence (execute trade, transfer)
```

Drives: authorization level, confirmation requirement, retry policy, idempotency handling, recovery behavior.

## 8. CapabilityCall Lifecycle

```
REQUESTED → AUTHORIZED → EXECUTING → COMPLETED | FAILED | TIMED_OUT | CANCELLED
```

CapabilityCall is one invocation attempt. An Action (externally meaningful side effect) is separate from the call. A call may time out while the action already occurred. Action state ≠ call state.

## 9. ToolResult + Evidence

```
ToolResult {
    capability_call_id, status
    structured_output, error
    started_at, completed_at
    side_effect_state
    evidence_refs[]
}

Evidence {
    evidence_id, source, source_type
    observed_at
    content
    provenance, confidence, freshness
    integrity_metadata
}
```

ToolResult = execution outcome. Evidence = what can support cognition. They are distinct.

## 10. Success ≠ Truth

`status = SUCCESS` means capability execution succeeded. It does NOT mean the returned claim is true. Evidence may be stale, conflicting, low-quality, or partial. Final judgment belongs to LLM cognition.

## 11. ToolResult → Context OS (Mandatory)

```
ToolResult + Evidence → Context OS incremental projection → Alignment → ModelProvider
```

Forbidden: `messages.append(tool_result); provider.chat(...)`. All bypass paths identified in P0-A must be closed.

## 12. Same-Turn Continuation

C-01: same `turn_id`. Tool loop = one logical turn. Capability calls are execution artifacts within the turn, not independent transcript messages.

## 13. Side-Effect Retry Safety

For `UNKNOWN` side-effect state on retry: Runtime MUST NOT blindly replay. Must verify completion where possible. For HIGH_IMPACT / EXTERNAL_SIDE_EFFECT: require explicit confirmation or idempotency proof before retry.

## 14. Parallel Tool Calls

If ModelProvider supports parallel requests: Runtime may execute them concurrently where policy permits. Must handle: correlation, partial failure, ordering, timeout, duplicate results, cancellation. ToolResultSet → Context OS as structured incremental projection.

## 15. Tool Errors — Structured, Model-Visible

```
PermissionDenied, CapabilityUnavailable, InvalidArguments, ExecutionFailed
Timeout, PartialResult, Cancelled, UnknownSideEffectState
```

All pass through Context OS → LLM. LLM decides: retry, ask user, use another tool, continue without it. NOT Runtime semantic planner.

## 16. Domain Capability — Evidence, Not Conclusion

Legal: market capability → sector strength, volume, event facts, signal measurements, source evidence.

Danger: market capability → "buy stock X." If the latter is structured output of an algorithm: represent as `algorithmic_signal`, `source = strategy_engine`. It is Evidence, not Julia's belief. Final cognitive integration by LLM.

## 17. Tool Grounding Invariant

```
Julia may claim an external action or observation
only when supported by corresponding execution evidence,
or explicitly state it as unverified inference.
```

"No capability result without execution evidence." If capability is unavailable: return `CapabilityUnavailable` — never fabricate a result. LLM must not claim execution that did not occur.

## 18. Provider-Native Tools — Must Normalize

Claude/OpenAI native tool APIs → CapabilityRequest normalization → C-08 authorization/execution. Provider SDK must not register functions that execute directly, bypassing Core.

## 19. Voice/S2S Tools — Same Path

Voice native realtime model → tool call → same CapabilityRequest → Runtime → ToolResult → Context OS. Voice does not own: voice-only tool router, voice-only authorization, voice-only direct result injection.

## 20. Capability ≠ Action

```
Capability      = what can be done
CapabilityCall  = invocation attempt
Action          = externally meaningful side effect
```

A call may time out while the action already occurred. Action state is not solely determined by call state. C-12 Evidence/Action/Trace defines full lifecycle.

## 21. Model-Directed Retrieval = Capability

C-03 Stage 2: LLM requests more information → MemoryRetrievalRequest / ConversationRetrievalRequest / DomainRetrievalRequest. These are capability uses. Retrieval result → Context OS. NOT RetrievalProvider directly appending to prompt.

## 22. Core Object Relationships

```
LLM → CapabilityRequest → AuthorizationDecision
  ├── DENY / CONFIRM
  └── ALLOW → CapabilityCall → Executor/Provider
        ├── Action / side effect
        └── ToolResult + Evidence → Context OS → LLM
```

## 23. P0-A Disposition

| Module | Verdict | Target |
|--------|---------|--------|
| `WorkflowRouter` (pre-cognitive intent) | REWRITE | Remove intent routing; expose capability manifest |
| `MarketBriefIntentResolver` | MOVE TO LLM | Intent classification = cognitive |
| `CapabilitySemanticRouter` (B2) | MOVE TO LLM | Tool-need recognition = cognitive |
| `MCPToolAdapter` | KEEP | Infrastructure capability transport |
| `CapabilityManager` | KEEP | Authorization + execution lifecycle |
| `capability_bridge.py` (tool_manifest) | KEEP WITH BOUNDARY | Manifest generation; route through C-03 |
| Direct tool_result append in `_chat_impl` | REMOVE | Route through Context OS |
| Provider-native tool paths | NORMALIZE | Route through C-08 authorization |
| Voice tool paths | NORMALIZE | Route through C-08 |

## 24. Forbidden Claims

```
❌ Runtime determines user semantic intent before LLM
❌ Semantic router selects Julia's tool path
❌ Tool executor interprets result for Julia
❌ Tool success means evidence is true
❌ Provider-native tool bypasses Core
❌ ToolResult bypasses Context OS
❌ Unavailable tool gets fabricated result
❌ Sensitive tool permission depends on Persona
❌ Relationship identity implies authorization
❌ Retry blindly repeats side effects
❌ Recovery blindly replays pending actions
❌ Domain capability becomes Julia's conclusion
❌ Tool output automatically becomes Memory / Identity
❌ Voice owns separate capability system
```

## 25. Acceptance Gates

- [x] CapabilityRequest first-class object (§3)
- [x] CapabilityManifest frozen (§4)
- [x] Need recognition belongs to LLM (§1)
- [x] Semantic router prohibition frozen (§5)
- [x] Deterministic command exception narrow and explicit (§5)
- [x] Runtime authorization boundary frozen (§6)
- [x] Permission decision model frozen (§6)
- [x] Side-effect classes frozen (§7)
- [x] CapabilityCall lifecycle frozen (§8)
- [x] Action separated from CapabilityCall (§20)
- [x] ToolResult + Evidence schema frozen (§9)
- [x] Success ≠ truth (§10)
- [x] ToolResult must re-enter Context OS (§11)
- [x] Same-turn continuation frozen (§12)
- [x] Side-effect retry/idempotency frozen (§13)
- [x] Parallel tool semantics frozen (§14)
- [x] Tool error semantics frozen (§15)
- [x] Domain signals = evidence, not conclusion (§16)
- [x] Tool Grounding invariant frozen (§17)
- [x] Provider-native tools normalize through C-08 (§18)
- [x] Voice/S2S tools normalize through C-08 (§19)
- [x] Authorization independent from relationship identity (§6)
- [x] P0-A tool/router modules dispositioned (§23)
- [x] Production changes = 0

## 26. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §14
Depends: C-00, C-01, C-03, C-07
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-12

C-08 FREEZE → C-09 Alignment GO
```
