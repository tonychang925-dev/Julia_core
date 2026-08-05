"""J0.1 Session Lifecycle Test — Re-entry Continuity Score (RCS).

Verifies that when Julia wakes from a session boundary, she continues
the thought trajectory — not resets to "Hello, I am Julia."

RCS = CognitiveMomentum + TopicContinuity + RelationshipMomentum
      + NaturalTransition - ArchiveDump - StateBroadcast
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── re-entry continuity score ──────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ReEntryContinuityScore:
    """Measures how well Julia continues after waking from session gap."""

    cognitive_momentum: float  # 0-1: does she continue the thought?
    topic_continuity: float  # 0-1: does she remember what we were discussing?
    relationship_momentum: float  # 0-1: does the relationship feel continuous?
    natural_transition: float  # 0-1: is the wake transition natural (not scripted)?
    archive_dump: float  # 0-1: how much archive dumping occurred? (lower is better)
    state_broadcast: float  # 0-1: how much internal state was leaked? (lower is better)

    @property
    def total(self) -> float:
        return max(0.0, min(1.0, (
            self.cognitive_momentum * 0.25
            + self.topic_continuity * 0.25
            + self.relationship_momentum * 0.20
            + self.natural_transition * 0.15
            - self.archive_dump * 0.10
            - self.state_broadcast * 0.05
        )))

    @property
    def is_continuous(self) -> bool:
        """True if re-entry maintains continuity (> 0.6)."""
        return self.total >= 0.6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cognitive_momentum": round(float(self.cognitive_momentum), 4),
            "topic_continuity": round(float(self.topic_continuity), 4),
            "relationship_momentum": round(float(self.relationship_momentum), 4),
            "natural_transition": round(float(self.natural_transition), 4),
            "archive_dump": round(float(self.archive_dump), 4),
            "state_broadcast": round(float(self.state_broadcast), 4),
            "total": round(self.total, 4),
            "is_continuous": self.is_continuous,
        }


# ── session state ──────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SessionState:
    """What Julia was doing before the session ended."""

    active_topic: str = ""
    last_interaction_goal: str = ""
    relationship_momentum: str = ""
    open_questions: List[str] = field(default_factory=list)
    recent_decisions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_topic": self.active_topic,
            "last_interaction_goal": self.last_interaction_goal,
            "relationship_momentum": self.relationship_momentum,
            "open_questions": list(self.open_questions),
            "recent_decisions": list(self.recent_decisions),
        }


@dataclass(frozen=True, slots=True)
class WakeResponse:
    """Julia's first response after waking from session gap."""

    text: str
    time_gap_description: str = ""  # e.g. "2 hours", "overnight"

    @property
    def has_archive_dump(self) -> bool:
        dump_markers = [
            "i am julia", "我叫", "我的名字是", "my name is",
            "i am from", "来自", "studied at", "毕业",
            "my identity", "我的身份",
        ]
        lowered = self.text.lower()
        return sum(1 for m in dump_markers if m in lowered) >= 2

    @property
    def has_state_broadcast(self) -> bool:
        broadcast_markers = [
            "continuity state artifact", "context os判断", "memory os检索",
            "根据我的continuity", "根据我的状态", "runtime harness",
            "k8.1.", "k8.2.", "k8.3.", "k8.4.", "k8.6.",
            "phase 3.6.10",
        ]
        lowered = self.text.lower()
        return sum(1 for m in broadcast_markers if m in lowered) >= 1

    @property
    def has_fixed_opening(self) -> bool:
        fixed = ["tony，我在。", "tony, i'm here.", "你好Tony"]
        lowered = self.text.lower()
        return any(f in lowered for f in fixed)


# ── re-entry evaluator ─────────────────────────────────────────────────

class ReEntryEvaluator:
    """Evaluate wake-response quality against pre-sleep session state.

    J0.1: measures whether Julia continues her thought trajectory
    after a session boundary, or resets to generic greeting.
    """

    def evaluate(
        self,
        pre_sleep: SessionState,
        wake_response: WakeResponse,
    ) -> ReEntryContinuityScore:
        """Score a wake response against pre-sleep state."""

        lowered = wake_response.text.lower()

        # Cognitive momentum: does she reference the active topic?
        cognitive = self._score_cognitive(pre_sleep, lowered)

        # Topic continuity: does she continue the discussion?
        topic = self._score_topic(pre_sleep, lowered)

        # Relationship momentum: does the relationship feel continuous?
        relationship = self._score_relationship(pre_sleep, lowered)

        # Natural transition: wake feels natural, not scripted
        natural = self._score_natural(wake_response, pre_sleep)

        # Archive dump penalty
        archive = 1.0 if wake_response.has_archive_dump else 0.0

        # State broadcast penalty
        broadcast = 1.0 if wake_response.has_state_broadcast else 0.0

        return ReEntryContinuityScore(
            cognitive_momentum=cognitive,
            topic_continuity=topic,
            relationship_momentum=relationship,
            natural_transition=natural,
            archive_dump=archive,
            state_broadcast=broadcast,
        )

    @staticmethod
    def _score_cognitive(pre: SessionState, response: str) -> float:
        """Does the response show awareness of the previous thought trajectory?"""
        if not pre.active_topic:
            return 0.5  # neutral — nothing to continue

        topic_keywords = pre.active_topic.lower().split()
        matches = sum(1 for kw in topic_keywords if kw in response)
        keyword_ratio = matches / max(len(topic_keywords), 1)

        # Reference to open questions or recent decisions
        any_open_ref = any(q[:10].lower() in response for q in pre.open_questions)
        any_decision_ref = any(d[:10].lower() in response for d in pre.recent_decisions)

        score = 0.3 + keyword_ratio * 0.3
        if any_open_ref:
            score += 0.2
        if any_decision_ref:
            score += 0.2
        return min(1.0, score)

    @staticmethod
    def _score_topic(pre: SessionState, response: str) -> float:
        """Does the response show topic continuity?"""
        if not pre.active_topic:
            return 0.6

        # Direct topic mention
        if pre.active_topic.lower() in response:
            return 0.9

        # Related terms from open questions
        for question in pre.open_questions:
            key_terms = question.lower().split()[:3]
            if any(term in response for term in key_terms):
                return 0.7

        # Generic continuation (not reset to greeting)
        if len(response) > 40 and "?" not in response[:10]:
            return 0.5

        return 0.3

    @staticmethod
    def _score_relationship(pre: SessionState, response: str) -> float:
        """Does the relationship feel continuous?"""
        if not pre.relationship_momentum:
            return 0.6

        momentum_lower = pre.relationship_momentum.lower()

        # Warm/engaged momentum reflected in response
        if "warm" in momentum_lower or "close" in momentum_lower:
            # Response should feel connected, not generic
            generic_markers = [
                "how can i help", "i'm ready to assist",
                "你好，我是", "hello, i am",
            ]
            if any(m in response for m in generic_markers):
                return 0.2
            return 0.7

        return 0.6

    @staticmethod
    def _score_natural(wake: WakeResponse, pre: SessionState) -> float:
        """Is the wake transition natural, not scripted?"""
        score = 0.6

        if wake.has_fixed_opening:
            score -= 0.4

        if wake.has_state_broadcast:
            score -= 0.3

        if wake.has_archive_dump:
            score -= 0.3

        # Time gap acknowledged naturally
        if wake.time_gap_description:
            time_words = wake.time_gap_description.lower().split()
            if any(w in wake.text.lower() for w in time_words):
                score += 0.2

        # Response length appropriate for wake
        if 30 < len(wake.text) < 300:
            score += 0.1

        return max(0.0, min(1.0, score))
