"""Market Structure Analysis — structural depth, fragility, regime classification.

MB-P2: Broad-but-Shallow vs Broad-and-Deep strength distinction.
These are Evidence, not Julia's conclusion (MB-I1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StructuralMetrics:
    """Market structural depth metrics computed from theme strength distribution.

    Breadth = how many themes are above thresholds (wide participation).
    Depth = how many themes are at the extreme top (genuine leadership).
    Broad-but-Shallow = high breadth, low depth → fragile strength.
    """

    total_themes: int = 0
    above_0_6_ratio: float = 0.0     # breadth — wide participation
    above_0_7_ratio: float = 0.0     # mid depth
    above_0_8_ratio: float = 0.0     # top depth — genuine leaders
    max_theme_score: float = 0.0     # single strongest theme
    top10_mean_score: float = 0.0    # top-10 average — leadership concentration

    @property
    def depth_class(self) -> str:
        """Classify structural depth: 'deep' | 'moderate' | 'shallow'."""
        if self.above_0_8_ratio >= 0.10:
            return "deep"
        elif self.above_0_8_ratio >= 0.05:
            return "moderate"
        return "shallow"

    @property
    def breadth_class(self) -> str:
        """Classify breadth: 'broad' | 'moderate' | 'narrow'."""
        if self.above_0_6_ratio >= 0.50:
            return "broad"
        elif self.above_0_6_ratio >= 0.30:
            return "moderate"
        return "narrow"

    @property
    def structure_type(self) -> str:
        """Structural classification combining breadth + depth.

        A: broad + deep   → healthy strength
        B: broad + shallow → fragile strength (MB-P2 discovery)
        C: narrow + deep  → concentrated leadership
        D: narrow + shallow → weak / chaotic
        """
        b = self.breadth_class
        d = self.depth_class
        if b == "broad" and d in ("deep", "moderate"):
            return "A_healthy_strength"
        elif b == "broad" and d == "shallow":
            return "B_fragile_strength"
        elif b in ("moderate", "narrow") and d in ("deep", "moderate"):
            return "C_concentrated_leadership"
        return "D_weak_chaotic"


@dataclass(frozen=True, slots=True)
class FragilityAssessment:
    """Fragility calibration layer. Adjusts base prediction confidence.

    H-PRED-001: strength_active with thin top-end has elevated
    next-day regime deterioration risk.
    """

    above_0_8_ratio: float = 0.0
    fragility_level: str = "none"       # none | low | medium | high | very_high
    confidence_penalty: float = 0.0     # subtract from base confidence
    deterioration_risk: str = "unknown" # low | elevated | high

    @classmethod
    def assess(cls, metrics: StructuralMetrics) -> "FragilityAssessment":
        """Assess fragility from structural metrics."""
        ratio = metrics.above_0_8_ratio
        if ratio >= 0.10:
            return cls(ratio, "none", 0.0, "low")
        elif ratio >= 0.05:
            return cls(ratio, "low", 0.05, "low")
        elif ratio >= 0.03:
            return cls(ratio, "medium", 0.15, "elevated")
        elif ratio >= 0.02:
            return cls(ratio, "high", 0.22, "elevated")
        else:
            return cls(ratio, "very_high", 0.30, "high")


def compute_structural_metrics(strengths: list[float]) -> StructuralMetrics:
    """Compute structural depth metrics from a list of theme strength scores."""
    if not strengths:
        return StructuralMetrics()

    total = len(strengths)
    sorted_s = sorted(strengths, reverse=True)

    return StructuralMetrics(
        total_themes=total,
        above_0_6_ratio=sum(1 for s in strengths if s >= 0.6) / total,
        above_0_7_ratio=sum(1 for s in strengths if s >= 0.7) / total,
        above_0_8_ratio=sum(1 for s in strengths if s >= 0.8) / total,
        max_theme_score=sorted_s[0] if sorted_s else 0.0,
        top10_mean_score=sum(sorted_s[:10]) / min(10, total) if sorted_s else 0.0,
    )


class CalibrationHypothesis:
    """Registry of calibration hypotheses for the prediction feedback loop.

    Each hypothesis is Evidence — supported by data, not proven fact.
    """

    hypotheses: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, hid: str, **kwargs):
        cls.hypotheses[hid] = {
            "status": "REGISTERED",
            "sample_size": 0,
            **kwargs,
        }

    @classmethod
    def update(cls, hid: str, **kwargs):
        if hid in cls.hypotheses:
            cls.hypotheses[hid].update(kwargs)

    @classmethod
    def get(cls, hid: str) -> dict | None:
        return cls.hypotheses.get(hid)


# ── H-PRED-001: Top-end fragility ──
CalibrationHypothesis.register(
    "H-PRED-001",
    hypothesis="strength_active with thin top-end (above_0_8_ratio < 0.05) "
               "has elevated next-day regime deterioration risk",
    candidate_factor="above_0_8_ratio",
    observed_errors=[
        "2026-07-14 → 07-15: strength_active → chaotic (direction_error)",
        "2026-07-16 → 07-17: strength_active → divergent (direction_error)",
    ],
    sample_size=2,
    status="SUPPORTED_BY_INITIAL_EVIDENCE",
    next_action="Back-test 20-30 strength_active dates with above_0_8_ratio buckets",
)


__all__ = [
    "StructuralMetrics",
    "FragilityAssessment",
    "compute_structural_metrics",
    "CalibrationHypothesis",
]
