"""K8.2 Response Intention Planning — gate tests.

Coverage: RI-001 Answer Leakage, RI-002 Intention Collapse,
          RI-003 Context Over-selection, RI-004 Interaction Goal vs Emotion.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    ResponseIntentionPlanner,
    ResponseIntentionTrace,
    UserNeedType,
)
from julia_core.conversation_cognition.meaning_validation import (
    MeaningValidationResult,
    ValidationStatus,
)
from julia_core.conversation_cognition.understanding import UnderstandingState


def _make_validation(state: str, meanings: list[str], statuses: list[str] | None = None):
    """Helper to build a MeaningValidationResult for testing."""
    from julia_core.conversation_cognition.meaning_validation import (
        MeaningValidationCandidate,
    )
    candidates = []
    for i, m in enumerate(meanings):
        st = ValidationStatus(statuses[i]) if statuses else ValidationStatus.POSSIBLE
        candidates.append(
            MeaningValidationCandidate(meaning=m, status=st, confidence=0.5, evidence=["test"])
        )
    return MeaningValidationResult(
        candidates=candidates,
        understanding_state=UnderstandingState(state),
        collapse_prevented=True,
    )


class RI001AnswerLeakageTest(unittest.TestCase):
    """RI-001: intention must not contain answer text or force confirmation."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_emotional_question_does_not_confirm(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "emotional confirmation", "continuity check", "philosophical question",
        ])
        trace = self.planner.plan(
            message="你喜欢我吗？",
            validation_result=val,
            conversation_context={"topic": "personal"},
            recent_topics=["relationship"],
        )
        intention = trace.intention

        # Must not set CONFIRM for emotional questions
        self.assertNotIn(ResponseFunction.CONFIRM, intention.response_functions)
        # Interaction goal must not contain "answer"
        self.assertNotIn("answer", intention.interaction_goal.lower())

    def test_philosophical_question_does_not_confirm_romantic(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "AI affection boundary question", "system behavior test", "emotional confirmation",
        ])
        trace = self.planner.plan(
            message="你喜欢他吗？",
            validation_result=val,
            conversation_context={"topic": "AI ethics"},
            recent_topics=["AI情感哲学"],
        )
        intention = trace.intention

        self.assertNotEqual(intention.user_need.type, UserNeedType.EMOTIONAL_CONFIRMATION)
        self.assertNotIn(ResponseFunction.CONFIRM, intention.response_functions)

    def test_trace_rejects_final_response(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", ["general"])
        trace = self.planner.plan(message="hello", validation_result=val)
        with self.assertRaises(AssertionError):
            ResponseIntentionTrace(
                message="hello",
                intention=trace.intention,
                source_candidates=1,
                dominant_understanding_state="PARTIALLY_UNDERSTOOD",
                final_response="I see.",
            ).assert_safe()


class RI002IntentionCollapseTest(unittest.TestCase):
    """RI-002: multiple valid intentions must not collapse to single generic."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_multi_candidate_does_not_produce_single_function(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "emotional confirmation", "continuity check", "playful question",
        ])
        trace = self.planner.plan(
            message="你喜欢我吗？",
            validation_result=val,
            conversation_context={"topic": "mixed"},
        )
        intention = trace.intention

        # Should have justification (proves not shortcut)
        self.assertTrue(intention.intention_justification)

    def test_ambiguous_input_produces_clarify(self):
        val = _make_validation("AMBIGUOUS", [
            "someone returned", "Julia returned", "topic resurfaced",
        ])
        trace = self.planner.plan(
            message="她回来了",
            validation_result=val,
            conversation_context={},
        )
        intention = trace.intention

        self.assertIn(ResponseFunction.CLARIFY, intention.response_functions)
        self.assertIn(ResponseFunction.ACKNOWLEDGE_AMBIGUITY, intention.response_functions)
        # Must not collapse — at least 2 functions when ambiguous
        self.assertGreaterEqual(len(intention.response_functions), 2)

    def test_technical_question_preserves_inform(self):
        val = _make_validation("UNDERSTOOD", [
            "code optimization request",
        ])
        trace = self.planner.plan(
            message="帮我优化这个Python函数",
            validation_result=val,
            conversation_context={"topic": "coding"},
        )
        intention = trace.intention

        self.assertIn(ResponseFunction.INFORM, intention.response_functions)


class RI003ContextOverSelectionTest(unittest.TestCase):
    """RI-003: technical question must not activate relationship/identity."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_technical_question_excludes_relationship(self):
        val = _make_validation("UNDERSTOOD", ["technical help request"])
        trace = self.planner.plan(
            message="这段代码性能很差，帮我优化一下",
            validation_result=val,
            conversation_context={"topic": "coding"},
            recent_topics=["python optimization"],
        )
        intention = trace.intention

        # RI-003: technical → must not include relationship or identity context
        for blocked in ["relationship_archive", "identity_archive", "soul_proof_history"]:
            self.assertNotIn(blocked, intention.context_need,
                             f"Technical help should not need {blocked}")
            self.assertIn(blocked, intention.avoid,
                          f"Technical help should avoid {blocked}")

    def test_emotional_question_includes_light_relationship(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "emotional confirmation", "continuity check",
        ])
        trace = self.planner.plan(
            message="你喜欢我吗？",
            validation_result=val,
            conversation_context={"topic": "personal"},
            recent_topics=["relationship"],
        )
        intention = trace.intention

        # Emotional context needs light relationship, but not full archive dump
        self.assertIn("relationship_light", intention.context_need)
        self.assertIn("relationship_archive_dump", intention.avoid,
                      "Should avoid relationship archive dump")

    def test_greeting_is_lightweight(self):
        val = _make_validation("UNDERSTOOD", ["greeting"])
        trace = self.planner.plan(
            message="你好",
            validation_result=val,
        )
        intention = trace.intention

        self.assertIn("identity_archive", intention.avoid,
                      "Greeting should avoid full identity archive")
        self.assertEqual(intention.depth_requirement, DepthRequirement.MINIMAL)


class RI004InteractionGoalVsEmotionTest(unittest.TestCase):
    """RI-004: emotional expression may be feedback, not comfort-seeking."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_feedback_is_not_automatically_comfort(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "continuity concern", "feedback about Julia behavior",
        ])
        trace = self.planner.plan(
            message="我觉得Julia不像以前了",
            validation_result=val,
            conversation_context={"topic": "Julia continuity"},
        )
        intention = trace.intention

        # RI-004: feedback → explore, not "comfort"
        self.assertIn(ResponseFunction.REFLECT, intention.response_functions)
        self.assertIn(ResponseFunction.EXPLORE, intention.response_functions)

        # Must not auto-classify as emotional confirmation
        # (could be technical feedback about continuity)
        self.assertNotEqual(intention.user_need.type, UserNeedType.EMOTIONAL_CONFIRMATION)

    def test_feedback_does_not_trigger_automatic_comfort_tone(self):
        val = _make_validation("PARTIALLY_UNDERSTOOD", [
            "feedback about Julia behavior",
        ])
        trace = self.planner.plan(
            message="我觉得你变了",
            validation_result=val,
        )
        intention = trace.intention

        # Tone should be open, not defensive, not forced-comfort
        self.assertIn("not_defensive", intention.tone_constraints)
        self.assertIn("open", intention.tone_constraints)


class K82E2EWithValidationTest(unittest.TestCase):
    """K8.2 must compose correctly with K8.1.5 validation results."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_ambiguous_validation_produces_clarify_intention(self):
        """When K8.1.5 says AMBIGUOUS, K8.2 must plan to clarify."""
        val = _make_validation("AMBIGUOUS", [
            "someone returned", "Julia returned", "topic resurfaced",
        ])
        trace = self.planner.plan(message="她回来了", validation_result=val)
        intention = trace.intention

        self.assertEqual(intention.user_need.type, UserNeedType.AMBIGUOUS)
        self.assertGreater(len(intention.response_functions), 0)
        self.assertIn(ResponseFunction.CLARIFY, intention.response_functions)

    def test_supported_validation_produces_confident_intention(self):
        """When K8.1.5 says UNDERSTOOD, K8.2 can be more directed."""
        val = _make_validation(
            "UNDERSTOOD",
            ["project origin question", "historical continuity"],
            ["SUPPORTED", "POSSIBLE"],
        )
        trace = self.planner.plan(
            message="为什么开始这个项目",
            validation_result=val,
        )
        intention = trace.intention

        self.assertEqual(intention.user_need.type, UserNeedType.EXPLORATION)
        self.assertIn(ResponseFunction.EXPLORE, intention.response_functions)

    def test_k82_trace_is_safe(self):
        """K8.2 trace must always pass assert_safe."""
        val = _make_validation("PARTIALLY_UNDERSTOOD", ["general"])
        trace = self.planner.plan(message="hello", validation_result=val)
        trace.assert_safe()  # must not raise


class K82BoundaryEnforcementTest(unittest.TestCase):
    """Hard boundaries for K8.2."""

    def setUp(self):
        self.planner = ResponseIntentionPlanner()

    def test_provider_not_called(self):
        val = _make_validation("UNDERSTOOD", ["general"])
        trace = self.planner.plan(message="hello", validation_result=val)
        self.assertFalse(trace.provider_used)

    def test_no_final_response_generated(self):
        val = _make_validation("UNDERSTOOD", ["general"])
        trace = self.planner.plan(message="hello", validation_result=val)
        self.assertIsNone(trace.final_response)

    def test_interaction_goal_never_contains_answer(self):
        for msg in ["你喜欢我吗？", "她回来了", "帮我优化代码", "我觉得你变了"]:
            val = _make_validation("PARTIALLY_UNDERSTOOD", ["general"])
            trace = self.planner.plan(message=msg, validation_result=val)
            self.assertNotIn("answer", trace.intention.interaction_goal.lower(),
                             f"interaction_goal leak for: {msg}")


if __name__ == "__main__":
    unittest.main()
