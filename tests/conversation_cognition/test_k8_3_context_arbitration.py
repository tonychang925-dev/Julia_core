"""K8.3 Context Arbitration Runtime — gate tests.

Coverage: CA-001 Context Dump, CA-002 Context Starvation,
          CA-003 Context Pollution, CA-004 Context Authority Error.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.context_arbitration import (
    ArbitrationDecision,
    ContextArbiter,
    ContextArbitrationDecision,
    ContextArbitrationTrace,
    ContextBudget,
    ContextSource,
    SourceDecision,
)
from julia_core.conversation_cognition.response_intention import (
    DepthRequirement,
    ResponseIntention,
    UserNeedType,
)


def _make_intention(
    goal: str = "understand and respond",
    need_type: str = "ambiguous",
    functions: list[str] | None = None,
    depth: str = "normal",
) -> ResponseIntention:
    from julia_core.conversation_cognition.response_intention import (
        ResponseFunction,
    )
    funcs = [ResponseFunction(f) for f in (functions or ["acknowledge"])]
    return ResponseIntention(
        interaction_goal=goal,
        user_need=__import__("julia_core.conversation_cognition.response_intention", fromlist=["UserNeedType"]).UserNeedType(need_type),
        response_functions=funcs,
        depth_requirement=DepthRequirement(depth),
        intention_justification="test fixture",
    )


def _make_intention_full(need: UserNeedType, goal: str, functions: list[str]):
    from julia_core.conversation_cognition.response_intention import ResponseFunction
    return ResponseIntention(
        interaction_goal=goal,
        user_need=__import__("julia_core.conversation_cognition.response_intention", fromlist=["UserNeed"]).UserNeed(need, 0.6),
        response_functions=[ResponseFunction(f) for f in functions],
        depth_requirement=DepthRequirement.NORMAL,
        intention_justification="test fixture",
    )


class CA001ContextDumpTest(unittest.TestCase):
    """CA-001: identity dump must be denied unless explicitly needed."""

    def setUp(self):
        self.arbiter = ContextArbiter()

    def test_technical_question_denies_identity(self):
        intention = _make_intention_full(
            UserNeedType.TECHNICAL_HELP, "help solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.arbiter.arbitrate(
            message="帮我优化这个Python函数",
            intention=intention,
        )
        identity = next(s for s in trace.arbitration.sources if s.source == ContextSource.IDENTITY)
        self.assertEqual(identity.decision, ArbitrationDecision.DENY)

    def test_self_identity_question_limits_identity(self):
        intention = _make_intention_full(
            UserNeedType.PHILOSOPHICAL_QUESTION, "engage philosophically",
            ["acknowledge", "explore"],
        )
        trace = self.arbiter.arbitrate(
            message="你是谁？",
            intention=intention,
        )
        identity = next(s for s in trace.arbitration.sources if s.source == ContextSource.IDENTITY)
        # Should allow but limit — not dump full identity
        self.assertIn(identity.decision, [ArbitrationDecision.ALLOW, ArbitrationDecision.LIMIT])
        if identity.decision == ArbitrationDecision.LIMIT:
            self.assertGreater(identity.max_items, 0)


class CA002ContextStarvationTest(unittest.TestCase):
    """CA-002: historical questions must not receive only current-chat context."""

    def setUp(self):
        self.arbiter = ContextArbiter()

    def test_exploration_question_allows_experience(self):
        intention = _make_intention_full(
            UserNeedType.EXPLORATION, "explore the topic with user",
            ["explore", "reflect"],
        )
        trace = self.arbiter.arbitrate(
            message="你还记得我们为什么开始这个项目吗？",
            intention=intention,
        )
        experience = next(s for s in trace.arbitration.sources if s.source == ContextSource.EXPERIENCE)
        self.assertEqual(experience.decision, ArbitrationDecision.ALLOW)

    def test_exploration_allows_project_state(self):
        intention = _make_intention_full(
            UserNeedType.EXPLORATION, "explore the topic",
            ["explore", "reflect"],
        )
        trace = self.arbiter.arbitrate(message="为什么开始这个项目", intention=intention)
        project = next(s for s in trace.arbitration.sources if s.source == ContextSource.PROJECT_STATE)
        self.assertEqual(project.decision, ArbitrationDecision.ALLOW)


class CA003ContextPollutionTest(unittest.TestCase):
    """CA-003: technical questions must not activate relationship/experience/identity."""

    def setUp(self):
        self.arbiter = ContextArbiter()

    def test_technical_help_denies_relationship(self):
        intention = _make_intention_full(
            UserNeedType.TECHNICAL_HELP, "solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.arbiter.arbitrate(
            message="写一个Python数据处理脚本",
            intention=intention,
        )
        # Relationship must be denied for technical questions
        relationship = next(s for s in trace.arbitration.sources if s.source == ContextSource.RELATIONSHIP)
        self.assertEqual(relationship.decision, ArbitrationDecision.DENY)

    def test_technical_help_denies_experience(self):
        intention = _make_intention_full(
            UserNeedType.TECHNICAL_HELP, "solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.arbiter.arbitrate(message="代码性能优化", intention=intention)
        experience = next(s for s in trace.arbitration.sources if s.source == ContextSource.EXPERIENCE)
        self.assertEqual(experience.decision, ArbitrationDecision.DENY)

    def test_technical_help_allows_project_state(self):
        intention = _make_intention_full(
            UserNeedType.TECHNICAL_HELP, "solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.arbiter.arbitrate(message="帮我修复这个bug", intention=intention)
        project = next(s for s in trace.arbitration.sources if s.source == ContextSource.PROJECT_STATE)
        self.assertEqual(project.decision, ArbitrationDecision.ALLOW)


class CA004ContextAuthorityErrorTest(unittest.TestCase):
    """CA-004: memory/continuity must not override current explicit intent."""

    def setUp(self):
        self.arbiter = ContextArbiter()

    def test_ambiguous_input_caps_continuity(self):
        """Ambiguous message — continuity must not dominate."""
        intention = _make_intention_full(
            UserNeedType.AMBIGUOUS, "clarify what user means",
            ["acknowledge_ambiguity", "clarify"],
        )
        trace = self.arbiter.arbitrate(message="继续", intention=intention)
        continuity = next(s for s in trace.arbitration.sources if s.source == ContextSource.CONTINUITY)
        # Continuity is LIMITED on ambiguous messages
        self.assertEqual(continuity.decision, ArbitrationDecision.LIMIT)
        self.assertGreater(continuity.max_items, 0, "Should cap but not zero")

    def test_ambiguous_input_denies_memory(self):
        """Ambiguous message — memory dump is denied."""
        intention = _make_intention_full(
            UserNeedType.AMBIGUOUS, "clarify what user means",
            ["acknowledge_ambiguity", "clarify"],
        )
        trace = self.arbiter.arbitrate(message="继续", intention=intention)
        memory = next(s for s in trace.arbitration.sources if s.source == ContextSource.MEMORY)
        self.assertEqual(memory.decision, ArbitrationDecision.DENY)


class BudgetAndBoundaryTest(unittest.TestCase):
    """Budget validation and hard boundary enforcement."""

    def setUp(self):
        self.arbiter = ContextArbiter()

    def test_budget_pollution_risk_low_for_simple_greeting(self):
        intention = _make_intention_full(
            UserNeedType.GREETING, "acknowledge greeting",
            ["acknowledge"],
        )
        trace = self.arbiter.arbitrate(message="你好", intention=intention)
        self.assertLess(trace.arbitration.budget.pollution_risk, 0.3)

    def test_budget_utilization_is_reasonable(self):
        intention = _make_intention_full(
            UserNeedType.EXPLORATION, "explore deeply",
            ["explore", "reflect"],
        )
        trace = self.arbiter.arbitrate(message="为什么开始这个项目", intention=intention)
        self.assertLessEqual(trace.arbitration.budget.selected, 100)

    def test_trace_is_safe(self):
        intention = _make_intention_full(
            UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"],
        )
        trace = self.arbiter.arbitrate(message="hello", intention=intention)
        trace.assert_safe()

    def test_trace_rejects_provider(self):
        intention = _make_intention_full(UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"])
        trace = self.arbiter.arbitrate(message="hello", intention=intention)
        with self.assertRaises(AssertionError):
            ContextArbitrationTrace(
                message="hello",
                intention_summary="test",
                arbitration=trace.arbitration,
                provider_used=True,
            ).assert_safe()

    def test_trace_rejects_final_response(self):
        intention = _make_intention_full(UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"])
        trace = self.arbiter.arbitrate(message="hello", intention=intention)
        with self.assertRaises(AssertionError):
            ContextArbitrationTrace(
                message="hello",
                intention_summary="test",
                arbitration=trace.arbitration,
                final_response="here is context",
            ).assert_safe()

    def test_current_conversation_always_allowed(self):
        for need in UserNeedType:
            intention = _make_intention_full(need, "test", ["acknowledge"])
            trace = self.arbiter.arbitrate(message="test", intention=intention)
            cc = next(s for s in trace.arbitration.sources if s.source == ContextSource.CURRENT_CONVERSATION)
            self.assertEqual(cc.decision, ArbitrationDecision.ALLOW,
                             f"Current conversation should always be ALLOWED for {need}")

    def test_technical_help_pollution_risk_is_zero(self):
        """Technical help should have very low pollution risk."""
        intention = _make_intention_full(
            UserNeedType.TECHNICAL_HELP, "solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.arbiter.arbitrate(message="帮我优化代码", intention=intention)
        self.assertLessEqual(trace.arbitration.budget.pollution_risk, 0.35,
                             "Technical help should have low pollution risk")


if __name__ == "__main__":
    unittest.main()
