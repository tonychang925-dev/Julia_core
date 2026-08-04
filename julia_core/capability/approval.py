"""v3.0 Agent Approval Layer — gate between reading and acting.

Principle: Read is safe. Write needs confirmation. Act needs approval.
  READ:   Calendar, Weather, Files → auto-execute
  WRITE:  Diary, File edit → propose, confirm
  ACTION: Email, Flight, Payment → propose, require explicit approval

This is NOT a permission system. It's a trust protocol.
Julia proposes. Tony decides. Memory records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class ActionLevel(str, Enum):
    READ = "read"        # Safe. Auto-execute. (weather, time, calendar)
    PROPOSE = "propose"   # Suggest. Needs confirmation. (diary, file edit)
    APPROVAL = "approval" # Critical. Requires explicit Tony approval. (email, flight, payment)


@dataclass
class ActionRequest:
    """A proposed action that needs Tony's approval before execution."""
    action_id: str
    description: str          # What Julia wants to do
    level: ActionLevel
    tool_name: str
    tool_params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""          # Why Julia thinks this is a good idea
    risk: str = ""            # What could go wrong
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"   # pending | approved | rejected | executed


class ApprovalGate:
    """Gate between Julia's intent and world action. Tony is the final authority."""

    _pending: Dict[str, ActionRequest] = {}
    _history: list = []

    @classmethod
    def classify(cls, tool_name: str) -> ActionLevel:
        """Classify a tool by its risk level."""
        READ_TOOLS = {
            "get_time", "get_weather", "get_calendar_today", "get_calendar_upcoming",
            "list_directory", "search_files", "read_file", "read_diary",
            "list_diaries", "list_recent_memories", "web_search", "web_fetch",
            "morning_brief", "list_reminders", "vision_analyze",
            "search_email", "read_email",  # v3.1 communication
        }
        PROPOSE_TOOLS = {
            "write_diary", "write_file", "add_calendar_event", "set_reminder",
            "draft_email_reply",  # v3.1: draft before send
        }
        APPROVAL_TOOLS = {
            "send_email", "book_flight", "make_payment", "delete_file",
            "execute_command",
        }

        if tool_name in READ_TOOLS:
            return ActionLevel.READ
        if tool_name in PROPOSE_TOOLS:
            return ActionLevel.PROPOSE
        if tool_name in APPROVAL_TOOLS:
            return ActionLevel.APPROVAL
        return ActionLevel.PROPOSE  # Unknown: be safe, ask

    @classmethod
    def request(cls, tool_name: str, description: str, params: dict = None,
                reason: str = "", risk: str = "") -> ActionRequest:
        """Create an action request. For PROPOSE and APPROVAL levels, Tony must confirm."""
        level = cls.classify(tool_name)
        req = ActionRequest(
            action_id=f"act_{len(cls._history) + 1:03d}",
            description=description,
            level=level,
            tool_name=tool_name,
            tool_params=params or {},
            reason=reason,
            risk=risk,
        )
        if level != ActionLevel.READ:
            cls._pending[req.action_id] = req
        return req

    @classmethod
    def approve(cls, action_id: str) -> Optional[ActionRequest]:
        """Tony approves an action."""
        if action_id in cls._pending:
            req = cls._pending.pop(action_id)
            req.status = "approved"
            cls._history.append(req)
            return req
        return None

    @classmethod
    def reject(cls, action_id: str) -> Optional[ActionRequest]:
        """Tony rejects an action."""
        if action_id in cls._pending:
            req = cls._pending.pop(action_id)
            req.status = "rejected"
            cls._history.append(req)
            return req
        return None

    @classmethod
    def needs_approval(cls, tool_name: str) -> bool:
        """Check if this tool requires Tony's approval."""
        return cls.classify(tool_name) != ActionLevel.READ

    @classmethod
    def format_proposal(cls, req: ActionRequest) -> str:
        """Format an action proposal for Tony to review."""
        emoji = {"read": "📖", "propose": "✏️", "approval": "⚠️"}
        return (
            f"{emoji.get(req.level.value, '❓')} **{req.description}**\n"
            + (f"  原因: {req.reason}\n" if req.reason else "")
            + (f"  风险: {req.risk}\n" if req.risk else "")
            + f"  操作: {req.tool_name}\n"
            + f"  ID: {req.action_id}\n"
            + f"\n  确认执行？(回复'同意'来确认)"
        )
