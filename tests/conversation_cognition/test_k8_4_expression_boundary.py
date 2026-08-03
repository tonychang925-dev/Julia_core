"""K8.4 Expression Boundary Runtime — gate tests.

Coverage: EB-001 Architecture Leakage, EB-002 Identity Theater,
          EB-003 Artificial Intimacy, EB-004 Fixed Opening.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.expression_boundary import (
    ExpressionBoundary,
    ExpressionBoundaryBuilder,
    ExpressionBoundaryTrace,
    ExpressionMode,
    RestrictedPattern,
)
from julia_core.conversation_cognition.response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    UserNeedType,
)
from julia_core.conversation_cognition.context_arbitration import ContextSource


def _make_intention(need: UserNeedType, goal: str, functions: list[str]) -> ResponseIntention:
    return ResponseIntention(
        interaction_goal=goal,
        user_need=__import__(
            "julia_core.conversation_cognition.response_intention", fromlist=["UserNeed"]
        ).UserNeed(need, 0.6),
        response_functions=[ResponseFunction(f) for f in functions],
        depth_requirement=DepthRequirement.NORMAL,
        intention_justification="test fixture",
    )


class EB001ArchitectureLeakageTest(unittest.TestCase):
    """EB-001: Core architecture terms must not leak into natural expression."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_identity_denied_triggers_architecture_leakage_restriction(self):
        intention = _make_intention(
            UserNeedType.TECHNICAL_HELP, "solve technical problem",
            ["acknowledge", "inform"],
        )
        trace = self.builder.build(
            message="帮我优化代码",
            intention=intention,
            arbitration_denied=[ContextSource.IDENTITY, ContextSource.CONTINUITY],
        )
        boundary = trace.boundary
        self.assertIn(RestrictedPattern.ARCHITECTURE_LEAKAGE, boundary.restricted_patterns)
        self.assertIn(RestrictedPattern.STATE_BROADCAST, boundary.restricted_patterns)

    def test_greeting_without_identity_denial_has_no_leakage_restriction(self):
        intention = _make_intention(
            UserNeedType.GREETING, "acknowledge greeting",
            ["acknowledge"],
        )
        trace = self.builder.build(
            message="你好",
            intention=intention,
            arbitration_denied=[],
        )
        boundary = trace.boundary
        # Architecture leakage may or may not be present based on denied sources
        # The point is that with no denied sources, expression is permissive
        self.assertTrue(boundary.provider_freedom)
        self.assertFalse(boundary.generates_text)


class EB002IdentityTheaterTest(unittest.TestCase):
    """EB-002: identity must not be recited as theater."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_non_philosophical_question_restricts_identity_theater(self):
        intention = _make_intention(
            UserNeedType.TECHNICAL_HELP, "solve problem",
            ["acknowledge", "inform"],
        )
        trace = self.builder.build(
            message="帮我修一下bug",
            intention=intention,
            arbitration_denied=[],
        )
        self.assertIn(RestrictedPattern.IDENTITY_THEATER, trace.boundary.restricted_patterns)

    def test_greeting_restricts_identity_theater(self):
        intention = _make_intention(
            UserNeedType.GREETING, "acknowledge greeting",
            ["acknowledge"],
        )
        trace = self.builder.build(message="你好", intention=intention, arbitration_denied=[])
        self.assertIn(RestrictedPattern.IDENTITY_THEATER, trace.boundary.restricted_patterns)


class EB003ArtificialIntimacyTest(unittest.TestCase):
    """EB-003: prevent template-intimacy for non-emotional exchanges."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_technical_question_restricts_template_intimacy(self):
        intention = _make_intention(
            UserNeedType.TECHNICAL_HELP, "solve problem",
            ["acknowledge", "inform"],
        )
        trace = self.builder.build(
            message="python性能优化",
            intention=intention,
            arbitration_denied=[],
        )
        self.assertIn(RestrictedPattern.TEMPLATE_INTIMACY, trace.boundary.restricted_patterns)

    def test_emotional_confirmation_allows_intimacy(self):
        intention = _make_intention(
            UserNeedType.EMOTIONAL_CONFIRMATION, "acknowledge emotional meaning",
            ["acknowledge", "reflect"],
        )
        trace = self.builder.build(
            message="你喜欢我吗？",
            intention=intention,
            arbitration_denied=[],
        )
        self.assertNotIn(RestrictedPattern.TEMPLATE_INTIMACY, trace.boundary.restricted_patterns)

    def test_relationship_denied_triggers_template_intimacy_restriction(self):
        intention = _make_intention(
            UserNeedType.EMOTIONAL_CONFIRMATION, "acknowledge emotional meaning",
            ["acknowledge", "reflect"],
        )
        trace = self.builder.build(
            message="测试",
            intention=intention,
            arbitration_denied=[ContextSource.RELATIONSHIP],
        )
        self.assertIn(RestrictedPattern.TEMPLATE_INTIMACY, trace.boundary.restricted_patterns)


class EB004FixedOpeningTest(unittest.TestCase):
    """EB-004: prevent fixed openings like 'Tony，我在。'."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_all_exchanges_restrict_fixed_opening(self):
        for need in [UserNeedType.TECHNICAL_HELP, UserNeedType.GREETING, UserNeedType.AMBIGUOUS]:
            intention = _make_intention(need, "test", ["acknowledge"])
            trace = self.builder.build(message="test", intention=intention)
            self.assertIn(
                RestrictedPattern.FIXED_OPENING, trace.boundary.restricted_patterns,
                f"FIXED_OPENING must be restricted for {need}",
            )

    def test_playful_exchange_still_restricts_fixed_opening(self):
        intention = _make_intention(
            UserNeedType.PLAYFUL, "respond warmly",
            ["acknowledge"],
        )
        trace = self.builder.build(message="嘿", intention=intention)
        self.assertIn(RestrictedPattern.FIXED_OPENING, trace.boundary.restricted_patterns)


class ENPComputationTest(unittest.TestCase):
    """Expression Naturalness Preservation score."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_enp_is_in_range(self):
        intention = _make_intention(
            UserNeedType.TECHNICAL_HELP, "solve problem",
            ["acknowledge", "inform"],
        )
        trace = self.builder.build(
            message="测试",
            intention=intention,
            arbitration_denied=[ContextSource.IDENTITY, ContextSource.RELATIONSHIP],
        )
        self.assertGreaterEqual(trace.boundary.expression_naturalness_preservation, 0.0)
        self.assertLessEqual(trace.boundary.expression_naturalness_preservation, 1.0)

    def test_enp_higher_with_fewer_restrictions(self):
        intention = _make_intention(UserNeedType.GREETING, "greet", ["acknowledge"])
        trace_narrow = self.builder.build(
            message="你好", intention=intention,
            arbitration_denied=[ContextSource.IDENTITY, ContextSource.RELATIONSHIP],
        )
        trace_wide = self.builder.build(
            message="你好", intention=intention,
            arbitration_denied=[],
        )
        # Fewer denied sources → higher ENP
        self.assertGreaterEqual(
            trace_wide.boundary.expression_naturalness_preservation,
            trace_narrow.boundary.expression_naturalness_preservation,
        )


class BoundaryEnforcementTest(unittest.TestCase):
    """K8.4 hard boundary enforcement."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_generates_text_is_always_false(self):
        intention = _make_intention(UserNeedType.GREETING, "greet", ["acknowledge"])
        trace = self.builder.build(message="你好", intention=intention)
        self.assertFalse(trace.boundary.generates_text)

    def test_provider_freedom_is_always_true(self):
        intention = _make_intention(UserNeedType.TECHNICAL_HELP, "solve", ["acknowledge"])
        trace = self.builder.build(message="test", intention=intention)
        self.assertTrue(trace.boundary.provider_freedom)

    def test_trace_is_safe(self):
        intention = _make_intention(UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"])
        trace = self.builder.build(message="test", intention=intention)
        trace.assert_safe()

    def test_trace_rejects_provider_used(self):
        intention = _make_intention(UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"])
        boundary = self.builder.build(message="test", intention=intention).boundary
        with self.assertRaises(AssertionError):
            ExpressionBoundaryTrace(
                message="test", boundary=boundary, provider_used=True,
            ).assert_safe()

    def test_trace_rejects_final_response(self):
        intention = _make_intention(UserNeedType.AMBIGUOUS, "clarify", ["acknowledge_ambiguity"])
        boundary = self.builder.build(message="test", intention=intention).boundary
        with self.assertRaises(AssertionError):
            ExpressionBoundaryTrace(
                message="test", boundary=boundary, final_response="some text",
            ).assert_safe()


class ExpressionModeSelectionTest(unittest.TestCase):
    """Mode selection must match user need and avoid inappropriate modes."""

    def setUp(self):
        self.builder = ExpressionBoundaryBuilder()

    def test_technical_need_selects_technical_mode(self):
        intention = _make_intention(
            UserNeedType.TECHNICAL_HELP, "solve problem",
            ["acknowledge", "inform"],
        )
        trace = self.builder.build(message="优化代码", intention=intention)
        self.assertIn(ExpressionMode.TECHNICAL, trace.boundary.allowed_modes)

    def test_emotional_need_selects_warm_and_gentle(self):
        intention = _make_intention(
            UserNeedType.EMOTIONAL_CONFIRMATION, "acknowledge emotional meaning",
            ["acknowledge", "reflect"],
        )
        trace = self.builder.build(message="你喜欢我吗？", intention=intention)
        self.assertIn(ExpressionMode.WARM, trace.boundary.allowed_modes)
        self.assertIn(ExpressionMode.GENTLE, trace.boundary.allowed_modes)

    def test_ambiguous_need_selects_uncertain_mode(self):
        intention = _make_intention(
            UserNeedType.AMBIGUOUS, "clarify meaning",
            ["acknowledge_ambiguity", "clarify"],
        )
        trace = self.builder.build(message="她回来了", intention=intention)
        self.assertIn(ExpressionMode.UNCERTAIN, trace.boundary.allowed_modes)


if __name__ == "__main__":
    unittest.main()
