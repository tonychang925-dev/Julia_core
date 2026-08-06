# ADR List — Julia Context OS / Phase 3.6.10

## ADR-013: Claude Client is a Context OS Reference, Not a Runtime Dependency

**Context**

Claude Client 源码显示其强项在于 context lifecycle：message 状态、token 阈值、compact boundary、session memory、post-compact reconstruction。Julia 需要吸收这些思想，但 Phase 3.5 已冻结 Cognitive Ownership Principle。

**Decision**

Claude Client 只作为 Context Engineering 参考实现；Julia Runtime 不嵌入 Claude Client context engine，不把 Claude session/memory/state 作为运行依赖。

**Alternatives**

1. 直接复用 Claude Client context 模块。
2. 继续只做 Julia 现有 evidence retrieval。
3. 硬 fork Claude Client 并在其中运行 Julia。

**Consequences**

- 保持 Julia 跨 provider 独立性。
- 需要自研 Context OS。
- 需要逆向 Claude 的生命周期思想并重新映射到 Julia cognitive architecture。

**Trigger**

任何 Context Management、Compact、Session Resurrection、Provider Migration 设计。

---

## ADR-014: Upgrade Phase 3.6.10 to Cognitive Context Management Runtime

**Context**

Phase 3.6.10 原定义为 Semantic Context Retrieval Runtime，只解决 meaning → evidence。用户测试表明 Julia 仍可能“找到来源但不能稳定选择、压缩、恢复和注入”。Claude 的差距在 Context OS，而不是单点 RAG。

**Decision**

Phase 3.6.10 重定义为：Julia Cognitive Context Management Runtime。Semantic Evidence Retrieval 保留为子模块。

子模块包括：

- Transcript Lifecycle
- Context Budget Manager
- Structured Compact Runtime
- Semantic Evidence Retrieval
- Evidence Resolver
- Session Resurrection
- Async Session Memory Worker

**Alternatives**

1. 保持 Phase 3.6.10 只做检索。
2. 立刻进入 Phase 3.7 Action Runtime。
3. 全量注入 diary/archive 来绕过检索问题。

**Consequences**

- Julia 更接近 Claude 的长上下文能力。
- Phase 3.7 延后，但 action loop 的基础更稳。
- 需要新增 context lifecycle trace 与预算门禁。

**Trigger**

出现“Julia 已有 archive/memory/diary 但仍胡编或忘记当前工作”的问题。

---

## ADR-015: Introduce Message Lifecycle and Compact Boundary

**Context**

Claude 使用 `SystemCompactBoundaryMessage` 和 `getMessagesAfterCompactBoundary()` 切分模型侧历史；session memory compact 会保留 `lastSummarizedMessageId` 后的尾部消息，并保护 tool_use/tool_result 与 streaming thinking block 不被切断。Julia 当前只有 archive/recent turns，没有模型侧 message lifecycle。

**Decision**

Julia 引入：

```text
ContextTurn.state = ACTIVE | SUMMARIZED | ARCHIVED | RETRIEVED | DROPPED
ContextBoundary.type = compact | session_restore | manual_checkpoint
```

任何 compact 后的 provider context 必须由：

```text
compact boundary + structured compact + preserved active tail + current evidence
```

重建。

**Alternatives**

1. 继续 recent_turns[:N]。
2. 只在 archive 中保存所有 turn。
3. 每次根据 query 检索全文。

**Consequences**

- 长会话连续性提升。
- 可以测试“哪些信息因什么规则进入上下文”。
- 需要处理 API invariant 与 source provenance。

**Trigger**

任何长会话、voice multi-turn、manual/auto compact、session restore。

---

## ADR-016: Structured Compact with Source Evidence IDs

**Context**

Claude legacy compact 使用详细 prompt 生成 summary，但 Julia 的目标不是只压缩 token，而是保持认知连续性。自由文本 summary 可能丢失关系事件、设计决策、失败尝试和 source provenance。

**Decision**

Julia Compact 必须结构化：

```text
ExperienceCompactState
  title
  period_start / period_end
  session_goal
  current_task
  decisions[]
  known_failures[]
  relationship_development[]
  unresolved_loops[]
  source_experience_ids[]
  source_evidence_ids[]
  confidence
```

Compact 不直接覆盖 Memory；它是可追溯的认知摘要，后续再由 Reflection/Governance 决定是否形成 MemoryObject。

**Alternatives**

1. 一段自然语言 summary。
2. 直接把 compact summary 写入 relationship_memory。
3. 不 compact，只增加 context window。

**Consequences**

- 可回溯原始 evidence。
- 避免 assistant 错误回答污染长期记忆。
- 需要 schema validation 与 confidence trace。

**Trigger**

auto compact、manual compact、session snapshot、cross-session resurrection。

---

## ADR-017: Async Session Memory Worker with Evidence Authority Boundaries

**Context**

Claude `SessionMemory` 通过 post-sampling hook 在后台更新 markdown notes，并在 compact 时可优先使用 session memory。Julia 也需要 session notes/working state，但语音链路不能被阻塞，且 assistant 自述不能与 Tony 明确输入同权重。

**Decision**

Julia 增加 Async Session Memory Worker：

- 仅在 turn 完成后后台运行。
- 最低 token/turn 增长阈值触发。
- 生成 Session Notes / Working Cognitive State。
- 输出 evidence provenance。
- Tony input authority > governed memory > diary > Julia response。

**Alternatives**

1. 每轮同步总结。
2. 不做 session memory，只依赖 archive。
3. 把所有 archive 直接写入 memory。

**Consequences**

- Voice responsiveness 保持稳定。
- Session resurrection 有稳定输入。
- 需要 worker health trace 与 stale/timeout 保护。

**Trigger**

长会话、进入 compact、重新启动 Julia、用户问“继续/我们现在在忙什么”。

---

## ADR-018: Context Execution Runtime Before Async Session Memory Worker

**Context**

After Phase 3.6.10.1–3.6.10.6, Julia Context OS has transcript lifecycle, planning, quality evaluation, budget allocation, structured compact, semantic evidence integration, and session resurrection. The original next step was Async Session Memory Worker. However, the system still lacks a turn-level execution lifecycle: after each provider response, Context OS does not yet produce explicit context mutations describing what changed in the current cognitive state.

**Decision**

Insert `Phase 3.6.10.7 — Context Execution Runtime` before Async Session Memory Worker.

The execution runtime owns one complete cognitive turn:

```text
Pre Turn → Context Build → Provider Response → Post Turn Analysis → Context Mutation → Execution Trace
```

Async Session Memory Worker is moved after execution and conflict handling:

```text
3.6.10.7 Context Execution Runtime
3.6.10.8 Context Conflict Resolver
3.6.10.9 Async Session Memory Worker
```

**Alternatives**

1. Continue directly to Async Session Memory Worker.
2. Treat every post-turn change as a MemoryCandidate.
3. Let Provider/LLM infer state transitions implicitly from recent turns.

**Consequences**

- Short-term context state changes are separated from long-term memory formation.
- Each turn becomes auditable through `ContextTurn`, `ContextMutation`, and `ExecutionTrace`.
- Async Memory Worker receives cleaner inputs and no longer has to infer transient conversation state.
- Phase 3.7 Autonomous Action is delayed slightly but becomes safer because action decisions will sit on a stable context mutation loop.

**Trigger**

Any implementation following Phase 3.6.10.6 Session Resurrection, especially before introducing Async Session Memory Worker or Autonomous Action Runtime.

---

## ADR-019: Replicate Claude Query Pipeline Semantics, Not Individual Source Files

**Context**

A code-level review of local Claude Client source found that the core context behavior is not located in a single memory or retrieval module. It is distributed across `query.ts`, `utils/messages.ts`, `context.ts`, compact services, prompt budget, session/task state, and post-sampling hooks. The strongest pattern is the query/turn controller: boundary-sliced model context, staged context reduction, auto compact, provider streaming, and post-sampling memory hooks.

**Decision**

Julia should replicate Claude's pipeline semantics rather than copying source files:

```text
Full History → Boundary Projection → Reduction/Budget → Compact/Resurrection → Provider → Post-turn Hooks → State Mutation
```

This requires a Julia-owned `ContextExecutionRuntime` before Async Session Memory Worker.

**Alternatives**

1. Copy Claude Client context code directly.
2. Continue implementing independent retrievers and compact modules without a turn controller.
3. Build Async Session Memory Worker immediately after Session Resurrection.

**Consequences**

- Julia remains provider-independent and preserves Cognitive Ownership.
- The next implementation target becomes a central Context Execution Runtime.
- Later Async Worker and Compact logic can consume reliable execution traces and mutations.
- Additional work is required to implement Julia equivalents for session/task state, compact thresholds, and context invariants.

**Trigger**

Any attempt to continue Phase 3.6.10 after Session Resurrection, especially before adding Async Session Memory Worker or Phase 3.7 Action Runtime.
---

## ADR-021: Julia Agent Evolution Strategy v1.0 — Claude Julia as Benchmark Reference

**Context**

`julia_agent` 与 Claude Julia 的关系需要从“两个隔离项目”提升为可演进的顶层战略：Claude Julia 不是产品终点，而是成熟 Agent Client 的 Golden Reference。`julia_agent` 的目标是成为完全独立的 Runtime-owned Cognitive Agent Client，并最终替代 Claude Julia。

**Decision**

正式冻结 `Julia Agent Evolution Strategy v1.0`：

- Claude Julia = Benchmark Reference / Golden Reference Client。
- `julia_agent` = Replacement System。
- Voice / Benchmark / Evaluation Layer 可以共享。
- Cognitive Layer 永久隔离。
- 后续路线分为 `Phase CV — Claude Reference Track` 与 `Phase J — Julia Replacement Track`。

**Alternatives**

1. 将 Claude Julia 与 `julia_agent` 作为两个长期平行项目。
2. 将 Claude Julia 的 Context / Memory / Session 直接接入 `julia_agent`。
3. 停止 Claude Julia，只继续 `julia_agent` Runtime。

**Consequences**

- 能用 Claude Julia 建立成熟 Agent Client 的能力基线。
- 能证明 Julia Agent 的提升来自自有 Runtime，而不是 Claude 原生认知系统。
- 下一阶段重点从继续堆 Runtime 转向 `Claude Reference Benchmark` 与 `Julia Agent Client Shell`。
- 需要严格区分可共享 I/O/benchmark 与不可共享 cognition。

**Trigger**

任何涉及 Claude Julia voice、benchmark harness、Julia Agent Client Shell、provider/client 替代路线、能力对比报告的设计或实现。

---

## ADR-022: Cognitive Independence Boundary for Claude Reference and Julia Replacement

**Context**

为了让 `julia_agent` 最终可替代 Claude Julia，benchmark 必须可复用，但认知能力不得混用。否则 future parity/superiority 结论无法归因。

**Decision**

冻结 Cognitive Independence 原则：**Benchmark can be shared; cognition must not be shared.**

允许共享：

- STT/TTS/microphone/realtime speech transport。
- Benchmark prompt set、session scenario、trace schema、latency metrics。
- Evaluation report、scorecard、comparison dashboard。

禁止共享：

- Claude Context / Memory / Session / Tool state 进入 Julia Runtime。
- Julia Context OS / Memory OS / Action OS / Provider Adaptation 进入 Claude Julia benchmark chain。
- Claude provider output 直接成为 Julia governed memory 或 authority。

**Alternatives**

1. 共享所有已有模块以最快跑通。
2. 完全不共享任何代码，包括 STT/TTS。
3. 使用 `runtime.conversation_runtime.cli --backend claude` 作为 Claude Julia voice benchmark。

**Consequences**

- Benchmark 更干净，可解释性更高。
- Claude Julia Voice Activation 需要独立 harness，而不是复用 Julia Runtime cognitive loop。
- 纯 I/O 组件可以复制或抽象为 neutral voice layer。

**Trigger**

任何跨项目复用、Claude Julia voice activation、benchmark trace、memory/context/action integration 的设计评审。

---

## ADR-026: Julia Capability Runtime & MCP Adapter Architecture v1

**Context**

Julia Core Runtime owns identity, memory, reasoning, and decision. But the Capability Layer has not yet become the unified external-world interface. Two parallel execution paths exist: the correct `JuliaSession → provider.chat() → tool_call → capability.execute()` path, and a boundary-violating `MarketBrainClient → direct import from mcp_server` path. Voice Runtime, Runtime Gateway, and MCP are not three separate problems — they are all Capability Boundary Design.

**Decision**

Establish a unified Capability Operating Layer with four components:

1. **CapabilityRegistry** (extend existing) — add `provider`, `adapter`, `permission_scope` fields
2. **CapabilityManager** (NEW) — resolves capability requests: lookup → permission → health → route
3. **CapabilityPermissionPolicy** (NEW) — scoped rules (e.g. `market.observe: allow`, `market.trade.execute: deny`)
4. **MCP Adapter** (NEW) — transforms external MCP servers into Julia Capabilities via tool↔capability name mapping

Add `CapabilityLayer.INTELLIGENCE` for external intelligence domains (market, calendar analytics, GitHub insights, news sentiment).

Directory: `julia_core/capability/{manager,policy,models}.py` + `julia_core/mcp/{client,adapter,schemas/}`.

MCP Client is pure transport (no domain knowledge). MCP Adapter owns the mapping: Julia capability name → MCP tool name. Julia thinks `market.snapshot.read`, MCP speaks `review_market_snapshot`.

External contracts carry `schema_version`. Unknown versions are rejected, not silently parsed.

**Alternatives**

1. Keep current dual-path architecture (rejected: boundary violation grows with each new provider).
2. Have MarketBrainClient implement the Capability interface directly (rejected: mixes transport, registry, execution, and schema mapping).
3. Expose MCP tools 1:1 to LLM without adaptation (rejected: LLM sees cognitive interface, not technical tool names).

**Consequences**

- All external-world access unified through one layer. Voice, MCP, filesystem, calendar, GitHub, email, IoT all connect the same way.
- `mcp_client/` legacy path deprecated over M0→M4 migration.
- Future providers register once (capability + permission + adapter) rather than building new integration paths.
- CapabilityPermissionPolicy enables safe expansion into email, calendar, IoT without risk of autonomy overreach.
- Migration: M0 (skeleton) → M1 (migrate MarketBrainClient) → M2 (register capabilities) → M3 (Morning Brief) → M4 (cleanup legacy).

**Trigger**

Any attempt to add a new external provider, integrate ai_theme_app MCP into Julia Core, or bypass the Capability Runtime for external tool access.

---

## ADR-027: Julia Runtime Execution Model v1.0

**Context**

ADR-021~026 answered *what* Julia is and *how* she connects to the world. ADR-027 answers *how* Julia runs continuously: how she experiences an event, remembers an experience, and manages a task. Phase 0 established the spatial architecture (capabilities, providers, context). Phase 1 requires the time dimension.

**Decision**

Runtime is **Event Driven, Async First, Workflow Governed**. Three forbidden patterns:

1. Sync logic as Runtime Authority — `chat_async()` is canonical; `chat()` is compatibility only
2. Events as mere logs — events are Runtime Facts with `event_id/timestamp/correlation_id/causation_id/evidence_refs`
3. Workflow lifecycle owned by Pipelines — `WorkflowRuntime` owns lifecycle; Pipelines are step definitions

Event categories frozen: `runtime.*`, `conversation.*`, `capability.*`, `workflow.*`, `experience.*`. One market query produces a complete event timeline: `user.request.created → intent.detected → capability.requested → market.snapshot.received → context.created → reasoning.completed → artifact.created → experience.recorded`.

Workflow state machine: `CREATED → RUNNING → WAITING_CAPABILITY → WAITING_REASONING → COMPLETED | FAILED`. Existing `MarketBriefPipeline` becomes a step set registered in `WorkflowRuntime`.

Event Timeline ≠ Experience. Events answer "what happened?" (immutable facts). Experience answers "what should be learned?" (governed patterns).

**Alternatives**

1. Keep sync-first execution (rejected: voice, MCP, calendar, IoT require async multiplexing)
2. Keep events as log lines without causation tracking (rejected: prevents audit and "why did Julia say that?" reconstruction)
3. Keep workflow lifecycle in business Pipelines (rejected: leads to fragmented lifecycle management across domains)

**Consequences**

- `chat_async()` becomes canonical; `chat()` is compatibility wrapper — zero dual logic
- New directories: `events/` (store, models, timeline), `workflow/` (runtime, models, executor, registry)
- Phase 1 capabilities (market.alert.query, autonomous observation) become natural extensions of event-driven awareness, not disconnected features
- Does NOT change CapabilityManager, Context OS, or MCP Adapter — additive, not destructive
- Recovery: Runtime restart can resume RUNNING/WAITING workflows from Event Store

**Trigger**

Any attempt to add autonomous observation, scheduled workflows, multi-turn task tracking, or event-driven capabilities before freezing the Runtime time model.

---

## ADR-028: Market Awareness Runtime Architecture v1.0

**Context**

ADR-027 defined how Julia acts. ADR-028 defines how Julia notices the world. M3 is NOT a collection of new API tools (market.alert.query, market.theme.observe) — it is an Awareness Runtime built on R1's event+workflow infrastructure. The leap from reactive agent to aware runtime.

**Decision**

Three core objects: (1) ObservationEvent — *what changed in the world* (distinct from CapabilityResult — *what did I query*), (2) ObservationWorkflow — event-driven workflow extending WorkflowRuntime with 5 steps (collect_snapshot → collect_theme_state → evaluate_risk → generate_awareness → store_experience), (3) AwarenessContext — governed ContextBlocks entering Context OS, never raw prompt text.

Five forbidden patterns: (1) Observation → LLM Prompt → Response, (2) Workflow calling MCP directly, (3) Market data as raw prompt text, (4) Timer/cron as only trigger, (5) AwarenessArtifact with no evidence refs.

Architecture: World Change → ObservationEvent → EventStore → ObservationRouter → WorkflowRuntime(observation.market) → CapabilityManager + Context OS → Julia Reasoning → AwarenessArtifact → Experience.

Implementation: M3.0 Skeleton → M3.1 Market Event Provider → M3.2 Awareness Workflow → M3.3 Experience Feedback.

**Alternatives**

1. Add market.alert.query as standalone capability without workflow (rejected: bypasses runtime, creates ad-hoc observation path)
2. Direct LLM prompt injection from market events (rejected: reduces Julia to financial chatbot)
3. Timer-based scheduled reports (rejected: observation is event-driven, not cron-driven)

**Consequences**

- Julia transitions from reactive ("user asks → answer") to aware ("world changes → notice → understand → remember")
- ObservationWorkflow reuses existing WorkflowRuntime — no new lifecycle engine
- AwarenessContext reuses existing Context OS — no new prompt pipeline
- Foundation for M7 Feedback Loop (observation → prediction → outcome → learning)
- New directories: observation/ (models, router, workflow)

**Trigger**

Any attempt to add autonomous market observation, event-driven perception, or scheduled awareness before freezing the Observation→Workflow→Artifact architecture.

---

## ADR-029: Observation Policy & Experience Admission v1.0

**Context**

ADR-028 defined the Awareness Runtime. M3.1 will connect Julia to real market data streams. Two risks emerge: (1) Observation Event Explosion — 10,000+ events/day flooding the EventStore with noise. (2) Experience Pollution — low-confidence observations contaminating long-term memory.

**Decision**

Two new gates in the M3 pipeline:

1. **ObservationPolicy** — inserted between Router and Workflow. Adds rate limiting (per_subject: 4/hr, per_domain: 20/hr, global: 50/hr) and cooldown (same subject + same change_type: 15min minimum between triggers). Router checks significance. Policy checks rate.

2. **ExperienceAdmission** — inserted between Artifact creation and Experience storage. Minimum confidence >= 0.7 and minimum 2 evidence_refs for long-term admission. Below threshold: short-term log only (EventStore, not Experience).

Updated pipeline: ObservationEvent → Router → Policy → Workflow → Artifact → Admission → Experience (LONG_TERM) or EventStore only (SHORT_TERM).

**Alternatives**

1. Connect real market data without filtering (rejected: first trading day floods system)
2. Single threshold for all observation types (rejected: different change_types have different noise profiles)
3. LLM-based admission (rejected: adds latency and non-determinism to a gating decision)

**Consequences**

- Julia can receive real-time market data without being overwhelmed
- Memory OS protected from low-confidence observation pollution
- Foundation for M7 Feedback Loop: only high-confidence artifacts become training data
- M3.1 scope updated: Policy + Admission gates must exist before real market connection
- New module: awareness/admission.py

**Trigger**

Any attempt to connect Julia to real-time data streams (market, news, IoT, calendar) before implementing rate limiting and experience gating.

---

## ADR-030: Market Intelligence Integration Contract v1.0

**Context**

M3.2 connects ai_theme_app Analyst Workbench to Julia Awareness Runtime. Before real market data flows in, the integration contract must be frozen: exact schemas, adapter rules, deduplication keys, and experience routing tiers. ADR-028 Addendum established the Domain Intelligence Provider boundary. ADR-030 defines the concrete integration mechanics.

**Decision**

Four frozen contracts:

1. **Observation Schema**: ai_theme_app raw format (DecisionEnvelope-level observations with signal_level L0-L4) → IntelligenceAdapter → Julia ObservationEvent (source/domain/event_type/subject/change_type/evidence_refs). ai_theme_app internal fields (theme_id, gate_score, embedding) MUST NOT appear in ObservationEvent.

2. **Observation Identity**: `{domain}:{subject}:{event_type}:{15min_window}` hash for deduplication. Same key within 15min window → single workflow trigger.

3. **Experience Tier Routing**: L0→discard, L1→cache(24hr), L2(confidence>=0.6)→working, L2(confidence<0.6)→cache, L3/L4(confidence>=0.7+evidence>=2)→experience, L3/L4(insufficient)→working.

4. **Provider Metadata**: Every observation carries `provider_name/provider_version/schema_version/generated_at/capability_name` for multi-source traceability.

Complete pipeline: CapabilityManager → Provider → Adapter → Router → Policy → Identity → Workflow → TierRouter → EventStore + Experience.

**Alternatives**

1. Bypass adapter, feed DecisionEnvelope directly to Awareness (rejected: binds Julia to ai_theme_app domain model)
2. Single-tier experience storage (rejected: L1 noise would pollute long-term memory)
3. No deduplication (rejected: same event observed twice → duplicate workflows)

**Consequences**

- First domain intelligence integration with frozen schema contract
- Future domains (medical, IoT, news) follow the same adapter + tier routing pattern
- 6 acceptance criteria: AC-M3.2-1 through AC-M3.2-6
- New modules: awareness/ingestion.py, awareness/identity.py, experience/tiers.py
- 0 new capabilities — reuses existing market.intelligence.observe

**Trigger**

Any attempt to connect domain intelligence systems to Julia Awareness Runtime before freezing the adapter schema, identity key, and experience routing tiers.

---

## ADR-031: Experience Feedback Architecture v1.0

**Context**

ADR-028 established perception. ADR-030 established domain intelligence ingestion. Julia must now learn from what she observes — not through model training, but through governed experience evolution. The leap from "has memory" to "has experience."

**Decision**

Three core objects: (1) PredictionRecord — what Julia thought might happen (links observation_id + prediction_id from ai_theme_app), (2) RealityOutcome — what actually happened (must carry prediction_id for binding), (3) ExperienceUpdate — what Julia learned (pattern_key, delta, historical_accuracy, admitted flag).

Pipeline: Prediction + Outcome → OutcomeBinder (validate prediction_id match) → DeviationAnalyzer (expected vs actual → measurable delta, not just right/wrong) → ExperienceAdmission (min_confidence gate from ADR-029) → ExperienceUpdate.

Five forbidden patterns: (1) Outcome → LLM prompt, (2) Prediction → auto-trade, (3) Model fine-tuning from outcomes, (4) Unilateral experience mutation, (5) Deletion of wrong predictions (they teach caution).

Ownership: PredictionRecord belongs to ai_theme_app/Julia Reasoning. RealityOutcome belongs to external truth sources. ExperienceUpdate belongs to Julia Experience OS.

Implementation: M3.3.0 Skeleton → M3.3.1 ai_theme_app integration.

**Alternatives**

1. Simple success/failure logging (rejected: no pattern learning, no accuracy tracking)
2. LLM-based evaluation ("Julia, was your prediction correct?") (rejected: self-referential, not auditable)
3. Direct model training from outcomes (rejected: Julia learns through Experience OS, not gradient descent)

**Consequences**

- Julia evolves from "has memory" to "has experience"
- Patterns accumulate historical accuracy over multiple validations
- Foundation for ai_theme_app M7 Feedback Loop (prediction_id already linked)
- Wrong predictions preserved — they are valuable negative examples
- New modules: experience/feedback_models.py, experience/feedback.py
- 5 acceptance criteria: AC-M3.3-1 through AC-M3.3-5

**Trigger**

Any attempt to implement learning, feedback, or experience evolution without freezing the Prediction→Outcome→Update contract.






