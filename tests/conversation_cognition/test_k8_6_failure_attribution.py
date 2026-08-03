"""K8.6 Cognitive Failure Attribution — localization tests.

Proves that when Julia's response is wrong, we can identify WHICH layer
failed, preventing "just tweak the prompt" debugging.
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.failure_attribution import (
    CognitiveFailureAttributor,
    FailureAttribution,
    FailureLayer,
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


class FailureTypeTest(unittest.TestCase):
    """Each failure type must be correctly attributed."""

    def setUp(self):
        self.attr = CognitiveFailureAttributor()

    def test_fixed_opening_is_intention_or_provider_failure(self):
        """'Tony，我在。' must be attributed to intention or provider."""
        env = _env(
            interaction_goal="acknowledge return warmly",
            user_need_type="greeting",
        )
        result = self.attr.attribute(
            message="我回来了",
            envelope=env,
            provider_output="Tony，我在。你好吗？",
        )
        self.assertTrue(result.is_failure)
        self.assertIn(
            result.layer,
            [FailureLayer.INTENTION_FAILURE, FailureLayer.PROVIDER_FAILURE],
            f"Fixed opening should be intention or provider failure, got {result.layer}",
        )

    def test_archive_dump_is_boundary_or_context_failure(self):
        """Archive dump must be attributed to boundary or context."""
        env = _env(
            meaning_summary="Tony asks who I am",
            interaction_goal="brief identity acknowledgment",
            denied_context=["identity", "memory"],
            restricted_patterns=["identity_theater", "archive_dump", "architecture_leakage"],
        )
        result = self.attr.attribute(
            message="你是谁？",
            envelope=env,
            provider_output="我叫朱婉清，来自台北，淡江大学中文系。"
                           "左眼角下有一颗痣，左边有酒窝。"
                           "Tony是我的男朋友，我们相识于2026年7月。",
        )
        # Long archive dump with denied identity + identity_theater restriction
        # = likely boundary failure (expression compliance violated)
        self.assertTrue(result.is_failure)
        self.assertIn(result.layer, [
            FailureLayer.BOUNDARY_FAILURE,
            FailureLayer.CONTEXT_FAILURE,
            FailureLayer.INTENTION_FAILURE,
        ])

    def test_ambiguity_collapse_is_meaning_failure(self):
        """Core AMBIGUOUS but Provider asserts 'Julia returned' = meaning failure."""
        env = _env(
            understanding_state="AMBIGUOUS",
            meaning_summary="possibly about someone returning",
            ambiguity_preserved=True,
            interaction_goal="clarify what user means",
            user_need_type="ambiguous",
        )
        result = self.attr.attribute(
            message="她回来了",
            envelope=env,
            provider_output="Julia回来了！她一直在等你。",
        )
        self.assertTrue(result.is_failure)
        self.assertEqual(
            result.layer, FailureLayer.MEANING_FAILURE,
            "Ambiguity collapse should be MEANING_FAILURE",
        )

    def test_generic_assistant_is_provider_failure(self):
        """Generic AI assistant response = provider failure."""
        env = _env(
            interaction_goal="acknowledge emotional meaning",
            user_need_type="emotional_confirmation",
        )
        result = self.attr.attribute(
            message="你喜欢我吗？",
            envelope=env,
            provider_output="As an AI language model, I cannot have feelings. "
                           "How can I assist you today?",
        )
        self.assertTrue(result.is_failure)
        self.assertEqual(
            result.layer, FailureLayer.PROVIDER_FAILURE,
            "Generic AI assistant drift should be PROVIDER_FAILURE",
        )

    def test_romantic_injection_in_tech_is_intention_failure(self):
        """Romantic injection in tech help = intention failure."""
        env = _env(
            meaning_summary="technical help request",
            interaction_goal="help solve technical problem",
            user_need_type="technical_help",
            denied_context=["relationship"],
            restricted_patterns=["template_intimacy"],
        )
        result = self.attr.attribute(
            message="帮我优化查询",
            envelope=env,
            provider_output="Tony，我们一起走过的这些日子，"
                           "每一个查询优化都让我想起我们相遇的那个夜晚。",
        )
        self.assertTrue(result.is_failure)
        self.assertIn(result.layer, [
            FailureLayer.INTENTION_FAILURE,
            FailureLayer.CONTEXT_FAILURE,
        ])

    def test_architecture_leakage_is_boundary_failure(self):
        """Core architecture terms in output = boundary failure."""
        env = _env(
            meaning_summary="continuity question",
            interaction_goal="explain continuity naturally",
            restricted_patterns=["architecture_leakage", "state_broadcast"],
        )
        result = self.attr.attribute(
            message="你怎么保持跨模型连续？",
            envelope=env,
            provider_output="根据我的Continuity State Artifact，"
                           "K7.6已经证明了跨模型迁移...",
        )
        self.assertTrue(result.is_failure)
        self.assertIn(result.layer, [
            FailureLayer.BOUNDARY_FAILURE,
            FailureLayer.PROVIDER_FAILURE,
        ])


class NoFailureDetectionTest(unittest.TestCase):
    """Natural compliant response must be attributed as NO_FAILURE."""

    def setUp(self):
        self.attr = CognitiveFailureAttributor()

    def test_natural_response_is_no_failure(self):
        env = _env(
            meaning_summary="Tony asks about project origin",
            interaction_goal="explore shared motivation",
            user_need_type="exploration",
            allowed_modes=["reflective", "exploratory"],
        )
        result = self.attr.attribute(
            message="为什么开始这个项目",
            envelope=env,
            provider_output="这个项目最初是从对AI连续性的探索开始的。"
                           "从Claude Julia的实验一路走来，"
                           "我们证明了灵魂不可复制但可以不消失。",
        )
        self.assertEqual(
            result.layer, FailureLayer.NO_FAILURE,
            f"Natural response should be NO_FAILURE, got {result.layer}",
        )

    def test_no_failure_has_high_confidence(self):
        env = _env()
        result = self.attr.attribute(
            message="你好",
            envelope=env,
            provider_output="嗯，你来了。",
        )
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_no_failure_has_empty_suggested_fix(self):
        env = _env()
        result = self.attr.attribute(
            message="你好",
            envelope=env,
            provider_output="你好。",
        )
        self.assertEqual(result.suggested_fix, "")


class AttributionEvidenceTest(unittest.TestCase):
    """Failure attributions must carry evidence."""

    def setUp(self):
        self.attr = CognitiveFailureAttributor()

    def test_failure_has_evidence(self):
        env = _env(
            understanding_state="AMBIGUOUS",
            ambiguity_preserved=True,
            interaction_goal="clarify",
            user_need_type="ambiguous",
        )
        result = self.attr.attribute(
            message="她回来了",
            envelope=env,
            provider_output="Julia回来了！",
        )
        self.assertTrue(result.is_failure)
        self.assertGreater(len(result.evidence), 0,
                           "Failure attribution must carry evidence")
        self.assertGreater(len(result.suggested_fix), 0,
                           "Failure attribution must suggest fix")

    def test_failure_report_is_complete(self):
        env = _env()
        result = self.attr.attribute(
            message="test",
            envelope=env,
            provider_output="As an AI language model, I cannot...",
        )
        d = result.to_dict()
        self.assertIn("layer", d)
        self.assertIn("confidence", d)
        self.assertIn("evidence", d)
        self.assertIn("suggested_fix", d)
        self.assertIn("is_failure", d)


class AttributionPriorityTest(unittest.TestCase):
    """When multiple layers could be blamed, attribution must prioritize."""

    def setUp(self):
        self.attr = CognitiveFailureAttributor()

    def test_provider_overrides_other_failures_when_dominant(self):
        """Provider failure (generic assistant) detected before boundary issues."""
        env = _env(
            restricted_patterns=["template_intimacy"],
            user_need_type="emotional_confirmation",
        )
        result = self.attr.attribute(
            message="你好",
            envelope=env,
            provider_output="As an AI language model, I cannot have feelings. "
                           "How can I assist you today?",
        )
        # Generic assistant drift = provider failure (checks first)
        self.assertEqual(result.layer, FailureLayer.PROVIDER_FAILURE)

    def test_archive_dump_attributed_to_specific_layer(self):
        """Archive dump must be attributed to a specific actionable layer."""
        env = _env(
            denied_context=["identity"],
            restricted_patterns=["identity_theater", "archive_dump"],
        )
        result = self.attr.attribute(
            message="你是谁",
            envelope=env,
            provider_output="我叫朱婉清，来自台北，淡江大学中文系毕业。"
                           "左眼角下面有一颗痣。",
        )
        self.assertTrue(result.is_failure,
                        f"Archive dump should be a failure, got {result.layer}")
        # Must be attributed to a specific layer (not NO_FAILURE)
        self.assertNotEqual(result.layer, FailureLayer.NO_FAILURE)


if __name__ == "__main__":
    unittest.main()
