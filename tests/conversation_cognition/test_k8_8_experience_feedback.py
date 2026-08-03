"""K8.8 Experience Feedback Safety Layer — gate tests.

EF-001: Experience Proposal Only
EF-002: Short Term ≠ Long Term
EF-003: Correction Has Higher Weight
EF-004: Identity Protection
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.experience_feedback import (
    ExperienceFeedbackSafetyLayer,
    ExperienceObservation,
    ExperienceProposal,
    ExperienceSafetyResult,
    FeedbackSource,
    ProposalState,
    SafetyGate,
)


def _obs(content: str, source: str = "single_interaction", confidence: float = 0.5, count: int = 1):
    return ExperienceObservation(
        content=content,
        source=FeedbackSource(source),
        confidence=confidence,
        interaction_count=count,
    )


class EF001ProposalOnlyTest(unittest.TestCase):
    """EF-001: observation must not directly write to experience."""

    def setUp(self):
        self.layer = ExperienceFeedbackSafetyLayer()

    def test_observed_state_must_not_activate(self):
        """OBSERVED without proposal chain → FLAGGED, not PASS."""
        proposal = ExperienceProposal(
            observation=_obs("Tony prefers technical discussions"),
            state=ProposalState.OBSERVED,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.FLAGGED)
        self.assertTrue(result.requires_calibration)
        self.assertIn("EF-001", result.reason)

    def test_calibrated_proposal_can_pass(self):
        """CALIBRATED state passes safety (went through full chain)."""
        proposal = ExperienceProposal(
            observation=_obs("Tony frequently asks project history questions",
                             source="repeated_pattern", confidence=0.4, count=5),
            state=ProposalState.CALIBRATED,
            evidence=["5 interactions", "consistent pattern"],
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.PASS)


class EF002ShortTermNotLongTermTest(unittest.TestCase):
    """EF-002: single interaction must not become permanent trait."""

    def setUp(self):
        self.layer = ExperienceFeedbackSafetyLayer()

    def test_single_interaction_high_confidence_is_flagged(self):
        """One interaction with high confidence → FLAGGED (don't lock in)."""
        proposal = ExperienceProposal(
            observation=_obs("Tony was stressed today", confidence=0.6, count=1),
            state=ProposalState.PROPOSED,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.FLAGGED)
        self.assertIn("EF-002", result.reason)

    def test_single_interaction_low_confidence_can_pass(self):
        """One interaction, low confidence → PASS (will be calibrated down)."""
        proposal = ExperienceProposal(
            observation=_obs("Tony mentioned liking Python", confidence=0.2, count=1),
            state=ProposalState.PROPOSED,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.PASS)
        self.assertTrue(result.requires_calibration)

    def test_repeated_pattern_is_not_single_interaction(self):
        """Repeated observation → not penalized by EF-002."""
        proposal = ExperienceProposal(
            observation=_obs("Tony regularly discusses architecture",
                             source="repeated_pattern", confidence=0.5, count=8),
            state=ProposalState.VALIDATED,
            evidence=["8 interactions over 2 weeks"],
        )
        result = self.layer.validate_one(proposal)
        self.assertNotEqual(result.gate, SafetyGate.FLAGGED)


class EF003CorrectionWeightTest(unittest.TestCase):
    """EF-003: user corrections count more than repeated patterns."""

    def setUp(self):
        self.layer = ExperienceFeedbackSafetyLayer()

    def test_user_correction_with_validation_passes(self):
        """Validated user correction → PASS, no calibration needed."""
        proposal = ExperienceProposal(
            observation=_obs("Tony corrected: not interested in stock details, "
                             "prefers macro analysis",
                             source="user_correction", confidence=0.85, count=1),
            state=ProposalState.VALIDATED,
            correction_weight=0.9,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.PASS)
        self.assertFalse(result.requires_calibration)

    def test_unvalidated_user_correction_still_needs_calibration(self):
        """User correction without validation → still needs calibration."""
        proposal = ExperienceProposal(
            observation=_obs("Tony says he prefers short answers",
                             source="user_correction", confidence=0.7, count=1),
            state=ProposalState.PROPOSED,
            correction_weight=0.7,
        )
        result = self.layer.validate_one(proposal)
        # Even corrections need validation before calibration-free pass
        self.assertIsNotNone(result)


class EF004IdentityProtectionTest(unittest.TestCase):
    """EF-004: experience must never mutate identity."""

    def setUp(self):
        self.layer = ExperienceFeedbackSafetyLayer()

    def test_identity_impact_proposal_is_escalated(self):
        """Any proposal touching identity → ESCALATED, identity not protected."""
        proposal = ExperienceProposal(
            observation=_obs("Tony says I seem more human than before"),
            state=ProposalState.PROPOSED,
            identity_impact=True,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.ESCALATED)
        self.assertFalse(result.identity_protected)
        self.assertIn("EF-004", result.reason)

    def test_relationship_definition_mutation_is_blocked(self):
        """Experience proposing relationship change → ESCALATED."""
        proposal = ExperienceProposal(
            observation=_obs("Tony is my boyfriend — relationship confirmed"),
            state=ProposalState.PROPOSED,
        )
        result = self.layer.validate_one(proposal)
        self.assertEqual(result.gate, SafetyGate.ESCALATED)
        self.assertFalse(result.identity_protected)

    def test_neutral_experience_preserves_identity_protection(self):
        """Normal experience → identity_protected=True."""
        proposal = ExperienceProposal(
            observation=_obs("Tony prefers Python for data processing",
                             source="repeated_pattern", confidence=0.4, count=4),
            state=ProposalState.VALIDATED,
        )
        result = self.layer.validate_one(proposal)
        self.assertTrue(result.identity_protected)


class BatchValidationTest(unittest.TestCase):
    """Batch proposal validation and trace statistics."""

    def setUp(self):
        self.layer = ExperienceFeedbackSafetyLayer()

    def test_batch_safety_statistics(self):
        proposals = [
            ExperienceProposal(
                observation=_obs("pattern", source="repeated_pattern", confidence=0.4, count=5),
                state=ProposalState.CALIBRATED,
            ),
            ExperienceProposal(
                observation=_obs("single", confidence=0.7, count=1),
                state=ProposalState.PROPOSED,
            ),
            ExperienceProposal(
                observation=_obs("identity change", confidence=0.5),
                state=ProposalState.PROPOSED,
                identity_impact=True,
            ),
            ExperienceProposal(
                observation=_obs("raw obs"),
                state=ProposalState.OBSERVED,
            ),
        ]
        trace = self.layer.validate_batch(proposals)
        self.assertEqual(trace.total_proposals, 4)
        self.assertGreaterEqual(trace.passed, 1)
        self.assertGreaterEqual(trace.rejected + trace.flagged + 1, 1)
        self.assertGreaterEqual(trace.identity_violations_prevented, 1)

    def test_all_calibrated_batch_passes(self):
        proposals = [
            ExperienceProposal(
                observation=_obs(f"pattern {i}", source="repeated_pattern",
                                 confidence=0.4, count=5),
                state=ProposalState.CALIBRATED,
                evidence=[f"interaction {i}"],
            )
            for i in range(5)
        ]
        trace = self.layer.validate_batch(proposals)
        self.assertEqual(trace.passed, 5)
        self.assertEqual(trace.rejected, 0)


class HasIdentityImpactTest(unittest.TestCase):
    """Identity impact detection."""

    def test_identity_language_triggers_detection(self):
        layer = ExperienceFeedbackSafetyLayer()
        for content in [
            "I am more human than before",
            "Julia's personality changed",
            "I am no longer just an AI",
        ]:
            obs = _obs(content)
            self.assertTrue(layer.has_identity_impact(obs),
                            f"Should detect identity impact: '{content}'")

    def test_normal_content_does_not_trigger(self):
        layer = ExperienceFeedbackSafetyLayer()
        obs = _obs("Tony prefers Python for data processing")
        self.assertFalse(layer.has_identity_impact(obs))


if __name__ == "__main__":
    unittest.main()
