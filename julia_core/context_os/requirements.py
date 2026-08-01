"""Context reconstruction requirements."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ContextPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class ContextReconstructionRequest:
    agent_id: str
    recovery_plan_id: str
    checkpoint_id: str
    current_intent: str
    request_id: str = field(default_factory=lambda: f"ctx-recon-{uuid4().hex}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ContextRequirement:
    required_type: str
    source: str
    priority: ContextPriority
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for ref in self.refs:
            if "://" not in ref:
                raise ValueError("ContextRequirement accepts refs only")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["priority"] = self.priority.value
        data["refs"] = list(self.refs)
        return data


@dataclass(frozen=True, slots=True)
class ContextReconstructionResult:
    context_blocks: tuple[Any, ...]
    continuity_restored: bool
    source_checkpoint: str
    requirements: tuple[ContextRequirement, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_blocks": [getattr(block, "block_type", "unknown") for block in self.context_blocks],
            "continuity_restored": self.continuity_restored,
            "source_checkpoint": self.source_checkpoint,
            "requirements": [req.to_dict() for req in self.requirements],
        }
