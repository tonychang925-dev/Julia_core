"""Market Brain Prediction Models — forward-looking structured predictions with feedback loop.

MB-P: Prediction → Market Truth → Deviation → Error Attribution → Calibration.

Predictions are Evidence, not Julia's belief. Market Truth is the objective outcome.
The feedback loop improves Evidence quality over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

CST = timezone(timedelta(hours=8))


@dataclass(frozen=True, slots=True)
class MarketPrediction:
    """A structured forward-looking market prediction.

    This is Evidence, not Julia's conclusion. Market Truth will validate or
    invalidate it. The prediction_id becomes part of the feedback loop.
    """

    prediction_id: str                          # unique, stable across retries
    created_at: str                             # ISO timestamp when prediction was made
    target_date: str                            # ISO date the prediction targets

    # What was predicted
    subject_type: str                           # "theme" | "stock" | "index" | "regime" | "sector"
    subject_key: str                            # theme_id, stock_code, index_code, etc.
    subject_label: str = ""                     # human-readable label

    direction: str = ""                         # "up" | "down" | "range" | "breakout" | "decay"
    confidence: float = 0.0                     # 0.0 - 1.0
    timeframe: str = ""                         # "intraday" | "daily" | "weekly" | "swing"

    # Supporting evidence (from when prediction was made)
    evidence_summary: str = ""                  # brief description of supporting evidence
    supporting_refs: tuple[str, ...] = ()       # DecisionEnvelope IDs, causal_link IDs
    market_context: dict[str, Any] = field(default_factory=dict)  # frozen market state at prediction time
    source: str = "market_brain"                # origin label

    # ---- Market Truth (filled after target date passes) ----
    truth_status: str = "pending"               # "pending" | "validated" | "invalidated" | "partial" | "indeterminate"
    truth_filled_at: str = ""                   # when truth was recorded
    actual_outcome: str = ""                    # what actually happened
    truth_source: str = ""                      # where truth came from (data provider, manual, etc.)

    # ---- Deviation Analysis ----
    deviation_direction: str = ""               # "correct" | "opposite" | "neutral" | "insufficient_data"
    deviation_magnitude: float = 0.0            # quantitative deviation if measurable
    error_classification: str = ""              # "timing_error" | "direction_error" | "magnitude_error"
                                                # | "unknown_factor" | "data_gap" | "model_limitation"
    calibration_notes: str = ""                 # what to adjust in future predictions

    @property
    def is_resolved(self) -> bool:
        return self.truth_status not in ("pending",)

    @property
    def was_correct(self) -> bool:
        return self.truth_status == "validated"

    @property
    def was_wrong(self) -> bool:
        return self.truth_status == "invalidated"


@dataclass
class PredictionLedger:
    """Tracks predictions over time. Feeds calibration back into Market Brain."""

    predictions: list[MarketPrediction] = field(default_factory=list)

    def record(self, prediction: MarketPrediction):
        self.predictions.append(prediction)

    def resolve(self, prediction_id: str, *, actual_outcome: str,
                truth_source: str = "", deviation_direction: str = "",
                error_classification: str = "", calibration_notes: str = ""):
        """Resolve a prediction with market truth."""
        for i, p in enumerate(self.predictions):
            if p.prediction_id == prediction_id:
                # Determine truth status from deviation
                if deviation_direction == "correct":
                    truth_status = "validated"
                elif deviation_direction == "opposite":
                    truth_status = "invalidated"
                elif deviation_direction == "neutral":
                    truth_status = "partial"
                else:
                    truth_status = "indeterminate"

                # Create resolved prediction (frozen dataclass → new instance)
                resolved = MarketPrediction(
                    prediction_id=p.prediction_id,
                    created_at=p.created_at,
                    target_date=p.target_date,
                    subject_type=p.subject_type,
                    subject_key=p.subject_key,
                    subject_label=p.subject_label,
                    direction=p.direction,
                    confidence=p.confidence,
                    timeframe=p.timeframe,
                    evidence_summary=p.evidence_summary,
                    supporting_refs=p.supporting_refs,
                    market_context=p.market_context,
                    source=p.source,
                    truth_status=truth_status,
                    truth_filled_at=datetime.now(CST).isoformat(),
                    actual_outcome=actual_outcome,
                    truth_source=truth_source,
                    deviation_direction=deviation_direction,
                    deviation_magnitude=0.0,
                    error_classification=error_classification,
                    calibration_notes=calibration_notes,
                )
                self.predictions[i] = resolved
                return resolved
        return None

    @property
    def pending_count(self) -> int:
        return sum(1 for p in self.predictions if not p.is_resolved)

    @property
    def accuracy_rate(self) -> float:
        resolved = [p for p in self.predictions if p.is_resolved]
        if not resolved:
            return 0.0
        correct = sum(1 for p in resolved if p.was_correct)
        return correct / len(resolved)

    def calibration_summary(self) -> dict[str, Any]:
        """Produce a calibration summary for feedback into Evidence quality."""
        resolved = [p for p in self.predictions if p.is_resolved]
        total = len(resolved)
        if total == 0:
            return {"status": "no_resolved_predictions", "total_pending": self.pending_count}

        correct = sum(1 for p in resolved if p.was_correct)
        wrong = sum(1 for p in resolved if p.was_wrong)
        partial = total - correct - wrong

        error_types: dict[str, int] = {}
        for p in resolved:
            if p.error_classification:
                error_types[p.error_classification] = error_types.get(p.error_classification, 0) + 1

        return {
            "total_predictions": len(self.predictions),
            "resolved": total,
            "pending": self.pending_count,
            "correct": correct,
            "wrong": wrong,
            "partial": partial,
            "accuracy": correct / total if total > 0 else 0.0,
            "error_distribution": error_types,
            "avg_confidence_correct": sum(p.confidence for p in resolved if p.was_correct) / max(correct, 1),
            "avg_confidence_wrong": sum(p.confidence for p in resolved if p.was_wrong) / max(wrong, 1),
        }


__all__ = ["MarketPrediction", "PredictionLedger"]
