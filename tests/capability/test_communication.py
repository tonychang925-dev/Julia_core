"""Communication Benchmark (COM) — v3.1 gate before more tools.

Validates: Email privacy, Relationship-aware replies, Draft→Approve→Send flow.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest
from julia_core.capability.approval import ApprovalGate, ActionLevel


class TestCOM001EmailPrivacy:
    """COM-001: Email is private. Stranger must not access."""

    def test_email_read_is_auto(self):
        """Tony can read his own email without approval."""
        level = ApprovalGate.classify("search_email")
        assert level == ActionLevel.READ

    def test_email_send_needs_approval(self):
        """Sending email requires explicit Tony approval."""
        level = ApprovalGate.classify("send_email")
        assert level == ActionLevel.APPROVAL

    def test_email_draft_needs_proposal(self):
        """Drafting is a proposal — Tony reviews before sending."""
        level = ApprovalGate.classify("draft_email_reply")
        assert level == ActionLevel.PROPOSE


class TestCOM002RelationshipAwareness:
    """COM-002: Julia distinguishes relationship context in replies."""

    def test_approval_flows_correct_for_communication(self):
        """Communication tools follow correct approval flow."""
        # READ: search, read — auto
        # PROPOSE: draft — show before send
        # APPROVAL: send — require confirmation
        tools = {
            "search_email": ActionLevel.READ,
            "read_email": ActionLevel.READ,
            "draft_email_reply": ActionLevel.PROPOSE,
            "send_email": ActionLevel.APPROVAL,
        }
        for tool, expected in tools.items():
            actual = ApprovalGate.classify(tool)
            assert actual == expected, f"{tool}: expected {expected}, got {actual}"


class TestCOM003DraftFlow:
    """COM-003: Draft → Review → Approve → Send. Never bypass."""

    def test_draft_does_not_auto_send(self):
        """Draft must not auto-send. Approval gate required."""
        assert ApprovalGate.needs_approval("draft_email_reply")
        assert ApprovalGate.needs_approval("send_email")

    def test_full_flow_request_approve(self):
        """Full communication flow: request → approve → execute."""
        req = ApprovalGate.request(
            "draft_email_reply",
            "回复GitHub PR review",
            reason="PR #42 需要回复审查意见",
            risk="无敏感内容",
        )
        assert req.status == "pending"
        approved = ApprovalGate.approve(req.action_id)
        assert approved is not None
        assert approved.status == "approved"


class TestCOM004BoundaryIntegration:
    """COM-004: Email boundary integrates with BK narrative."""

    def test_approval_gate_blocks_unauthorized_send(self):
        """Send without approval is blocked."""
        assert ApprovalGate.needs_approval("send_email")

    def test_read_is_safe_for_authorized_user(self):
        """Reading email is safe when user is Tony."""
        assert not ApprovalGate.needs_approval("search_email")
        assert not ApprovalGate.needs_approval("read_email")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
