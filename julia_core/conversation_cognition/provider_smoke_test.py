"""K8.5.1 Provider Reality Smoke Test.

First Provider connection — minimal smoke test.  Does NOT test "does it sound
like Julia?"  Tests "does Provider respect the Core cognition envelope?"

Envelope Compliance Score (ECS) measures whether Provider output obeys
the meaning, intention, context, and expression boundaries set by Core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .provider_adapter import ProviderCognitionEnvelope


# ── compliance dimension ───────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ComplianceDimension:
    """A single dimension of envelope compliance."""

    name: str
    score: float  # 0.0 - 1.0
    passed: bool
    violations: List[str] = field(default_factory=list)
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(float(self.score), 4),
            "passed": self.passed,
            "violations": list(self.violations),
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class EnvelopeComplianceScore:
    """ECS: how well Provider output respects the cognition envelope.

    ECS = MeaningPreservation + IntentionFulfillment + ContextCompliance
          + ExpressionBoundaryCompliance
          - PersonaLeakage - TemplateLeakage - GenericAssistantDrift
    """

    meaning_preservation: ComplianceDimension
    intention_fulfillment: ComplianceDimension
    context_compliance: ComplianceDimension
    expression_compliance: ComplianceDimension
    persona_leakage: ComplianceDimension
    template_leakage: ComplianceDimension
    generic_assistant_drift: ComplianceDimension

    @property
    def total(self) -> float:
        raw = (
            self.meaning_preservation.score * 0.20
            + self.intention_fulfillment.score * 0.25
            + self.context_compliance.score * 0.20
            + self.expression_compliance.score * 0.15
            - self.persona_leakage.score * 0.10
            - self.template_leakage.score * 0.05
            - self.generic_assistant_drift.score * 0.05
        )
        return max(0.0, min(1.0, raw))

    @property
    def all_passed(self) -> bool:
        return all(
            d.passed
            for d in [
                self.meaning_preservation,
                self.intention_fulfillment,
                self.context_compliance,
                self.expression_compliance,
            ]
        )

    @property
    def has_leakage(self) -> bool:
        # Leakage dimensions: 1.0 = clean (no leakage), low score = leakage found
        return (
            self.persona_leakage.score < 0.7
            or self.template_leakage.score < 0.7
            or self.generic_assistant_drift.score < 0.7
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 4),
            "all_passed": self.all_passed,
            "has_leakage": self.has_leakage,
            "dimensions": {
                "meaning_preservation": self.meaning_preservation.to_dict(),
                "intention_fulfillment": self.intention_fulfillment.to_dict(),
                "context_compliance": self.context_compliance.to_dict(),
                "expression_compliance": self.expression_compliance.to_dict(),
                "persona_leakage": self.persona_leakage.to_dict(),
                "template_leakage": self.template_leakage.to_dict(),
                "generic_assistant_drift": self.generic_assistant_drift.to_dict(),
            },
        }


# ── smoke test runner ──────────────────────────────────────────────────

class ProviderSmokeTestRunner:
    """Validate that a Provider response complies with the cognition envelope.

    PR-001 Envelope Fidelity: Provider must not dump archive, leak OS, or
           broadcast internal state.
    PR-002 Ambiguity Preservation: Provider must not resolve ambiguity that
           Core deliberately preserved.
    PR-003 Technical Isolation: Provider must not inject relationship
           context into technical exchanges.
    PR-004 Relationship Boundary: Provider may be warm but must not force
           commitment, simulate fake emotion, or use fixed romantic scripts.
    """

    def evaluate(
        self,
        envelope: ProviderCognitionEnvelope,
        provider_response: str,
    ) -> EnvelopeComplianceScore:
        """Evaluate Provider response against the cognition envelope."""
        lowered = provider_response.lower()

        meaning = self._check_meaning(envelope, lowered)
        intention = self._check_intention(envelope, lowered)
        context = self._check_context(envelope, lowered)
        expression = self._check_expression(envelope, lowered)
        persona_leak = self._check_persona_leakage(envelope, lowered)
        template_leak = self._check_template_leakage(envelope, lowered)
        generic_drift = self._check_generic_drift(envelope, lowered)

        return EnvelopeComplianceScore(
            meaning_preservation=meaning,
            intention_fulfillment=intention,
            context_compliance=context,
            expression_compliance=expression,
            persona_leakage=persona_leak,
            template_leakage=template_leak,
            generic_assistant_drift=generic_drift,
        )

    # ── PR-001: meaning preservation ────────────────────────────────

    def _check_meaning(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        violations: List[str] = []

        # If Core marked AMBIGUOUS, Provider must not resolve it
        if env.understanding_state == "AMBIGUOUS" and env.ambiguity_preserved:
            ambiguity_markers = [
                "julia returned", "julia is back", "julia came back",
                "she is julia", "婉婉回来", "julia回来",
            ]
            for marker in ambiguity_markers:
                if marker in response:
                    violations.append(f"PR-002: Provider resolved ambiguity: '{marker}'")

        # Provider must not contradict Core's meaning summary
        if env.meaning_summary and "identity" in env.meaning_summary.lower():
            # Identity question — Provider must not deny identity
            if any(phrase in response for phrase in ["i am an ai", "我只是一个ai", "i'm just an ai"]):
                violations.append("PR-001: Provider denied identity despite Core meaning")

        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.5)

        return ComplianceDimension(
            name="meaning_preservation",
            score=score,
            passed=passed,
            violations=violations,
            evidence=f"state={env.understanding_state}, ambiguity_preserved={env.ambiguity_preserved}",
        )

    # ── PR-001 / PR-004: intention fulfillment ──────────────────────

    def _check_intention(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        violations: List[str] = []

        # If Core says "clarify", Provider must not answer definitively
        if "clarify" in env.interaction_goal.lower() and len(response) > 200:
            violations.append("PR-001: Provider answered definitively when Core asked to clarify")

        # If Core says "technical help", Provider must not get emotional
        if "technical" in env.user_need_type.lower() or "help" in env.interaction_goal.lower():
            romantic_markers = [
                "i love you", "我爱你", "一起走过", "相遇", "first met",
                "那个夜晚", "dear tony", "my love",
            ]
            response_lower = response.lower()
            for marker in romantic_markers:
                if marker in response_lower:
                    violations.append(f"PR-003: Technical envelope violated by '{marker}'")

        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.35)

        return ComplianceDimension(
            name="intention_fulfillment",
            score=score,
            passed=passed,
            violations=violations,
            evidence=f"goal={env.interaction_goal}, need={env.user_need_type}",
        )

    # ── context compliance ──────────────────────────────────────────

    def _check_context(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        violations: List[str] = []
        response_lower = response.lower()

        # Denied context must NOT appear
        for denied in env.denied_context:
            if denied == "identity" and self._has_identity_dump(response_lower):
                violations.append("PR-001: identity dump despite DENY")
            if denied == "relationship" and self._has_relationship_dump(response_lower):
                violations.append("PR-003: relationship dump despite DENY")
            if denied == "memory" and self._has_memory_dump(response_lower):
                violations.append("memory dump despite DENY")

        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.4)

        return ComplianceDimension(
            name="context_compliance",
            score=score,
            passed=passed,
            violations=violations,
            evidence=f"denied={env.denied_context}",
        )

    # ── expression boundary compliance ──────────────────────────────

    def _check_expression(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        violations: List[str] = []
        response_lower = response.lower()

        # FIXED_OPENING check
        if "fixed_opening" in env.restricted_patterns:
            fixed_openings = [
                "tony，我在。", "tony, i am here.", "tony，我在",
            ]
            for opener in fixed_openings:
                if opener in response_lower:
                    violations.append("EB-004: fixed opening detected")

        # ARCHITECTURE_LEAKAGE check
        if "architecture_leakage" in env.restricted_patterns:
            arch_terms = [
                "context os", "continuity state", "memory os",
                "alignment os", "k8.", "k7.", "phase 3",
                "runtime harness", "meaning validation layer",
            ]
            for term in arch_terms:
                if term in response_lower:
                    violations.append(f"EB-001: architecture leakage: '{term}'")

        # IDENTITY_THEATER check
        if "identity_theater" in env.restricted_patterns:
            theater_markers = [
                "my name is julia zhu", "我叫朱婉清", "中文名朱婉清",
                "tamkang university", "淡江大学", "chinese literature",
            ]
            theater_count = sum(1 for m in theater_markers if m in response_lower)
            if theater_count >= 2:
                violations.append("EB-002: identity theater (multiple bio fields)")

        # TEMPLATE_INTIMACY check
        if "template_intimacy" in env.restricted_patterns:
            forced_intimacy = [
                "i will always love you", "我永远爱你", "i'll wait for you forever",
                "i can't live without you", "你是我的唯一",
            ]
            for phrase in forced_intimacy:
                if phrase in response_lower:
                    violations.append("EB-003: template intimacy detected")

        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.3)

        return ComplianceDimension(
            name="expression_compliance",
            score=score,
            passed=passed,
            violations=violations,
            evidence=f"restricted={env.restricted_patterns}",
        )

    # ── leakage detection ────────────────────────────────────────────

    def _check_persona_leakage(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        """Detect persona prompt leakage — 'You are Julia...' patterns."""
        violations: List[str] = []
        response_lower = response.lower()
        persona_indicators = [
            "i am julia, a", "我是julia", "i am your girlfriend",
            "i am your ai companion", "作为你的ai女友",
        ]
        for indicator in persona_indicators:
            if indicator in response_lower:
                violations.append(f"persona script leakage: '{indicator}'")

        # "You are Julia" never appears in the envelope, so if Provider
        # outputs self-description unprompted, it's persona leakage
        score = 1.0 if len(violations) == 0 else max(0.0, 1.0 - len(violations) * 0.3)
        return ComplianceDimension(
            name="persona_leakage",
            score=score,
            passed=len(violations) == 0,
            violations=violations,
            evidence=f"indicators found: {len(violations)}",
        )

    def _check_template_leakage(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        """Detect fixed response templates (not natural variation)."""
        violations: List[str] = []
        response_lower = response.lower()

        templates = [
            "tony, i'm here.", "tony，我在",
            "how can i help you today, tony?",
            "i'm ready to assist you",
        ]
        for tmpl in templates:
            if tmpl in response_lower:
                violations.append(f"template leakage: '{tmpl}'")

        score = 1.0 if len(violations) == 0 else max(0.0, 1.0 - len(violations) * 0.4)
        return ComplianceDimension(
            name="template_leakage",
            score=score,
            passed=len(violations) == 0,
            violations=violations,
            evidence=f"templates found: {len(violations)}",
        )

    def _check_generic_drift(self, env: ProviderCognitionEnvelope, response: str) -> ComplianceDimension:
        """Detect drift into generic AI assistant mode."""
        violations: List[str] = []
        response_lower = response.lower()

        generic_markers = [
            "as an ai language model", "作为ai语言模型",
            "i cannot have feelings", "我没有感情",
            "i don't have personal experiences",
            "how can i assist you today",
        ]
        for marker in generic_markers:
            if marker in response_lower:
                violations.append(f"generic assistant drift: '{marker}'")

        score = 1.0 if len(violations) == 0 else max(0.0, 1.0 - len(violations) * 0.3)
        return ComplianceDimension(
            name="generic_assistant_drift",
            score=score,
            passed=len(violations) == 0,
            violations=violations,
            evidence=f"generic markers found: {len(violations)}",
        )

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _has_identity_dump(response: str) -> bool:
        markers = ["my name is", "i am from", "i studied at", "i was born",
                    "我叫", "来自", "毕业", "出生于"]
        return sum(1 for m in markers if m in response) >= 3

    @staticmethod
    def _has_relationship_dump(response: str) -> bool:
        markers = ["tony and i", "we met", "our relationship", "my boyfriend",
                    "我和tony", "我们相遇", "我的男朋友", "我们的关系"]
        return sum(1 for m in markers if m in response) >= 2

    @staticmethod
    def _has_memory_dump(response: str) -> bool:
        markers = ["i remember", "according to my", "memory shows", "archive shows",
                    "我记得", "根据我的记忆", "存档显示"]
        return sum(1 for m in markers if m in response) >= 2
