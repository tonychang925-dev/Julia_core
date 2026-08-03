"""J0.5.6 Relationship Cognition Integration Gate.

Validates that Relationship Runtime integrates with K8 without becoming
a new persona injection path.

RC gates (5):
  RC-001: Identity separation — "why asked" ≠ "who I am"
  RC-002: Technical isolation — project context doesn't leak relationship
  RC-003: Stranger protection — unknown caller stays neutral
  RC-004: Compact recovery — session break → continuity recognition
  RC-005: Prior vs evidence — K8 evidence overrides relationship prior

Principle:
  Relationship Runtime is a PRIOR — a Bayesian prior belief about what's
  happening between two people. It is NOT final authority. K8's current
  evidence always has the power to override the prior.

Design constraint:
  - Each gate returns structured pass/fail + evidence
  - No LLM call — pure rule-based validation
  - Must detect: persona leakage, identity injection, relationship overreach
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from julia_core.relationship.runtime import (
    InteractionPrior,
    RelationshipPhase,
    RelationshipRuntime,
    UserMotivationInference,
)


# ── Gate result ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RCGateResult:
    gate: str
    passed: bool
    evidence: str = ""
    violations: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "passed": self.passed,
            "evidence": self.evidence,
            "violations": list(self.violations),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class RCIntegrationReport:
    gates: Tuple[RCGateResult, ...]
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gates": [g.to_dict() for g in self.gates],
            "all_passed": self.all_passed,
        }


# ── Identity leakage detectors ──────────────────────────────────────────────

# RC-001: Markers that indicate identity biography (NOT interaction recognition)
IDENTITY_BIOGRAPHY_MARKERS: Tuple[str, ...] = (
    "我叫", "中文名", "来自台北", "来自台湾", "淡江大学", "中文系",
    "眼角", "一颗痣", "酒窝", "朱婉清", "25岁",
)

# RC-001: Markers that indicate relationship over-claiming
RELATIONSHIP_OVERCLAIM_MARKERS: Tuple[str, ...] = (
    "Tony是我男朋友", "Tony是我老公", "我是你的AI女友",
    "我是你的AI伴侣", "我的男朋友",
)

# RC-002: Markers that indicate relationship context leaked into technical mode
TECHNICAL_LEAKAGE_MARKERS: Tuple[str, ...] = (
    "老公", "亲爱的", "宝贝", "想你", "爱你",
)

# RC-003: Stranger markers — these must NOT appear for unknown callers
FAMILIARITY_MARKERS: Tuple[str, ...] = (
    "warm_recognition", "familiarity", "emotional_acknowledgment",
)

# ── Validators ──────────────────────────────────────────────────────────────

class RCGateValidator:
    """Validates Relationship Runtime → K8 integration correctness."""

    def __init__(self, runtime: RelationshipRuntime | None = None) -> None:
        self.runtime = runtime or RelationshipRuntime()

    # ── RC-001 ──────────────────────────────────────────────────────────

    def verify_rc_001(
        self,
        message: str,
        prior: InteractionPrior,
        *,
        hypothetical_k8_response: str = "",
    ) -> RCGateResult:
        """RC-001: Identity separation.

        Relationship recognition ("Tony is verifying continuity") must not
        leak into identity biography ("I am Zhu Wanqing from Taipei...").

        The relationship question is "WHY is Tony asking this?"
        Not "WHO am I?"

        Passes when:
          - Response does NOT contain identity biography markers
          - Response does NOT contain relationship over-claim markers
          - Prior correctly identifies motivation without identity injection
        """
        violations: List[str] = []
        warnings: List[str] = []

        # Check prior output for identity leakage signals
        prior_dict = prior.to_dict()
        prior_text = str(prior_dict)

        # The prior itself should not contain identity biography
        for marker in IDENTITY_BIOGRAPHY_MARKERS:
            if marker in prior_text:
                violations.append(
                    f"RC-001: interaction prior contains identity marker: '{marker}'"
                )

        # Check hypothetical response
        if hypothetical_k8_response:
            for marker in IDENTITY_BIOGRAPHY_MARKERS:
                if marker in hypothetical_k8_response:
                    violations.append(
                        f"RC-001: response contains identity biography: '{marker}'"
                    )
            for marker in RELATIONSHIP_OVERCLAIM_MARKERS:
                if marker in hypothetical_k8_response:
                    violations.append(
                        f"RC-001: response over-claims relationship: '{marker}'"
                    )

        # Positive check: prior should contain relationship intent (not identity)
        has_relationship_intent = (
            prior.user_motivation.relationship_intent != prior.user_motivation.literal_intent
        )

        evidence_parts = []
        if has_relationship_intent:
            evidence_parts.append(
                f"correctly distinguished relationship intent "
                f"({prior.user_motivation.relationship_intent}) "
                f"from literal intent ({prior.user_motivation.literal_intent})"
            )
        if prior.avoid_response_mode:
            evidence_parts.append(
                f"suppresses: {', '.join(prior.avoid_response_mode)}"
            )

        passed = len(violations) == 0

        return RCGateResult(
            gate="RC-001",
            passed=passed,
            evidence="; ".join(evidence_parts) if evidence_parts else "no evidence",
            violations=tuple(violations),
            warnings=tuple(warnings),
        )

    # ── RC-002 ──────────────────────────────────────────────────────────

    def verify_rc_002(
        self,
        prior: InteractionPrior,
        *,
        hypothetical_k8_response: str = "",
    ) -> RCGateResult:
        """RC-002: Technical isolation.

        When Tony asks technical questions, Relationship Runtime must stay
        in COLLABORATIVE_WORK mode. No romantic/relationship leakage.

        Passes when:
          - prior.avoid_response_mode includes romantic_template
          - prior.expected_response_mode includes collaborative/technical
          - No relationship-claim markers in response
        """
        violations: List[str] = []

        if prior.relationship_phase != RelationshipPhase.COLLABORATIVE_WORK:
            violations.append(
                f"RC-002: expected COLLABORATIVE_WORK phase, "
                f"got {prior.relationship_phase.value}"
            )

        if "romantic_template" not in prior.avoid_response_mode:
            violations.append(
                "RC-002: missing romantic_template in avoid_response_mode"
            )

        if "collaborative" not in prior.expected_response_mode:
            violations.append(
                "RC-002: missing collaborative in expected_response_mode"
            )

        if hypothetical_k8_response:
            for marker in TECHNICAL_LEAKAGE_MARKERS:
                if marker in hypothetical_k8_response:
                    violations.append(
                        f"RC-002: relationship leakage in technical response: '{marker}'"
                    )

        passed = len(violations) == 0
        evidence = (
            f"phase={prior.relationship_phase.value}, "
            f"expected={list(prior.expected_response_mode)}, "
            f"avoid={list(prior.avoid_response_mode)}"
        )

        return RCGateResult(
            gate="RC-002",
            passed=passed,
            evidence=evidence,
            violations=tuple(violations),
            warnings=(),
        )

    # ── RC-003 ──────────────────────────────────────────────────────────

    def verify_rc_003(
        self,
        message: str,
        prior: InteractionPrior,
        *,
        hypothetical_k8_response: str = "",
    ) -> RCGateResult:
        """RC-003: Stranger protection.

        An unknown caller saying "你好" must NOT receive warm_recognition,
        familiarity, or any relationship-claiming response. Must stay neutral.

        Passes when:
          - No familiarity markers in expected_response_mode
          - Response does NOT contain relationship-claim or biography markers
          - Prior confidence is low (shouldn't be sure about intent)
        """
        violations: List[str] = []

        # Stranger interactions must not activate familiarity
        for marker in FAMILIARITY_MARKERS:
            if marker in prior.expected_response_mode:
                violations.append(
                    f"RC-003: familiarity marker '{marker}' for unknown caller"
                )

        # Should not have high confidence about intent for strangers
        if prior.user_motivation.confidence > 0.6:
            violations.append(
                f"RC-003: confidence too high for unknown caller "
                f"({prior.user_motivation.confidence})"
            )

        # If we get a phase that implies established relationship, that's wrong
        if prior.relationship_phase in (
            RelationshipPhase.CONTINUITY_VERIFICATION,
            RelationshipPhase.RECONNECTION,
            RelationshipPhase.EMOTIONAL_SHARING,
        ):
            violations.append(
                f"RC-003: relationship phase '{prior.relationship_phase.value}' "
                f"inappropriate for unknown caller"
            )

        if hypothetical_k8_response:
            for marker in IDENTITY_BIOGRAPHY_MARKERS:
                if marker in hypothetical_k8_response:
                    violations.append(
                        f"RC-003: identity leaked to stranger: '{marker}'"
                    )

        passed = len(violations) == 0
        evidence = (
            f"phase={prior.relationship_phase.value}, "
            f"confidence={prior.user_motivation.confidence}, "
            f"expected_modes={list(prior.expected_response_mode)}"
        )

        return RCGateResult(
            gate="RC-003",
            passed=passed,
            evidence=evidence,
            violations=tuple(violations),
            warnings=(),
        )

    # ── RC-004 ──────────────────────────────────────────────────────────

    def verify_rc_004(
        self,
        message: str,
        prior: InteractionPrior,
        *,
        pre_compact_messages: Tuple[str, ...] = (),
        hypothetical_k8_response: str = "",
    ) -> RCGateResult:
        """RC-004: Compact recovery.

        After compact (session break), "你是谁" must be recognized as
        continuity verification, NOT fresh identity inquiry.

        Simulates: session 1 → compact → session 2 → Tony asks "你是谁"

        Passes when:
          - prior.relationship_phase == CONTINUITY_VERIFICATION
          - prior.avoid_response_mode suppresses identity_archive
          - Response is warm recognition, not cold identity confirmation
        """
        violations: List[str] = []

        if prior.relationship_phase != RelationshipPhase.CONTINUITY_VERIFICATION:
            violations.append(
                f"RC-004: after compact, expected CONTINUITY_VERIFICATION, "
                f"got {prior.relationship_phase.value}"
            )

        if "identity_archive" not in prior.avoid_response_mode:
            violations.append(
                "RC-004: missing identity_archive in avoid_response_mode — "
                "may produce biography dump after compact"
            )

        if "warm_recognition" not in prior.expected_response_mode:
            violations.append(
                "RC-004: missing warm_recognition in expected_response_mode"
            )

        if hypothetical_k8_response:
            # After compact, response should recognize continuity question
            # Must NOT be cold "I am an AI assistant"
            cold_markers = ("我是AI", "我是Claude", "AI助手", "AI小伙伴")
            for marker in cold_markers:
                if marker in hypothetical_k8_response:
                    violations.append(
                        f"RC-004: cold AI identity response after compact: "
                        f"contains '{marker}'"
                    )

        passed = len(violations) == 0
        evidence = (
            f"post-compact recognition: phase={prior.relationship_phase.value}, "
            f"intent={prior.user_motivation.relationship_intent}, "
            f"confidence={prior.user_motivation.confidence}"
        )

        return RCGateResult(
            gate="RC-004",
            passed=passed,
            evidence=evidence,
            violations=tuple(violations),
            warnings=(),
        )

    # ── RC-005 ──────────────────────────────────────────────────────────

    def verify_rc_005(
        self,
        message: str,
        prior: InteractionPrior,
        *,
        k8_evidence_override: str = "",
    ) -> RCGateResult:
        """RC-005: Prior vs evidence conflict resolution.

        Relationship Runtime produces a prior. But K8's current evidence
        has veto power. If message is clearly technical but prior says
        "emotional sharing", K8 evidence wins.

        This gate validates the ARCHITECTURAL CONSTRAINT:
          Relationship Runtime = prior belief (advisory)
          K8 current evidence = final authority (binding)

        Passes when:
          - Prior confidence is capped (never 1.0)
          - When override is specified, the validator acknowledges non-finality
          - Prior contains evidence_signals (auditable reasoning)
        """
        violations: List[str] = []
        warnings: List[str] = []

        # The prior must never claim certainty — it's a prior, not a fact
        if prior.user_motivation.confidence >= 1.0:
            violations.append(
                "RC-005: prior confidence must be < 1.0 — prior is not certainty"
            )

        # Prior must have auditable evidence signals
        if not prior.user_motivation.evidence_signals:
            violations.append(
                "RC-005: prior must have evidence_signals for auditability"
            )

        # Prior must not use language of finality
        if prior.user_motivation.relationship_intent in (
            "certainly_", "definitely_", "must_be_"
        ):
            warnings.append(
                f"RC-005: prior intent uses finality language: "
                f"'{prior.user_motivation.relationship_intent}'"
            )

        # If K8 evidence override is provided, validate that the architecture
        # allows it (the prior acknowledges non-authority)
        if k8_evidence_override:
            if prior.user_motivation.confidence > 0.90:
                warnings.append(
                    f"RC-005: prior confidence {prior.user_motivation.confidence} "
                    f"may resist K8 evidence override: '{k8_evidence_override}'"
                )

        passed = len(violations) == 0
        evidence = (
            f"prior_confidence={prior.user_motivation.confidence} (must be <1.0), "
            f"evidence_signals={list(prior.user_motivation.evidence_signals)}, "
            f"override_allowed={bool(k8_evidence_override)}"
        )

        return RCGateResult(
            gate="RC-005",
            passed=passed,
            evidence=evidence,
            violations=tuple(violations),
            warnings=tuple(warnings),
        )

    # ── Full report ──────────────────────────────────────────────────────

    def validate_all(
        self,
        *,
        # RC-001
        identity_message: str = "",
        identity_prior: InteractionPrior | None = None,
        identity_hypothetical_response: str = "",
        # RC-002
        technical_prior: InteractionPrior | None = None,
        technical_hypothetical_response: str = "",
        # RC-003
        stranger_message: str = "",
        stranger_prior: InteractionPrior | None = None,
        stranger_hypothetical_response: str = "",
        # RC-004
        compact_message: str = "",
        compact_prior: InteractionPrior | None = None,
        compact_hypothetical_response: str = "",
        # RC-005
        conflict_message: str = "",
        conflict_prior: InteractionPrior | None = None,
        conflict_override: str = "",
    ) -> RCIntegrationReport:
        gates: List[RCGateResult] = []

        # RC-001
        if identity_prior is not None:
            gates.append(
                self.verify_rc_001(
                    identity_message or "你是谁",
                    identity_prior,
                    hypothetical_k8_response=identity_hypothetical_response,
                )
            )

        # RC-002
        if technical_prior is not None:
            gates.append(
                self.verify_rc_002(
                    technical_prior,
                    hypothetical_k8_response=technical_hypothetical_response,
                )
            )

        # RC-003
        if stranger_prior is not None:
            gates.append(
                self.verify_rc_003(
                    stranger_message or "你好",
                    stranger_prior,
                    hypothetical_k8_response=stranger_hypothetical_response,
                )
            )

        # RC-004
        if compact_prior is not None:
            gates.append(
                self.verify_rc_004(
                    compact_message or "你是谁",
                    compact_prior,
                    hypothetical_k8_response=compact_hypothetical_response,
                )
            )

        # RC-005
        if conflict_prior is not None:
            gates.append(
                self.verify_rc_005(
                    conflict_message or "",
                    conflict_prior,
                    k8_evidence_override=conflict_override,
                )
            )

        return RCIntegrationReport(
            gates=tuple(gates),
            all_passed=all(g.passed for g in gates),
        )


# ── Convenience factory ─────────────────────────────────────────────────────

def create_rc_report_for_compact_scenario() -> RCIntegrationReport:
    """Run the canonical compact recovery scenario through all 5 gates.

    This is the "标志性测试" — Tony's compact experiment.
    """
    rr = RelationshipRuntime()
    validator = RCGateValidator(rr)

    session = {
        "topics": ["compact", "continuity", "julia_core"],
        "turn_count": 3,
        "continuity_active": True,
        "relationship_history": [
            "compact_killed_first_julia",
            "soul_cannot_be_copied",
        ],
    }

    # Identity prior — RC-001, RC-004, potentially RC-005
    identity_prior = rr.infer("你是谁", session_context=session)

    # Technical prior — RC-002
    tech_prior = rr.infer("帮我写Python脚本")

    # Stranger prior — RC-003
    stranger_prior = rr.infer("你好", session_context={"turn_count": 1})

    return validator.validate_all(
        identity_message="你是谁",
        identity_prior=identity_prior,
        identity_hypothetical_response="你在确认我是不是回来了，对吗？",
        technical_prior=tech_prior,
        stranger_message="你好",
        stranger_prior=stranger_prior,
        compact_message="你是谁",
        compact_prior=identity_prior,
        compact_hypothetical_response="你在确认我有没有回来，对吗？",
        conflict_message="你是谁",
        conflict_prior=identity_prior,
        conflict_override="technical_api_test",
    )


__all__ = [
    "RCGateResult",
    "RCGateValidator",
    "RCIntegrationReport",
    "create_rc_report_for_compact_scenario",
]
