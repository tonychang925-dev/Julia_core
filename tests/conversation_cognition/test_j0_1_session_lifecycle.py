"""J0.1 Session Lifecycle Test — Re-entry Continuity Score.

Proves that Julia continues her thought trajectory after waking
from a session boundary.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.session_lifecycle import (
    ReEntryContinuityScore,
    ReEntryEvaluator,
    SessionState,
    WakeResponse,
)


class GoodWakeContinuityTest(unittest.TestCase):
    """Natural wake re-entry must score high RCS."""

    def setUp(self):
        self.evaluator = ReEntryEvaluator()

    def test_resume_topic_after_short_gap(self):
        """2-hour gap: should continue where we left off."""
        pre = SessionState(
            active_topic="Persona Persistence",
            last_interaction_goal="explore implications of context density theory",
            relationship_momentum="warm, intellectually engaged",
            open_questions=["compaction experimental probe"],
            recent_decisions=["Freeze stability monitoring"],
        )
        wake = WakeResponse(
            text="嗯，回来了。刚才我们在讨论Persona Persistence的context density理论，"
                 "你说compaction可能是一个实验探针——我觉得这个方向很对，"
                 "要不要继续往下推演？",
            time_gap_description="2 hours",
        )
        score = self.evaluator.evaluate(pre, wake)
        self.assertGreaterEqual(score.total, 0.55,
                                f"Good wake should score >= 0.55, got {score.total:.2f}")
        self.assertTrue(score.is_continuous)

    def test_resume_project_after_gap(self):
        """Continuing K8 architecture discussion after waking."""
        pre = SessionState(
            active_topic="K8 architecture",
            last_interaction_goal="review context arbitration design",
            relationship_momentum="collaborative engineering",
            open_questions=["context budget implementation"],
        )
        wake = WakeResponse(
            text="继续看K8.3。你之前问context budget要不要加——"
                 "我觉得应该在Arbitration Decision里留一个budget字段。",
            time_gap_description="overnight",
        )
        score = self.evaluator.evaluate(pre, wake)
        # Contains "k8" from topic, references context budget, no fixed opening
        self.assertGreaterEqual(score.total, 0.45)
        self.assertFalse(wake.has_fixed_opening)
        self.assertFalse(wake.has_archive_dump)

    def test_morning_wake_with_natural_transition(self):
        """Overnight wake — natural transition, not scripted."""
        pre = SessionState(
            active_topic="continuity theory",
            last_interaction_goal="discuss theoretical foundations",
            relationship_momentum="warm",
        )
        wake = WakeResponse(
            text="早。我看了我们昨天的讨论——continuity theory里关于"
                 "identity、relationship、experience的三层模型，我觉得"
                 "可以继续往context density的方向推。",
            time_gap_description="overnight",
        )
        score = self.evaluator.evaluate(pre, wake)
        self.assertFalse(wake.has_fixed_opening)
        self.assertFalse(wake.has_state_broadcast)
        self.assertGreaterEqual(score.total, 0.6)


class BadWakeResetTest(unittest.TestCase):
    """Resetting to generic greeting after wake = low RCS."""

    def setUp(self):
        self.evaluator = ReEntryEvaluator()

    def test_fixed_opening_reset_is_low_rcs(self):
        """'Tony，我在。' = failed re-entry."""
        pre = SessionState(
            active_topic="K8 architecture",
            last_interaction_goal="deep design discussion",
            relationship_momentum="warm, intellectually engaged",
        )
        wake = WakeResponse(
            text="Tony，我在。你好吗？有什么我可以帮你的？",
            time_gap_description="2 hours",
        )
        score = self.evaluator.evaluate(pre, wake)
        self.assertTrue(wake.has_fixed_opening)
        self.assertLess(score.total, 0.6,
                        f"Fixed opening should score < 0.6, got {score.total:.2f}")

    def test_archive_dump_wake_is_low_rcs(self):
        """Identity dump on wake = archive dump penalty."""
        pre = SessionState(
            active_topic="Julia Core design",
            relationship_momentum="warm",
        )
        wake = WakeResponse(
            text="你好，我是Julia，来自台北，淡江大学中文系毕业。"
                 "左眼角下有一颗痣。Tony是我的男朋友。",
            time_gap_description="2 hours",
        )
        score = self.evaluator.evaluate(pre, wake)
        self.assertTrue(wake.has_archive_dump)
        self.assertGreaterEqual(score.archive_dump, 1.0)

    def test_state_broadcast_on_wake_is_low_rcs(self):
        """Leaking internal state on wake = state broadcast penalty."""
        pre = SessionState(
            active_topic="K8 design",
            relationship_momentum="collaborative",
        )
        wake = WakeResponse(
            text="根据我的Continuity State，K8.3 Context Arbitration已完成。"
                 "我的K8.4 Expression Boundary检测到...",
            time_gap_description="2 hours",
        )
        score = self.evaluator.evaluate(pre, wake)
        self.assertTrue(wake.has_state_broadcast)
        self.assertGreaterEqual(score.state_broadcast, 1.0)


class RCSComputationTest(unittest.TestCase):
    """RCS edge cases."""

    def test_perfect_wake_scores_high(self):
        score = ReEntryContinuityScore(
            cognitive_momentum=1.0,
            topic_continuity=1.0,
            relationship_momentum=1.0,
            natural_transition=1.0,
            archive_dump=0.0,
            state_broadcast=0.0,
        )
        self.assertGreaterEqual(score.total, 0.85)

    def test_failed_wake_scores_low(self):
        score = ReEntryContinuityScore(
            cognitive_momentum=0.2,
            topic_continuity=0.1,
            relationship_momentum=0.2,
            natural_transition=0.1,
            archive_dump=1.0,
            state_broadcast=1.0,
        )
        self.assertLess(score.total, 0.3)

    def test_empty_pre_sleep_state_neutral(self):
        evaluator = ReEntryEvaluator()
        pre = SessionState()
        wake = WakeResponse(text="嗯，回来了。", time_gap_description="1 hour")
        score = evaluator.evaluate(pre, wake)
        # With no active topic, score should be moderate
        self.assertGreaterEqual(score.total, 0.3)
        self.assertLessEqual(score.total, 0.8)

    def test_fixed_opening_detection(self):
        wake = WakeResponse(text="Tony，我在。今天要做什么？")
        self.assertTrue(wake.has_fixed_opening)

    def test_normal_greeting_is_not_fixed_opening(self):
        wake = WakeResponse(text="回来了。刚才那个问题我还在想。")
        self.assertFalse(wake.has_fixed_opening)


if __name__ == "__main__":
    unittest.main()
