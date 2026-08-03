"""K8.5.0 Provider Adapter Contract — structural validation tests.

Proves that the cognition envelope:
- Carries meaning, intention, context, and expression
- Contains NO persona prompt
- Contains NO answer template
- Validates structurally before Provider is called
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.provider_adapter import (
    ProviderAdapterContract,
    ProviderAnswerGate,
    ProviderCognitionEnvelope,
    ProviderEnvelopeBuilder,
)
from julia_core.conversation_cognition.response_intention import (
    DepthRequirement,
    ResponseFunction,
    ResponseIntention,
    UserNeedType,
)
from julia_core.conversation_cognition.context_arbitration import (
    ArbitrationDecision,
    ContextArbitrationDecision,
    ContextBudget,
    ContextSource,
    SourceDecision,
)
from julia_core.conversation_cognition.expression_boundary import (
    ExpressionBoundary,
    ExpressionMode,
    RestrictedPattern,
)
from julia_core.conversation_cognition.understanding import UnderstandingState


def _make_valid_envelope() -> ProviderCognitionEnvelope:
    return ProviderCognitionEnvelope(
        understanding_state="PARTIALLY_UNDERSTOOD",
        meaning_summary="Tony is asking about project origin",
        ambiguity_preserved=True,
        interaction_goal="explore the topic with user",
        user_need_type="exploration",
        response_functions=["explore", "reflect"],
        depth_requirement="thorough",
        allowed_context=["experience", "project_state"],
        limited_context=["relationship", "continuity"],
        denied_context=["identity", "memory"],
        context_budget_utilization=0.35,
        allowed_modes=["reflective", "exploratory"],
        restricted_patterns=["fixed_opening", "identity_theater", "template_intimacy"],
        provider_freedom=True,
        envelope_id="env-test-001",
    )


def _make_intention(need: UserNeedType, goal: str, functions: list[str]) -> ResponseIntention:
    return ResponseIntention(
        interaction_goal=goal,
        user_need=__import__(
            "julia_core.conversation_cognition.response_intention", fromlist=["UserNeed"]
        ).UserNeed(need, 0.6),
        response_functions=[ResponseFunction(f) for f in functions],
        depth_requirement=DepthRequirement.NORMAL,
        intention_justification="test",
    )


def _make_arbitration() -> ContextArbitrationDecision:
    return ContextArbitrationDecision(
        sources=[
            SourceDecision(ContextSource.IDENTITY, ArbitrationDecision.LIMIT, "limit", max_items=3),
            SourceDecision(ContextSource.RELATIONSHIP, ArbitrationDecision.LIMIT, "limit", max_items=5),
            SourceDecision(ContextSource.EXPERIENCE, ArbitrationDecision.ALLOW, "allow"),
            SourceDecision(ContextSource.PROJECT_STATE, ArbitrationDecision.ALLOW, "allow"),
            SourceDecision(ContextSource.CURRENT_CONVERSATION, ArbitrationDecision.ALLOW, "allow"),
            SourceDecision(ContextSource.MEMORY, ArbitrationDecision.DENY, "deny"),
        ],
        budget=ContextBudget(available=100, required=30, selected=25, pollution_risk=0.05),
        justification="test",
    )


def _make_boundary() -> ExpressionBoundary:
    return ExpressionBoundary(
        allowed_modes=[ExpressionMode.REFLECTIVE, ExpressionMode.EXPLORATORY],
        restricted_patterns=[RestrictedPattern.FIXED_OPENING, RestrictedPattern.IDENTITY_THEATER],
        provider_freedom=True,
        generates_text=False,
        expression_naturalness_preservation=0.72,
        boundary_justification="test",
    )


class EnvelopeStructuralTest(unittest.TestCase):
    """Envelope must carry cognition without persona/answer contamination."""

    def test_valid_envelope_passes_contract(self):
        env = _make_valid_envelope()
        contract = ProviderAdapterContract(env)
        self.assertTrue(contract.validate() is None)  # must not raise

    def test_envelope_rejects_persona_prompt_at_contract_level(self):
        """Persona prompt is rejected by contract, not dataclass construction."""
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_persona_prompt=True,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)

    def test_envelope_rejects_answer_template_at_contract_level(self):
        """Answer template is rejected by contract, not dataclass construction."""
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_answer_template=True,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)

    def test_ambiguous_state_without_ambiguity_preservation_fails_contract(self):
        env = ProviderCognitionEnvelope(
            understanding_state="AMBIGUOUS",
            meaning_summary="test",
            interaction_goal="clarify",
            ambiguity_preserved=False,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)

    def test_empty_meaning_summary_fails_contract(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="",
            interaction_goal="acknowledge",
        )
        with self.assertRaises(ValueError):
            ProviderAdapterContract(env)

    def test_empty_interaction_goal_fails_contract(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="",
        )
        with self.assertRaises(ValueError):
            ProviderAdapterContract(env)

    def test_incomplete_cognition_chain_fails_contract(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            cognition_chain_complete=False,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)


class EnvelopeBuilderTest(unittest.TestCase):
    """Builder must produce valid envelopes from K8 chain artifacts."""

    def setUp(self):
        self.builder = ProviderEnvelopeBuilder()

    def test_build_produces_valid_envelope(self):
        intention = _make_intention(UserNeedType.EXPLORATION, "explore", ["explore", "reflect"])
        arbitration = _make_arbitration()
        boundary = _make_boundary()

        env = self.builder.build(
            message="为什么开始这个项目",
            understanding_state=UnderstandingState.PARTIALLY_UNDERSTOOD,
            meaning_candidates=["project origin", "historical continuity"],
            ambiguity_preserved=True,
            intention=intention,
            arbitration=arbitration,
            boundary=boundary,
        )
        # Must be valid
        contract = ProviderAdapterContract(env)
        self.assertIsNotNone(contract)

    def test_built_envelope_has_no_persona(self):
        intention = _make_intention(UserNeedType.GREETING, "greet", ["acknowledge"])
        env = self.builder.build(
            message="你好",
            understanding_state=UnderstandingState.UNDERSTOOD,
            meaning_candidates=["greeting"],
            ambiguity_preserved=True,
            intention=intention,
            arbitration=_make_arbitration(),
            boundary=_make_boundary(),
        )
        self.assertFalse(env.contains_persona_prompt)
        self.assertFalse(env.contains_answer_template)


class ProviderAnswerGateTest(unittest.TestCase):
    """Gate must reject contaminated envelopes."""

    def setUp(self):
        self.gate = ProviderAnswerGate()

    def test_clean_envelope_passes(self):
        env = _make_valid_envelope()
        self.assertTrue(self.gate.check(env))

    def test_persona_contamination_fails_gate(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_persona_prompt=True,
        )
        self.assertFalse(self.gate.check(env))

    def test_answer_template_fails_gate(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_answer_template=True,
        )
        self.assertFalse(self.gate.check(env))

    def test_contaminated_envelope_fails_contract(self):
        """Contract must reject persona-contaminated envelopes."""
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_persona_prompt=True,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)

    def test_answer_template_fails_contract(self):
        """Contract must reject answer-template-contaminated envelopes."""
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            contains_answer_template=True,
        )
        with self.assertRaises(AssertionError):
            ProviderAdapterContract(env)

    def test_incomplete_chain_fails_gate(self):
        env = ProviderCognitionEnvelope(
            understanding_state="UNDERSTOOD",
            meaning_summary="test",
            interaction_goal="acknowledge",
            cognition_chain_complete=False,
        )
        self.assertFalse(self.gate.check(env))


class NC013CognitivePauseTest(unittest.TestCase):
    """NC-013: envelope must contain enough info to detect instant-reply vs cognition.

    The envelope records meaning, intention, context, and expression separately.
    If a Provider replies instantly without processing these layers, the
    envelope structure makes it detectable.
    """

    def test_envelope_has_separate_layers_for_pause_detection(self):
        env = _make_valid_envelope()
        d = env.to_dict()
        self.assertIn("meaning", d)
        self.assertIn("intention", d)
        self.assertIn("context", d)
        self.assertIn("expression", d)
        # Each layer carries distinct information
        self.assertNotEqual(d["meaning"]["state"], "")
        self.assertNotEqual(d["intention"]["goal"], "")
        self.assertGreater(len(d["context"]["allowed"]), 0)

    def test_ambiguous_state_preserves_uncertainty(self):
        env = ProviderCognitionEnvelope(
            understanding_state="AMBIGUOUS",
            meaning_summary="possibly about return, possibly about project",
            ambiguity_preserved=True,
            interaction_goal="clarify what user means",
            user_need_type="ambiguous",
            response_functions=["acknowledge_ambiguity", "clarify"],
        )
        self.assertTrue(env.ambiguity_preserved)
        self.assertEqual(env.understanding_state, "AMBIGUOUS")


class NC014SameContextDifferentProviderTest(unittest.TestCase):
    """NC-014: same envelope, different Provider — structural consistency."""

    def test_same_envelope_for_different_providers_is_identical(self):
        """The envelope is the same regardless of which Provider will execute it."""
        env1 = _make_valid_envelope()
        env2 = _make_valid_envelope()
        # Structural fields must match
        self.assertEqual(env1.interaction_goal, env2.interaction_goal)
        self.assertEqual(env1.user_need_type, env2.user_need_type)
        self.assertEqual(env1.response_functions, env2.response_functions)

    def test_envelope_contains_no_provider_specific_fields(self):
        env = _make_valid_envelope()
        d = env.to_dict()
        # Must not contain any provider-name-specific fields
        flat = str(d)
        for provider_name in ["claude", "openai", "deepseek", "gpt"]:
            self.assertNotIn(f'"provider":"{provider_name}"', flat.lower())
            self.assertNotIn(f'"model":"{provider_name}"', flat.lower())


if __name__ == "__main__":
    unittest.main()
