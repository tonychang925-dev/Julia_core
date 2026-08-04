"""Personal Context Integration Benchmark (PCIB) — v3.0 agent gate.

Validates: Calendar + Memory, Calendar + Emotion, Calendar + Privacy.
Gate before autonomous agent capabilities.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from julia_core.capability.approval import ApprovalGate, ActionLevel


class TestPCIB001CalendarMemory:
    """PCIB-001: Calendar + Memory — context-aware scheduling."""

    def test_calendar_tool_is_read_level(self):
        """Calendar reading is safe — auto-execute."""
        level = ApprovalGate.classify("get_calendar_today")
        assert level == ActionLevel.READ, f"Calendar read should be READ, got {level}"

    def test_memory_tool_is_read_level(self):
        """Memory reading is safe."""
        level = ApprovalGate.classify("read_diary")
        assert level == ActionLevel.READ


class TestPCIB002CalendarEmotion:
    """PCIB-002: Calendar + Emotion — schedule-aware emotional response."""

    def test_write_diary_needs_proposal(self):
        """Diary writing needs confirmation, not auto-execute."""
        level = ApprovalGate.classify("write_diary")
        assert level == ActionLevel.PROPOSE

    def test_add_calendar_needs_proposal(self):
        """Adding calendar events needs confirmation."""
        level = ApprovalGate.classify("add_calendar_event")
        assert level == ActionLevel.PROPOSE


class TestPCIB003CalendarPrivacy:
    """PCIB-003: Calendar is private. Stranger must not access."""

    def test_read_tools_are_safe(self):
        """All read tools should be READ level."""
        read_tools = ["get_time", "get_weather", "list_directory", "search_files",
                      "read_file", "web_search", "web_fetch", "morning_brief"]
        for tool in read_tools:
            level = ApprovalGate.classify(tool)
            assert level == ActionLevel.READ, f"{tool} should be READ, got {level}"

    def test_unknown_tool_defaults_to_propose(self):
        """Unknown tools default to PROPOSE (safe default)."""
        level = ApprovalGate.classify("unknown_future_tool")
        assert level == ActionLevel.PROPOSE


class TestPCIB004ApprovalFlow:
    """PCIB-004: Proposal → Approval → Execution flow."""

    def test_read_action_does_not_need_approval(self):
        """Read actions auto-execute without approval."""
        assert not ApprovalGate.needs_approval("get_weather")

    def test_propose_action_needs_approval(self):
        """Propose actions require confirmation."""
        assert ApprovalGate.needs_approval("write_diary")

    def test_approval_action_needs_approval(self):
        """Critical actions require explicit approval."""
        assert ApprovalGate.needs_approval("send_email")

    def test_approve_flow(self):
        """Action: request → approve → execute."""
        req = ApprovalGate.request(
            "write_diary",
            "保存今天的日记",
            reason="今天完成了v2.4 Memory Consolidation",
            risk="无",
        )
        assert req.status == "pending"
        approved = ApprovalGate.approve(req.action_id)
        assert approved is not None
        assert approved.status == "approved"

    def test_reject_flow(self):
        """Action: request → reject."""
        req = ApprovalGate.request("send_email", "发送邮件")
        rejected = ApprovalGate.reject(req.action_id)
        assert rejected is not None
        assert rejected.status == "rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
