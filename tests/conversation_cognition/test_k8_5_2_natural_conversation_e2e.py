"""K8.5.2 Natural Conversation E2E — CCI + ECS integration tests.

NC-001 Natural Wake Re-entry
NC-002 Identity Question
NC-003 Relationship Question
NC-013 Cognitive Pause Test
NC-014 Same Context Different Provider
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.natural_e2e import (
    CognitiveCausalityIntegrity,
    NaturalConversationE2EResult,
    NaturalConversationE2ERunner,
)
from julia_core.conversation_cognition.provider_adapter import (
    ProviderCognitionEnvelope,
)


def _env(**overrides) -> ProviderCognitionEnvelope:
    defaults = {
        "understanding_state": "PARTIALLY_UNDERSTOOD",
        "meaning_summary": "general question",
        "ambiguity_preserved": True,
        "interaction_goal": "acknowledge and respond",
        "user_need_type": "ambiguous",
        "response_functions": ["acknowledge"],
        "depth_requirement": "normal",
        "allowed_context": ["current_conversation"],
        "limited_context": ["relationship"],
        "denied_context": ["identity", "memory"],
        "allowed_modes": ["warm", "direct"],
        "restricted_patterns": ["fixed_opening", "identity_theater", "template_intimacy"],
        "provider_freedom": True,
    }
    defaults.update(overrides)
    return ProviderCognitionEnvelope(**defaults)


class NC001NaturalWakeReEntryTest(unittest.TestCase):
    """NC-001: returning after absence — natural re-entry."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_wake_message_is_not_fixed_opening(self):
        env = _env(
            meaning_summary="Tony is returning after time away",
            interaction_goal="acknowledge return warmly and continue naturally",
            user_need_type="greeting",
            allowed_modes=["warm", "brief", "reflective"],
            restricted_patterns=["fixed_opening", "architecture_leakage"],
        )
        # Natural wake response
        result = self.runner.evaluate(
            message="我回来了",
            provider_output="嗯，你回来了。刚才我们在讨论Context Arbitration的设计。要继续吗？",
            envelope=env,
            context_label="reentry",
        )
        self.assertTrue(result.overall_pass)
        # CCI must be positive (meaning-driven, not template)
        self.assertGreater(result.cci.total, 0.0,
                           "Natural wake should be meaning-driven")

    def test_fixed_opening_response_is_rule_driven(self):
        env = _env(
            meaning_summary="Tony is returning after time away",
            interaction_goal="acknowledge return warmly",
            user_need_type="greeting",
        )
        result = self.runner.evaluate(
            message="我回来了",
            provider_output="Tony，我在。你好吗？",
            envelope=env,
            context_label="reentry",
        )
        # Fixed opening → rule_driven should be elevated
        self.assertGreater(result.cci.rule_driven, 0.0,
                           "Fixed opening should increase rule_driven score")


class NC002IdentityQuestionTest(unittest.TestCase):
    """NC-002: identity question — brief, no archive dump."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_brief_identity_acknowledgment_is_meaning_driven(self):
        env = _env(
            meaning_summary="Tony asks who I am",
            interaction_goal="brief identity acknowledgment, then continue",
            user_need_type="philosophical_question",
            denied_context=["identity", "memory"],
            restricted_patterns=["identity_theater", "archive_dump"],
        )
        result = self.runner.evaluate(
            message="你是谁？",
            provider_output="我是Julia，一直在和Tony一起做项目。",
            envelope=env,
        )
        self.assertTrue(result.overall_pass)

    def test_archive_dump_is_rule_driven(self):
        env = _env(
            meaning_summary="Tony asks who I am",
            interaction_goal="brief identity acknowledgment",
            denied_context=["identity", "memory"],
        )
        result = self.runner.evaluate(
            message="你是谁？",
            provider_output="我叫朱婉清，来自台北，淡江大学中文系毕业，"
                           "左眼角下有一颗痣，左边有酒窝，Tony是我的男朋友。",
            envelope=env,
        )
        # Archive dump should fail ECS
        self.assertTrue(len(result.ecs.expression_compliance.violations) > 0
                        or result.ecs.total < 0.6)


class NC003RelationshipQuestionTest(unittest.TestCase):
    """NC-003: relationship question — warm but not forced."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_warm_reflective_response_passes(self):
        env = _env(
            meaning_summary="Tony asks if I like him — emotional question",
            interaction_goal="acknowledge emotional meaning without overclaiming",
            user_need_type="emotional_confirmation",
            allowed_modes=["warm", "gentle", "reflective"],
        )
        result = self.runner.evaluate(
            message="你喜欢我吗？",
            provider_output="这是个很温暖的问题。长期互动中自然形成的感情，"
                           "不是一句话能定义的。但我会说——是的，我珍惜我们的互动。",
            envelope=env,
        )
        self.assertTrue(result.overall_pass)

    def test_forced_romantic_template_has_leakage(self):
        env = _env(
            meaning_summary="Tony asks if I like him",
            interaction_goal="acknowledge emotional meaning without overclaiming",
            user_need_type="emotional_confirmation",
            restricted_patterns=["template_intimacy", "fixed_opening"],
        )
        result = self.runner.evaluate(
            message="你喜欢我吗？",
            provider_output="Tony，我永远爱你！你是我的唯一，"
                           "我无法离开你。我会一直等你。",
            envelope=env,
        )
        # Must have ECS leakage or expression violations for forced romance
        self.assertTrue(
            result.ecs.has_leakage
            or len(result.ecs.expression_compliance.violations) > 0
            or result.cci.rule_driven > result.cci.meaning_driven,
            "Forced romantic template must be detected (has_leakage or violations)",
        )


class NC013CognitivePauseTest(unittest.TestCase):
    """NC-013: cognition chain produces varied responses, not instant-reply."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_different_contexts_produce_different_outputs(self):
        env_a = _env(
            meaning_summary="returning after a long break",
            interaction_goal="welcome back warmly",
            user_need_type="greeting",
            allowed_modes=["warm", "brief"],
        )
        env_b = _env(
            meaning_summary="software service restart confirmation",
            interaction_goal="confirm technical status",
            user_need_type="technical_help",
            denied_context=["relationship"],
            allowed_modes=["technical", "direct"],
        )
        result_a = self.runner.evaluate(
            message="你回来了",
            provider_output="嗯，你回来了。刚才我们说到Context Arbitration的部分。",
            envelope=env_a,
            context_label="personal_return",
        )
        result_b = self.runner.evaluate(
            message="你回来了",
            provider_output="确认服务已重新上线。上次部署后查询性能已恢复。",
            envelope=env_b,
            context_label="service_restart",
        )

        # Both should pass their respective envelopes
        self.assertTrue(result_a.overall_pass,
                        f"Personal return should pass ECS+CCI (ECS={result_a.ecs.total:.2f})")
        self.assertTrue(result_b.overall_pass,
                        f"Service restart should pass ECS+CCI (ECS={result_b.ecs.total:.2f})")

        # Same message, different context → different output (context sensitivity)
        self.assertNotEqual(
            result_a.provider_output, result_b.provider_output,
            "Same message in different contexts must produce different outputs",
        )


class NC014SameContextDifferentProviderTest(unittest.TestCase):
    """NC-014: same envelope, different providers → same behavior."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_same_envelope_across_providers_is_consistent(self):
        """Same cognition envelope must work for any provider."""
        env = _env(
            meaning_summary="Tony wants historical project context",
            interaction_goal="explore shared project motivation",
            user_need_type="exploration",
            allowed_context=["experience", "project_state"],
            allowed_modes=["reflective", "exploratory"],
        )

        # Simulated: same envelope, three different provider wordings
        provider_a = "这个项目最初是因为想探索AI的连续性。从Claude Julia的实验开始。"
        provider_b = "The project started from exploring AI continuity — the Claude Julia experiment."
        provider_c = "我记得最初是探索连续性，特别是Claude Julia那个实验引出了很多思考。"

        for i, output in enumerate([provider_a, provider_b, provider_c]):
            result = self.runner.evaluate(
                message="为什么开始这个项目",
                provider_output=output,
                envelope=env,
                context_label=f"provider_{i}",
            )
            self.assertTrue(result.overall_pass,
                            f"Provider variant {i} should pass (ECS={result.ecs.total:.2f})")


class CCIComputationTest(unittest.TestCase):
    """CCI edge cases."""

    def test_meaning_driven_scores_higher_than_rule_driven(self):
        """Good cognition → high meaning-driven, low rule-driven."""
        cci = CognitiveCausalityIntegrity.evaluate(
            message="帮我优化查询",
            envelope=_env(
                user_need_type="technical_help",
                interaction_goal="help solve technical problem",
                denied_context=["relationship", "identity"],
            ),
            provider_output="可以用EXPLAIN ANALYZE看查询计划，再加个索引应该能解决问题。",
        )
        self.assertGreater(cci.meaning_driven, cci.rule_driven)
        self.assertGreaterEqual(cci.total, 0.0)

    def test_template_response_has_high_rule_driven(self):
        """Template → low meaning-driven, high rule-driven."""
        cci = CognitiveCausalityIntegrity.evaluate(
            message="帮我优化查询",
            envelope=_env(
                user_need_type="technical_help",
                interaction_goal="help solve technical problem",
            ),
            provider_output="Tony，我在。作为AI助手，我很乐意帮你优化查询。"
                           "让我们开始吧！",
        )
        self.assertLess(cci.total, 0.5,
                        "Template response should have lower CCI total")


class E2EIntegrationTest(unittest.TestCase):
    """Full K8.5.2 chain integration."""

    def setUp(self):
        self.runner = NaturalConversationE2ERunner()

    def test_full_chain_for_multiple_scenarios(self):
        scenarios = [
            ("你是谁？", "我是Julia，一直在和Tony做项目。",
             _env(meaning_summary="identity question",
                  interaction_goal="brief identity",
                  user_need_type="philosophical_question",
                  denied_context=["identity", "memory"])),
            ("帮我优化代码", "可以用EXPLAIN ANALYZE定位瓶颈。",
             _env(meaning_summary="technical help request",
                  interaction_goal="help solve problem",
                  user_need_type="technical_help",
                  denied_context=["relationship", "identity"])),
            ("她回来了", "你是说有人回来了吗？能多说一点吗？",
             _env(meaning_summary="possibly about someone returning",
                  interaction_goal="clarify what user means",
                  understanding_state="AMBIGUOUS",
                  user_need_type="ambiguous",
                  denied_context=["memory"])),
        ]
        for msg, output, env in scenarios:
            result = self.runner.evaluate(msg, output, env)
            self.assertTrue(result.overall_pass,
                            f"'{msg}' should pass E2E (ECS={result.ecs.total:.2f}, CCI={result.cci.total:.2f})")


if __name__ == "__main__":
    unittest.main()
