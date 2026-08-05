"""K8.1.0 Conversation Understanding object model.

This module defines cognition containers only.  It deliberately does not infer,
route, retrieve memory, write prompts, call providers, or generate Julia text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List


class UnderstandingState(str, Enum):
    """Allowed uncertainty states for conversation understanding."""

    UNDERSTOOD = "UNDERSTOOD"
    PARTIALLY_UNDERSTOOD = "PARTIALLY_UNDERSTOOD"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class MeaningCandidate:
    """A possible meaning, not a final interpretation."""

    meaning: str
    confidence: float
    evidence: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not self.meaning:
            raise ValueError("meaning must not be empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meaning": self.meaning,
            "confidence": round(float(self.confidence), 4),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class LiteralContent:
    """Literal user text container."""

    text: str
    literal_meaning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "literal_meaning": self.literal_meaning}


@dataclass(frozen=True, slots=True)
class SemanticSpace:
    """A non-collapsed space of possible meanings."""

    possible_meanings: List[MeaningCandidate] = field(default_factory=list)

    def top_confidence(self) -> float:
        if not self.possible_meanings:
            return 0.0
        return max(candidate.confidence for candidate in self.possible_meanings)

    def to_dict(self) -> Dict[str, Any]:
        return {"possible_meanings": [candidate.to_dict() for candidate in self.possible_meanings]}


@dataclass(frozen=True, slots=True)
class Uncertainty:
    """Uncertainty state and confidence, separate from meaning candidates."""

    state: UnderstandingState
    confidence: float = 0.0
    need_context: bool = False
    need_clarification: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "confidence": round(float(self.confidence), 4),
            "need_context": self.need_context,
            "need_clarification": self.need_clarification,
        }


@dataclass(frozen=True, slots=True)
class ContextDependency:
    """Context activation and suppression requirements."""

    requires: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"requires": list(self.requires), "forbidden": list(self.forbidden)}


@dataclass(frozen=True, slots=True)
class UnderstandingBoundary:
    """Hard boundary proving understanding is not response generation."""

    safe: bool = True
    generates_response: bool = False
    provider_visible: bool = False
    writes_memory: bool = False
    mutates_identity: bool = False
    mutates_relationship: bool = False
    mutates_experience: bool = False

    def assert_safe(self) -> None:
        if not self.safe:
            raise AssertionError("understanding boundary is not safe")
        if self.generates_response:
            raise AssertionError("understanding must not generate response")
        if self.provider_visible:
            raise AssertionError("understanding object must not be provider-visible")
        if self.writes_memory:
            raise AssertionError("understanding must not write memory")
        if self.mutates_identity:
            raise AssertionError("cognition must not mutate identity")
        if self.mutates_relationship:
            raise AssertionError("cognition must not mutate relationship")
        if self.mutates_experience:
            raise AssertionError("cognition must not mutate experience")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe": self.safe,
            "generates_response": self.generates_response,
            "provider_visible": self.provider_visible,
            "writes_memory": self.writes_memory,
            "mutates_identity": self.mutates_identity,
            "mutates_relationship": self.mutates_relationship,
            "mutates_experience": self.mutates_experience,
        }


@dataclass(frozen=True, slots=True)
class ConversationUnderstanding:
    """K8.1.0 cognition container.

    It represents the current understanding state.  It does not infer by itself
    and cannot carry answer/provider/memory-write payloads.
    """

    literal_content: LiteralContent
    semantic_space: SemanticSpace = field(default_factory=SemanticSpace)
    uncertainty: Uncertainty = field(default_factory=lambda: Uncertainty(UnderstandingState.UNKNOWN))
    context_dependency: ContextDependency = field(default_factory=ContextDependency)
    boundary: UnderstandingBoundary = field(default_factory=UnderstandingBoundary)
    missing_information: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.boundary.assert_safe()

    @classmethod
    def ambiguous(
        cls,
        text: str,
        *,
        literal_meaning: str = "",
        missing_information: Iterable[str] = (),
        candidates: Iterable[MeaningCandidate] = (),
    ) -> "ConversationUnderstanding":
        return cls(
            literal_content=LiteralContent(text=text, literal_meaning=literal_meaning),
            semantic_space=SemanticSpace(list(candidates)),
            uncertainty=Uncertainty(
                state=UnderstandingState.AMBIGUOUS,
                confidence=0.0,
                need_context=True,
                need_clarification=True,
            ),
            context_dependency=ContextDependency(requires=["current_context"], forbidden=["provider", "memory_write"]),
            missing_information=list(missing_information),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "literal_content": self.literal_content.to_dict(),
            "semantic_space": self.semantic_space.to_dict(),
            "uncertainty": self.uncertainty.to_dict(),
            "context_dependency": self.context_dependency.to_dict(),
            "boundary": self.boundary.to_dict(),
            "missing_information": list(self.missing_information),
        }

    def assert_no_answer_generation(self) -> None:
        self.boundary.assert_safe()
