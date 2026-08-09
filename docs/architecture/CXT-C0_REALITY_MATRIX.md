# CXT-C0 — Implementation Reality Matrix

**Date**: 2026-08-09
**Status**: FROZEN — Git-tracked source only, no __pycache__ inference

## DESIGNED + IMPLEMENTED + PRODUCTION-BOUND

| Module | Path | Role |
|--------|------|------|
| ConversationRuntime | `runtime/conversation_runtime.py` | Canonical transcript authority |
| SessionRepository | `conversation_state/repository.py` | Atomic persistence + import/export |
| ConversationMessage | `conversation_state/models.py` | Canonical message identity |
| ConversationInteractionState | `runtime/relationship.py` | Per-conversation interaction cache |
| JuliaSession.process() | `runtime/julia_session.py` | Cognitive executor |
| JuliaSession.process_stream() | `runtime/julia_session.py` | Streaming cognitive executor |
| TurnContext | `runtime/julia_session.py` | Per-turn execution isolation |
| ActionRuntime (per-turn) | `runtime/action.py` | correlation_id-keyed action tracking |
| MarketBrainClient | `mcp_client/client.py` | Read-only MCP transport |
| MCPToolAdapter | `capability/providers/ai_theme/adapter.py` | Capability→MCP tool mapping |
| MarketEvidenceFormatter | `capability/market_evidence_formatter.py` | Reusable market evidence→context |
| WorkflowRouter | `runtime/workflow_router.py` | Intent→capability dispatch |
| MarketBriefIntentResolver | `reasoning/intents/market_brief.py` | Market intent detection |
| CapabilitySemanticRouter | `server_v2_1_semantic_router.py` (julia_ai_assistant) | B2 semantic routing |

## DESIGNED + IMPLEMENTED + NOT PRODUCTION-BOUND

| Module | Path | Reason |
|--------|------|--------|
| ContextPlanner | `context_os/planner.py` | Full pipeline not wired to production path |
| ContextResolver | `context_os/resolver.py` | Same — standalone, not in cognitive pipeline |
| ContextBlock | `context_os/block.py` | Defined but _prepare_turn() doesn't use it |
| ContextReconstructor | `context_os/reconstruction.py` | Only used in compact simulation |
| ContinuityCheckpoint | `continuity/checkpoint.py` | Compact scenario only |
| RecoveryPlan | `continuity/recovery.py` | Compact scenario only |
| SessionRecorder | `runtime/session_recorder.py` | Works but not bound to conversation lifecycle |
| SessionSummarizer | `runtime/session/summarizer.py` | Works but ad-hoc trigger |

## DESIGNED + SOURCE MISSING

| Module | Documented In | Status |
|--------|-------------|--------|
| `context_os/transcript/` | ADR-015, ARCHITECTURE_OVERVIEW | No Git-tracked `.py` files |
| `context_os/resurrection/` | ADR-015, ARCHITECTURE_OVERVIEW | No Git-tracked `.py` files |
| `context_os/execution/` | CONTEXT_OS_DESIGN | No Git-tracked `.py` files |
| `conversation_archive/` | ARCHITECTURE_OVERVIEW | Directory does not exist |
| `conversation_runtime/` (dir) | ARCHITECTURE_OVERVIEW | Single file, not directory |
| `context_assembly/` (full) | ARCHITECTURE_OVERVIEW | Only `cd_gate.py`, `density_engine.py` exist |

## LEGACY / TRANSITIONAL

| Path | Current Role | Retirement Plan |
|------|-------------|-----------------|
| `_prepare_turn()` string concat | Model context assembly | CXT-C3: delegate to ContextExecutionRuntime |
| `history[-20:]` | Hardcoded window | CXT-C4: Context OS transcript lifecycle |
| `_load_recent_experiences()` | SessionStore Wake State | CXT-C3: Context OS reconstruction |
| `~/.julia/sessions.json` | Legacy metadata store | CXT-C2: migrate, then read-only compat |
| Voice last-10-turn bootstrap | C1B compatibility bridge | CXT-C5: Context OS → ContextPackage → S2S |
| `js.chat()` / `js.chat_async()` | Legacy singleton entry | Already documented legacy; Gateway :8100 not in product topology |
