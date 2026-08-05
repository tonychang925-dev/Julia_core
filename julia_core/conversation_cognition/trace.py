"""Trace-only cognition artifacts for K8.0.6.

These objects deliberately do not contain final Julia language.  They are
machine-readable evidence that a message passed through cognition before any
future provider adapter is allowed to generate text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

UNDERSTOOD = "UNDERSTOOD"
PARTIALLY_UNDERSTOOD = "PARTIALLY_UNDERSTOOD"
AMBIGUOUS = "AMBIGUOUS"
UNKNOWN = "UNKNOWN"
UNDERSTANDING_STATES = {UNDERSTOOD, PARTIALLY_UNDERSTOOD, AMBIGUOUS, UNKNOWN}


@dataclass(frozen=True)
class MeaningCandidate:
    """A possible contextual meaning with uncertainty preserved."""

    meaning: str
    confidence: float
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meaning": self.meaning,
            "confidence": round(float(self.confidence), 4),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class UnderstandingTrace:
    """Conversation understanding artifact.

    This is not an intent router and does not contain an answer.
    """

    literal: str
    state: str
    meaning_candidates: List[MeaningCandidate] = field(default_factory=list)
    need_clarification: bool = False
    missing_information: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in UNDERSTANDING_STATES:
            raise ValueError(f"invalid understanding state: {self.state}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "literal": self.literal,
            "state": self.state,
            "meaning_candidates": [c.to_dict() for c in self.meaning_candidates],
            "need_clarification": self.need_clarification,
            "missing_information": list(self.missing_information),
        }


@dataclass(frozen=True)
class MeaningValidationTrace:
    """Contextual meaning validation artifact.

    It records context needs and suppressions.  It is debug-only and must not be
    sent to Provider.
    """

    requires_context: List[str] = field(default_factory=list)
    avoid_context: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    provider_visible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requires_context": list(self.requires_context),
            "avoid_context": list(self.avoid_context),
            "missing_information": list(self.missing_information),
            "provider_visible": self.provider_visible,
        }


@dataclass(frozen=True)
class CognitionTrace:
    """Top-level K8.0.6 trace-only artifact."""

    user_message: str
    understanding: UnderstandingTrace
    meaning_validation: MeaningValidationTrace
    intention: Optional[Dict[str, Any]] = None
    provider_request: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    cognitive_causality_trace: Dict[str, Any] = field(default_factory=dict)
    failure_labels: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cognition_trace": {
                "input": {"user_message": self.user_message},
                "understanding": self.understanding.to_dict(),
                "meaning_validation": self.meaning_validation.to_dict(),
                "intention": self.intention,
                "provider_request": self.provider_request,
                "final_response": self.final_response,
                "cognitive_causality_trace": dict(self.cognitive_causality_trace),
                "failure_labels": list(self.failure_labels),
            }
        }

    def assert_trace_only(self) -> None:
        """Raise if any response/provider path leaked into K8.0.6."""
        if self.final_response is not None:
            raise AssertionError("K8.0.6 trace leaked final_response")
        if self.provider_request is not None:
            raise AssertionError("K8.0.6 trace leaked provider_request")
        if self.meaning_validation.provider_visible:
            raise AssertionError("debug-only meaning validation became provider-visible")
