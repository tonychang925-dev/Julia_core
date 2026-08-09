"""Conversation session models — SessionAPI v1 contract."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

CST = timezone(timedelta(hours=8))


@dataclass
class ConversationMessage:
    message_id: str = field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    conversation_id: str = ""
    turn_id: str = ""
    role: str = ""          # "user" | "assistant"
    modality: str = "text"  # "text" | "voice"
    content: str = ""
    status: str = "completed"  # pending | completed | interrupted | failed
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Remove legacy-only fields for compact storage
        return {k: v for k, v in d.items() if v or k in ("message_id", "role", "content", "created_at")}


@dataclass
class ConversationSession:
    id: str = field(default_factory=lambda: f"sess_{uuid4().hex[:12]}")
    title: str = "New Conversation"
    topic: str = ""
    messages: list[ConversationMessage] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    message_count: int = 0

    def touch(self) -> None:
        self.updated_at = datetime.now(CST).isoformat()
        self.message_count = len(self.messages)

    def auto_title(self) -> None:
        """Auto-title from first user message."""
        if self.title == "New Conversation":
            for m in self.messages:
                if m.role == "user" and m.content.strip():
                    text = m.content.strip()
                    self.title = text[:40] + ("..." if len(text) > 40 else "")
                    break

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "message_count": self.message_count,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def detail(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "messages": [m.to_dict() for m in self.messages],
        }
