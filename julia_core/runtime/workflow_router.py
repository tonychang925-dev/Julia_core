"""R0.3 Workflow Router — intent → workflow dispatch.

Connects MarketBriefPipeline into the runtime execution path.
Future: HealthWorkflow, CalendarWorkflow, DailyPlanWorkflow.

Architecture:
  User utterance → IntentResolver → WorkflowRouter → Pipeline → Result
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from julia_core.reasoning.intents.market_brief import (
    MarketBriefIntentResolver,
    MarketIntent,
)


@dataclass
class WorkflowResult:
    """Structured output from any workflow execution."""
    workflow: str                       # "market_brief", "file_read", etc.
    intent: str                         # detected intent
    status: str                         # "completed", "no_match", "error"
    pipeline_result: Optional[object] = None  # MarketBriefResult or similar
    error: str = ""


class WorkflowRouter:
    """Routes user utterance to the appropriate workflow.

    Currently supports market_brief. Extensible for future workflows.
    """

    def __init__(self, bridge):
        self.bridge = bridge
        self._market_resolver = MarketBriefIntentResolver()

    async def route(self, user_text: str, session_id: str = None) -> WorkflowResult:
        """Detect intent and dispatch to correct workflow.

        Returns WorkflowResult even on no-match — caller decides how to respond.
        """
        # Step 1: Detect market intent
        intent_result = self._market_resolver.resolve(user_text)

        if intent_result.is_market_related:
            return await self._run_market_brief(user_text, session_id, intent_result)

        # Step 2: Check for file intent (file triggers → LLM tool call path)
        if self._is_file_request(user_text):
            return WorkflowResult(
                workflow="file_read",
                intent="file_access",
                status="no_match",  # Delegated to LLM tool call path
            )

        # No matching workflow — LLM handles conversation directly
        return WorkflowResult(
            workflow="conversation",
            intent="general",
            status="no_match",
        )

    async def _run_market_brief(self, user_text, session_id, intent_result) -> WorkflowResult:
        """Execute MarketBriefPipeline through capability bridge."""
        try:
            pipeline_result = await self.bridge.resolve_market_intent(
                user_text, session_id
            )
            return WorkflowResult(
                workflow="market_brief",
                intent=intent_result.intent.value,
                status="completed" if pipeline_result.capability_status == "success" else pipeline_result.capability_status,
                pipeline_result=pipeline_result,
            )
        except Exception as e:
            return WorkflowResult(
                workflow="market_brief",
                intent=intent_result.intent.value,
                status="error",
                error=str(e),
            )

    def _is_file_request(self, text: str) -> bool:
        """Check if user is asking for file operations."""
        file_triggers = [
            "读一下", "读取", "打开", "看看文件", "查看文件",
            "列出目录", "搜索一下", "找一下", "文件",
        ]
        return any(t in text for t in file_triggers)


__all__ = ["WorkflowRouter", "WorkflowResult"]
