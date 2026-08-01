"""Continuity OS v0.1 contracts.

Continuity OS owns continuity policy objects, not memory storage, persona
mutation, context building, or provider calls.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ContinuityLevel(str, Enum):
    L0_EPHEMERAL = "L0_EPHEMERAL"
    L1_SESSION = "L1_SESSION"
    L2_MEMORY = "L2_MEMORY"
    L3_IDENTITY = "L3_IDENTITY"


class TTLPolicy(str, Enum):
    DISCARD = "discard"
    SUMMARIZE = "summarize"
    RETAIN_REF = "retain_ref"
    PROTECT = "protect"


class ContinuityStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    CLASSIFIED = "CLASSIFIED"
    CHECKPOINTED = "CHECKPOINTED"
    RESTORED = "RESTORED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ContinuityRequest:
    request_id: str
    agent_id: str
    event_type: str
    source: str
    candidate_refs: list[str] = field(default_factory=list)
    signals: dict[str, bool] = field(default_factory=dict)
    current_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ContinuityDecision:
    decision_id: str
    request_id: str
    level: ContinuityLevel
    preserve: bool
    checkpoint_required: bool
    reason: str
    protected_refs: list[str] = field(default_factory=list)
    ttl_policy: TTLPolicy = TTLPolicy.DISCARD
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["level"] = self.level.value
        data["ttl_policy"] = self.ttl_policy.value
        return data


@dataclass(frozen=True, slots=True)
class ContinuityCheckpoint:
    checkpoint_version: str
    checkpoint_id: str
    agent_id: str
    created_at: str
    identity_refs: list[str] = field(default_factory=list)
    protected_memory_refs: list[str] = field(default_factory=list)
    relationship_refs: list[str] = field(default_factory=list)
    active_project_refs: list[str] = field(default_factory=list)
    continuity_levels: dict[str, list[str]] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    recovery_plan_id: str
    agent_id: str
    recovery_reason: str
    checkpoint_id: str
    required_steps: list[str] = field(default_factory=list)
    required_context_blocks: list[str] = field(default_factory=list)
    provider_constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ContinuityTrace:
    status: ContinuityStatus
    checkpoint_id: str | None = None
    continuity_levels_used: list[ContinuityLevel] = field(default_factory=list)
    identity_preserved: bool = False
    memory_recovered: bool = False
    context_rebuilt: bool = False
    provider_changed: bool = False
    protected_refs: list[str] = field(default_factory=list)
    recovery_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checkpoint_id": self.checkpoint_id,
            "continuity_levels_used": [level.value for level in self.continuity_levels_used],
            "identity_preserved": self.identity_preserved,
            "memory_recovered": self.memory_recovered,
            "context_rebuilt": self.context_rebuilt,
            "provider_changed": self.provider_changed,
            "protected_refs": list(self.protected_refs),
            "recovery_reason": self.recovery_reason,
        }
