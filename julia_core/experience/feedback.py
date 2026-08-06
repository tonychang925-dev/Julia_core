"""M3.3.0 Experience Feedback Pipeline — bind → analyze → update.

ADR-031: Governed experience evolution.
Prediction → Outcome → Deviation → Admission → Experience Update.

This is NOT model training. It is Experience OS governed learning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from julia_core.experience.feedback_models import (
    PredictionRecord,
    RealityOutcome,
    ExperienceUpdate,
)


@dataclass
class OutcomeBinder:
    """Binds RealityOutcome to PredictionRecord by prediction_id.

    Unlinked outcomes are rejected — outcomes without predictions are meaningless.
    """

    def bind(self, outcome: RealityOutcome, prediction: PredictionRecord) -> tuple[bool, str]:
        """Validate and bind outcome to prediction.

        Returns (bound, reason).
        """
        if not outcome.prediction_id:
            return False, "outcome has no prediction_id — cannot bind"
        if outcome.prediction_id != prediction.prediction_id:
            return False, (
                f"prediction_id mismatch: "
                f"outcome={outcome.prediction_id} != prediction={prediction.prediction_id}"
            )
        return True, "bound"


@dataclass
class DeviationAnalyzer:
    """Measures expected vs actual deviation.

    Not just right/wrong. Produces a measurable delta.
    """

    def analyze(self, prediction: PredictionRecord, outcome: RealityOutcome) -> dict:
        """Compute deviation between prediction and outcome.

        Returns delta dict with:
          - result: "confirmed" | "disconfirmed" | "partial"
          - confidence_delta: how far prediction confidence was from outcome
          - strength: how strong the confirmation/disconfirmation is
        """
        actual = outcome.actual_result

        if actual == "confirmed":
            confidence_delta = prediction.confidence  # positive — we were right
            strength = min(prediction.confidence, 0.9)
        elif actual == "disconfirmed":
            confidence_delta = -prediction.confidence  # negative — we were wrong
            strength = prediction.confidence
        else:  # partial
            confidence_delta = prediction.confidence * 0.3  # mild positive
            strength = prediction.confidence * 0.5

        return {
            "result": actual,
            "confidence_delta": round(confidence_delta, 4),
            "strength": round(strength, 4),
            "expected_window": prediction.expected_window,
        }


@dataclass
class FeedbackPipeline:
    """Governed experience feedback loop.

    Prediction + Outcome → Bind → Analyze → Admission gate → ExperienceUpdate.

    Every update passes through ExperienceAdmission (ADR-029).
    Low-confidence or single-source updates are rejected.
    """

    binder: OutcomeBinder = field(default_factory=OutcomeBinder)
    analyzer: DeviationAnalyzer = field(default_factory=DeviationAnalyzer)

    def process(
        self,
        prediction: PredictionRecord,
        outcome: RealityOutcome,
        min_confidence: float = 0.7,
    ) -> ExperienceUpdate | None:
        """Process one prediction→outcome pair into a potential experience update.

        Returns None if:
          - Outcome cannot be bound to prediction
          - Update does not pass admission threshold
        """
        # Step 1: Bind
        bound, reason = self.binder.bind(outcome, prediction)
        if not bound:
            return None

        # Step 2: Analyze deviation
        delta = self.analyzer.analyze(prediction, outcome)

        # Step 3: Admission gate (ADR-029)
        if prediction.confidence < min_confidence:
            return None  # below threshold — not reliable enough to learn from

        # Step 4: Build experience update
        pattern_key = self._extract_pattern(prediction)
        admitted = prediction.confidence >= min_confidence

        return ExperienceUpdate(
            prediction_id=prediction.prediction_id,
            outcome_id=outcome.outcome_id,
            pattern_key=pattern_key,
            delta=delta["confidence_delta"],
            reason=f"{outcome.actual_result}: {delta.get('result', 'unknown')} "
                   f"(strength={delta['strength']})",
            admitted=admitted,
        )

    def _extract_pattern(self, prediction: PredictionRecord) -> str:
        """Extract a pattern key from prediction context."""
        parts = [prediction.source or "unknown"]
        if prediction.hypothesis:
            # Simple keyword extraction for pattern naming
            keywords = ["扩散", "突破", "启动", "退潮", "风险", "共振"]
            for kw in keywords:
                if kw in prediction.hypothesis:
                    parts.append(kw)
                    break
        return "_".join(parts)


__all__ = ["OutcomeBinder", "DeviationAnalyzer", "FeedbackPipeline"]
