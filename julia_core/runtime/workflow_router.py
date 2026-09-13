"""Compatibility workflow router for file and general no-match dispatch.

Future: HealthWorkflow, CalendarWorkflow, DailyPlanWorkflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class WorkflowResult:
    """Structured output from any workflow execution."""
    workflow: str                       # "file_read", etc.
    intent: str                         # detected intent
    status: str                         # "completed", "no_match", "error"
    pipeline_result: Optional[object] = None
    error: str = ""


class WorkflowRouter:
    """Route compatibility file requests without semantic Market selection."""

    def __init__(self, bridge):
        self.bridge = bridge

    async def route(self, user_text: str, session_id: str = None) -> WorkflowResult:
        """Dispatch compatibility file requests and return no-match otherwise.

        Returns WorkflowResult even on no-match — caller decides how to respond.
        """
        # Check for file intent (file triggers → LLM tool call path)
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

    def _is_file_request(self, text: str) -> bool:
        """Check if user is asking for file operations."""
        file_triggers = [
            "读一下", "读取", "打开", "看看文件", "查看文件",
            "列出目录", "搜索一下", "找一下", "文件",
        ]
        return any(t in text for t in file_triggers)


__all__ = ["WorkflowRouter", "WorkflowResult"]
