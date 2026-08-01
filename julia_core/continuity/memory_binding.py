"""Memory ↔ Continuity governance binding contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from .contracts import ContinuityLevel, ContinuityRequest
from .policy import ContinuityPolicy


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class MemoryContinuityRequest:
    request_id: str
    agent_id: str
    memory_ref: str
    memory_type: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    signals: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_continuity_request(self) -> ContinuityRequest:
        return ContinuityRequest(
            request_id=self.request_id,
            agent_id=self.agent_id,
            event_type="memory_candidate",
            source="memory_os",
            candidate_refs=[self.memory_ref],
            signals=dict(self.signals),
            current_context={"memory_type": self.memory_type, "importance": self.importance.value, **self.metadata},
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["importance"] = self.importance.value
        return data


@dataclass(frozen=True, slots=True)
class ContinuityEligibilityDecision:
    eligible: bool
    level: ContinuityLevel
    reason: str
    protected_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "level": self.level.value,
            "reason": self.reason,
            "protected_ref": self.protected_ref,
        }


@dataclass(frozen=True, slots=True)
class ProtectedMemoryRef:
    ref: str
    level: ContinuityLevel
    reason: str
    source: str = "continuity_policy"

    def to_dict(self) -> dict[str, Any]:
        return {"ref": self.ref, "level": self.level.value, "reason": self.reason, "source": self.source}


class MemoryContinuityBinder:
    """Applies ContinuityPolicy to memory refs.

    This binder does not read or write memory content. It accepts refs only.
    """

    def __init__(self, policy: ContinuityPolicy | None = None) -> None:
        self.policy = policy or ContinuityPolicy()

    def decide(self, request: MemoryContinuityRequest) -> ContinuityEligibilityDecision:
        if "://" not in request.memory_ref:
            raise ValueError("memory continuity binding accepts refs only")
        continuity_decision = self.policy.decide(request.to_continuity_request())
        eligible = continuity_decision.preserve and continuity_decision.checkpoint_required
        protected_ref = request.memory_ref if eligible else None
        return ContinuityEligibilityDecision(
            eligible=eligible,
            level=continuity_decision.level,
            reason=continuity_decision.reason,
            protected_ref=protected_ref,
        )

    def protect(self, decision: ContinuityEligibilityDecision) -> ProtectedMemoryRef | None:
        if not decision.eligible or not decision.protected_ref:
            return None
        return ProtectedMemoryRef(ref=decision.protected_ref, level=decision.level, reason=decision.reason)


def request_from_memory_ref(
    *,
    agent_id: str,
    memory_ref: str,
    memory_type: str,
    importance: MemoryImportance = MemoryImportance.MEDIUM,
    signals: dict[str, bool] | None = None,
) -> MemoryContinuityRequest:
    return MemoryContinuityRequest(
        request_id=f"memory-continuity-{uuid4().hex}",
        agent_id=agent_id,
        memory_ref=memory_ref,
        memory_type=memory_type,
        importance=importance,
        signals=dict(signals or {}),
    )
