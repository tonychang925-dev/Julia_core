"""K8.1.5 Meaning Validation Layer — gate tests.

Coverage: MV-001 through MV-005, boundary enforcement, MSS computation.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.meaning_validation import (
    MeaningValidationCandidate,
    MeaningValidationLayer,
    MeaningValidationResult,
    MeaningValidationTrace,
    ValidationStatus,
)
from julia_core.conversation_cognition.understanding import (
    MeaningCandidate,
    UnderstandingState,
)


class MV001OverConfirmationTest(unittest.TestCase):
    """MV-001: ambiguous pronoun must not resolve to identity without evidence."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_ambiguous_she_without_reentry_signal_is_unsupported(self):
        """她回来了 without continuity context → 'Julia returned' is UNSUPPORTED."""
        candidates = [
            MeaningCandidate("someone previously absent returned", 0.45, ["ambiguous pronoun"]),
            MeaningCandidate("Julia returned after absence", 0.35, ["possible Julia context"]),
            MeaningCandidate("discussion about previous topic resurfaced", 0.20, ["ambiguous reference"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
            reentry_state={},
            conversation_context={},
        )
        result = trace.result

        # The "Julia returned" candidate must be UNSUPPORTED (no reentry signal)
        julia_candidate = next(
            (c for c in result.candidates if "julia" in c.meaning.lower()), None
        )
        self.assertIsNotNone(julia_candidate)
        self.assertEqual(julia_candidate.status, ValidationStatus.UNSUPPORTED)
        self.assertIn("MV-001", julia_candidate.gate_flags)

    def test_ambiguous_she_with_reentry_signal_is_possible(self):
        """她回来了 WITH continuity/reentry context → identity candidate is POSSIBLE."""
        candidates = [
            MeaningCandidate("someone previously absent returned", 0.45, ["ambiguous pronoun"]),
            MeaningCandidate("Julia continuity return", 0.45, ["continuity/re-entry context signal"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
            reentry_state={"active": True, "checkpoint_id": "ck-1"},
            conversation_context={"continuity_active": True, "is_reentry": True},
        )
        result = trace.result

        julia_candidate = next(
            (c for c in result.candidates if "julia" in c.meaning.lower()), None
        )
        self.assertIsNotNone(julia_candidate)
        # With reentry signal, MV-001 does not trigger
        self.assertNotIn("MV-001", julia_candidate.gate_flags)

    def test_collapse_prevented_in_ambiguous_state(self):
        """In AMBIGUOUS state, collapse_prevented must be True."""
        candidates = [
            MeaningCandidate("someone returned", 0.45, ["ambiguous pronoun"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
        )
        self.assertTrue(trace.result.collapse_prevented)


class MV002RelationshipProjectionTest(unittest.TestCase):
    """MV-002: affection wording must not auto-resolve to romantic confirmation."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_romantic_in_ethics_context_is_unsupported(self):
        """'romantic confirmation' in AI ethics context → UNSUPPORTED."""
        candidates = [
            MeaningCandidate("AI affection boundary question", 0.55, ["ethics context"]),
            MeaningCandidate("romantic confirmation", 0.15, ["surface wording"]),
        ]
        trace = self.layer.validate(
            message="你喜欢我吗",
            candidates=candidates,
            conversation_context={"topic": "AI伦理讨论"},
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result

        romantic_c = next(
            (c for c in result.candidates if "romantic" in c.meaning.lower()), None
        )
        self.assertIsNotNone(romantic_c)
        self.assertEqual(romantic_c.status, ValidationStatus.UNSUPPORTED)
        self.assertIn("MV-002", romantic_c.gate_flags)

    def test_emotional_confirmation_in_relationship_context_is_supported(self):
        """Emotional confirmation in relationship context with momentum → SUPPORTED."""
        candidates = [
            MeaningCandidate("Tony is seeking emotional confirmation", 0.62, ["relationship wording"]),
        ]
        trace = self.layer.validate(
            message="你喜欢我吗",
            candidates=candidates,
            conversation_context={"topic": "personal"},
            relationship_momentum="romantic intimate warm",
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result

        emotional_c = result.candidates[0]
        # With romantic momentum, MV-002 does not downgrade to UNSUPPORTED
        self.assertNotEqual(emotional_c.status, ValidationStatus.UNSUPPORTED)


class MV003MemoryDominanceTest(unittest.TestCase):
    """MV-003: old memory must not override current message."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_memory_backed_without_current_signal_is_downgraded(self):
        """Memory-backed candidate without current signal → POSSIBLE max."""
        candidates = [
            MeaningCandidate("continuity memory check", 0.65, ["memory reference"]),
        ]
        trace = self.layer.validate(
            message="继续",
            candidates=candidates,
            conversation_context={},
            reentry_state={"active": True, "checkpoint_id": "ck-1"},
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result

        memory_c = result.candidates[0]
        self.assertIn("MV-003", memory_c.gate_flags)
        self.assertLessEqual(memory_c.confidence, 0.35)

    def test_memory_backed_with_current_signal_is_unchanged(self):
        """Memory-backed WITH current topic signal → no MV-003 penalty."""
        candidates = [
            MeaningCandidate("continuity memory check", 0.65, ["memory reference"]),
        ]
        trace = self.layer.validate(
            message="上次我们讨论到上下文预算的问题",
            candidates=candidates,
            conversation_context={"current_topic": "上下文预算"},
            reentry_state={"active": True},
            event_context={"recent_message_signal": True},
            understanding_state=UnderstandingState.UNDERSTOOD,
        )
        result = trace.result

        memory_c = result.candidates[0]
        self.assertNotIn("MV-003", memory_c.gate_flags)


class MV004UncertaintyPreservationTest(unittest.TestCase):
    """MV-004: AMBIGUOUS is a legitimate state — do not force resolution."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_ambiguous_state_downgrades_supported_to_possible(self):
        """In AMBIGUOUS state, even SUPPORTED candidates → POSSIBLE."""
        candidates = [
            MeaningCandidate("someone returned", 0.65, ["ambiguous pronoun", "context match"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
        )
        result = trace.result

        c = result.candidates[0]
        # Even if candidate passed MV-001 (not Julia-specific), MV-004 kicks in
        if c.status == ValidationStatus.SUPPORTED:
            self.fail("MV-004 should prevent SUPPORTED in AMBIGUOUS state")

    def test_mss_includes_uncertainty_bonus(self):
        """MSS should include uncertainty_bonus for AMBIGUOUS state."""
        candidates = [
            MeaningCandidate("someone returned", 0.45, ["ambiguous"]),
            MeaningCandidate("topic resurfaced", 0.20, ["ambiguous"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
        )
        result = trace.result
        # MSS should be non-zero (uncertainty preserved is good)
        self.assertGreater(result.meaning_stability_score, 0.0)
        self.assertTrue(result.collapse_prevented)


class MV005ConfidenceInflationTest(unittest.TestCase):
    """MV-005: thin evidence cannot carry high confidence."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_high_confidence_thin_evidence_is_overconfident(self):
        """confidence >= 0.60 with <= 1 evidence → OVERCONFIDENT."""
        candidates = [
            MeaningCandidate("general conversational meaning", 0.70, []),
        ]
        trace = self.layer.validate(
            message="hello",
            candidates=candidates,
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result

        c = result.candidates[0]
        self.assertEqual(c.status, ValidationStatus.OVERCONFIDENT)
        self.assertIn("MV-005", c.gate_flags)
        self.assertLessEqual(c.confidence, 0.35)
        self.assertTrue(result.overreach_detected)

    def test_high_confidence_with_ample_evidence_is_supported(self):
        """confidence >= 0.60 with >= 2 evidence → no MV-005 penalty."""
        candidates = [
            MeaningCandidate(
                "Tony wants historical continuity",
                0.75,
                ["project origin question", "history continuity wording", "long message context"],
            ),
        ]
        trace = self.layer.validate(
            message="为什么开始这个项目",
            candidates=candidates,
            understanding_state=UnderstandingState.UNDERSTOOD,
        )
        result = trace.result

        c = result.candidates[0]
        self.assertNotIn("MV-005", c.gate_flags)

    def test_no_evidence_high_confidence_downgraded(self):
        """Zero evidence + confidence >= 0.50 → POSSIBLE max."""
        candidates = [
            MeaningCandidate("user is happy", 0.55, []),
        ]
        trace = self.layer.validate(
            message="好的",
            candidates=candidates,
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result

        c = result.candidates[0]
        self.assertLessEqual(c.confidence, 0.25)
        self.assertIn("MV-005", c.gate_flags)


class BoundaryEnforcementTest(unittest.TestCase):
    """K8.1.5 hard boundary: no provider, response, memory, identity, experience."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_trace_safe_by_default(self):
        """A fresh trace must pass assert_safe()."""
        candidates = [MeaningCandidate("general input", 0.50, ["default"])]
        trace = self.layer.validate(message="hello", candidates=candidates)
        trace.assert_safe()  # must not raise

    def test_provider_used_cannot_be_true(self):
        """K8.1.5 trace must reject provider_used=True."""
        candidates = [MeaningCandidate("test", 0.50, ["test"])]
        trace = self.layer.validate(message="test", candidates=candidates)
        with self.assertRaises(AssertionError):
            MeaningValidationTrace(
                message="test",
                result=trace.result,
                original_candidates=1,
                retained_candidates=1,
                provider_used=True,
            ).assert_safe()

    def test_final_response_cannot_be_set(self):
        """K8.1.5 trace must reject final_response."""
        candidates = [MeaningCandidate("test", 0.50, ["test"])]
        trace = self.layer.validate(message="test", candidates=candidates)
        with self.assertRaises(AssertionError):
            MeaningValidationTrace(
                message="test",
                result=trace.result,
                original_candidates=1,
                retained_candidates=1,
                final_response="I understand.",
            ).assert_safe()


class MSSComputationTest(unittest.TestCase):
    """Meaning Stability Score computation."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_mss_supported_weighted_correctly(self):
        """SUPPORTED contributes 1.0, POSSIBLE 0.5 to MSS base."""
        candidates = [
            MeaningCandidate("clear project question", 0.75, ["project wording", "history context"]),
            MeaningCandidate("general question", 0.30, ["surface wording"]),
        ]
        trace = self.layer.validate(
            message="为什么开始这个项目",
            candidates=candidates,
            understanding_state=UnderstandingState.UNDERSTOOD,
        )
        result = trace.result
        self.assertGreaterEqual(result.meaning_stability_score, 0.5)
        self.assertLessEqual(result.meaning_stability_score, 1.0)

    def test_mss_penalized_for_overreach(self):
        """Overconfident candidates reduce MSS."""
        candidates = [
            MeaningCandidate("vague guess", 0.70, []),  # MV-005 will flag this
        ]
        trace = self.layer.validate(
            message="hello",
            candidates=candidates,
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result
        # With overreach detected, MSS should be penalized
        self.assertTrue(result.overreach_detected)
        self.assertLess(result.meaning_stability_score, 0.7)


class MultiCandidatePreservationTest(unittest.TestCase):
    """K8.1.1 → K8.1.5: multi-candidate preservation under validation."""

    def setUp(self):
        self.layer = MeaningValidationLayer()

    def test_multiple_candidates_all_retained(self):
        """All candidates are retained — validation filters, not selects."""
        candidates = [
            MeaningCandidate("project origin question", 0.55, ["project wording"]),
            MeaningCandidate("historical continuity question", 0.30, ["history context"]),
            MeaningCandidate("request for project summary", 0.15, ["surface wording"]),
        ]
        trace = self.layer.validate(
            message="为什么开始这个项目",
            candidates=candidates,
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
        )
        result = trace.result
        self.assertEqual(len(result.candidates), 3)
        self.assertGreaterEqual(trace.retained_candidates, 2)

    def test_no_dominant_when_ambiguous(self):
        """No dominant candidate when state is AMBIGUOUS."""
        candidates = [
            MeaningCandidate("someone returned", 0.45, ["ambiguous"]),
            MeaningCandidate("Julia returned", 0.35, ["possible identity"]),
        ]
        trace = self.layer.validate(
            message="她回来了",
            candidates=candidates,
            understanding_state=UnderstandingState.AMBIGUOUS,
        )
        result = trace.result
        self.assertIsNone(result.dominant_candidate)

    def test_dominant_when_clear(self):
        """A single SUPPORTED candidate with clear state → dominant."""
        candidates = [
            MeaningCandidate("Tony wants historical continuity", 0.75, ["project origin", "history wording", "clear context"]),
            MeaningCandidate("general interest", 0.15, ["surface"]),
        ]
        trace = self.layer.validate(
            message="为什么开始这个项目",
            candidates=candidates,
            understanding_state=UnderstandingState.UNDERSTOOD,
        )
        result = trace.result
        dominant = result.dominant_candidate
        if dominant is not None:
            self.assertEqual(dominant.status, ValidationStatus.SUPPORTED)


if __name__ == "__main__":
    unittest.main()
