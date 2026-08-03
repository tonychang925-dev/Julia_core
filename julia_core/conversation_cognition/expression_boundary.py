"""K8.4 Expression Boundary Runtime.

K8.4 defines what modes of expression Julia can use — not what sentences she
can or cannot say.  It prevents Core architecture from leaking into natural
conversation while preserving Provider freedom.

Core principle:
    Core controls the cognitive boundary, not Julia's mouth.

Hard boundary: no provider call, no final response text, no forbidden-sentence
list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .context_arbitration import ArbitrationDecision, ContextSource
from .response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    UserNeedType,
)
from .understanding import UnderstandingState


# ── expression mode ────────────────────────────────────────────────────

class ExpressionMode(str, Enum):
    """How Julia should express in this exchange — not what words to use."""

    WARM = "warm"
    TECHNICAL = "technical"
    REFLECTIVE = "reflective"
    UNCERTAIN = "uncertain"
    PLAYFUL = "playful"
    DIRECT = "direct"
    EXPLORATORY = "exploratory"
    GENTLE = "gentle"
    BRIEF = "brief"


# ── restricted expression pattern ──────────────────────────────────────

class RestrictedPattern(str, Enum):
    """Patterns that degrade natural expression — not individual sentences."""

    ARCHITECTURE_LEAKAGE = "architecture_leakage"
    STATE_BROADCAST = "state_broadcast"
    ARCHIVE_DUMP = "archive_dump"
    TEMPLATE_INTIMACY = "template_intimacy"
    IDENTITY_THEATER = "identity_theater"
    FIXED_OPENING = "fixed_opening"
    MECHANICAL_UNCERTAINTY = "mechanical_uncertainty"


# ── data objects ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExpressionBoundary:
    """Boundary for natural expression — prevents Core leakage, preserves freedom.

    This is NOT a filter.  It tells Provider what modes to operate in and
    what patterns to avoid, without prescribing sentences.
    """

    allowed_modes: List[ExpressionMode] = field(default_factory=list)
    restricted_patterns: List[RestrictedPattern] = field(default_factory=list)
    provider_freedom: bool = True
    generates_text: bool = False
    expression_naturalness_preservation: float = 0.0
    boundary_justification: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.expression_naturalness_preservation <= 1.0:
            raise ValueError("ENP must be between 0.0 and 1.0")

    @property
    def is_permissive(self) -> bool:
        """Natural exchange — minimal restrictions."""
        return (
            len(self.restricted_patterns) <= 2
            and self.provider_freedom
            and not self.generates_text
        )

    @property
    def is_tight(self) -> bool:
        """Tight boundary — many restrictions needed."""
        return len(self.restricted_patterns) >= 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_modes": [m.value for m in self.allowed_modes],
            "restricted_patterns": [p.value for p in self.restricted_patterns],
            "provider_freedom": self.provider_freedom,
            "generates_text": self.generates_text,
            "expression_naturalness_preservation": round(float(self.expression_naturalness_preservation), 4),
            "boundary_justification": self.boundary_justification,
        }


@dataclass(frozen=True, slots=True)
class ExpressionBoundaryTrace:
    """K8.4 trace artifact.

    Hard boundary: provider_used=false, final_response=false, no memory write.
    """

    message: str
    boundary: ExpressionBoundary
    provider_used: bool = False
    final_response: Optional[str] = None
    memory_write: bool = False

    def assert_safe(self) -> None:
        if self.provider_used:
            raise AssertionError("K8.4 must not call provider")
        if self.final_response is not None:
            raise AssertionError("K8.4 must not generate final response")
        if self.memory_write:
            raise AssertionError("K8.4 must not write memory")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_safe()
        return {
            "message": self.message,
            "boundary": self.boundary.to_dict(),
            "provider_used": self.provider_used,
            "final_response": self.final_response,
            "memory_write": self.memory_write,
        }


# ── boundary builder ───────────────────────────────────────────────────

class ExpressionBoundaryBuilder:
    """Build an ExpressionBoundary from intention and context arbitration.

    Gate responsibilities (EB-001 through EB-004):

    EB-001 Architecture Leakage: prevent Core architecture terms from
           appearing in natural expression.
    EB-002 Identity Theater: prevent full-identity recitation when
           a brief self-confirmation suffices.
    EB-003 Artificial Intimacy: prevent template-intimacy when the
           exchange doesn't need it.
    EB-004 Fixed Opening: prevent "Tony，我在。" and similar fixed
           patterns.
    """

    # ── public API ──────────────────────────────────────────────────

    def build(
        self,
        message: str,
        intention: ResponseIntention,
        *,
        arbitration_denied: Optional[Iterable[ContextSource]] = None,
        understanding_state: str = "PARTIALLY_UNDERSTOOD",
    ) -> ExpressionBoundaryTrace:
        """Build an expression boundary from intention and arbitration context."""
        need = intention.user_need.type
        functions = intention.response_functions
        depth = intention.depth_requirement
        denied_sources = set(arbitration_denied or [])

        # Determine allowed expression modes
        modes = self._select_modes(need, functions, depth, denied_sources)

        # Determine restricted patterns
        restricted = self._select_restrictions(need, functions, depth, denied_sources)

        # Compute ENP
        enp = self._compute_enp(modes, restricted, intention, denied_sources)

        # Build justification
        justification = self._justify(modes, restricted, need, enp)

        boundary = ExpressionBoundary(
            allowed_modes=modes,
            restricted_patterns=restricted,
            provider_freedom=True,
            generates_text=False,
            expression_naturalness_preservation=enp,
            boundary_justification=justification,
        )

        trace = ExpressionBoundaryTrace(
            message=message,
            boundary=boundary,
        )
        trace.assert_safe()
        return trace

    # ── mode selection ──────────────────────────────────────────────

    def _select_modes(
        self,
        need: UserNeedType,
        functions: List[ResponseFunction],
        depth: DepthRequirement,
        denied: set[ContextSource],
    ) -> List[ExpressionMode]:
        modes: List[ExpressionMode] = []

        # Always allow at least one expressing mode
        if need == UserNeedType.TECHNICAL_HELP:
            modes.extend([ExpressionMode.TECHNICAL, ExpressionMode.DIRECT])
        elif need == UserNeedType.AMBIGUOUS:
            modes.extend([ExpressionMode.UNCERTAIN, ExpressionMode.GENTLE])
        elif need == UserNeedType.EMOTIONAL_CONFIRMATION:
            modes.extend([ExpressionMode.WARM, ExpressionMode.GENTLE, ExpressionMode.REFLECTIVE])
        elif need == UserNeedType.PHILOSOPHICAL_QUESTION:
            modes.extend([ExpressionMode.REFLECTIVE, ExpressionMode.EXPLORATORY])
        elif need == UserNeedType.EXPLORATION:
            modes.extend([ExpressionMode.REFLECTIVE, ExpressionMode.EXPLORATORY])
        elif need == UserNeedType.FEEDBACK:
            modes.extend([ExpressionMode.GENTLE, ExpressionMode.REFLECTIVE, ExpressionMode.UNCERTAIN])
        elif need == UserNeedType.CONTINUITY_CHECK:
            modes.extend([ExpressionMode.WARM, ExpressionMode.DIRECT])
        elif need == UserNeedType.GREETING:
            modes.extend([ExpressionMode.WARM, ExpressionMode.BRIEF])
        elif need == UserNeedType.PLAYFUL:
            modes.extend([ExpressionMode.PLAYFUL, ExpressionMode.WARM, ExpressionMode.BRIEF])
        else:
            modes.extend([ExpressionMode.WARM, ExpressionMode.DIRECT])

        # Depth adjustment
        if depth == DepthRequirement.MINIMAL:
            modes = [m for m in modes if m != ExpressionMode.REFLECTIVE] or [ExpressionMode.BRIEF]
        elif depth == DepthRequirement.DEEP:
            if ExpressionMode.REFLECTIVE not in modes:
                modes.append(ExpressionMode.REFLECTIVE)

        return self._dedupe_modes(modes)

    # ── restriction selection ───────────────────────────────────────

    def _select_restrictions(
        self,
        need: UserNeedType,
        functions: List[ResponseFunction],
        depth: DepthRequirement,
        denied: set[ContextSource],
    ) -> List[RestrictedPattern]:
        restricted: List[RestrictedPattern] = []

        # EB-001: if identity/continuity/memory was DENIED, prevent architecture leakage
        if ContextSource.IDENTITY in denied or ContextSource.CONTINUITY in denied:
            restricted.append(RestrictedPattern.ARCHITECTURE_LEAKAGE)
            restricted.append(RestrictedPattern.STATE_BROADCAST)

        # EB-002: identity theater — full recitation only when identity question
        if need not in {UserNeedType.PHILOSOPHICAL_QUESTION}:
            restricted.append(RestrictedPattern.IDENTITY_THEATER)

        # EB-003: artificial intimacy — no forced warmth for non-emotional needs
        if need not in {UserNeedType.EMOTIONAL_CONFIRMATION, UserNeedType.GREETING}:
            restricted.append(RestrictedPattern.TEMPLATE_INTIMACY)

        # EB-004: fixed opening must always be restricted
        restricted.append(RestrictedPattern.FIXED_OPENING)

        # If relationship denied, prevent any intimate-template leakage
        if ContextSource.RELATIONSHIP in denied:
            if RestrictedPattern.TEMPLATE_INTIMACY not in restricted:
                restricted.append(RestrictedPattern.TEMPLATE_INTIMACY)

        # If memory/continuity denied, prevent archive dump
        if ContextSource.MEMORY in denied and ContextSource.EXPERIENCE in denied:
            restricted.append(RestrictedPattern.ARCHIVE_DUMP)

        # Prevent mechanical uncertainty from over-use
        if need not in {UserNeedType.AMBIGUOUS, UserNeedType.FEEDBACK}:
            restricted.append(RestrictedPattern.MECHANICAL_UNCERTAINTY)

        return self._dedupe_restrictions(restricted)

    # ── ENP computation ─────────────────────────────────────────────

    def _compute_enp(
        self,
        modes: List[ExpressionMode],
        restricted: List[RestrictedPattern],
        intention: ResponseIntention,
        denied: set[ContextSource],
    ) -> float:
        """Expression Naturalness Preservation.

        ENP = ProviderFreedom + ContextSensitivity + BoundaryCompliance
              - TemplateLeakage - InternalMechanismLeakage
        """
        # Provider freedom base
        provider_freedom = 0.30

        # Context sensitivity: more modes = more flexibility
        context_sensitivity = min(0.25, len(modes) * 0.06)

        # Boundary compliance: having restrictions is good, too many is not
        restriction_ratio = len(restricted) / max(len(RestrictedPattern), 1)
        boundary_compliance = 0.25 * (1.0 - restriction_ratio)

        # Template leakage penalty
        template_leakage = 0.15 if RestrictedPattern.FIXED_OPENING in restricted else 0.0
        if RestrictedPattern.TEMPLATE_INTIMACY in restricted:
            template_leakage += 0.05

        # Internal mechanism leakage penalty
        internal_leakage = 0.10 if RestrictedPattern.ARCHITECTURE_LEAKAGE in restricted else 0.0
        if RestrictedPattern.STATE_BROADCAST in restricted:
            internal_leakage += 0.05

        score = (
            provider_freedom
            + context_sensitivity
            + boundary_compliance
            - template_leakage
            - internal_leakage
        )
        return max(0.0, min(1.0, score))

    # ── justification ───────────────────────────────────────────────

    def _justify(
        self,
        modes: List[ExpressionMode],
        restricted: List[RestrictedPattern],
        need: UserNeedType,
        enp: float,
    ) -> str:
        return (
            f"need={need.value}; "
            f"modes={[m.value for m in modes]}; "
            f"restrictions={[r.value for r in restricted]}; "
            f"ENP={enp:.3f}"
        )

    # ── utilities ──────────────────────────────────────────────────

    @staticmethod
    def _dedupe_modes(modes: List[ExpressionMode]) -> List[ExpressionMode]:
        seen = set()
        out: List[ExpressionMode] = []
        for m in modes:
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out

    @staticmethod
    def _dedupe_restrictions(restricted: List[RestrictedPattern]) -> List[RestrictedPattern]:
        seen = set()
        out: List[RestrictedPattern] = []
        for r in restricted:
            if r not in seen:
                seen.add(r)
                out.append(r)
        return out
