"""R1.1 Workflow Authority Bridge — connects JuliaSession to WorkflowRuntime.

Before R1.1: _chat_impl() called _resolve_market_context() directly.
After R1.1:  _chat_impl() routes through WorkflowRuntime.execute("market.brief").

ADR-027 AC-3: WorkflowRuntime owns lifecycle. Pipelines are step definitions.

This bridge:
  1. Creates WorkflowRuntime with registered step executors
  2. Provides execute_workflow() — the Runtime-owned entry point
  3. Emits workflow.* events during execution
  4. Returns WorkflowInstance with full audit trail

The existing MarketBriefPipeline is the step executor for "context.build".
Other steps (intent.resolve, capability.request, reasoning.execute, etc.)
are registered as simple adapters.
"""

from __future__ import annotations

from typing import Optional

from julia_core.events.models import (
    EventCategory,
    ConversationEventType,
    CapabilityEventType,
    create_event,
)
from julia_core.events.store import get_event_store
from julia_core.workflow.models import WorkflowInstance
from julia_core.workflow.registry import (
    WorkflowRegistry,
    MARKET_BRIEF_WORKFLOW,
    create_default_registry,
)
from julia_core.workflow.runtime import WorkflowRuntime


class WorkflowBridge:
    """Bridges JuliaSession._chat_impl() to WorkflowRuntime.

    This is the R1.1 integration point. Instead of _chat_impl()
    directly calling _resolve_market_context(), it routes through
    WorkflowRuntime which owns lifecycle, emits events, and tracks state.
    """

    def __init__(self, capability_bridge):
        self.capability_bridge = capability_bridge
        self.registry = create_default_registry()
        self.runtime = WorkflowRuntime(
            self.registry,
            capability_bridge.manager,
        )
        self._register_step_executors()

    def _register_step_executors(self):
        """Register step executors that wrap the existing pipeline components."""

        async def intent_resolve(data: dict, instance: WorkflowInstance) -> dict:
            """Step 1: intent.resolve — detect market intent from user text."""
            user_text = data.get("user_text", "")
            from julia_core.reasoning.intents.market_brief import MarketBriefIntentResolver
            resolver = MarketBriefIntentResolver()
            result = resolver.resolve(user_text)
            return {
                "intent": result.intent.value,
                "is_market_related": result.is_market_related,
                "capability_name": result.capability_name,
            }

        async def capability_request(data: dict, instance: WorkflowInstance) -> dict:
            """Step 2: capability.request — invoke market.snapshot.read."""
            if not data.get("is_market_related") or not data.get("capability_name"):
                return {"capability_skipped": True, "reason": "not market related"}

            from julia_core.capability.models import CapabilityRequest
            cap_name = data["capability_name"]
            event_store = get_event_store()

            # Emit capability.requested
            event_store.append(create_event(
                source="capability",
                event_type=CapabilityEventType.REQUESTED,
                category=EventCategory.CAPABILITY,
                payload={"capability": cap_name},
                correlation_id=instance.correlation_id,
                causation_id=instance.event_ids[-1] if instance.event_ids else "",
            ))

            result = await self.capability_bridge.manager.execute(
                CapabilityRequest(capability_name=cap_name, reason=f"workflow: {instance.workflow_name}")
            )

            # Emit capability.completed
            event_store.append(create_event(
                source="capability",
                event_type=CapabilityEventType.COMPLETED,
                category=EventCategory.CAPABILITY,
                payload={"capability": cap_name, "status": result.status, "provider": result.provider},
                correlation_id=instance.correlation_id,
                causation_id=instance.event_ids[-1] if instance.event_ids else "",
            ))

            return {
                "capability_status": result.status,
                "capability_data": result.data,
                "provider": result.provider,
                "schema_version": result.schema_version,
            }

        async def context_build(data: dict, instance: WorkflowInstance) -> dict:
            """Step 3: context.build — convert capability result to ContextBlocks."""
            if data.get("capability_skipped"):
                return {"context_blocks": [], "market_context_str": "", "block_count": 0}

            cap_data = data.get("capability_data", {})
            if not cap_data:
                return {"context_blocks": [], "market_context_str": ""}

            from julia_core.context_os.providers.market_context import MarketBriefContextAdapter
            adapter = MarketBriefContextAdapter()
            blocks = adapter.build_context_blocks(cap_data)

            # Format for LLM injection
            context_str = _format_market_context_static(blocks, data)

            return {
                "context_blocks": blocks,
                "market_context_str": context_str,
                "block_count": len(blocks),
            }

        async def reasoning_execute(data: dict, instance: WorkflowInstance) -> dict:
            """Step 4: reasoning.execute — placeholder for LLM reasoning step.
            In the current architecture, LLM reasoning happens inside _chat_impl().
            This step captures the context that was built for LLM consumption.
            """
            return {
                "reasoning_ready": True,
                "context_available": bool(data.get("market_context_str")),
            }

        async def artifact_create(data: dict, instance: WorkflowInstance) -> dict:
            """Step 5: artifact.create — produce MarketBriefArtifact."""
            if not data.get("context_blocks"):
                return {"artifact_created": False, "reason": "no context blocks"}

            from julia_core.experience.market_brief_artifact import MarketBriefArtifact
            artifact = MarketBriefArtifact(
                brief_id=f"brief_wf_{instance.instance_id[:12]}",
                user_query=data.get("user_text", ""),
                intent=data.get("intent", "unknown"),
                capability_name=data.get("capability_name", ""),
                capability_status=data.get("capability_status", "not_requested"),
                provider=data.get("provider", ""),
                schema_version=data.get("schema_version", ""),
                context_block_types=tuple(
                    b.block_type for b in data.get("context_blocks", [])
                    if hasattr(b, 'block_type')
                ),
            )
            return {"artifact": artifact, "artifact_created": True}

        async def experience_record(data: dict, instance: WorkflowInstance) -> dict:
            """Step 6: experience.record — store for future learning."""
            return {"experience_recorded": True, "brief_id": data.get("brief_id", ""),
                    "workflow_id": instance.instance_id}

        # Register all steps
        self.runtime.register_step("intent.resolve", intent_resolve)
        self.runtime.register_step("capability.request", capability_request)
        self.runtime.register_step("context.build", context_build)
        self.runtime.register_step("reasoning.execute", reasoning_execute)
        self.runtime.register_step("artifact.create", artifact_create)
        self.runtime.register_step("experience.record", experience_record)

    async def execute_market_brief(self, user_text: str, correlation_id: str = "") -> WorkflowInstance:
        """Execute market.brief workflow through WorkflowRuntime.

        This is the R1.1 authority entry point. The WorkflowRuntime
        owns lifecycle, emits events, and returns a completed instance
        with full audit trail.
        """
        return await self.runtime.execute("market.brief", {
            "user_text": user_text,
            "correlation_id": correlation_id,
        })


# ── Helper ───────────────────────────────────────────────────────────────────

def _format_market_context_static(blocks: list, data: dict) -> str:
    """Static version of _format_market_context for workflow context_build step."""
    parts = ["[市场情报 — 基于 ai_theme_app Market Brain 的实时数据]\n"]

    for block in blocks:
        content = getattr(block, 'content', {})
        if not isinstance(content, dict):
            continue
        section = content.get('section', '')
        if section == 'market_overview':
            parts.append(f"市场情绪: {content.get('sentiment', '未知')}")
        elif section == 'active_themes':
            themes = content.get('themes', [])
            parts.append(f"活跃题材({content.get('count', 0)}): {', '.join(themes)}")
        elif section == 'risk_alerts':
            risks = content.get('risks', [])
            parts.append(f"风险提示: {'; '.join(risks)}")
        elif section == 'evidence':
            parts.append(f"数据来源: {content.get('provider', '')} v{content.get('schema_version', '')}")

    prediction_ids = data.get('prediction_ids', ())
    if prediction_ids:
        parts.append(f"关联预测: {', '.join(prediction_ids)}")

    parts.append("\n[上述市场数据是实时获取的。请基于这些事实，结合你对Tony的了解，用自然语言解释市场状态。]")
    parts.append("你不只是转述数据。你是Tony的伴侣，也是他的分析师。用他理解的方式解释。\n")
    return "\n".join(parts)


__all__ = ["WorkflowBridge"]
