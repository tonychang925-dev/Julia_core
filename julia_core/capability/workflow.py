"""v3.3 Workflow Agent — multi-step task execution.

LLM plans, Runtime provides tools, Approval at each action point.
Not a traditional workflow engine. LLM owns the plan, decides the steps.

Architecture:
  Goal → LLM plans → Tool calls → Observations → Reflection → Proposal → Approval → Execute

Principle: Julia proposes the plan. Tony confirms the actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class WorkflowStep:
    """A single step in a multi-step plan."""
    step_id: int
    description: str          # what this step does
    tool_name: str            # which tool to call
    tool_params: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"   # pending | running | done | failed | skipped
    result: str = ""
    needs_approval: bool = False


@dataclass
class WorkflowPlan:
    """A multi-step plan proposed by Julia for Tony to review."""
    goal: str
    steps: List[WorkflowStep]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "draft"  # draft | approved | running | done | cancelled

    def summary(self) -> str:
        """Generate plan summary for Tony to review."""
        lines = [f"📋 **计划: {self.goal}**", ""]
        for s in self.steps:
            icon = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌", "skipped": "⏭️"}
            lines.append(f"  {icon.get(s.status, '❓')} 步骤{s.step_id}: {s.description}")
            if s.needs_approval:
                lines.append(f"      ⚠️ 需要确认")
        lines.append(f"\n共 {len(self.steps)} 步。确认后执行。")
        return "\n".join(lines)

    def run_step(self, step_id: int, execute_fn: Callable) -> WorkflowStep:
        """Execute a single step. Returns updated step."""
        step = self.steps[step_id]
        try:
            step.status = "running"
            step.result = execute_fn(step.tool_name, **step.tool_params)
            step.status = "done"
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
        return step


class WorkflowAgent:
    """LLM-driven multi-step task execution. Runtime provides tools, LLM plans."""

    @staticmethod
    def create_plan(goal: str, steps: List[Dict]) -> WorkflowPlan:
        """Create a workflow plan from LLM-generated steps."""
        workflow_steps = []
        for i, s in enumerate(steps):
            ws = WorkflowStep(
                step_id=i,
                description=s.get("description", f"Step {i}"),
                tool_name=s.get("tool", ""),
                tool_params=s.get("params", {}),
                needs_approval=s.get("needs_approval", False),
            )
            workflow_steps.append(ws)
        return WorkflowPlan(goal=goal, steps=workflow_steps)

    @staticmethod
    def format_meeting_prep_plan(calendar_data: str = "", project_context: str = "") -> WorkflowPlan:
        """Pre-built plan template for meeting preparation."""
        return WorkflowPlan(
            goal="会议准备",
            steps=[
                WorkflowStep(0, "查看当天日程", "get_calendar_today", {}),
                WorkflowStep(1, "搜索相关项目文件", "search_files",
                            {"pattern": "project", "directory": "/Users/admin"}),
                WorkflowStep(2, "查看最近记忆", "list_recent_memories", {}),
                WorkflowStep(3, "生成会议简报", "morning_brief", {}),
            ],
        )


def register_workflow_tools(registry):
    """Register workflow agent tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="create_plan",
            description="创建一个多步骤任务计划。当Tony说'帮我准备...'或需要多个步骤才能完成的任务时使用。生成计划后请Tony确认再执行。",
            category=ToolCategory.SYSTEM,
            parameters={"goal": "任务目标", "steps": "步骤列表"},
            example="create_plan(goal='准备明天AI项目会议', steps=[...])",
        ),
        lambda goal="", steps=None: (
            WorkflowAgent.create_plan(goal, steps or []).summary()
        ),
    )

    registry.register(
        ToolSchema(
            name="meeting_prep",
            description="自动准备会议：查看日程→搜索文件→查看记忆→生成简报。一站式会议准备。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="meeting_prep()",
        ),
        lambda: WorkflowAgent.format_meeting_prep_plan().summary(),
    )
