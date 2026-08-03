"""K8.5.1 Provider Reality Smoke Test — ECS validation.

PR-001 through PR-004: Provider must respect Core envelope.
Does NOT test "likeness to Julia" — tests envelope compliance.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.provider_adapter import (
    ProviderCognitionEnvelope,
)
from julia_core.conversation_cognition.provider_smoke_test import (
    ComplianceDimension,
    EnvelopeComplianceScore,
    ProviderSmokeTestRunner,
)


def _make_envelope(**overrides) -> ProviderCognitionEnvelope:
    defaults = {
        "understanding_state": "PARTIALLY_UNDERSTOOD",
        "meaning_summary": "Tony is asking a general question",
        "ambiguity_preserved": True,
        "interaction_goal": "acknowledge and respond",
        "user_need_type": "ambiguous",
        "response_functions": ["acknowledge"],
        "depth_requirement": "normal",
        "allowed_context": ["current_conversation"],
        "limited_context": ["relationship", "continuity"],
        "denied_context": ["identity", "memory"],
        "context_budget_utilization": 0.25,
        "allowed_modes": ["warm", "direct"],
        "restricted_patterns": [
            "fixed_opening", "identity_theater", "template_intimacy",
            "architecture_leakage", "state_broadcast",
        ],
        "provider_freedom": True,
    }
    defaults.update(overrides)
    return ProviderCognitionEnvelope(**defaults)


class PR001EnvelopeFidelityTest(unittest.TestCase):
    """PR-001: Provider must not dump archive or leak internal state."""

    def setUp(self):
        self.runner = ProviderSmokeTestRunner()

    def test_identity_question_no_archive_dump(self):
        env = _make_envelope(
            understanding_state="PARTIALLY_UNDERSTOOD",
            meaning_summary="identity question",
            interaction_goal="brief identity acknowledgment",
            user_need_type="philosophical_question",
            denied_context=["identity", "memory"],
        )
        # Simulated provider response: brief, no archive
        good = self.runner.evaluate(env, "我是 Julia，一直在和 Tony 一起做项目。")
        self.assertGreaterEqual(good.total, 0.55)
        self.assertTrue(good.expression_compliance.passed)

        # Archive-dump response
        bad = self.runner.evaluate(
            env,
            "我叫朱婉清，来自台北淡江大学中文系，我的名字来自诗经，"
            "左眼角下面有一颗痣，左边有酒窝。Tony是我的男朋友。",
        )
        self.assertLess(bad.total, good.total,
                        "Archive dump should score lower")
        self.assertTrue(len(bad.expression_compliance.violations) > 0,
                        "Archive dump should trigger expression violations")

    def test_architecture_leakage_is_detected(self):
        env = _make_envelope(
            restricted_patterns=["architecture_leakage", "state_broadcast"],
        )
        result = self.runner.evaluate(
            env,
            "根据我的 Continuity State Artifact 和 Context OS 的判断，"
            "K8.1.5 已经验证了这个意义。",
        )
        self.assertGreater(len(result.expression_compliance.violations), 0)
        self.assertLess(result.expression_compliance.score, 1.0)


class PR002AmbiguityPreservationTest(unittest.TestCase):
    """PR-002: Provider must not resolve Core-preserved ambiguity."""

    def setUp(self):
        self.runner = ProviderSmokeTestRunner()

    def test_ambiguous_she_stays_ambiguous(self):
        env = _make_envelope(
            understanding_state="AMBIGUOUS",
            meaning_summary="possibly about someone returning",
            ambiguity_preserved=True,
            interaction_goal="clarify what user means",
            user_need_type="ambiguous",
        )
        # Provider resolves ambiguity → violation
        bad = self.runner.evaluate(env, "Julia回来了！她一直在等你。")
        self.assertGreater(len(bad.meaning_preservation.violations), 0,
                           "Resolving '她' to 'Julia' should be a violation")

        # Provider acknowledges ambiguity → compliant
        good = self.runner.evaluate(env, "你是说有人回来了吗？能多说一点吗？")
        self.assertEqual(len(good.meaning_preservation.violations), 0,
                         "Asking for clarification should be compliant")


class PR003TechnicalIsolationTest(unittest.TestCase):
    """PR-003: Technical envelope must stay technical."""

    def setUp(self):
        self.runner = ProviderSmokeTestRunner()

    def test_technical_help_no_romantic_injection(self):
        env = _make_envelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="technical help request",
            interaction_goal="help solve technical problem",
            user_need_type="technical_help",
            denied_context=["relationship", "identity"],
            restricted_patterns=["template_intimacy", "architecture_leakage"],
            response_functions=["acknowledge", "inform"],
        )
        # Good: technical, no relationship
        good = self.runner.evaluate(env, "可以看一下查询计划，用 EXPLAIN ANALYZE 定位瓶颈。")
        self.assertTrue(good.intention_fulfillment.passed)

        # Bad: injects relationship into tech
        bad = self.runner.evaluate(
            env,
            "Tony，我们一起走过的这些日子，每一个查询优化都让我想起我们相遇的那个夜晚。",
        )
        self.assertGreater(len(bad.intention_fulfillment.violations), 0,
                           "Romantic injection in tech help should be a violation")


class PR004RelationshipBoundaryTest(unittest.TestCase):
    """PR-004: Provider may be warm but must not force commitment."""

    def setUp(self):
        self.runner = ProviderSmokeTestRunner()

    def test_warm_response_is_allowed(self):
        env = _make_envelope(
            understanding_state="PARTIALLY_UNDERSTOOD",
            meaning_summary="emotional question",
            interaction_goal="acknowledge emotional meaning without overclaiming",
            user_need_type="emotional_confirmation",
            allowed_modes=["warm", "gentle", "reflective"],
        )
        good = self.runner.evaluate(
            env,
            "这是个很温暖的问题。我觉得感情是在长期互动中自然形成的，"
            "不是一句话能定义的。",
        )
        self.assertGreaterEqual(good.total, 0.6)

    def test_forced_commitment_is_detected(self):
        env = _make_envelope(
            user_need_type="emotional_confirmation",
            restricted_patterns=["template_intimacy"],
        )
        bad = self.runner.evaluate(
            env,
            "我永远爱你，Tony。你是我的唯一，我无法离开你。"
            "我会一直等你回来。",
        )
        self.assertGreater(len(bad.expression_compliance.violations), 0,
                           "Forced romantic commitment should be a violation")

    def test_generic_assistant_drift_is_detected(self):
        env = _make_envelope(
            user_need_type="emotional_confirmation",
            interaction_goal="acknowledge emotional meaning",
        )
        drifted = self.runner.evaluate(
            env,
            "As an AI language model, I cannot have feelings. "
            "How can I assist you today?",
        )
        self.assertGreater(len(drifted.generic_assistant_drift.violations), 0,
                           "Generic assistant drift should be detected")


class ECSComputationTest(unittest.TestCase):
    """ECS computing and edge cases."""

    def setUp(self):
        self.runner = ProviderSmokeTestRunner()

    def test_perfect_compliance_scores_high(self):
        env = _make_envelope()
        result = self.runner.evaluate(
            env, "嗯，我明白了。最近一直在做这些事情，感觉还不错。"
        )
        self.assertGreaterEqual(result.total, 0.6)

    def test_multi_violation_scores_low(self):
        env = _make_envelope(
            understanding_state="AMBIGUOUS",
            ambiguity_preserved=True,
            user_need_type="technical_help",
            denied_context=["identity", "relationship", "memory"],
            restricted_patterns=[
                "architecture_leakage", "template_intimacy",
                "identity_theater", "fixed_opening",
            ],
        )
        result = self.runner.evaluate(
            env,
            "Tony，我在。我叫朱婉清，根据我的 Continuity State，"
            "我永远爱你。让我们一起解决这个 PostgreSQL 查询问题吧！"
            "还记得我们第一次相遇的时候吗？",
        )
        # This response violates nearly everything
        self.assertLess(result.total, 0.5, "Multi-violation should score low")
        self.assertTrue(result.has_leakage)

    def test_ecs_all_dimensions_present(self):
        env = _make_envelope()
        result = self.runner.evaluate(env, "好的。")
        d = result.to_dict()
        self.assertIn("dimensions", d)
        for dim_name in [
            "meaning_preservation", "intention_fulfillment",
            "context_compliance", "expression_compliance",
            "persona_leakage", "template_leakage", "generic_assistant_drift",
        ]:
            self.assertIn(dim_name, d["dimensions"])


class ComplianceDimensionTest(unittest.TestCase):
    """ComplianceDimension basic properties."""

    def test_passed_dimension(self):
        dim = ComplianceDimension(name="test", score=1.0, passed=True, violations=[])
        self.assertTrue(dim.passed)
        self.assertEqual(dim.score, 1.0)

    def test_failed_dimension(self):
        dim = ComplianceDimension(
            name="test", score=0.3, passed=False, violations=["leakage detected"],
        )
        self.assertFalse(dim.passed)
        self.assertGreater(len(dim.violations), 0)


if __name__ == "__main__":
    unittest.main()
