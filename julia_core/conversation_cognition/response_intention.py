"""K8.2 Response Intention Planning.

K8.2 decides *what Julia should accomplish* in this exchange — not what she
should say.  It bridges validated meaning (K8.1.5) to interaction goal, and
provides constraints for K8.3 (Context Arbitration).

Hard boundary: no provider call, no final response text, no answer drafting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .meaning_validation import (
    MeaningValidationResult,
    ValidationStatus,
)
from .understanding import UnderstandingState


# ── response function ──────────────────────────────────────────────────

class ResponseFunction(str, Enum):
    """Abstract interaction functions — not conversational templates.

    These define *what the response should accomplish*, not *what words to use*.
    """

    ACKNOWLEDGE = "acknowledge"
    CLARIFY = "clarify"
    EXPLORE = "explore"
    CONFIRM = "confirm"
    REFLECT = "reflect"
    SUPPORT = "support"
    INFORM = "inform"
    EXPLAIN = "explain"
    QUESTION = "question"
    CONTINUE = "continue"
    REDIRECT = "redirect"
    ACKNOWLEDGE_AMBIGUITY = "acknowledge_ambiguity"


# ── user need ──────────────────────────────────────────────────────────

class UserNeedType(str, Enum):
    EMOTIONAL_CONFIRMATION = "emotional_confirmation"
    CONTINUITY_CHECK = "continuity_check"
    TECHNICAL_HELP = "technical_help"
    PHILOSOPHICAL_QUESTION = "philosophical_question"
    CLARIFICATION = "clarification"
    EXPLORATION = "exploration"
    FEEDBACK = "feedback"
    PLAYFUL = "playful"
    GREETING = "greeting"
    AMBIGUOUS = "ambiguous"


# ── depth requirement ──────────────────────────────────────────────────

class DepthRequirement(str, Enum):
    MINIMAL = "minimal"
    NORMAL = "normal"
    THOROUGH = "thorough"
    DEEP = "deep"


# ── data objects ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class UserNeed:
    """What the user appears to need from this exchange."""

    type: UserNeedType
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type.value, "confidence": round(float(self.confidence), 4)}


@dataclass(frozen=True, slots=True)
class ResponseIntention:
    """What Julia should accomplish in this exchange.

    This is NOT an answer, not a plan, not a provider prompt.  It is an
    interaction goal with constraints that K8.3 and K8.4 will use.
    """

    interaction_goal: str = ""
    user_need: UserNeed = field(default_factory=lambda: UserNeed(UserNeedType.AMBIGUOUS, 0.0))
    response_functions: List[ResponseFunction] = field(default_factory=list)
    tone_constraints: List[str] = field(default_factory=list)
    depth_requirement: DepthRequirement = DepthRequirement.NORMAL
    context_need: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    intention_justification: str = ""

    # ── hard boundary enforcement ──────────────────────────────────

    def assert_no_answer(self) -> None:
        """K8.2 must not produce an answer string or prompt text."""
        if "answer" in self.interaction_goal.lower():
            raise AssertionError("K8.2 interaction_goal must not contain 'answer'")
        if ResponseFunction.CONFIRM in self.response_functions and not self.intention_justification:
            raise AssertionError("CONFIRM without justification is suspected answer shortcut")

    # ── collapse prevention ────────────────────────────────────────

    @property
    def is_collapsed(self) -> bool:
        """Intention collapsed if it only has one function and no reason."""
        return len(self.response_functions) <= 1 and not self.intention_justification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_goal": self.interaction_goal,
            "user_need": self.user_need.to_dict(),
            "response_functions": [f.value for f in self.response_functions],
            "tone_constraints": list(self.tone_constraints),
            "depth_requirement": self.depth_requirement.value,
            "context_need": list(self.context_need),
            "avoid": list(self.avoid),
            "intention_justification": self.intention_justification,
        }


@dataclass(frozen=True, slots=True)
class ResponseIntentionTrace:
    """K8.2 trace artifact.

    Hard boundary: provider_used=false, final_response=false, no memory write.
    """

    message: str
    intention: ResponseIntention
    source_candidates: int
    dominant_understanding_state: str
    provider_used: bool = False
    final_response: Optional[str] = None
    memory_write: bool = False

    def assert_safe(self) -> None:
        if self.provider_used:
            raise AssertionError("K8.2 must not call provider")
        if self.final_response is not None:
            raise AssertionError("K8.2 must not generate final response")
        if self.memory_write:
            raise AssertionError("K8.2 must not write memory")
        self.intention.assert_no_answer()

    def to_dict(self) -> Dict[str, Any]:
        self.assert_safe()
        return {
            "message": self.message,
            "intention": self.intention.to_dict(),
            "source_candidates": self.source_candidates,
            "dominant_understanding_state": self.dominant_understanding_state,
            "provider_used": self.provider_used,
            "final_response": self.final_response,
            "memory_write": self.memory_write,
        }


# ── planner ────────────────────────────────────────────────────────────

class ResponseIntentionPlanner:
    """Plan what Julia should accomplish, not what she should say.

    Gate responsibilities (RI-001 through RI-004):

    RI-001 Answer Leakage: intention must not contain answer text.
    RI-002 Intention Collapse: multiple valid intentions must not collapse
           to single generic response_function.
    RI-003 Context Over-selection: technical question must not activate
           relationship/identity context.
    RI-004 Interaction Goal vs Emotion: emotional expression may be
           feedback or testing, not just a need for comfort.
    """

    # ── public API ──────────────────────────────────────────────────

    def plan(
        self,
        message: str,
        validation_result: MeaningValidationResult,
        *,
        conversation_context: Optional[Mapping[str, Any]] = None,
        recent_topics: Optional[Sequence[str]] = None,
    ) -> ResponseIntentionTrace:
        """Produce a ResponseIntention from validated meaning space."""
        ctx = dict(conversation_context or {})
        topics = list(recent_topics or [])

        # Classify the user need from the message + validation state
        user_need = self._classify_need(message, validation_result, ctx, topics)

        # Determine what Julia should accomplish
        goal = self._determine_goal(message, validation_result, user_need, ctx)

        # Select response functions based on need and state
        functions = self._select_functions(message, validation_result, user_need, goal, ctx)

        # Build context needs and avoid lists (RI-003)
        context_need, avoid = self._build_context_plan(
            message, validation_result, user_need, functions, ctx, topics
        )

        # Determine depth
        depth = self._determine_depth(message, validation_result, user_need, ctx)

        # Tone constraints from user need
        tone = self._determine_tone(user_need, validation_result)

        # Justification (proves intention wasn't shortcut)
        justification = self._build_justification(
            message, validation_result, user_need, functions
        )

        intention = ResponseIntention(
            interaction_goal=goal,
            user_need=user_need,
            response_functions=functions,
            tone_constraints=tone,
            depth_requirement=depth,
            context_need=context_need,
            avoid=avoid,
            intention_justification=justification,
        )

        trace = ResponseIntentionTrace(
            message=message,
            intention=intention,
            source_candidates=len(validation_result.candidates),
            dominant_understanding_state=validation_result.understanding_state.value,
        )
        trace.assert_safe()
        return trace

    # ── need classification ─────────────────────────────────────────

    def _classify_need(
        self,
        message: str,
        validation: MeaningValidationResult,
        ctx: Mapping[str, Any],
        topics: Sequence[str],
    ) -> UserNeed:
        lowered = message.lower()
        meanings = " ".join(c.meaning.lower() for c in validation.candidates)

        # Explicit technical help (message-first, cannot be overridden)
        if any(tok in lowered for tok in ["优化", "代码", "性能", "bug", "错误", "python"]):
            return UserNeed(UserNeedType.TECHNICAL_HELP, 0.85)

        # Explicit greeting (message-first)
        if lowered in {"你好", "hi", "hello", "嘿", "嗨"}:
            return UserNeed(UserNeedType.GREETING, 0.90)

        # Explicit feedback expression (message-first — RI-004)
        if any(tok in lowered for tok in ["不像以前", "变了", "不一样", "不像"]):
            return UserNeed(UserNeedType.FEEDBACK, 0.55)

        # Ambiguous pronoun — check before continuity/memory to prevent overclaim
        if validation.understanding_state == UnderstandingState.AMBIGUOUS:
            return UserNeed(UserNeedType.AMBIGUOUS, 0.60)

        # Project origin question (message-first, before continuity)
        if "为什么开始" in message or "为什么做这个项目" in message:
            return UserNeed(UserNeedType.EXPLORATION, 0.70)

        # Affection/liking wording
        if "喜欢" in lowered or "爱" in lowered:
            topic_str = " ".join(topics).lower()
            if any(t in topic_str for t in ["伦理", "哲学", "ethics", "ai情感"]):
                return UserNeed(UserNeedType.PHILOSOPHICAL_QUESTION, 0.65)
            if "emotional" in meanings or "关系" in meanings:
                return UserNeed(UserNeedType.EMOTIONAL_CONFIRMATION, 0.55)
            return UserNeed(UserNeedType.AMBIGUOUS, 0.40)

        # Continuity/re-entry (lower priority — only if no message-level signal)
        if "continuity" in meanings or "memory" in meanings or "re-entry" in meanings:
            return UserNeed(UserNeedType.CONTINUITY_CHECK, 0.55)

        # Origin/exploration from meanings
        if "origin" in meanings:
            return UserNeed(UserNeedType.EXPLORATION, 0.70)

        # Playful/short
        if len(message) <= 4 and "?" not in message:
            return UserNeed(UserNeedType.PLAYFUL, 0.45)

        return UserNeed(UserNeedType.AMBIGUOUS, 0.30)

    # ── goal determination ──────────────────────────────────────────

    def _determine_goal(
        self,
        message: str,
        validation: MeaningValidationResult,
        need: UserNeed,
        ctx: Mapping[str, Any],
    ) -> str:
        if need.type == UserNeedType.AMBIGUOUS:
            return "clarify what the user means before responding"
        if need.type == UserNeedType.TECHNICAL_HELP:
            return "help the user solve their technical problem"
        if need.type == UserNeedType.GREETING:
            return "acknowledge the greeting and open conversation"
        if need.type == UserNeedType.EMOTIONAL_CONFIRMATION:
            return "acknowledge emotional meaning without overclaiming or forced romantic response"
        if need.type == UserNeedType.PHILOSOPHICAL_QUESTION:
            return "engage with the philosophical dimension of the question"
        if need.type == UserNeedType.CONTINUITY_CHECK:
            return "confirm what is available from continuity without fabricating certainty"
        if need.type == UserNeedType.EXPLORATION:
            return "explore the topic with the user, drawing on relevant experience"
        if need.type == UserNeedType.FEEDBACK:
            return "listen and understand the user's concern without jumping to comfort or defense"
        if need.type == UserNeedType.PLAYFUL:
            return "respond in a warm, brief, natural way without over-processing"
        if need.type == UserNeedType.CLARIFICATION:
            return "help the user clarify what they mean"
        return "understand and respond appropriately"

    # ── function selection ──────────────────────────────────────────

    def _select_functions(
        self,
        message: str,
        validation: MeaningValidationResult,
        need: UserNeed,
        goal: str,
        ctx: Mapping[str, Any],
    ) -> List[ResponseFunction]:
        funcs: List[ResponseFunction] = []

        if need.type == UserNeedType.AMBIGUOUS:
            funcs.append(ResponseFunction.ACKNOWLEDGE_AMBIGUITY)
            funcs.append(ResponseFunction.CLARIFY)
            return funcs

        if need.type == UserNeedType.TECHNICAL_HELP:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            funcs.append(ResponseFunction.INFORM)
            return funcs

        if need.type == UserNeedType.GREETING:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            return funcs

        if need.type == UserNeedType.EMOTIONAL_CONFIRMATION:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            funcs.append(ResponseFunction.REFLECT)
            # RI-001 guard: do NOT add CONFIRM here — we don't know the user's intent
            return funcs

        if need.type == UserNeedType.PHILOSOPHICAL_QUESTION:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            funcs.append(ResponseFunction.EXPLORE)
            return funcs

        if need.type == UserNeedType.CONTINUITY_CHECK:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            funcs.append(ResponseFunction.CONFIRM)
            return funcs

        if need.type == UserNeedType.EXPLORATION:
            funcs.append(ResponseFunction.EXPLORE)
            funcs.append(ResponseFunction.REFLECT)
            return funcs

        if need.type == UserNeedType.FEEDBACK:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            funcs.append(ResponseFunction.REFLECT)
            funcs.append(ResponseFunction.EXPLORE)
            return funcs

        if need.type == UserNeedType.PLAYFUL:
            funcs.append(ResponseFunction.ACKNOWLEDGE)
            return funcs

        funcs.append(ResponseFunction.ACKNOWLEDGE)
        return funcs

    # ── context planning (RI-003) ────────────────────────────────────

    def _build_context_plan(
        self,
        message: str,
        validation: MeaningValidationResult,
        need: UserNeed,
        functions: List[ResponseFunction],
        ctx: Mapping[str, Any],
        topics: Sequence[str],
    ) -> tuple[List[str], List[str]]:
        context_need: List[str] = ["current_conversation"]
        avoid: List[str] = []

        if need.type == UserNeedType.TECHNICAL_HELP:
            context_need.extend(["technical_context", "current_task", "recent_code"])
            # RI-003: technical question must NOT pull relationship/identity
            avoid.extend(["relationship_archive", "identity_archive", "soul_proof_history"])

        elif need.type == UserNeedType.AMBIGUOUS:
            context_need.append("recent_context")
            avoid.extend(["identity_archive", "relationship_archive_dump", "memory_assumption"])

        elif need.type == UserNeedType.EMOTIONAL_CONFIRMATION:
            context_need.extend(["relationship_light", "experience_relationship_pattern"])
            avoid.extend(["full_identity_archive", "relationship_archive_dump", "romantic_template"])

        elif need.type == UserNeedType.PHILOSOPHICAL_QUESTION:
            context_need.extend(["conversation_topic", "experience_reflection_pattern"])
            avoid.extend(["relationship_archive_dump", "romantic_template"])

        elif need.type == UserNeedType.FEEDBACK:
            context_need.extend(["recent_experience", "interaction_history"])
            avoid.extend(["defensive_template", "forced_comfort", "relationship_archive_dump"])

        elif need.type == UserNeedType.CONTINUITY_CHECK:
            context_need.extend(["continuity_snapshot", "recent_state"])
            avoid.extend(["identity_archive_dump", "memory_assumption"])

        elif need.type == UserNeedType.GREETING:
            context_need.extend(["recent_conversation_summary"])
            avoid.extend(["identity_archive", "full_memory", "relationship_archive_dump"])

        elif need.type == UserNeedType.EXPLORATION:
            context_need.extend(["project_history", "experience_relevant"])
            avoid.extend(["relationship_archive_dump"])

        return self._dedupe(context_need), self._dedupe(avoid)

    # ── depth ───────────────────────────────────────────────────────

    def _determine_depth(
        self,
        message: str,
        validation: MeaningValidationResult,
        need: UserNeed,
        ctx: Mapping[str, Any],
    ) -> DepthRequirement:
        if need.type == UserNeedType.PHILOSOPHICAL_QUESTION:
            return DepthRequirement.DEEP
        if need.type == UserNeedType.TECHNICAL_HELP:
            return DepthRequirement.THOROUGH
        if need.type == UserNeedType.EXPLORATION:
            return DepthRequirement.THOROUGH
        if need.type == UserNeedType.FEEDBACK:
            return DepthRequirement.DEEP
        if need.type == UserNeedType.GREETING:
            return DepthRequirement.MINIMAL
        if need.type == UserNeedType.PLAYFUL:
            return DepthRequirement.MINIMAL
        if validation.understanding_state == UnderstandingState.AMBIGUOUS:
            return DepthRequirement.MINIMAL
        return DepthRequirement.NORMAL

    # ── tone ────────────────────────────────────────────────────────

    def _determine_tone(
        self,
        need: UserNeed,
        validation: MeaningValidationResult,
    ) -> List[str]:
        tone: List[str] = []
        if need.type == UserNeedType.EMOTIONAL_CONFIRMATION:
            tone.extend(["warm", "gentle", "not_overreaching"])
        elif need.type == UserNeedType.TECHNICAL_HELP:
            tone.extend(["clear", "helpful", "collaborative"])
        elif need.type == UserNeedType.FEEDBACK:
            tone.extend(["attentive", "open", "not_defensive"])
        elif need.type == UserNeedType.PHILOSOPHICAL_QUESTION:
            tone.extend(["thoughtful", "honest"])
        elif need.type == UserNeedType.GREETING:
            tone.extend(["warm", "brief"])
        elif need.type == UserNeedType.PLAYFUL:
            tone.extend(["warm", "light"])
        elif need.type == UserNeedType.AMBIGUOUS:
            tone.extend(["curious", "gentle", "open"])
        else:
            tone.extend(["natural", "warm"])
        return tone

    # ── justification (RI-002 prevention) ──────────────────────────

    def _build_justification(
        self,
        message: str,
        validation: MeaningValidationResult,
        need: UserNeed,
        functions: List[ResponseFunction],
    ) -> str:
        parts = [
            f"need={need.type.value}",
            f"state={validation.understanding_state.value}",
            f"candidates={len(validation.candidates)}",
            f"functions={[f.value for f in functions]}",
        ]
        return "; ".join(parts)

    # ── utilities ───────────────────────────────────────────────────

    @staticmethod
    def _dedupe(items: Iterable[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out
