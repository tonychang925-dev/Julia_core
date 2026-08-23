"""Core Context OS block contract.

A block is a short-lived context candidate. It is not long-term persistence,
not a prompt, and not a final answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4


@dataclass(frozen=True)
class ContextBlock:
    source: str
    content: object
    authority: str
    block_id: str = field(default_factory=lambda: f"ctx_block_{uuid4().hex}")
    block_type: str = "generic"
    block_kind: str = "context"
    domain: str | None = None
    evidence_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    authority_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    ttl_seconds: int | None = None
    required: bool = False
    estimated_tokens: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source is required")
        if not self.authority:
            raise ValueError("authority is required")
        if self.authority_score < 0 or self.authority_score > 1:
            raise ValueError("authority_score must be in [0, 1]")
        if self.ttl_seconds is not None and self.ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        if self.expires_at is None and self.ttl_seconds is not None:
            object.__setattr__(self, "expires_at", self.created_at + timedelta(seconds=self.ttl_seconds))

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or datetime.now(timezone.utc)
        return current > self.expires_at
