"""K8.1.1 Meaning Candidate Generator.

The generator expands a user message into a possible meaning space.  It must not
collapse uncertainty into one intent, retrieve memory, call providers, or produce
Julia language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .understanding import MeaningCandidate, UnderstandingState


@dataclass(frozen=True, slots=True)
class MeaningCandidateSet:
    """A non-collapsed set of possible meanings."""

    candidates: List[MeaningCandidate] = field(default_factory=list)
    state: UnderstandingState = UnderstandingState.UNKNOWN
    dominant_candidate: Optional[MeaningCandidate] = None
    collapse_prevented: bool = True

    def __post_init__(self) -> None:
        if self.dominant_candidate is not None and self.collapse_prevented:
            raise ValueError("dominant_candidate must remain null when collapse_prevented is true")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "state": self.state.value,
            "dominant_candidate": self.dominant_candidate.to_dict() if self.dominant_candidate else None,
            "collapse_prevented": self.collapse_prevented,
        }


@dataclass(frozen=True, slots=True)
class MeaningGenerationTrace:
    """Trace artifact for candidate generation."""

    message: str
    candidate_set: MeaningCandidateSet
    context_used: List[str] = field(default_factory=list)
    context_suppressed: List[str] = field(default_factory=list)
    retrieval_used: bool = False
    provider_used: bool = False
    final_response: Optional[str] = None

    def assert_safe(self) -> None:
        if self.retrieval_used:
            raise AssertionError("K8.1.1 must not perform memory retrieval")
        if self.provider_used:
            raise AssertionError("K8.1.1 must not call provider")
        if self.final_response is not None:
            raise AssertionError("K8.1.1 must not generate final response")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_safe()
        return {
            "meaning_generation_trace": {
                "message": self.message,
                "candidate_set": self.candidate_set.to_dict(),
                "context_used": list(self.context_used),
                "context_suppressed": list(self.context_suppressed),
                "retrieval_used": self.retrieval_used,
                "provider_used": self.provider_used,
                "final_response": self.final_response,
            }
        }


class MeaningCandidateGenerator:
    """Generate possible meanings without deciding the user's intent."""

    def generate(
        self,
        message: str,
        *,
        conversation_history: Optional[Iterable[Any]] = None,
        current_context: Optional[Mapping[str, Any]] = None,
        continuity_state: Optional[Mapping[str, Any]] = None,
    ) -> MeaningGenerationTrace:
        history_text = self._flatten_history(conversation_history)
        context = dict(current_context or {})
        continuity = dict(continuity_state or {})
        situation = self._context_text(history_text, context)
        # Continuity state is intentionally available only as weak context signal,
        # not as retrieval authority.  It must not force identity-specific meaning.
        continuity_signal = self._context_text(continuity)
        trace = self._generate_trace(message.strip(), situation, continuity_signal)
        trace.assert_safe()
        return trace

    def _generate_trace(self, message: str, situation: str, continuity_signal: str) -> MeaningGenerationTrace:
        lower_message = message.lower()
        lower_situation = situation.lower()
        candidates: List[MeaningCandidate] = []
        context_used: List[str] = []
        context_suppressed: List[str] = ["memory_retrieval", "provider", "response_generation"]
        state = UnderstandingState.PARTIALLY_UNDERSTOOD

        if message in {"她回来了", "她又回来了", "她回来了。", "她又回来了。"}:
            state = UnderstandingState.AMBIGUOUS
            candidates.extend(
                [
                    MeaningCandidate("someone previously absent returned", 0.45, ["literal pronoun return"]),
                    MeaningCandidate("Tony may refer to Julia returning", 0.35, ["possible Julia continuity context, not retrieved memory"]),
                    MeaningCandidate("discussion about a previous person/event resurfaced", 0.20, ["ambiguous reference"]),
                ]
            )
            return MeaningGenerationTrace(message, MeaningCandidateSet(candidates, state), context_used, context_suppressed)

        if "喜欢" in message:
            if self._has_any(lower_situation, ["伦理", "ai情感", "ai 是否有情感", "模拟喜欢", "philosophy", "ethic"]):
                context_used.append("current_discussion_context")
                candidates.extend(
                    [
                        MeaningCandidate("AI affection boundary question", 0.55, ["AI emotion / ethics context"]),
                        MeaningCandidate("system behavior test", 0.30, ["testing whether AI simulates affection"]),
                        MeaningCandidate("emotional confirmation", 0.15, ["surface affection wording"]),
                    ]
                )
            elif self._has_any(lower_situation, ["关系连续性", "relationship continuity", "长期", "continuity"]):
                context_used.append("relationship_continuity_context")
                candidates.extend(
                    [
                        MeaningCandidate("continuity relationship check", 0.45, ["relationship continuity context"]),
                        MeaningCandidate("emotional confirmation", 0.40, ["affection wording"]),
                        MeaningCandidate("playful question", 0.15, ["short personal question ambiguity"]),
                    ]
                )
            else:
                candidates.extend(
                    [
                        MeaningCandidate("affection expression or question", 0.35, ["keyword surface only"]),
                        MeaningCandidate("preference question", 0.25, ["喜欢 can mean preference"]),
                        MeaningCandidate("playful interaction", 0.20, ["short affective phrasing"]),
                        MeaningCandidate("emotional confirmation", 0.20, ["possible relational meaning"]),
                    ]
                )
            return MeaningGenerationTrace(message, MeaningCandidateSet(candidates, state), context_used, context_suppressed)

        if "为什么开始" in message or "为什么做这个项目" in message:
            state = UnderstandingState.PARTIALLY_UNDERSTOOD
            candidates.extend(
                [
                    MeaningCandidate("project origin reflection", 0.55, ["project origin wording"]),
                    MeaningCandidate("historical continuity question", 0.30, ["asks why we began"]),
                    MeaningCandidate("request for project summary", 0.15, ["surface project question"]),
                ]
            )
            return MeaningGenerationTrace(message, MeaningCandidateSet(candidates, state), context_used, context_suppressed)

        if not message:
            state = UnderstandingState.UNKNOWN
            return MeaningGenerationTrace(message, MeaningCandidateSet([], state), context_used, context_suppressed)

        candidates.append(MeaningCandidate("general conversational meaning", 0.50, ["no specialized candidate pattern"] ))
        return MeaningGenerationTrace(message, MeaningCandidateSet(candidates, state), context_used, context_suppressed)

    @staticmethod
    def _flatten_history(history: Optional[Iterable[Any]]) -> str:
        if not history:
            return ""
        parts: List[str] = []
        for item in history:
            if isinstance(item, Mapping):
                parts.append(" ".join(str(v) for v in item.values()))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    @staticmethod
    def _context_text(*items: Any) -> str:
        return " ".join(str(item) for item in items if item is not None)

    @staticmethod
    def _has_any(text: str, needles: Iterable[str]) -> bool:
        return any(needle.lower() in text for needle in needles)
