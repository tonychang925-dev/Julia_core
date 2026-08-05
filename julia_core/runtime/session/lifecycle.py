"""Session Lifecycle — state machine for session existence.

States: draft → active → reflecting → consolidated → archived

A session starts as 'draft' (created but no messages).
First message activates it. Session end triggers reflection.
"""

from __future__ import annotations
from enum import Enum


class SessionState(str, Enum):
    DRAFT = "draft"            # Created, no messages yet
    ACTIVE = "active"          # Has messages, being used
    REFLECTING = "reflecting"  # Session ended, generating summary
    CONSOLIDATED = "consolidated"  # Summary done, memories formed
    ARCHIVED = "archived"      # Long-term storage


class SessionLifecycle:
    """Manages session state transitions."""

    @staticmethod
    def initial() -> str:
        return SessionState.DRAFT.value

    @staticmethod
    def activate(meta: dict) -> dict:
        if meta.get("lifecycle") in (None, SessionState.DRAFT.value):
            meta["lifecycle"] = SessionState.ACTIVE.value
        return meta

    @staticmethod
    def start_reflection(meta: dict) -> dict:
        meta["lifecycle"] = SessionState.REFLECTING.value
        return meta

    @staticmethod
    def consolidate(meta: dict, summary: str = "") -> dict:
        meta["lifecycle"] = SessionState.CONSOLIDATED.value
        if summary:
            meta["summary"] = summary
        return meta

    @staticmethod
    def should_reflect(meta: dict, idle_minutes: int = 30) -> bool:
        """Check if session should enter reflection state."""
        if meta.get("lifecycle") != SessionState.ACTIVE.value:
            return False
        msg_count = meta.get("message_count", 0)
        return msg_count >= 4  # Enough substance to summarize
