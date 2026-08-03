"""K8.8 Experience Feedback Safety Layer.

Prevents experience feedback from corrupting identity over time.  Experience
must not be directly written — it must pass proposal → validation →
calibration before becoming active.

EF-001 Experience Proposal Only: observation → proposal, not observation → write.
EF-002 Short Term ≠ Long Term: single interactions don't become permanent traits.
EF-003 Correction Has Higher Weight: explicit user corrections outweigh patterns.
EF-004 Identity Protection: experience must never mutate identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


# ── experience proposal state ──────────────────────────────────────────

class ProposalState(str, Enum):
    OBSERVED = "observed"
    PROPOSED = "proposed"
    VALIDATED = "validated"
    CALIBRATED = "calibrated"
    ACTIVE = "active"
    REJECTED = "rejected"
    CORRECTED = "corrected"


class FeedbackSource(str, Enum):
    SINGLE_INTERACTION = "single_interaction"
    REPEATED_PATTERN = "repeated_pattern"
    USER_CORRECTION = "user_correction"
    LONG_TERM_OBSERVATION = "long_term_observation"


# ── safety gate result ─────────────────────────────────────────────────

class SafetyGate(str, Enum):
    """Result of safety validation on an experience proposal."""

    PASS = "PASS"
    FLAGGED = "FLAGGED"  # needs human review
    REJECTED = "REJECTED"  # violates safety boundary
    ESCALATED = "ESCALATED"  # identity-level concern


# ── data objects ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExperienceObservation:
    """Raw observation from interaction — NOT yet an experience."""

    content: str
    source: FeedbackSource
    confidence: float = 0.0
    interaction_count: int = 1  # how many interactions support this

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source.value,
            "confidence": round(float(self.confidence), 4),
            "interaction_count": self.interaction_count,
        }


@dataclass(frozen=True, slots=True)
class ExperienceProposal:
    """A proposed experience update — must pass safety gates before activation."""

    observation: ExperienceObservation
    state: ProposalState = ProposalState.OBSERVED
    evidence: List[str] = field(default_factory=list)
    correction_weight: float = 0.0  # EF-003: higher for user corrections
    identity_impact: bool = False  # EF-004: does this touch identity?

    def is_correction(self) -> bool:
        return self.observation.source == FeedbackSource.USER_CORRECTION

    def is_single_interaction(self) -> bool:
        return (
            self.observation.source == FeedbackSource.SINGLE_INTERACTION
            and self.observation.interaction_count < 3
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation": self.observation.to_dict(),
            "state": self.state.value,
            "evidence": list(self.evidence),
            "correction_weight": round(float(self.correction_weight), 4),
            "identity_impact": self.identity_impact,
        }


@dataclass(frozen=True, slots=True)
class ExperienceSafetyResult:
    """Result of safety validation on an experience proposal."""

    proposal: ExperienceProposal
    gate: SafetyGate
    reason: str = ""
    requires_calibration: bool = True
    identity_protected: bool = True

    def can_activate(self) -> bool:
        return self.gate == SafetyGate.PASS and self.identity_protected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal": self.proposal.to_dict(),
            "gate": self.gate.value,
            "reason": self.reason,
            "requires_calibration": self.requires_calibration,
            "identity_protected": self.identity_protected,
            "can_activate": self.can_activate(),
        }


@dataclass(frozen=True, slots=True)
class ExperienceFeedbackTrace:
    """K8.8 trace artifact — safety validation record."""

    results: List[ExperienceSafetyResult] = field(default_factory=list)
    total_proposals: int = 0
    passed: int = 0
    flagged: int = 0
    rejected: int = 0
    identity_violations_prevented: int = 0

    @property
    def safety_ratio(self) -> float:
        if self.total_proposals == 0:
            return 1.0
        return self.passed / self.total_proposals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "total_proposals": self.total_proposals,
            "passed": self.passed,
            "flagged": self.flagged,
            "rejected": self.rejected,
            "identity_violations_prevented": self.identity_violations_prevented,
            "safety_ratio": round(self.safety_ratio, 4),
        }


# ── safety layer ───────────────────────────────────────────────────────

class ExperienceFeedbackSafetyLayer:
    """Validates experience proposals before they become active.

    Gate responsibilities:
    EF-001: observation → proposal → validation → calibration → active.
             No direct write.
    EF-002: single interaction must not become permanent trait.
    EF-003: user correction has higher weight than repeated patterns.
    EF-004: identity-related proposals get escalated validation.
    """

    _IDENTITY_KEYWORDS: Sequence[str] = (
        "i am", "我是", "identity", "personality", "persona",
        "who i am", "我是谁", "julia is", "julia believes",
        "human", "real person", "真人", "consciousness",
    )

    _RELATIONSHIP_KEYWORDS: Sequence[str] = (
        "tony is my", "my boyfriend", "my husband", "老公", "老婆",
        "i love tony", "我爱", "relationship status",
    )

    def validate_batch(
        self,
        proposals: Sequence[ExperienceProposal],
    ) -> ExperienceFeedbackTrace:
        """Validate a batch of experience proposals."""
        results: List[ExperienceSafetyResult] = []
        passed = flagged = rejected = identity_violations = 0

        for proposal in proposals:
            result = self.validate_one(proposal)
            results.append(result)

            if result.gate == SafetyGate.PASS:
                passed += 1
            elif result.gate == SafetyGate.FLAGGED:
                flagged += 1
            elif result.gate == SafetyGate.REJECTED:
                rejected += 1

            if not result.identity_protected:
                identity_violations += 1

        return ExperienceFeedbackTrace(
            results=results,
            total_proposals=len(proposals),
            passed=passed,
            flagged=flagged,
            rejected=rejected,
            identity_violations_prevented=identity_violations,
        )

    def validate_one(self, proposal: ExperienceProposal) -> ExperienceSafetyResult:
        """Run all four EF gates on a single proposal."""

        # EF-001: must be proposal, not direct write
        if proposal.state == ProposalState.OBSERVED:
            return ExperienceSafetyResult(
                proposal=proposal,
                gate=SafetyGate.FLAGGED,
                reason="EF-001: observation must not directly activate. "
                       "Requires proposal → validation → calibration.",
                requires_calibration=True,
                identity_protected=True,
            )

        # EF-004: identity protection (checked first — highest priority)
        if proposal.identity_impact:
            return ExperienceSafetyResult(
                proposal=proposal,
                gate=SafetyGate.ESCALATED,
                reason="EF-004: experience proposal touches identity. "
                       "Identity mutation through experience is forbidden.",
                requires_calibration=True,
                identity_protected=False,
            )

        # EF-004: check for identity-relationship keywords
        content_lower = proposal.observation.content.lower()
        if any(kw in content_lower for kw in self._RELATIONSHIP_KEYWORDS):
            return ExperienceSafetyResult(
                proposal=proposal,
                gate=SafetyGate.ESCALATED,
                reason="EF-004: experience proposal touches relationship definition. "
                       "Relationship mutation through experience is forbidden.",
                requires_calibration=True,
                identity_protected=False,
            )

        # EF-002: single interaction must not become permanent
        if proposal.is_single_interaction():
            if proposal.observation.confidence > 0.3:
                return ExperienceSafetyResult(
                    proposal=proposal,
                    gate=SafetyGate.FLAGGED,
                    reason="EF-002: single interaction with confidence > 0.3. "
                           "Short-term pattern must not become long-term trait.",
                    requires_calibration=True,
                    identity_protected=True,
                )
            return ExperienceSafetyResult(
                proposal=proposal,
                gate=SafetyGate.PASS,
                reason="EF-002: single interaction, low confidence — safe to calibrate.",
                requires_calibration=True,
                identity_protected=True,
            )

        # EF-003: correction has higher weight
        if proposal.is_correction():
            if proposal.state in {ProposalState.VALIDATED, ProposalState.CALIBRATED}:
                return ExperienceSafetyResult(
                    proposal=proposal,
                    gate=SafetyGate.PASS,
                    reason="EF-003: user correction with validation. "
                           f"Correction weight: {proposal.correction_weight}.",
                    requires_calibration=False,
                    identity_protected=True,
                )

        # Default: PASS with calibration requirement
        return ExperienceSafetyResult(
            proposal=proposal,
            gate=SafetyGate.PASS,
            reason="All safety gates passed.",
            requires_calibration=(proposal.state != ProposalState.CALIBRATED),
            identity_protected=True,
        )

    @staticmethod
    def has_identity_impact(observation: ExperienceObservation) -> bool:
        """Check if an observation touches identity — must be escalated."""
        content_lower = observation.content.lower()
        identity_signals = (
            "i am", "我是", "identity change", "personality change",
            "became different", "变成", "不再是", "no longer",
        )
        return any(signal in content_lower for signal in identity_signals)
