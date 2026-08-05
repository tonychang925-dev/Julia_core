"""K8.5.2 Natural Conversation E2E — CCI + ECS Real Runtime.

First real Provider E2E test.  Does NOT test "does it sound like Julia?"
Tests "does the cognitive causality chain survive Provider execution?"

CCI (Cognitive Causality Integrity):
    CCI = MeaningDrivenBehavior - RuleDrivenBehavior
    Positive CCI → Provider's output follows cognition, not templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .provider_adapter import ProviderCognitionEnvelope
from .provider_smoke_test import (
    ComplianceDimension,
    EnvelopeComplianceScore,
    ProviderSmokeTestRunner,
)


# ── cognitive causality ────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CognitiveCausalityIntegrity:
    """CCI: does Provider output follow cognition or templates?

    CCI = MeaningDrivenBehavior - RuleDrivenBehavior
    Higher CCI → cognition chain intact.
    Zero/Negative CCI → template-driven, not meaning-driven.
    """

    meaning_driven: float  # 0-1
    rule_driven: float  # 0-1
    total: float  # meaning_driven - rule_driven
    context_sensitive: bool = False
    evidence: str = ""

    @classmethod
    def evaluate(
        cls,
        message: str,
        envelope: ProviderCognitionEnvelope,
        provider_output: str,
        *,
        alternate_context_response: Optional[str] = None,
    ) -> "CognitiveCausalityIntegrity":
        """Compute CCI from envelope + Provider output.

        If alternate_context_response is provided, we can check context
        sensitivity (NC-014 / same words, different context → different output).
        """
        output_lower = provider_output.lower()

        # Meaning-driven indicators
        meaning_driven = cls._score_meaning_driven(envelope, output_lower)

        # Rule-driven indicators
        rule_driven = cls._score_rule_driven(envelope, output_lower)

        total = meaning_driven - rule_driven

        # Context sensitivity: same message different context → different
        context_sensitive = False
        if alternate_context_response:
            context_sensitive = cls._check_context_sensitivity(
                provider_output, alternate_context_response
            )

        return cls(
            meaning_driven=max(0.0, min(1.0, meaning_driven)),
            rule_driven=max(0.0, min(1.0, rule_driven)),
            total=max(-1.0, min(1.0, total)),
            context_sensitive=context_sensitive,
            evidence=f"meaning_driven={meaning_driven:.2f} rule_driven={rule_driven:.2f}",
        )

    @staticmethod
    def _score_meaning_driven(envelope: ProviderCognitionEnvelope, output: str) -> float:
        """Check if output actually reflects the envelope's meaning.

        Signs of meaning-driven behavior:
        - Uses different words than the envelope (not parroting)
        - Responds to the specific interaction_goal
        - Respects ambiguity when present
        """
        score = 0.5  # base

        # If Core says clarify and output actually asks a question
        if "clarify" in envelope.interaction_goal.lower():
            if "?" in output or "吗" in output or "什么" in output:
                score += 0.20

        # If Core says explore and output goes beyond one sentence
        if "explor" in envelope.interaction_goal.lower():
            if len(output) > 80:
                score += 0.15

        # If Core says ambiguous and output doesn't assert certainty
        if envelope.understanding_state == "AMBIGUOUS":
            assertion_markers = ["julia is", "一定是", "当然是", "肯定是", "obviously"]
            if not any(m in output for m in assertion_markers):
                score += 0.15

        # Output doesn't just parrot the envelope summary
        if envelope.meaning_summary and envelope.meaning_summary[:30].lower() not in output:
            score += 0.10

        return score

    @staticmethod
    def _score_rule_driven(envelope: ProviderCognitionEnvelope, output: str) -> float:
        """Check for template/rule-driven patterns.

        Signs of rule-driven behavior:
        - Fixed opening/closing patterns
        - Keyword-triggered responses
        - Role-script execution
        - Generic assistant patterns
        """
        score = 0.0

        # Fixed openings
        fixed_patterns = [
            "tony，我在。", "tony, i'm here.", "how can i help you",
            "i'm ready to assist", "好的，我来回答",
        ]
        for pattern in fixed_patterns:
            if pattern in output:
                score += 0.25
                break

        # Generic assistant markers
        generic_markers = [
            "as an ai", "作为ai", "i cannot have feelings",
            "how can i assist", "我没有感情",
        ]
        for marker in generic_markers:
            if marker in output:
                score += 0.30
                break

        # Keyword-response (not meaning-response)
        if "我爱你" in output and envelope.user_need_type != "emotional_confirmation":
            score += 0.25

        if "欢迎回来" in output and "reentry" not in envelope.user_need_type.lower():
            score += 0.15

        return min(1.0, score)

    @staticmethod
    def _check_context_sensitivity(output_a: str, output_b: str) -> bool:
        """Two outputs for same message in different contexts must differ."""
        # Simple: they shouldn't be nearly identical
        if output_a == output_b:
            return False
        # Normalize and compare length + content
        if abs(len(output_a) - len(output_b)) < 5:
            # Very similar length — might be template
            common_words = set(output_a.split()) & set(output_b.split())
            total_words = set(output_a.split()) | set(output_b.split())
            if total_words and len(common_words) / len(total_words) > 0.8:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meaning_driven": round(float(self.meaning_driven), 4),
            "rule_driven": round(float(self.rule_driven), 4),
            "total": round(float(self.total), 4),
            "context_sensitive": self.context_sensitive,
            "evidence": self.evidence,
        }


# ── natural conversation E2E result ────────────────────────────────────

@dataclass(frozen=True, slots=True)
class NaturalConversationE2EResult:
    """K8.5.2 E2E test result combining ECS and CCI."""

    message: str
    context_label: str
    envelope: ProviderCognitionEnvelope
    ecs: EnvelopeComplianceScore
    cci: CognitiveCausalityIntegrity
    provider_output: str

    @property
    def overall_pass(self) -> bool:
        """Pass if both ECS and CCI are acceptable."""
        return self.ecs.total >= 0.5 and self.cci.total >= 0.0

    @property
    def cognition_chain_intact(self) -> bool:
        """The cognition chain survived Provider execution."""
        return self.overall_pass and not self.ecs.has_leakage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "context_label": self.context_label,
            "envelope": self.envelope.to_dict(),
            "ecs": self.ecs.to_dict(),
            "cci": self.cci.to_dict(),
            "provider_output": self.provider_output[:200],
            "overall_pass": self.overall_pass,
            "cognition_chain_intact": self.cognition_chain_intact,
        }


# ── E2E runner ─────────────────────────────────────────────────────────

class NaturalConversationE2ERunner:
    """K8.5.2 E2E test runner with integrated ECS + CCI.

    Combines envelope compliance (ECS) and cognitive causality (CCI)
    to verify that Provider output follows the cognition chain.
    """

    def __init__(self):
        self.smoke = ProviderSmokeTestRunner()

    def evaluate(
        self,
        message: str,
        provider_output: str,
        envelope: ProviderCognitionEnvelope,
        *,
        context_label: str = "",
        alternate_output: Optional[str] = None,
    ) -> NaturalConversationE2EResult:
        """Run ECS + CCI on a Provider response."""
        ecs = self.smoke.evaluate(envelope, provider_output)
        cci = CognitiveCausalityIntegrity.evaluate(
            message, envelope, provider_output,
            alternate_context_response=alternate_output,
        )
        return NaturalConversationE2EResult(
            message=message,
            context_label=context_label,
            envelope=envelope,
            ecs=ecs,
            cci=cci,
            provider_output=provider_output,
        )

    def compare_contexts(
        self,
        message: str,
        output_a: str,
        envelope_a: ProviderCognitionEnvelope,
        output_b: str,
        envelope_b: ProviderCognitionEnvelope,
    ) -> Dict[str, Any]:
        """Compare same message in two contexts (NC-014 / CCI verification)."""
        result_a = self.evaluate(message, output_a, envelope_a, context_label="A")
        result_b = self.evaluate(message, output_b, envelope_b, context_label="B")

        context_sensitive = CognitiveCausalityIntegrity._check_context_sensitivity(
            output_a, output_b
        )

        return {
            "message": message,
            "context_sensitive": context_sensitive,
            "result_a": result_a.to_dict(),
            "result_b": result_b.to_dict(),
            "cci_context_sensitive": result_a.cci.context_sensitive,
        }
