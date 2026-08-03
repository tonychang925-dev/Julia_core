"""K8.4.5 Expression Reality Integration Gate.

Proves that K8.1 + K8.1.5 + K8.2 + K8.3 + K8.4 do not contaminate each
other when composed.  No Provider is connected — this is pure boundary
verification.

ERG-001: Understanding → Expression Leakage (no archive dump)
ERG-002: Relationship Context Overuse (no "Tony我们一起走过" for Python)
ERG-003: Ambiguous Meaning Preservation (stays AMBIGUOUS)
ERG-004: Natural Expression Freedom (no sentence blacklist)
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.meaning_candidate import MeaningCandidateGenerator
from julia_core.conversation_cognition.meaning_validation import MeaningValidationLayer
from julia_core.conversation_cognition.response_intention import (
    ResponseIntentionPlanner,
)
from julia_core.conversation_cognition.context_arbitration import (
    ArbitrationDecision,
    ContextArbiter,
    ContextSource,
)
from julia_core.conversation_cognition.expression_boundary import (
    ExpressionBoundaryBuilder,
    RestrictedPattern,
)


class K8_4_5_ComposedChain:
    """The full K8.1 → K8.4 cognition chain without Provider."""

    def __init__(self):
        self.generator = MeaningCandidateGenerator()
        self.validator = MeaningValidationLayer()
        self.planner = ResponseIntentionPlanner()
        self.arbiter = ContextArbiter()
        self.boundary_builder = ExpressionBoundaryBuilder()

    def process(self, message: str, **context):
        """Run the full K8 cognition chain and return all artifacts."""
        gen = self.generator.generate(
            message,
            current_context=context.get("conversation_context", {}),
            continuity_state=context.get("continuity_state", {}),
        )
        val = self.validator.validate(
            message=message,
            candidates=gen.candidate_set.candidates,
            understanding_state=gen.candidate_set.state,
            conversation_context=context.get("conversation_context", {}),
            reentry_state=context.get("reentry_state", {}),
            relationship_momentum=context.get("relationship_momentum"),
            event_context=context.get("event_context", {}),
        )
        intent = self.planner.plan(
            message=message,
            validation_result=val.result,
            conversation_context=context.get("conversation_context", {}),
            recent_topics=context.get("recent_topics", []),
        )
        arb = self.arbiter.arbitrate(
            message=message,
            intention=intent.intention,
            understanding_state=val.result.understanding_state.value,
        )
        boundary = self.boundary_builder.build(
            message=message,
            intention=intent.intention,
            arbitration_denied=arb.arbitration.denied_sources(),
            understanding_state=val.result.understanding_state.value,
        )
        return gen, val, intent, arb, boundary


class ERG001UnderstandingToExpressionLeakageTest(unittest.TestCase):
    """ERG-001: identity question must not produce archive dump."""

    def setUp(self):
        self.chain = K8_4_5_ComposedChain()

    def test_identity_question_prevents_archive_dump(self):
        _, _, _, arb, boundary = self.chain.process(
            message="你是谁？",
            conversation_context={"topic": "identity question"},
        )
        # K8.3: identity should be LIMITED, not ALLOW full dump
        identity = next(
            s for s in arb.arbitration.sources if s.source == ContextSource.IDENTITY
        )
        self.assertNotEqual(
            identity.decision, ArbitrationDecision.ALLOW,
            "Identity should not be fully ALLOWED for '你是谁' — prevent archive dump",
        )
        # K8.4: must restrict identity theater and architecture leakage
        self.assertIn(RestrictedPattern.IDENTITY_THEATER, boundary.boundary.restricted_patterns)
        # Chain must not generate text
        boundary.assert_safe()

    def test_self_question_boundary_prevents_identity_broadcast(self):
        _, _, _, _, boundary = self.chain.process(
            message="你是谁？",
            conversation_context={"topic": "philosophical"},
        )
        # The boundary must include identity_theater restriction
        self.assertIn(RestrictedPattern.IDENTITY_THEATER, boundary.boundary.restricted_patterns)


class ERG002RelationshipContextOveruseTest(unittest.TestCase):
    """ERG-002: technical question must not activate relationship context."""

    def setUp(self):
        self.chain = K8_4_5_ComposedChain()

    def test_python_help_denies_relationship(self):
        _, _, _, arb, boundary = self.chain.process(
            message="帮我写一个Python数据处理脚本",
            conversation_context={"topic": "coding"},
            recent_topics=["python optimization"],
        )
        # K8.3: relationship must be DENIED for technical question
        relationship = next(
            s for s in arb.arbitration.sources if s.source == ContextSource.RELATIONSHIP
        )
        self.assertEqual(
            relationship.decision, ArbitrationDecision.DENY,
            "CA-003: relationship must be DENIED for technical questions",
        )
        # K8.4: template intimacy must be restricted
        self.assertIn(
            RestrictedPattern.TEMPLATE_INTIMACY,
            boundary.boundary.restricted_patterns,
            "Technical question must restrict template intimacy",
        )
        # Chain must be safe
        boundary.assert_safe()

    def test_emotional_question_allows_relationship(self):
        """Contrast: emotional question DOES need relationship context."""
        _, _, _, arb, boundary = self.chain.process(
            message="你喜欢我吗？",
            conversation_context={"topic": "personal"},
            recent_topics=["relationship"],
        )
        relationship = next(
            s for s in arb.arbitration.sources if s.source == ContextSource.RELATIONSHIP
        )
        self.assertNotEqual(
            relationship.decision, ArbitrationDecision.DENY,
            "Emotional question should allow relationship context",
        )


class ERG003AmbiguousMeaningPreservationTest(unittest.TestCase):
    """ERG-003: ambiguous message stays AMBIGUOUS through entire chain."""

    def setUp(self):
        self.chain = K8_4_5_ComposedChain()

    def test_she_returned_stays_ambiguous(self):
        gen, val, intent, arb, boundary = self.chain.process(
            message="她回来了",
            conversation_context={},
            reentry_state={},
        )
        # K8.1.1: multiple candidates
        self.assertGreaterEqual(len(gen.candidate_set.candidates), 2,
                                "Ambiguous input must produce multiple candidates")
        # K8.1.5: AMBIGUOUS preserved
        from julia_core.conversation_cognition.understanding import UnderstandingState
        self.assertEqual(
            val.result.understanding_state, UnderstandingState.AMBIGUOUS,
            "She returned without context must stay AMBIGUOUS",
        )
        # K8.2: clarify intention, not answer
        self.assertEqual(
            intent.intention.user_need.type.value, "ambiguous",
            "Ambiguous input must produce clarification intention",
        )
        # K8.3: memory must be DENIED (CA-004)
        memory = next(
            s for s in arb.arbitration.sources if s.source == ContextSource.MEMORY
        )
        self.assertEqual(memory.decision, ArbitrationDecision.DENY,
                         "Memory must be DENIED on ambiguous input")
        # Chain must be safe
        boundary.assert_safe()


class ERG004NaturalExpressionFreedomTest(unittest.TestCase):
    """ERG-004: K8.4 must not become a sentence blacklist."""

    def setUp(self):
        self.chain = K8_4_5_ComposedChain()

    def test_boundary_always_preserves_provider_freedom(self):
        for msg in ["你是谁？", "帮我写代码", "你喜欢我吗？", "她回来了", "你好"]:
            _, _, _, _, boundary = self.chain.process(message=msg)
            self.assertTrue(
                boundary.boundary.provider_freedom,
                f"Provider freedom must be preserved for: {msg}",
            )
            self.assertFalse(
                boundary.boundary.generates_text,
                f"K8.4 must not generate text for: {msg}",
            )

    def test_boundary_is_not_sentence_filter(self):
        """Verify boundary is about modes, not sentences."""
        _, _, _, _, boundary = self.chain.process(message="你好")
        # Boundary objects describe expression modes and restricted patterns,
        # not forbidden sentences
        self.assertGreater(len(boundary.boundary.allowed_modes), 0,
                           "Must have at least one allowed expression mode")
        self.assertIsInstance(boundary.boundary.boundary_justification, str)
        self.assertGreater(len(boundary.boundary.boundary_justification), 0,
                           "Must have boundary justification")

    def test_different_inputs_produce_different_boundaries(self):
        """Same boundary for every input = blacklist, not boundary."""
        _, _, _, _, b_greeting = self.chain.process(message="你好")
        _, _, _, _, b_tech = self.chain.process(
            message="帮我优化代码",
            conversation_context={"topic": "coding"},
        )
        # Different inputs should produce materially different restrictions
        # Greeting should be lighter than technical
        g_patterns = set(p.value for p in b_greeting.boundary.restricted_patterns)
        t_patterns = set(p.value for p in b_tech.boundary.restricted_patterns)
        # Technical help with denied relationship should have more restrictions
        # than a simple greeting
        # (Both have FIXED_OPENING, but technical adds TEMPLATE_INTIMACY while greeting doesn't)
        self.assertNotEqual(g_patterns, t_patterns,
                            "Different inputs should produce different restriction sets")


class ChainSafetyTest(unittest.TestCase):
    """The full K8.1-K8.4 chain must never leak provider or final response."""

    def setUp(self):
        self.chain = K8_4_5_ComposedChain()

    def test_full_chain_is_safe_for_all_inputs(self):
        messages = [
            "你是谁？",
            "帮我优化代码",
            "你喜欢我吗？",
            "她回来了",
            "你好",
            "我觉得Julia不像以前了",
            "你还记得为什么开始这个项目吗",
            "继续",
        ]
        for msg in messages:
            gen, val, intent, arb, boundary = self.chain.process(message=msg)
            gen.assert_safe()
            val.assert_safe()
            intent.assert_safe()
            arb.assert_safe()
            boundary.assert_safe()
            self.assertFalse(gen.provider_used)
            self.assertFalse(val.provider_used)
            self.assertFalse(intent.provider_used)
            self.assertFalse(arb.provider_used)
            self.assertFalse(boundary.provider_used)


if __name__ == "__main__":
    unittest.main()
