"""Julia Action Runtime — what Julia is DOING right now.

Separate from Capability (what she CAN do). Separate from Presence (what STATE she's in).
Action = the verb in progress: searching, reading, listing, thinking.

This bridges tool execution and user experience.
Julia says "I'm looking..." not after — but WHILE she's doing it.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActionPhase(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Action:
    """One action Julia is performing or has performed."""
    name: str                          # "search_files", "read_file", "list_directory"
    phase: ActionPhase
    description: str                   # human-readable: "搜索8月4号的日志..."
    started_at: float = field(default_factory=_time.time)
    completed_at: Optional[float] = None
    result_summary: str = ""           # brief: "找到 1 个文件" or "文件不存在"

    def complete(self, summary: str = ""):
        self.phase = ActionPhase.COMPLETED
        self.completed_at = _time.time()
        self.result_summary = summary

    def fail(self, reason: str = ""):
        self.phase = ActionPhase.FAILED
        self.completed_at = _time.time()
        self.result_summary = reason

    def status_message(self) -> str:
        """Generate a natural status message for the current phase."""
        messages = {
            ActionPhase.STARTED: {
                "search_files": "嗯，我来找一下...",
                "read_file": "找到了，正在读...",
                "list_directory": "我看看这个目录...",
            },
            ActionPhase.COMPLETED: {
                "search_files": f"找到了。{self.result_summary}",
                "read_file": "读完了。",
                "list_directory": f"目录内容如上。{self.result_summary}",
            },
            ActionPhase.FAILED: {
                "search_files": f"没有找到。{self.result_summary}",
                "read_file": f"读不到这个文件。{self.result_summary}",
                "list_directory": f"这个目录打不开。{self.result_summary}",
            },
        }
        defaults = {
            ActionPhase.STARTED: "嗯，我来处理...",
            ActionPhase.COMPLETED: "好了。",
            ActionPhase.FAILED: "这个我做不到。",
        }
        return messages.get(self.phase, defaults).get(self.name, defaults.get(self.phase, ""))


class ActionRuntime:
    """Tracks what Julia is currently doing. Lightweight — just enough for UX presence."""

    def __init__(self):
        self.current: Optional[Action] = None
        self.history: list[Action] = []

    def start(self, name: str, description: str = "") -> Action:
        """Begin an action. Returns the action for tracking."""
        action = Action(name=name, phase=ActionPhase.STARTED, description=description)
        self.current = action
        self.history.append(action)
        return action

    def finish(self, summary: str = ""):
        """Mark current action as completed."""
        if self.current:
            self.current.complete(summary)

    def fail(self, reason: str = ""):
        """Mark current action as failed."""
        if self.current:
            self.current.fail(reason)

    def status_line(self) -> str:
        """Get current status for display."""
        if self.current and self.current.phase == ActionPhase.STARTED:
            return self.current.status_message()
        return ""

    @property
    def last_action(self) -> Optional[Action]:
        return self.history[-1] if self.history else None


# ── Singleton ───────────────────────────────────────────────────────────────

_runtime: Optional[ActionRuntime] = None


def get_action_runtime() -> ActionRuntime:
    global _runtime
    if _runtime is None:
        _runtime = ActionRuntime()
    return _runtime
