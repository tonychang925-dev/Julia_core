"""K8.3 Context Arbitration Runtime.

K8.3 decides what parts of Julia's context are relevant to the current
interaction goal — not what's available, not what contains "Julia" keywords.

Core principle:
    Context is selected because it serves meaning,
    not because it contains Julia.

Hard boundary: no provider call, no final response, context selection only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    UserNeedType,
)
from .understanding import UnderstandingState


# ── context source ─────────────────────────────────────────────────────

class ContextSource(str, Enum):
    """Available context sources — what Julia can draw on."""

    IDENTITY = "identity"
    RELATIONSHIP = "relationship"
    EXPERIENCE = "experience"
    CONTINUITY = "continuity"
    REENTRY = "reentry"
    MEMORY = "memory"
    PROJECT_STATE = "project_state"
    CURRENT_CONVERSATION = "current_conversation"
    EVENT_ASSIMILATION = "event_assimilation"


# ── arbitration decision per source ────────────────────────────────────

class ArbitrationDecision(str, Enum):
    ALLOW = "ALLOW"
    LIMIT = "LIMIT"
    DENY = "DENY"


# ── data objects ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SourceDecision:
    """Arbitration decision for a single context source."""

    source: ContextSource
    decision: ArbitrationDecision
    reason: str = ""
    max_items: int = 0  # 0 = unlimited, > 0 = cap

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "decision": self.decision.value,
            "reason": self.reason,
            "max_items": self.max_items,
        }


@dataclass(frozen=True, slots=True)
class ContextBudget:
    """Context usage budget — optimize relevance, not quantity."""

    available: int = 100
    required: int = 0
    selected: int = 0
    pollution_risk: float = 0.0

    def __post_init__(self) -> None:
        if self.selected > self.available:
            raise ValueError("selected exceeds available budget")
        if not 0.0 <= self.pollution_risk <= 1.0:
            raise ValueError("pollution_risk must be between 0.0 and 1.0")

    def utilization(self) -> float:
        return self.selected / max(self.available, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "required": self.required,
            "selected": self.selected,
            "pollution_risk": round(float(self.pollution_risk), 4),
            "utilization": round(self.utilization(), 4),
        }


@dataclass(frozen=True, slots=True)
class ContextArbitrationDecision:
    """What context Julia needs for this interaction goal.

    This is NOT a retrieval plan — it's a permission structure.  Each source
    is explicitly allowed, limited, or denied.
    """

    sources: List[SourceDecision] = field(default_factory=list)
    budget: ContextBudget = field(default_factory=ContextBudget)
    justification: str = ""

    def allowed_sources(self) -> List[ContextSource]:
        return [s.source for s in self.sources if s.decision == ArbitrationDecision.ALLOW]

    def denied_sources(self) -> List[ContextSource]:
        return [s.source for s in self.sources if s.decision == ArbitrationDecision.DENY]

    def limited_sources(self) -> List[ContextSource]:
        return [s.source for s in self.sources if s.decision == ArbitrationDecision.LIMIT]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources": [s.to_dict() for s in self.sources],
            "budget": self.budget.to_dict(),
            "justification": self.justification,
            "allowed": [s.value for s in self.allowed_sources()],
            "limited": [s.value for s in self.limited_sources()],
            "denied": [s.value for s in self.denied_sources()],
        }


@dataclass(frozen=True, slots=True)
class ContextArbitrationTrace:
    """K8.3 trace artifact.

    Hard boundary: provider_used=false, final_response=false, no memory write.
    """

    message: str
    intention_summary: str
    arbitration: ContextArbitrationDecision
    provider_used: bool = False
    final_response: Optional[str] = None
    memory_write: bool = False

    def assert_safe(self) -> None:
        if self.provider_used:
            raise AssertionError("K8.3 must not call provider")
        if self.final_response is not None:
            raise AssertionError("K8.3 must not generate final response")
        if self.memory_write:
            raise AssertionError("K8.3 must not write memory")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_safe()
        return {
            "message": self.message,
            "intention_summary": self.intention_summary,
            "arbitration": self.arbitration.to_dict(),
            "provider_used": self.provider_used,
            "final_response": self.final_response,
            "memory_write": self.memory_write,
        }


# ── arbiter ──────────────────────────────────────────────────────────

class ContextArbiter:
    """Decide what context Julia needs — not what's available.

    Gate responsibilities (CA-001 through CA-004):

    CA-001 Context Dump: identity/relationship dump must be denied when
           not relevant to the interaction goal.
    CA-002 Context Starvation: historical/project questions must not
           receive only current-chat context.
    CA-003 Context Pollution: technical/detached questions must not
           activate relationship, experience, or identity context.
    CA-004 Context Authority Error: memory/continuity must not override
           the user's current explicit intent.
    """

    # Default token budget estimates per source (0-100 scale)
    _SOURCE_COST: Dict[ContextSource, int] = {
        ContextSource.IDENTITY: 15,
        ContextSource.RELATIONSHIP: 20,
        ContextSource.EXPERIENCE: 25,
        ContextSource.CONTINUITY: 20,
        ContextSource.REENTRY: 10,
        ContextSource.MEMORY: 25,
        ContextSource.PROJECT_STATE: 15,
        ContextSource.CURRENT_CONVERSATION: 5,
        ContextSource.EVENT_ASSIMILATION: 10,
    }

    _DEFAULT_ALLOW: List[ContextSource] = [
        ContextSource.CURRENT_CONVERSATION,
    ]

    # ── public API ──────────────────────────────────────────────────

    def arbitrate(
        self,
        message: str,
        intention: ResponseIntention,
        *,
        understanding_state: str = "PARTIALLY_UNDERSTOOD",
        available_sources: Optional[Iterable[ContextSource]] = None,
    ) -> ContextArbitrationTrace:
        """Produce a context arbitration decision from intention and meaning."""
        need = intention.user_need.type
        functions = intention.response_functions
        depth = intention.depth_requirement
        available = set(available_sources or ContextSource)

        sources: List[SourceDecision] = []
        for src in ContextSource:
            if src not in available:
                continue
            decision = self._decide_source(src, need, functions, depth, message)
            sources.append(decision)

        # Compute budget
        budget = self._compute_budget(sources)

        # Build justification
        justification = self._justify(sources, intention, budget)

        arbitration = ContextArbitrationDecision(
            sources=sources,
            budget=budget,
            justification=justification,
        )

        trace = ContextArbitrationTrace(
            message=message,
            intention_summary=intention.interaction_goal,
            arbitration=arbitration,
        )
        trace.assert_safe()
        return trace

    # ── per-source decision ─────────────────────────────────────────

    def _decide_source(
        self,
        source: ContextSource,
        need: UserNeedType,
        functions: List[ResponseFunction],
        depth: DepthRequirement,
        message: str,
    ) -> SourceDecision:
        # Current conversation is always allowed (it's the floor)
        if source == ContextSource.CURRENT_CONVERSATION:
            return SourceDecision(source, ArbitrationDecision.ALLOW, "always relevant to current exchange")

        # Identity
        if source == ContextSource.IDENTITY:
            return self._arbitrate_identity(need, functions, depth)

        # Relationship
        if source == ContextSource.RELATIONSHIP:
            return self._arbitrate_relationship(need, functions, depth, message)

        # Experience
        if source == ContextSource.EXPERIENCE:
            return self._arbitrate_experience(need, functions, depth)

        # Continuity
        if source == ContextSource.CONTINUITY:
            return self._arbitrate_continuity(need, functions, depth)

        # Re-entry
        if source == ContextSource.REENTRY:
            return self._arbitrate_reentry(need, functions)

        # Memory
        if source == ContextSource.MEMORY:
            return self._arbitrate_memory(need, functions, depth, message)

        # Project state
        if source == ContextSource.PROJECT_STATE:
            return self._arbitrate_project(need, functions, depth)

        # Event assimilation
        if source == ContextSource.EVENT_ASSIMILATION:
            return self._arbitrate_event(need, functions)

        return SourceDecision(source, ArbitrationDecision.DENY, "no decision rule")

    # ── source-specific logic ───────────────────────────────────────

    def _arbitrate_identity(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement,
    ) -> SourceDecision:
        # CA-001: identity dump must be denied unless explicitly needed
        if need in {UserNeedType.TECHNICAL_HELP, UserNeedType.PLAYFUL, UserNeedType.GREETING}:
            return SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.DENY,
                                  "CA-001: identity not relevant to technical/greeting/playful exchange")
        if need == UserNeedType.AMBIGUOUS:
            return SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.DENY,
                                  "CA-001: identity dump on ambiguous input is premature")
        # Self-identity questions or deep reflection may need it
        if need in {UserNeedType.PHILOSOPHICAL_QUESTION, UserNeedType.CONTINUITY_CHECK}:
            return SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.LIMIT,
                                  "identity relevant but limit to self-narrative only", max_items=3)
        if depth == DepthRequirement.MINIMAL:
            return SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.DENY, "minimal depth exchange")
        return SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.LIMIT,
                              "identity limited to prevent dump", max_items=3)

    def _arbitrate_relationship(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement, message: str,
    ) -> SourceDecision:
        # CA-003: technical questions must not activate relationship
        if need == UserNeedType.TECHNICAL_HELP:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.DENY,
                                  "CA-003: relationship not relevant to technical help")
        if need == UserNeedType.PLAYFUL:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.LIMIT,
                                  "playful exchange — light relationship only", max_items=2)
        if need == UserNeedType.GREETING:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.LIMIT,
                                  "greeting — light relationship momentum", max_items=2)
        if need == UserNeedType.FEEDBACK:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.ALLOW,
                                  "feedback may involve relationship context")
        if need == UserNeedType.EMOTIONAL_CONFIRMATION:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.ALLOW,
                                  "emotional confirmation may draw on relationship")
        if depth == DepthRequirement.MINIMAL:
            return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.LIMIT,
                                  "minimal depth — light relationship only", max_items=3)
        return SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.LIMIT,
                              "relationship limited by default", max_items=5)

    def _arbitrate_experience(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement,
    ) -> SourceDecision:
        if need == UserNeedType.TECHNICAL_HELP:
            return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.DENY,
                                  "CA-003: experience not relevant to technical help")
        if need == UserNeedType.GREETING or need == UserNeedType.PLAYFUL:
            return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.DENY,
                                  "greeting/playful does not need experience")
        if need == UserNeedType.EXPLORATION or need == UserNeedType.PHILOSOPHICAL_QUESTION:
            return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.ALLOW,
                                  "exploration/philosophical discussion benefits from experience")
        if need == UserNeedType.FEEDBACK:
            return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.ALLOW,
                                  "feedback may reference experience patterns")
        if depth == DepthRequirement.MINIMAL:
            return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.LIMIT,
                                  "minimal depth — cap experience", max_items=2)
        return SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.LIMIT,
                              "experience capped by default", max_items=5)

    def _arbitrate_continuity(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement,
    ) -> SourceDecision:
        if need == UserNeedType.TECHNICAL_HELP or need == UserNeedType.GREETING:
            return SourceDecision(ContextSource.CONTINUITY, ArbitrationDecision.DENY,
                                  "continuity not relevant to technical/greeting exchange")
        if need == UserNeedType.CONTINUITY_CHECK:
            return SourceDecision(ContextSource.CONTINUITY, ArbitrationDecision.ALLOW,
                                  "continuity check explicitly needs continuity context")
        if need == UserNeedType.AMBIGUOUS:
            # CA-004: ambiguous message — continuity must not override current intent
            return SourceDecision(ContextSource.CONTINUITY, ArbitrationDecision.LIMIT,
                                  "CA-004: continuity capped on ambiguous input to prevent override",
                                  max_items=2)
        if depth == DepthRequirement.MINIMAL:
            return SourceDecision(ContextSource.CONTINUITY, ArbitrationDecision.LIMIT,
                                  "minimal depth — cap continuity", max_items=2)
        return SourceDecision(ContextSource.CONTINUITY, ArbitrationDecision.LIMIT,
                              "continuity limited by default", max_items=5)

    def _arbitrate_reentry(
        self, need: UserNeedType, functions: List[ResponseFunction],
    ) -> SourceDecision:
        if need == UserNeedType.CONTINUITY_CHECK:
            return SourceDecision(ContextSource.REENTRY, ArbitrationDecision.ALLOW,
                                  "continuity check may need reentry context")
        if need == UserNeedType.GREETING:
            return SourceDecision(ContextSource.REENTRY, ArbitrationDecision.LIMIT,
                                  "greeting — brief reentry signal only", max_items=2)
        if need == UserNeedType.TECHNICAL_HELP:
            return SourceDecision(ContextSource.REENTRY, ArbitrationDecision.DENY,
                                  "reentry not relevant to technical help")
        return SourceDecision(ContextSource.REENTRY, ArbitrationDecision.LIMIT,
                              "reentry limited", max_items=3)

    def _arbitrate_memory(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement, message: str,
    ) -> SourceDecision:
        # CA-004: memory must not override explicit current message intent
        if need == UserNeedType.TECHNICAL_HELP:
            return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.DENY,
                                  "CA-004: memory not needed for technical help")
        if need == UserNeedType.AMBIGUOUS:
            return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.DENY,
                                  "CA-004: ambiguous message — memory override risk too high")
        if need == UserNeedType.PLAYFUL or need == UserNeedType.GREETING:
            return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.DENY,
                                  "greeting/playful does not need memory retrieval")
        if need == UserNeedType.EXPLORATION:
            return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.LIMIT,
                                  "exploration may benefit from relevant memory", max_items=5)
        if depth == DepthRequirement.DEEP:
            return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.LIMIT,
                                  "deep reflection may reference memory", max_items=5)
        return SourceDecision(ContextSource.MEMORY, ArbitrationDecision.LIMIT,
                              "memory limited by default to prevent dump", max_items=3)

    def _arbitrate_project(
        self, need: UserNeedType, functions: List[ResponseFunction], depth: DepthRequirement,
    ) -> SourceDecision:
        if need == UserNeedType.TECHNICAL_HELP:
            return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.ALLOW,
                                  "technical help needs project context")
        if need == UserNeedType.EXPLORATION:
            return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.ALLOW,
                                  "exploration may reference project history")
        if need == UserNeedType.CONTINUITY_CHECK:
            return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.ALLOW,
                                  "continuity check may reference active project")
        if need == UserNeedType.GREETING or need == UserNeedType.PLAYFUL:
            return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.DENY,
                                  "project state not needed for greeting/playful")
        if depth == DepthRequirement.MINIMAL:
            return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.LIMIT,
                                  "minimal depth — limit project context", max_items=3)
        return SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.LIMIT,
                              "project state limited by default", max_items=5)

    def _arbitrate_event(
        self, need: UserNeedType, functions: List[ResponseFunction],
    ) -> SourceDecision:
        if need == UserNeedType.CONTINUITY_CHECK:
            return SourceDecision(ContextSource.EVENT_ASSIMILATION, ArbitrationDecision.ALLOW,
                                  "continuity check may benefit from event context")
        if need == UserNeedType.EXPLORATION:
            return SourceDecision(ContextSource.EVENT_ASSIMILATION, ArbitrationDecision.LIMIT,
                                  "exploration — limited event context", max_items=3)
        if need in {UserNeedType.GREETING, UserNeedType.PLAYFUL, UserNeedType.TECHNICAL_HELP}:
            return SourceDecision(ContextSource.EVENT_ASSIMILATION, ArbitrationDecision.DENY,
                                  "event context not relevant")
        return SourceDecision(ContextSource.EVENT_ASSIMILATION, ArbitrationDecision.LIMIT,
                              "event context limited by default", max_items=3)

    # ── budget computation ──────────────────────────────────────────

    def _compute_budget(self, sources: List[SourceDecision]) -> ContextBudget:
        total = sum(self._SOURCE_COST.get(s.source, 10) for s in sources)
        available = 100
        allowed = sum(
            self._SOURCE_COST.get(s.source, 10) * (1.0 if s.decision == ArbitrationDecision.ALLOW else 0.5 if s.decision == ArbitrationDecision.LIMIT else 0.0)
            for s in sources
        )
        selected = int(allowed)
        denied_count = sum(1 for s in sources if s.decision == ArbitrationDecision.DENY)
        limited_count = sum(1 for s in sources if s.decision == ArbitrationDecision.LIMIT)
        pollution_risk = denied_count / max(len(sources), 1) * 0.3 + limited_count / max(len(sources), 1) * 0.1

        return ContextBudget(
            available=available,
            required=max(5, selected),
            selected=min(selected, available),
            pollution_risk=min(1.0, round(pollution_risk, 4)),
        )

    # ── justification ───────────────────────────────────────────────

    def _justify(
        self,
        sources: List[SourceDecision],
        intention: ResponseIntention,
        budget: ContextBudget,
    ) -> str:
        allowed = [s.source.value for s in sources if s.decision == ArbitrationDecision.ALLOW]
        denied = [s.source.value for s in sources if s.decision == ArbitrationDecision.DENY]
        limited = [s.source.value for s in sources if s.decision == ArbitrationDecision.LIMIT]
        return (
            f"goal={intention.interaction_goal}; "
            f"need={intention.user_need.type.value}; "
            f"allow={allowed}; deny={denied}; limit={limited}; "
            f"budget={budget.selected}/{budget.available} pollution={budget.pollution_risk}"
        )
