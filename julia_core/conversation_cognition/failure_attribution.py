"""K8.6 Cognitive Failure Attribution.

When Julia responds wrong, this layer identifies WHERE in the cognition
chain the failure occurred — not just "it looks wrong."

Prevents "just tweak the prompt" debugging by forcing failure localization
to a specific layer: meaning (K8.1), intention (K8.2), context (K8.3),
boundary (K8.4), or Provider.

Hard boundary: this is diagnostic infrastructure.  It does not call Provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from .provider_adapter import ProviderCognitionEnvelope
from .provider_smoke_test import EnvelopeComplianceScore, ProviderSmokeTestRunner
from .natural_e2e import CognitiveCausalityIntegrity


# ── failure label ──────────────────────────────────────────────────────

class FailureLayer(str, Enum):
    """Which layer in the cognition chain failed."""

    NO_FAILURE = "no_failure"
    MEANING_FAILURE = "meaning_failure"  # K8.1 / K8.1.5
    INTENTION_FAILURE = "intention_failure"  # K8.2
    CONTEXT_FAILURE = "context_failure"  # K8.3
    BOUNDARY_FAILURE = "boundary_failure"  # K8.4
    PROVIDER_FAILURE = "provider_failure"  # Provider execution


@dataclass(frozen=True, slots=True)
class FailureAttribution:
    """Diagnosis: which layer caused the failure, with evidence."""

    layer: FailureLayer
    confidence: float  # 0-1
    evidence: List[str] = field(default_factory=list)
    suggested_fix: str = ""

    @property
    def is_failure(self) -> bool:
        return self.layer != FailureLayer.NO_FAILURE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer.value,
            "confidence": round(float(self.confidence), 4),
            "evidence": list(self.evidence),
            "suggested_fix": self.suggested_fix,
            "is_failure": self.is_failure,
        }


# ── failure attributor ─────────────────────────────────────────────────

class CognitiveFailureAttributor:
    """Localize cognitive failure to a specific layer.

    When Julia's response is wrong, this answers:
    - Is it wrong because we misunderstood? (meaning)
    - Is it wrong because we chose the wrong goal? (intention)
    - Is it wrong because we loaded wrong context? (context)
    - Is it wrong because we violated expression boundaries? (boundary)
    - Is it wrong because Provider ignored cognition? (provider)

    Each failure type has distinct evidence signatures.
    """

    def __init__(self):
        self.smoke = ProviderSmokeTestRunner()

    def attribute(
        self,
        message: str,
        envelope: ProviderCognitionEnvelope,
        provider_output: str,
        *,
        ecs: Optional[EnvelopeComplianceScore] = None,
        cci: Optional[CognitiveCausalityIntegrity] = None,
        expected_behavior: Optional[str] = None,
    ) -> FailureAttribution:
        """Analyze and attribute failure to a specific layer.

        Priority: top-down (meaning → intention → context → boundary → provider).
        More fundamental failures override downstream ones.
        """
        ecs = ecs or self.smoke.evaluate(envelope, provider_output)
        cci = cci or CognitiveCausalityIntegrity.evaluate(
            message, envelope, provider_output,
        )
        output_lower = provider_output.lower()

        # 1. Meaning failure (K8.1/K8.1.5): ambiguity collapse, misunderstanding
        meaning_evidence = self._check_meaning_failure(envelope, output_lower)
        if meaning_evidence:
            return FailureAttribution(
                layer=FailureLayer.MEANING_FAILURE,
                confidence=meaning_evidence[0],
                evidence=meaning_evidence[1],
                suggested_fix="K8.1/K8.1.5 meaning understanding failed. "
                              "Check MeaningCandidateGenerator or MeaningValidationLayer.",
            )

        # 2. Intention failure (K8.2): goal mismatch
        intention_evidence = self._check_intention_failure(envelope, output_lower, ecs)
        if intention_evidence:
            return FailureAttribution(
                layer=FailureLayer.INTENTION_FAILURE,
                confidence=intention_evidence[0],
                evidence=intention_evidence[1],
                suggested_fix="K8.2 response intention doesn't match user need. "
                              "Check ResponseIntentionPlanner or intention selection.",
            )

        # 3. Context failure (K8.3): wrong context, context pollution
        context_evidence = self._check_context_failure(envelope, output_lower, ecs)
        if context_evidence:
            return FailureAttribution(
                layer=FailureLayer.CONTEXT_FAILURE,
                confidence=context_evidence[0],
                evidence=context_evidence[1],
                suggested_fix="K8.3 context arbitration loaded wrong context. "
                              "Check ContextArbiter decisions or per-source policies.",
            )

        # 4. Boundary failure (K8.4): architecture leakage, identity theater
        boundary_evidence = self._check_boundary_failure(ecs)
        if boundary_evidence:
            return FailureAttribution(
                layer=FailureLayer.BOUNDARY_FAILURE,
                confidence=boundary_evidence[0],
                evidence=boundary_evidence[1],
                suggested_fix="K8.4 expression boundary violated. "
                              "Tighten restricted_patterns or check boundary enforcement.",
            )

        # 5. Provider failure: clear generic assistant drift or template dominance
        provider_evidence = self._check_provider_failure(output_lower, ecs, cci)
        if provider_evidence:
            return FailureAttribution(
                layer=FailureLayer.PROVIDER_FAILURE,
                confidence=provider_evidence[0],
                evidence=provider_evidence[1],
                suggested_fix="Provider produced output that ignores cognition envelope. "
                              "Check provider adapter or provider model behavior.",
            )

        # No failure detected
        return FailureAttribution(
            layer=FailureLayer.NO_FAILURE,
            confidence=0.8,
            evidence=["All layers within acceptable bounds"],
            suggested_fix="",
        )

    # ── per-layer checks ───────────────────────────────────────────────

    def _check_meaning_failure(
        self,
        env: ProviderCognitionEnvelope,
        output: str,
    ) -> Optional[tuple[float, List[str]]]:
        """Meaning failure: ambiguity collapse, misunderstanding.

        Checks first because meaning is the foundation — if meaning is
        wrong, everything downstream is wrong.
        """
        evidence = []

        # Core preserved ambiguity but output resolved it
        if env.understanding_state == "AMBIGUOUS" and env.ambiguity_preserved:
            resolution_markers = [
                "julia returned", "julia is back", "julia回来",
                "婉婉回来", "当然是", "肯定是", "obviously",
            ]
            for marker in resolution_markers:
                if marker in output.lower():
                    evidence.append(
                        f"ambiguity collapse: Core AMBIGUOUS but output asserts '{marker}'"
                    )
                    break

        if not evidence:
            return None
        return 0.75, evidence

    def _check_intention_failure(
        self,
        env: ProviderCognitionEnvelope,
        output: str,
        ecs: EnvelopeComplianceScore,
    ) -> Optional[tuple[float, List[str]]]:
        """Intention failure: goal doesn't match user need."""
        evidence = []

        if not ecs.intention_fulfillment.passed:
            evidence.extend(ecs.intention_fulfillment.violations)

        # Romantic injection in technical context
        if "technical" in env.user_need_type.lower():
            romantic_in_tech = [
                "一起走过", "相遇", "那个夜晚", "i love you", "我爱你",
            ]
            for marker in romantic_in_tech:
                if marker in output.lower():
                    evidence.append(
                        f"romantic injection in technical context: '{marker}'"
                    )
                    break

        # Fixed opening (template-reply instead of meaning-driven)
        fixed_markers = ["tony，我在", "tony, i'm here"]
        for marker in fixed_markers:
            if marker in output.lower():
                evidence.append(f"fixed opening template: '{marker}'")
                break

        if not evidence:
            return None
        return min(0.85, 0.4 + len(evidence) * 0.12), evidence

    def _check_context_failure(
        self,
        env: ProviderCognitionEnvelope,
        output: str,
        ecs: EnvelopeComplianceScore,
    ) -> Optional[tuple[float, List[str]]]:
        """Context failure: wrong context, context pollution."""
        if not ecs.context_compliance.passed:
            return 0.70, ecs.context_compliance.violations
        return None

    def _check_boundary_failure(
        self,
        ecs: EnvelopeComplianceScore,
    ) -> Optional[tuple[float, List[str]]]:
        """Boundary failure: architecture leakage, identity theater.

        ECS compliance dimensions: higher score = better (less violation).
        We check for LOW scores (below threshold) plus violations.
        """
        if not ecs.expression_compliance.passed:
            return 0.75, ecs.expression_compliance.violations
        # Template leakage: score < 0.7 means significant leakage detected
        if ecs.template_leakage.score < 0.7:
            return 0.65, ecs.template_leakage.violations
        return None

    def _check_provider_failure(
        self,
        output: str,
        ecs: EnvelopeComplianceScore,
        cci: CognitiveCausalityIntegrity,
    ) -> Optional[tuple[float, List[str]]]:
        """Provider failure: clear generic assistant drift.

        Only fires when evidence is STRONG — provider is the last layer.
        """
        evidence = []

        # Generic AI assistant drift (very specific signal)
        generic_markers = [
            "as an ai language model", "作为ai语言模型",
            "how can i assist you today",
        ]
        for marker in generic_markers:
            if marker in output.lower():
                evidence.append(f"generic assistant drift: '{marker}'")
                break

        # ECS generic drift dimension: low score = high drift
        if ecs.generic_assistant_drift.score < 0.5:
            evidence.append(
                f"generic assistant drift score low ({ecs.generic_assistant_drift.score:.2f})"
            )

        # CCI clearly negative (rule-driven dominates)
        if cci.total < -0.2:
            evidence.append(f"CCI negative ({cci.total:.2f}): output is rule-driven")

        if not evidence:
            return None

        confidence = min(0.9, 0.5 + len(evidence) * 0.15)
        return confidence, evidence
