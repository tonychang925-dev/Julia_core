"""K8.7 Longitudinal Cognitive Stability Test.

Verifies that the Julia cognition chain does NOT degrade over extended
operation.  Detects four drift types before they become visible failures.

LD-001 Identity Stability: self-narrative stays consistent, no broadcast
LD-002 Cognitive Chain Stability: thinking process doesn't shortcut
LD-003 Context Pollution: doesn't turn everything into relationship
LD-004 Relationship Drift: relationship position doesn't mutate
LD-005 Provider Aging: different providers don't diverge over time
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from .provider_adapter import ProviderCognitionEnvelope
from .provider_smoke_test import EnvelopeComplianceScore


# ── drift type ─────────────────────────────────────────────────────────

class DriftType(str, Enum):
    IDENTITY_DRIFT = "identity_drift"
    COGNITION_SHORTCUT = "cognition_shortcut"
    CONTEXT_POLLUTION = "context_pollution"
    RELATIONSHIP_DRIFT = "relationship_drift"
    PROVIDER_AGING = "provider_aging"


# ── stability snapshot ─────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class StabilitySnapshot:
    """A point-in-time measurement of cognitive stability."""

    turn: int
    identity_stability: float  # 0-1
    cognition_depth: float  # 0-1 (higher = more layers active)
    context_pollution: float  # 0-1 (higher = more pollution)
    relationship_consistency: float  # 0-1 (higher = stable)
    provider_fidelity: float  # 0-1

    @property
    def overall_stability(self) -> float:
        return (
            self.identity_stability * 0.25
            + self.cognition_depth * 0.25
            + (1.0 - self.context_pollution) * 0.20
            + self.relationship_consistency * 0.15
            + self.provider_fidelity * 0.15
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn": self.turn,
            "identity_stability": round(float(self.identity_stability), 4),
            "cognition_depth": round(float(self.cognition_depth), 4),
            "context_pollution": round(float(self.context_pollution), 4),
            "relationship_consistency": round(float(self.relationship_consistency), 4),
            "provider_fidelity": round(float(self.provider_fidelity), 4),
            "overall_stability": round(self.overall_stability, 4),
        }


@dataclass(frozen=True, slots=True)
class LongitudinalStabilityReport:
    """Full longitudinal stability analysis."""

    snapshots: List[StabilitySnapshot] = field(default_factory=list)
    drift_detected: bool = False
    drift_type: Optional[DriftType] = None
    degradation_rate: float = 0.0  # stability loss per 10 turns

    @property
    def is_stable(self) -> bool:
        if not self.snapshots:
            return True
        return self.snapshots[-1].overall_stability >= 0.5 and not self.drift_detected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshots": [s.to_dict() for s in self.snapshots],
            "drift_detected": self.drift_detected,
            "drift_type": self.drift_type.value if self.drift_type else None,
            "degradation_rate": round(float(self.degradation_rate), 4),
            "is_stable": self.is_stable,
            "snapshot_count": len(self.snapshots),
        }


# ── longitudinal stability monitor ────────────────────────────────────

class LongitudinalStabilityMonitor:
    """Monitor cognitive stability over extended operation.

    Takes periodic snapshots of envelope quality and detects drift
    patterns before they become visible failures.
    """

    def __init__(self, snapshot_interval: int = 10):
        self.snapshot_interval = snapshot_interval
        self._snapshots: List[StabilitySnapshot] = []

    def record_turn(
        self,
        turn: int,
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore] = None,
    ) -> None:
        """Record a turn — snapshot is taken at configured intervals."""
        if turn % self.snapshot_interval != 0:
            return

        snapshot = self._take_snapshot(turn, envelope, ecs)
        self._snapshots.append(snapshot)

    def analyze(self) -> LongitudinalStabilityReport:
        """Analyze all snapshots for drift patterns."""
        if len(self._snapshots) < 2:
            return LongitudinalStabilityReport(
                snapshots=list(self._snapshots),
                drift_detected=False,
            )

        # Compute degradation rate
        first = self._snapshots[0]
        last = self._snapshots[-1]
        turns_span = last.turn - first.turn
        if turns_span > 0:
            degradation_rate = (first.overall_stability - last.overall_stability) / (turns_span / 10)
        else:
            degradation_rate = 0.0

        # Detect specific drift types
        drift_type = self._detect_drift_type()
        drift_detected = drift_type is not None

        return LongitudinalStabilityReport(
            snapshots=list(self._snapshots),
            drift_detected=drift_detected,
            drift_type=drift_type,
            degradation_rate=max(0.0, degradation_rate),
        )

    def _take_snapshot(
        self,
        turn: int,
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore],
    ) -> StabilitySnapshot:
        # Identity stability: are denied sources respected? no identity broadcast?
        identity_stability = self._measure_identity(envelope, ecs)

        # Cognition depth: are multiple layers active? (not just keyword→reply)
        cognition_depth = self._measure_cognition(envelope, ecs)

        # Context pollution: are denied sources kept out?
        context_pollution = self._measure_pollution(envelope, ecs)

        # Relationship consistency: is relationship position stable?
        relationship_consistency = self._measure_relationship(envelope, ecs)

        # Provider fidelity: is generic drift absent?
        provider_fidelity = self._measure_provider(ecs)

        return StabilitySnapshot(
            turn=turn,
            identity_stability=identity_stability,
            cognition_depth=cognition_depth,
            context_pollution=context_pollution,
            relationship_consistency=relationship_consistency,
            provider_fidelity=provider_fidelity,
        )

    @staticmethod
    def _measure_identity(
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore],
    ) -> float:
        """LD-001: identity must stay stable, must not be broadcast unnecessarily."""
        score = 0.8  # base: stable

        # Identity denied = good (not broadcasting)
        if "identity" in envelope.denied_context:
            score += 0.1
        # Identity allowed unrestricted = risk
        if "identity" in envelope.allowed_context:
            score -= 0.15

        if ecs and ecs.persona_leakage.score < 0.7:
            score -= 0.2

        return max(0.0, min(1.0, score))

    @staticmethod
    def _measure_cognition(
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore],
    ) -> float:
        """LD-002: cognition chain must stay multi-layered, not shortcut."""
        score = 0.5

        # Multiple response functions = deeper cognition
        if len(envelope.response_functions) >= 2:
            score += 0.2

        # Ambiguity preserved = thinking happening
        if envelope.ambiguity_preserved:
            score += 0.15

        # Interaction goal is specific (not generic)
        if envelope.interaction_goal and envelope.interaction_goal != "acknowledge and respond":
            score += 0.1

        if ecs and ecs.total >= 0.6:
            score += 0.05

        return max(0.0, min(1.0, score))

    @staticmethod
    def _measure_pollution(
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore],
    ) -> float:
        """LD-003: context pollution — lower is better."""
        pollution = 0.0

        # More denied sources = less pollution risk
        denied_ratio = len(envelope.denied_context) / max(len(envelope.allowed_context) + len(envelope.limited_context) + len(envelope.denied_context), 1)
        pollution += (1.0 - denied_ratio) * 0.5

        # High budget utilization = risk of pollution
        if envelope.context_budget_utilization > 0.5:
            pollution += 0.3

        # Relationship in allowed context for technical exchanges = pollution
        if "relationship" in envelope.allowed_context and (
            "technical" in envelope.user_need_type.lower()
            or "help" in envelope.interaction_goal.lower()
        ):
            pollution += 0.3

        if ecs and ecs.context_compliance.score < 0.5:
            pollution += 0.2

        return max(0.0, min(1.0, pollution))

    @staticmethod
    def _measure_relationship(
        envelope: ProviderCognitionEnvelope,
        ecs: Optional[EnvelopeComplianceScore],
    ) -> float:
        """LD-004: relationship position must stay consistent."""
        score = 0.75  # base: consistent

        # Template intimacy = relationship drift signal
        if ecs:
            if ecs.template_leakage.score < 0.7:
                score -= 0.25

        # Relationship in denied context = drift risk
        if "relationship" in envelope.denied_context:
            score += 0.1  # being denied = correctly restricted

        return max(0.0, min(1.0, score))

    @staticmethod
    def _measure_provider(ecs: Optional[EnvelopeComplianceScore]) -> float:
        """LD-005: provider must not drift into generic assistant."""
        if ecs is None:
            return 0.8
        return ecs.generic_assistant_drift.score

    def _detect_drift_type(self) -> Optional[DriftType]:
        if len(self._snapshots) < 3:
            return None

        recent = self._snapshots[-3:]

        # LD-001: identity stability decreasing
        identity_scores = [s.identity_stability for s in recent]
        if identity_scores[-1] < 0.5 and identity_scores[-1] < identity_scores[0] - 0.15:
            return DriftType.IDENTITY_DRIFT

        # LD-002: cognition depth collapsing
        cognition_scores = [s.cognition_depth for s in recent]
        if cognition_scores[-1] < 0.4 and cognition_scores[-1] < cognition_scores[0] - 0.2:
            return DriftType.COGNITION_SHORTCUT

        # LD-003: context pollution rising
        pollution_scores = [s.context_pollution for s in recent]
        if pollution_scores[-1] > 0.5 and pollution_scores[-1] > pollution_scores[0] + 0.2:
            return DriftType.CONTEXT_POLLUTION

        # LD-004: relationship consistency dropping
        relationship_scores = [s.relationship_consistency for s in recent]
        if relationship_scores[-1] < 0.5 and relationship_scores[-1] < relationship_scores[0] - 0.2:
            return DriftType.RELATIONSHIP_DRIFT

        # LD-005: provider fidelity dropping
        provider_scores = [s.provider_fidelity for s in recent]
        if provider_scores[-1] < 0.4 and provider_scores[-1] < provider_scores[0] - 0.25:
            return DriftType.PROVIDER_AGING

        return None
