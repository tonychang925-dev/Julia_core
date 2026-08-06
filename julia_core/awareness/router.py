"""M3.0 Observation Router — filter, not analyst.

ADR-028 Section 3: Determines if an ObservationEvent is significant
enough to enter Julia Runtime. Does NOT use LLM. Uses rule-based
significance checks with configurable thresholds.

Forbidden: Observation → LLM → judgment. This destroys the awareness boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from julia_core.awareness.models import ObservationEvent


@dataclass
class SignificanceResult:
    """Router decision: should Julia pay attention to this?"""
    significant: bool
    reason: str
    event: ObservationEvent


class ObservationRouter:
    """Filters ObservationEvents for significance.

    Does NOT call LLM. Uses configurable thresholds and domain rules.
    This is a gate, not an analyst.
    """

    # M3.0: Simple significance rules per change_type
    SIGNIFICANCE_THRESHOLDS = {
        "heat_jump": {"min_delta_abs": 10, "min_confidence": 0.5},
        "risk_spike": {"min_delta_abs": 5, "min_confidence": 0.4},
        "sentiment_shift": {"min_delta_abs": 15, "min_confidence": 0.5},
        "new_pattern": {"min_confidence": 0.6},
        "volume_surge": {"min_delta_abs": 20, "min_confidence": 0.5},
    }

    def __init__(self, thresholds: dict | None = None):
        self.thresholds = thresholds or self.SIGNIFICANCE_THRESHOLDS

    def evaluate(self, event: ObservationEvent) -> SignificanceResult:
        """Determine if an observation is significant enough to process.

        Returns SignificanceResult with decision and reason.
        Non-significant events are still logged (in EventStore) but
        do not trigger workflow creation.
        """
        if event.confidence <= 0:
            return SignificanceResult(False, "zero confidence — noise", event)

        threshold = self.thresholds.get(event.change_type)
        if threshold is None:
            # Unknown change type: accept with low confidence check
            if event.confidence >= 0.7:
                return SignificanceResult(True, f"unknown change type '{event.change_type}' with high confidence", event)
            return SignificanceResult(False, f"unknown change type '{event.change_type}' below threshold", event)

        min_delta = threshold.get("min_delta_abs", 0)
        min_conf = threshold.get("min_confidence", 0.5)

        if event.confidence < min_conf:
            return SignificanceResult(False, f"confidence {event.confidence} < {min_conf}", event)

        # Parse delta value (strip sign, check absolute)
        if min_delta > 0 and event.delta:
            try:
                delta_val = abs(int(event.delta.replace("%", "").replace("+", "")))
                if delta_val < min_delta:
                    return SignificanceResult(False, f"delta {delta_val} < {min_delta}", event)
            except ValueError:
                pass

        return SignificanceResult(True, f"significant: {event.change_type} on {event.subject}", event)


__all__ = ["ObservationRouter", "SignificanceResult"]
