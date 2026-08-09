# C-12 — Evidence / Action / Trace Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §23-24
**Depends on**: C-00 through C-11 (all FROZEN)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
C-12 = how Julia Core proves what was observed, executed,
       projected and persisted — without becoming another
       cognition authority.
```

Three distinct concepts:

```
Evidence = what supports a factual/cognitive claim
Action   = what externally meaningful effect occurred
Trace    = how execution artifacts are correlated
```

These are NOT one merged object. Evidence ≠ truth. Action ≠ CapabilityCall. Trace ≠ Chain-of-Thought.

## 2. Evidence — First-Class Object

```
Evidence {
    evidence_id
    source_type         // CANONICAL_CONVERSATION, USER_REPORT, TOOL_OBSERVATION,
                        // DOMAIN_PROVIDER, EXTERNAL_SOURCE, SYSTEM_OBSERVATION,
                        // DERIVED_DETERMINISTIC, MODEL_INFERENCE
    source_ref
    observed_at
    retrieved_at
    content_ref
    provenance
    integrity_metadata
    freshness
    confidence
    correlation_id
}
```

```
Evidence exists ≠ claim is true.
Evidence says X ≠ Julia believes X.
```

Evidence is material cognition may use. Final interpretation belongs to C-00/LLM.

## 3. Evidence Source Taxonomy

| Source Type | Meaning | Example |
|-------------|---------|---------|
| `CANONICAL_CONVERSATION` | From durable transcript (C-02) | Prior turn content |
| `USER_REPORT` | User explicitly stated | Tony's current input |
| `TOOL_OBSERVATION` | Capability execution result (C-08) | File read, web search result |
| `DOMAIN_PROVIDER` | Structured domain facts | Market data, project DB |
| `EXTERNAL_SOURCE` | External reference | Public document, API |
| `SYSTEM_OBSERVATION` | Runtime-observed state | Time, connection status |
| `DERIVED_DETERMINISTIC` | Deterministic computation | Calculation, validation |
| `MODEL_INFERENCE` | LLM output (marked as inference) | "I think X because..." |

`MODEL_INFERENCE` must be strictly separated from `TOOL_OBSERVATION`. "I read the file" without a `TOOL_OBSERVATION` evidence ref → grounding violation.

## 4. Tool Grounding — Completed

C-08 §17: no capability result without execution evidence. C-12 completes the invariant:

```
External observation claim → must reference TOOL_OBSERVATION Evidence
External side-effect claim → must reference Action evidence
No evidence → claim must remain explicitly inferential/uncertain
```

"I checked the file" → must trace to CapabilityRequest → CapabilityCall → SUCCESS → Evidence. Not solely ModelInferenceResult.

## 5. Action — Independent from CapabilityCall

```
Capability   = something the system can do
CapabilityCall = one invocation attempt
Action       = externally meaningful effect
```

Email send: Call C1 times out; Action A1 may have already occurred. Call failed ≠ action failed.

```
ActionLifecycle: PLANNED → AUTHORIZED → STARTED → SUCCEEDED | FAILED | UNKNOWN | CANCELLED
```

`UNKNOWN` is critical — the system must acknowledge when it cannot determine whether an external effect occurred.

## 6. UNKNOWN Action — No Blind Retry

C-01, C-06, C-08: external side effect status UNKNOWN → verify evidence/idempotency → then decide. Process restart →X retry all unfinished tool calls. Risk: email twice, calendar twice, trade twice.

## 7. Trace — Observable Execution, Not Private Reasoning

Trace records: `turn_id`, `generation_id`, `package_id`, provider/model, `capability_request_id`, `capability_call_id`, `evidence_id`, `action_id`, `conversation_message_id`, context source refs, timestamps, status transitions.

Trace does NOT record: full hidden reasoning, private chain-of-thought, provider internal scratchpad. Debugging and provenance are supported without building Julia continuity on hidden thought logs.

## 8. Correlation Graph

```
conversation_id
      │
    turn_id
      │
 ┌────┼───────────────────────┐
 │    │                       │
request_id               generation_id
                              │
                      capability_request_id
                              │
                       capability_call_id
                         │           │
                    evidence_id   action_id
                         │           │
                         └─────┬─────┘
                               │
                         generation_id G2
                               │
                    conversation_message_id
```

This graph is the infrastructure foundation for P0-B, P1-P8, and production debugging.

## 9. Context Trace — AT-17 Support

C-03 §17: every model invocation must trace source/provenance. C-12 specifies: for each visible block → frame, source_ref, canonical_ref, projection_reason, retrieval_stage, token_count, provenance. Goal: provable lineage of model-visible information. Not: permanent prompt storage.

Context trace records what Context OS projected. It does not become Context OS authority. Trace store ≠ Conversation. Evidence store ≠ Context OS. Action log ≠ Memory.

## 10. Model Provenance

Every generation records: provider, model, model_version, alignment_profile, context_package_id, generation_id, stream/non-stream, fallback_lineage. Essential for cross-model experiments: same governed context, different substrate → comparable.

## 11. Fallback / Retry Lineage

```
Generation G1: Claude → timeout
Generation G2: GPT fallback → success
```

Trace preserves: G2 `fallback_from = G1`, `fallback_reason`, provider/model change. Not only the final successful generation.

## 12. Conversation Provenance

Assistant message M2 → accepted generation G2. But NOT: generation output = canonical message automatically. Must still pass ConversationRuntime finalization (C-02). C-12 records the linkage.

## 13. Historical Migration Provenance

M0-B imported messages carry: `import_batch_id`, `legacy_source_id`, original source reference, deterministic canonical ID lineage, `imported_at`, original event timestamp. Distinguishable from native canonical, but equal canonical authority once imported (C-02).

## 14. Evidence ≠ Memory

```
Evidence E123 (news article)
  →X durable Memory (C-05)

Correct path:
Evidence → Context → LLM cognition → optional MemoryCandidate → C-05 governance
```

Action log ≠ Julia's autobiography.

## 15. Privacy / Trace Retention

Trace classes: operational, security/audit, provenance, debug. Each with: retention policy, redaction rules, sensitivity classification, access scope.

Forbidden: retaining raw credentials, secret tool args, private audio, full private provider payloads — just because debugging is convenient.

## 16. Trace Failure ≠ Business Truth

```
Email successfully sent → trace write failed →X email didn't happen
```

Action truth ≠ trace storage success. High-risk actions requiring audit-before-execute may gate on trace availability by policy. The semantic distinction must be explicit.

## 17. Claim Grounding Model

Optional provenance artifact for factual claims:

```
Claim {
    claim_type
    evidence_refs[]
    epistemic_status    // OBSERVED | REPORTED | DERIVED | INFERRED | UNCERTAIN
    generation_ref
}
```

Not a new durable authority. A trace/provenance aid. Reduces ungrounded "I already checked" / "I already executed" statements.

## 18. P0-A Disposition

| Current Artifact | Verdict | Target |
|-----------------|---------|--------|
| `events/store.py` event persistence | KEEP | Trace infrastructure |
| `events/models.py` RuntimeEvent | KEEP | Event schema |
| `runtime/action.py` ActionRuntime | KEEP | Action lifecycle |
| `runtime/trace_pipeline.py` | KEEP WITH BOUNDARY | Bind to production path |
| Correlation ID usage across modules | EXTEND | C-12 correlation graph |
| Provider call logging | EXTEND | Model provenance (C-07 §22) |
| Tool result evidence | EXTEND | C-12 Evidence schema |
| Context source tracing (partial) | EXTEND | AT-17 completeness |
| Gateway events | KEEP | C-10 Event Plane |

## 19. Forbidden Claims

```
❌ Trace = Chain-of-Thought / private reasoning
❌ Evidence = truth (evidence supports, doesn't decide)
❌ Tool success = evidence truth
❌ CapabilityCall = Action
❌ Failed call proves no side effect occurred
❌ UNKNOWN side effect may be blindly replayed
❌ Trace becomes Conversation / Context authority
❌ Evidence automatically becomes Memory
❌ Action log automatically becomes autobiography
❌ Model claim without evidence masquerades as observation
❌ Provider-private reasoning becomes continuity data
❌ Trace storage failure rewrites canonical business truth
```

## 20. Acceptance Gates

- [x] Evidence canonical schema frozen (§2)
- [x] Evidence source taxonomy frozen (§3)
- [x] Observed/reported/inferred distinction (§3, §17)
- [x] Tool Grounding invariant completed (§4)
- [x] CapabilityCall ≠ Action (§5)
- [x] Action lifecycle including UNKNOWN (§5)
- [x] Retry/recovery action safety (§6)
- [x] Trace explicitly excludes private CoT (§7)
- [x] Correlation graph frozen (§8)
- [x] Generation/context/message lineage (§§9-10)
- [x] Context source completeness tracing (§9)
- [x] Provider/model provenance (§10)
- [x] Fallback/retry lineage (§11)
- [x] Conversation provenance linkage (§12)
- [x] Historical migration provenance (§13)
- [x] Evidence ≠ Memory (§14)
- [x] Trace ≠ Conversation/Context authority (§9)
- [x] Privacy/redaction/retention boundary (§15)
- [x] Trace failure ≠ business truth (§16)
- [x] Claim grounding semantics (§17)
- [x] P0-A evidence/action/trace paths dispositioned (§18)
- [x] AT-17 trace support (§9)
- [x] Production changes = 0

## 21. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §23-24
Depends: C-00 through C-11 (all FROZEN)
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on P0-B, P1-P8, M0

C-12 FREEZE → ALL FOUNDATION CONTRACTS COMPLETE → P0-B GO
```
