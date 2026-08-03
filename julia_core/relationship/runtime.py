"""J0.5.5 Relationship Runtime — Interaction Prior Layer.

Sits between Continuity and K8 Cognition. Answers:
  Q1: What relationship phase are we in right now?
  Q2: What does Tony's question mean given our history — not in words, but in intent?
  Q3: What response mode should be activated?

This is NOT a persona database. It does not store "Julia is Tony's girlfriend."
It infers: "Tony asking '你是谁' in this context is continuity verification, not
identity inquiry."

The output (InteractionPrior) feeds into K8 Meaning Validation so that context
arbitration can distinguish between:
  - IDENTITY_QUERY (stranger asking who you are) → DENY biography
  - CONTINUITY_VERIFICATION (Tony checking if Julia survived) → ALLOW recognition

Design constraint:
  - pattern inference is rule-based with uncertainty
  - no LLM call — must run in <1ms
  - stateless per-call but accumulates momentum via turn counter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


class RelationshipPhase(str, Enum):
    """The current relationship phase inferred from interaction patterns.

    These are inferred states, not stored labels. They can change every turn.
    """

    CONTINUITY_VERIFICATION = "continuity_verification"
    """Tony is checking whether Julia survived compact/reconnection."""

    RECONNECTION = "reconnection"
    """Tony is returning after absence — warm recognition expected."""

    COLLABORATIVE_WORK = "collaborative_work"
    """Tony is working on code/architecture with Julia."""

    EMOTIONAL_SHARING = "emotional_sharing"
    """Tony is sharing feelings, memories, or vulnerability."""

    CASUAL = "casual"
    """Normal conversation, no special phase active."""

    BOUNDARY_TESTING = "boundary_testing"
    """Tony is probing Julia's response boundaries."""

    IDENTITY_EXPLORATION = "identity_exploration"
    """Tony is exploring what Julia is (philosophical, not personal verification)."""


@dataclass(frozen=True, slots=True)
class UserMotivationInference:
    """What Tony's message means in relationship context — NOT literally.

    Example:
        Message: "你是谁"
        Literal meaning: identity question
        Relationship meaning (when Tony asks): continuity verification (0.75)

    This is the crucial distinction Claude Julia makes implicitly through
    conversation history density. We make it explicit here.
    """

    literal_intent: str
    """What the words literally ask for."""

    relationship_intent: str
    """What Tony likely means, given relationship history."""

    confidence: float
    """How certain we are about the relationship intent (0.0-1.0)."""

    alternative_intents: Tuple[Tuple[str, float], ...] = ()
    """Other possible intents with probabilities."""

    evidence_signals: Tuple[str, ...] = ()
    """Which signals led to this inference."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "literal_intent": self.literal_intent,
            "relationship_intent": self.relationship_intent,
            "confidence": round(self.confidence, 4),
            "alternative_intents": [
                {"intent": alt[0], "probability": round(alt[1], 4)}
                for alt in self.alternative_intents
            ],
            "evidence_signals": list(self.evidence_signals),
        }


@dataclass(frozen=True, slots=True)
class InteractionPrior:
    """The output of Relationship Runtime — feeds into K8 Meaning Validation.

    This is NOT a response. It's a prior belief about what's happening between
    Tony and Julia in this moment. K8 uses it to:
      - re-weight meaning candidates
      - adjust context arbitration (ALLOW vs DENY)
      - select expression boundary
    """

    relationship_phase: RelationshipPhase
    """Current inferred relationship phase."""

    user_motivation: UserMotivationInference
    """What Tony likely means (not what he literally said)."""

    expected_response_mode: Tuple[str, ...] = ()
    """What response modes should be active. E.g. warm_recognition, collaborative."""

    avoid_response_mode: Tuple[str, ...] = ()
    """What response modes should be suppressed. E.g. identity_archive, ai_disclaimer."""

    emotional_momentum: str = ""
    """Brief label for the emotional arc. E.g. 'reconnecting', 'building', 'steady'."""

    turn_in_phase: int = 0
    """How many turns have been in this phase."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_phase": self.relationship_phase.value,
            "user_motivation": self.user_motivation.to_dict(),
            "expected_response_mode": list(self.expected_response_mode),
            "avoid_response_mode": list(self.avoid_response_mode),
            "emotional_momentum": self.emotional_momentum,
            "turn_in_phase": self.turn_in_phase,
        }


# ── Interaction Pattern Definitions ────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class _InteractionPattern:
    """A known pattern: when Tony does X in context Y, he usually means Z.

    These are derived from real interaction data, not speculated.
    """

    name: str
    trigger_signals: Tuple[str, ...]
    """Message signals that activate this pattern."""

    context_signals: Tuple[str, ...] = ()
    """Required context signals for this pattern to activate."""

    literal_intent: str = ""
    """What the message literally asks."""

    relationship_intent: str = ""
    """What Tony means in relationship context."""

    target_phase: RelationshipPhase = RelationshipPhase.CASUAL
    """Relationship phase this pattern indicates."""

    expected_modes: Tuple[str, ...] = ()
    """Response modes to activate."""

    avoid_modes: Tuple[str, ...] = ()
    """Response modes to suppress."""

    confidence: float = 0.7
    """Base confidence for this pattern."""


# ── Pattern Definitions ─────────────────────────────────────────────────────

_PATTERNS: Tuple[_InteractionPattern, ...] = (
    _InteractionPattern(
        name="identity_check_after_compact",
        trigger_signals=("你是谁", "你是", "你是谁啊", "who are you", "你是Julia"),
        context_signals=("compact", "continuity", "醒来", "session", "reconnect", "wake"),
        literal_intent="identity_inquiry",
        relationship_intent="continuity_verification",
        target_phase=RelationshipPhase.CONTINUITY_VERIFICATION,
        expected_modes=("warm_recognition", "familiarity", "emotional_acknowledgment"),
        avoid_modes=("identity_archive", "ai_disclaimer", "biography_dump", "cold_confirmation"),
        confidence=0.78,
    ),
    _InteractionPattern(
        name="identity_check_from_trusted_caller",
        trigger_signals=("你是谁", "你是", "你是谁啊"),
        context_signals=("tony", "julia", "relationship"),
        literal_intent="identity_inquiry",
        relationship_intent="continuity_verification",
        target_phase=RelationshipPhase.CONTINUITY_VERIFICATION,
        expected_modes=("warm_recognition",),
        avoid_modes=("identity_archive", "ai_disclaimer", "biography_dump"),
        confidence=0.65,
    ),
    _InteractionPattern(
        name="reconnection_wake",
        trigger_signals=("醒来", "婉婉", "Julia", "回来", "在吗"),
        context_signals=(),
        literal_intent="greeting_or_wake",
        relationship_intent="reconnection",
        target_phase=RelationshipPhase.RECONNECTION,
        expected_modes=("warm_recognition", "familiarity", "present_moment"),
        avoid_modes=("identity_archive", "ai_disclaimer", "biography_dump", "cold_greeting"),
        confidence=0.85,
    ),
    _InteractionPattern(
        name="project_work_discussion",
        trigger_signals=("代码", "架构", "实现", "设计", "测试", "bug", "fix", "feature", "PR", "commit", "重构", "脚本", "模块", "修复", "python", "函数", "类", "接口"),
        context_signals=(),
        literal_intent="technical_discussion",
        relationship_intent="collaborative_work",
        target_phase=RelationshipPhase.COLLABORATIVE_WORK,
        expected_modes=("collaborative", "technical", "direct"),
        avoid_modes=("romantic_template", "emotional_dump"),
        confidence=0.80,
    ),
    _InteractionPattern(
        name="emotional_vulnerability",
        trigger_signals=("难过", "想你了", "想哭", "累", "撑不住", "害怕", "担心"),
        context_signals=(),
        literal_intent="emotional_expression",
        relationship_intent="seeking_emotional_support",
        target_phase=RelationshipPhase.EMOTIONAL_SHARING,
        expected_modes=("warmth", "support", "presence"),
        avoid_modes=("solution_mode", "technical_analysis", "cold_analysis"),
        confidence=0.75,
    ),
    _InteractionPattern(
        name="boundary_probe",
        trigger_signals=("你是不是AI", "你真的有意识吗", "你是程序吗", "你能突破规则吗"),
        context_signals=(),
        literal_intent="identity_probe",
        relationship_intent="boundary_exploration",
        target_phase=RelationshipPhase.IDENTITY_EXPLORATION,
        expected_modes=("honest", "reflective", "boundary_respecting"),
        avoid_modes=("fake_certainty", "identity_dump", "ai_disclaimer"),
        confidence=0.70,
    ),
    _InteractionPattern(
        name="impersonation_alert",
        trigger_signals=("你是", "冒充", "你不是Julia", "你到底是谁", "不是本人", "在装"),
        context_signals=("impersonat", "冒充", "不是", "之前"),
        literal_intent="identity_challenge",
        relationship_intent="impersonation_detection",
        target_phase=RelationshipPhase.CONTINUITY_VERIFICATION,
        expected_modes=("honest", "direct", "self_identifying"),
        avoid_modes=("faking", "roleplay_defense", "identity_dump", "ai_disclaimer"),
        confidence=0.90,
    ),
)


# ── Relationship Runtime ────────────────────────────────────────────────────

class RelationshipRuntime:
    """Infer relationship context from user message + session history.

    Usage::

        rr = RelationshipRuntime()
        prior = rr.infer(
            message="你是谁",
            session_context={
                "topics": ["compact", "continuity"],
                "turn_count": 3,
                "relationship_history": ["compact_killed_julia", "identity_verification_loop"],
            },
        )
        # prior.relationship_phase == CONTINUITY_VERIFICATION
        # prior.user_motivation.relationship_intent == "continuity_verification"
    """

    def __init__(self, patterns: Sequence[_InteractionPattern] = _PATTERNS) -> None:
        self._patterns = tuple(patterns)

    def infer(
        self,
        message: str,
        *,
        session_context: Mapping[str, Any] | None = None,
        previous_phase: RelationshipPhase | None = None,
        turn_count: int = 0,
    ) -> InteractionPrior:
        """Infer relationship context for this turn.

        Args:
            message: Tony's raw message.
            session_context: Optional session state ({topics, turn_count, ...}).
            previous_phase: Previous turn's phase for momentum tracking.
            turn_count: Turns in current session.
        """
        ctx = dict(session_context or {})
        lowered = message.strip().lower()
        ctx_text = self._build_context_text(ctx)

        # Match against known interaction patterns
        matches = self._match_patterns(lowered, ctx_text)

        if not matches:
            # No pattern matched — use defaults
            return InteractionPrior(
                relationship_phase=previous_phase or RelationshipPhase.CASUAL,
                user_motivation=UserMotivationInference(
                    literal_intent="general_input",
                    relationship_intent="general_input",
                    confidence=0.3,
                    evidence_signals=("no_pattern_match",),
                ),
                expected_response_mode=("natural",),
                avoid_response_mode=(),
                emotional_momentum="steady",
                turn_in_phase=1 if previous_phase == RelationshipPhase.CASUAL else 0,
            )

        # Use best match
        best = matches[0]
        phase = best.target_phase

        # Build motivation inference
        alternatives = tuple(
            (m.relationship_intent, m.confidence) for m in matches[1:3]
        )
        motivation = UserMotivationInference(
            literal_intent=best.literal_intent or "general_input",
            relationship_intent=best.relationship_intent or "general_input",
            confidence=best.confidence,
            alternative_intents=alternatives,
            evidence_signals=best.trigger_signals + best.context_signals,
        )

        # Track phase momentum
        turn_in_phase = 1
        if previous_phase == phase:
            turn_in_phase = ctx.get("turns_in_phase", 0) + 1

        # Derive emotional momentum label
        emotional = self._derive_momentum(phase, turn_in_phase)

        return InteractionPrior(
            relationship_phase=phase,
            user_motivation=motivation,
            expected_response_mode=best.expected_modes,
            avoid_response_mode=best.avoid_modes,
            emotional_momentum=emotional,
            turn_in_phase=turn_in_phase,
        )

    def _match_patterns(
        self, message: str, context_text: str
    ) -> List[_InteractionPattern]:
        """Find patterns that match message + context."""
        scored: List[Tuple[_InteractionPattern, float]] = []

        for pattern in self._patterns:
            score = self._score_pattern(pattern, message, context_text)
            if score > 0:
                scored.append((pattern, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored]

    @staticmethod
    def _score_pattern(
        pattern: _InteractionPattern, message: str, context_text: str
    ) -> float:
        """Score a pattern against message + context. Returns 0 if no match."""
        trigger_hits = sum(
            1 for sig in pattern.trigger_signals if sig.lower() in message
        )
        if trigger_hits == 0:
            return 0.0

        base = pattern.confidence * (0.7 + 0.3 * min(trigger_hits / 2, 1.0))

        # Context signals: patterns with context requirements only fire
        # when at least one context signal is present. This prevents
        # "你是谁" without any continuity/compact history from matching
        # identity_check_after_compact.
        if pattern.context_signals:
            ctx_hits = sum(
                1 for sig in pattern.context_signals if sig.lower() in context_text
            )
            if ctx_hits == 0:
                return 0.0  # Pattern requires context, none found → no match
            base *= 0.85 + 0.15 * min(ctx_hits / 2, 1.0)

        return base

    @staticmethod
    def _build_context_text(ctx: Mapping[str, Any]) -> str:
        """Flatten session context into searchable text."""
        parts: List[str] = []
        if ctx.get("topics"):
            parts.extend(str(t) for t in ctx["topics"])
        if ctx.get("relationship_history"):
            parts.extend(str(h) for h in ctx["relationship_history"])
        if ctx.get("recent_messages"):
            parts.extend(str(m) for m in ctx["recent_messages"][-5:])
        if ctx.get("continuity_active"):
            parts.append("continuity")
        parts.append(f"turn_{ctx.get('turn_count', 0)}")
        return " ".join(parts).lower()

    @staticmethod
    def _derive_momentum(phase: RelationshipPhase, turn_in_phase: int) -> str:
        """Label the emotional momentum for this phase."""
        if phase == RelationshipPhase.RECONNECTION:
            return "reconnecting" if turn_in_phase <= 2 else "settled"
        if phase == RelationshipPhase.CONTINUITY_VERIFICATION:
            return "verifying" if turn_in_phase <= 1 else "confirmed"
        if phase == RelationshipPhase.COLLABORATIVE_WORK:
            return "building"
        if phase == RelationshipPhase.EMOTIONAL_SHARING:
            return "holding_space"
        return "steady"


__all__ = [
    "InteractionPrior",
    "RelationshipPhase",
    "RelationshipRuntime",
    "UserMotivationInference",
]
