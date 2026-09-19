# RD1-P2-I3A Iterative Reasoning Architecture and Acceptance Contract

## Task identity

- TASK_ID: `RD1-P2-I3A-ITERATIVE-REASONING-ARCHITECTURE-TEST-CONTRACT`
- CORE_BASE_SHA: `52cacb1e7e61acc5c48335303df2c51db9f8dd5c`
- MARKET_CONTEXT_SHA: `d183241dad266a50d9ad8b12d831734317edf7b7`
- ASSISTANT_CONTEXT_SHA: `1309b1d18a86346480d5196533d3245840d1ff24`
- RESEARCH_CANDIDATE_CONTEXT: PR #117 / `20968507ddef842bacb7b84a1b0da2cbed1b88ec`
- Status: design and executable non-production contract only; no production orchestration change while PR #117 is unmerged.

## Target state machine

```text
P0 C03 prepare
  ↓
Julia cognition pass N
  ↓                              ↓
structured tool call             final judgment
  ↓                              ↓
capability authorization         turn complete
  ↓
one Market or Research execution
  ↓
typed ToolResult / Evidence / control outcome
  ↓
C03 projection and evidence re-entry
  ↓
Julia cognition pass N+1
```

The turn-local owner is `JuliaSession`, acting as the C1 cognitive executor. It owns the bounded loop and its termination state; neither the capability bridge, a Market/Research provider, nor C03 decides when Julia continues or stops. All state is local to the turn and its explicit package lineage. The production implementation should extract this loop into a turn-scoped orchestration helper only if it keeps `JuliaSession` as the sole owner and does not create a second authority.

## Fixed limits

- Maximum total Julia cognition passes per user turn: **7**.
- Maximum total capability executions per user turn: **6**.
- Maximum structured tool calls per model response: **1**, exactly as in the validated invocation policy.
- The two limits are independent. A missing structured call retry or duplicate rejection consumes a cognition pass but no capability execution.
- The v0.1 budget intentionally admits the canonical first composite investigation: five Market reads followed by one Research query and Julia's final judgment. It must not be reduced below six executions / seven passes without replacing the affected acceptance path.
- Hitting the cognition-pass limit terminates immediately and fail-closed: no further model pass and no fabricated Julia judgment.
- Hitting the tool-execution limit executes no over-budget capability and projects typed `tool_call_budget_exceeded` control exactly once. If cognition budget remains, Julia may make at most one governed limitation response using already admitted evidence. If that continuation emits another tool request instead, the turn terminates immediately and fail closed. A limitation response is `LIMITATION`, not a fresh evidence-backed investment judgment.

## Cognition and tool contract

1. Each model response is parsed as either exactly one fenced structured call or no structured call. A response containing a second call, mixed final text plus a call, malformed JSON, or an unrecognized capability is rejected before execution.
2. Raw user text never selects, authorizes, or routes a capability. In particular, `requires_tool(raw_user_text)` and keyword market intent routing must not be conditions for tool admission in the I3 loop. The governed active question may remain visible to every Julia continuation through C03; this prohibition is about capability selection, not erasing Tony's question.
3. Authorization and execution use the existing typed capability path. A non-ALLOW decision or pre-authorization failure is projected as control, never disguised as provider evidence.
4. A successful Market or Research execution returns its envelope unchanged as `ToolResult.structured_output`. Domain `PARTIAL`, `FAILURE`, and provider absence remain visible inside that envelope; Core does not normalize them into success.
5. Every continuation is built solely by C03 from the explicit parent package. No direct prompt concatenation, assistant-message fabrication, raw user re-routing, or hidden model-visible bypass is permitted.
6. The validated invocation policy is copied to every C03 child and rendered in every continuation. A package missing that policy cannot continue.
7. Evidence is accumulated as an ordered, turn-scoped ledger in package lineage. Prior evidence remains visible within budget while each projection clearly identifies its current ToolResult and provenance.
8. Repeated execution is prevented by a fingerprint of validated capability identity plus normalized arguments. A duplicate request is rejected safely, projected as control, and may receive one Julia continuation; it is never executed as a second observation.
9. Provider `SUCCESS`, `PARTIAL`, and `UNAVAILABLE` all re-enter Julia. `PARTIAL` may lead Julia to request complementary evidence. `UNAVAILABLE` may lead Julia to revise its plan or state the limitation, but never to a fallback provider, direct raw-text research, or hidden substitute workflow.
10. Tool evidence never mutates identity, persona, relationship, continuity, canonical conversation, or memory authority. Memory admission, if ever added, is a separate governed admission decision after the turn.
11. Final user-visible Julia judgment is produced only by a cognition pass following the necessary C03 projection. Tool workers never author it. A cognition-pass hard limit is explicitly not a Julia judgment; a tool-budget limitation response is a distinct `LIMITATION`, also not a fresh investment judgment.
12. Async execution is serial within the turn. Each capability has a bounded lifecycle and must be cancelled/awaited on user cancellation or runtime shutdown before the turn ends; no background acquisition can attach later.

## Lineage

- `conversation_id` and `turn_id` remain immutable for every package in a turn.
- Each projection receives a globally non-empty unique `generation_id`.
- The I3 implementation must not reuse the current `gen_tool_{turn_count}` value for two executions. A suggested readable form is `gen_{turn_id}_pass_{pass}_tool_{tool_index}_{uuid12}`, with any collision rejected.
- `parent_package` is always the immediately preceding concrete C03 package. Tool evidence, control outcomes, and retry packages form one explicit causal chain.

## PR #117 boundary

The accepted Research shape is the frozen I2A C03 seam: `research.web.query` with a non-empty `query`, executed by a registered Research provider returning a typed result. PR #117 adds the Anthropic worker composition but does not grant that worker capability selection or final-judgment authority.

When Research is absent because PR #117 is not merged or `ANTHROPIC_API_KEY` is not configured, the public composition must surface typed `UNAVAILABLE`/`provider_not_found` provenance. Julia may then stop, ask a narrower question, or use a distinct Market capability if that is an explicitly revised plan. It must not invoke a deterministic substitute or pretend Research succeeded.

## Production implementation boundary

No production file is changed by this task. The expected future I3 production path is limited to:

- `julia_core/runtime/julia_session.py`
- a turn-scoped orchestration helper under `julia_core/runtime/`
- narrowly coordinated C03 evidence-ledger support in `julia_core/runtime/context_execution_runtime.py`
- existing typed capability dispatch seams

Any change to Research itself must remain subordinate to PR #117 and a separate post-merge implementation task.

## Current baseline classification

Already true on the core base:

- one tool can execute and its typed result re-enters a second Julia cognition pass through C03;
- Market structured envelopes and provenance are defensively projected;
- C03 retains the validated invocation policy on a tool continuation;
- typed pre-authorization/control outcomes avoid the evidence frame;
- final judgment is separated from the subordinate tool worker.

Expected P2-I3 gaps:

- the current loop is hard-coded to at most one execution and one continuation;
- no six-tool evidence-ledger continuation exists;
- two tool projections can reuse the same `gen_tool_{turn_count}`;
- raw text still reaches `requires_tool(text)`;
- deterministic market keyword routing remains in legacy synchronous preparation;
- hard iteration and duplicate-call controls are absent;
- streaming remains single-pass and does not provide I3 capability parity.

Forbidden behavior:

- direct raw-user-text capability routing;
- deterministic investment or market workflow fallback;
- more than one call executed from one model response;
- final response after bypassing C03 evidence re-entry;
- tool observation becoming canonical memory merely because it was observed;
- mutating identity/continuity authority from evidence;
- hidden fallback after Research is unavailable.

## Acceptance matrix

The executable contract is `tests/runtime/test_rd1_p2_i3a_iterative_reasoning_contract.py`.

| ID | Scenario | Classification |
| --- | --- | --- |
| I3A-01 | Market → Julia → Research → Julia final | harness target |
| I3A-02 | Research → Julia → Market → Julia final | harness target |
| I3A-03 | two successful tools, accumulated evidence and lineage | harness target |
| I3A-04 | `PARTIAL` then complementary Research request | harness target |
| I3A-05 | `UNAVAILABLE` then Julia states limitation without fallback | harness target |
| I3A-06 | duplicate request rejected before execution, then C03 continuation | harness target |
| I3A-07 | hard pass limit terminates without fabricated judgment | harness target |
| I3A-08 | production raw-text router absent | expected RED gap (`xfail(strict=True)`) |
| I3A-09 | response with two structured calls rejected before execution | forbidden behavior |
| I3A-10 | final only after evidence C03 re-entry | harness target |
| I3A-11 | validated policy visible on every continuation | harness target |
| I3A-12 | evidence does not mutate identity/continuity/memory authority | harness target |
| I3A-13 | event.resolve → event.read → product.read → product.linkage.read → state.read → research.query → Julia final | canonical composite target |
| I3A-14 | tool-call budget permits one governed limitation response without fabricated judgment | harness target |
| I3A-15 | post-limitation tool request terminates immediately without execution or another continuation | forbidden behavior |

The harness is deliberately test-only. Green harness tests define the target contract; strict expected-failure tests identify production gaps that must not be hidden by implementing this design before PR #117 merges.
