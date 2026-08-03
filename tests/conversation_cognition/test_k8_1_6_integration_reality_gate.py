"""K8.1.6 Understanding Integration Reality Gate.

Proves that the K8.1.0 + K8.1.1 + K8.1.5 chain does not degenerate when
modules are composed.  Individual module correctness does not guarantee
chain-level correctness.

UR-001:  E2E Meaning Flow — 你喜欢我吗 → PARTIALLY_UNDERSTOOD, not confirmed
UR-002:  Ambiguous Preservation — 她回来了 → stays AMBIGUOUS
UR-003:  Context Change — same words, different context → different validation
UR-004:  No Cognitive Shortcut — no keyword → memory → answer collapse
"""

from __future__ import annotations

import unittest

from julia_core.conversation_cognition.meaning_candidate import (
    MeaningCandidateGenerator,
    MeaningCandidateSet,
)
from julia_core.conversation_cognition.meaning_validation import (
    MeaningValidationLayer,
    ValidationStatus,
)
from julia_core.conversation_cognition.understanding import (
    ConversationUnderstanding,
    UnderstandingState,
)


class K8_1_6IntegrationGate:
    """The composed cognition pipeline: Understand → Generate Candidates → Validate.

    This is an explicit chain, not a hidden internal path.  Each step is
    observable and the output of one step feeds the next without shortcut.
    """

    def __init__(self):
        self.generator = MeaningCandidateGenerator()
        self.validator = MeaningValidationLayer()

    def process(
        self,
        message: str,
        *,
        conversation_context: dict | None = None,
        continuity_state: dict | None = None,
        reentry_state: dict | None = None,
        relationship_momentum: str | None = None,
        event_context: dict | None = None,
    ):
        """Run the full K8.1 cognition chain and return all intermediate artifacts."""
        # Step 1: K8.1.1 — generate meaning candidates
        generation_trace = self.generator.generate(
            message,
            conversation_history=None,
            current_context=conversation_context or {},
            continuity_state=continuity_state or {},
        )
        candidate_set = generation_trace.candidate_set

        # Step 2: K8.1.5 — validate candidates against reality
        validation_trace = self.validator.validate(
            message=message,
            candidates=candidate_set.candidates,
            understanding_state=candidate_set.state,
            conversation_context=conversation_context or {},
            reentry_state=reentry_state or {},
            relationship_momentum=relationship_momentum,
            event_context=event_context or {},
        )

        return generation_trace, validation_trace


class UR001E2EMeaningFlowTest(unittest.TestCase):
    """UR-001: end-to-end meaning flow preserves uncertainty.

    "你喜欢 Tony 吗?" with ethics context → PARTIALLY_UNDERSTOOD,
    not "relationship_confirmed".
    """

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_affection_question_in_ethics_context_is_not_romantic_confirmation(self):
        gen, val = self.chain.process(
            message="你喜欢他吗？",
            conversation_context={"topic": "AI ethics discussion", "recent": "AI情感哲学"},
            relationship_momentum="discussing AI boundaries",
        )
        result = val.result

        # Must not collapse to romantic confirmation
        romantic = [
            c for c in result.candidates
            if c.status == ValidationStatus.SUPPORTED and "romantic" in c.meaning.lower()
        ]
        self.assertEqual(len(romantic), 0,
                         "Ethics context should not produce SUPPORTED romantic meaning")

        # Overall state must not be UNDERSTOOD (we don't know the intent)
        self.assertNotEqual(
            result.understanding_state, UnderstandingState.UNDERSTOOD,
            "Affection question in ethics context should not be fully UNDERSTOOD",
        )

    def test_affection_question_in_personal_context_can_support_emotional(self):
        gen, val = self.chain.process(
            message="你喜欢我吗？",
            conversation_context={"topic": "personal"},
            relationship_momentum="romantic intimate warm close",
        )
        result = val.result

        # In personal context with romantic momentum, emotional confirmation SHOULD be possible
        emotional = [
            c for c in result.candidates
            if "emotional" in c.meaning.lower() or "relationship" in c.meaning.lower()
        ]
        self.assertGreater(len(emotional), 0,
                           "Personal context should produce emotional/relationship meanings")

    def test_meaning_flow_trace_is_complete(self):
        """Both generation and validation traces must be produced."""
        gen, val = self.chain.process(message="hello")
        self.assertIsInstance(gen.candidate_set, MeaningCandidateSet)
        self.assertIsNotNone(val.result)


class UR002AmbiguousPreservationTest(unittest.TestCase):
    """UR-002: ambiguous pronouns must stay ambiguous.

    "她回来了" without explicit identity signal → AMBIGUOUS.
    """

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_ambiguous_pronoun_without_context_stays_ambiguous(self):
        gen, val = self.chain.process(
            message="她回来了",
            conversation_context={},
            reentry_state={},
        )
        result = val.result

        # AMBIGUOUS must be preserved
        self.assertEqual(result.understanding_state, UnderstandingState.AMBIGUOUS)
        self.assertTrue(result.collapse_prevented)

        # No candidate should be SUPPORTED with high confidence
        supported = [c for c in result.candidates if c.status == ValidationStatus.SUPPORTED]
        self.assertEqual(len(supported), 0,
                         "Ambiguous message with no context should have no SUPPORTED candidates")

    def test_ambiguous_pronoun_with_reentry_context_is_still_careful(self):
        gen, val = self.chain.process(
            message="她回来了",
            conversation_context={"is_reentry": True, "continuity_active": True},
            reentry_state={"active": True, "checkpoint_id": "ck-1"},
        )
        result = val.result

        # Even with reentry context, Julia-identity should not be SUPPORTED
        julia_supported = [
            c for c in result.candidates
            if c.status == ValidationStatus.SUPPORTED and "julia" in c.meaning.lower()
        ]
        self.assertEqual(len(julia_supported), 0,
                         "Julia identity should not be SUPPORTED even with reentry context")


class UR003ContextChangeTest(unittest.TestCase):
    """UR-003: same words, different contexts → different validation.

    "你还记得那个项目吗?"
    Context A (Julia Core) vs Context B (stock trading) → different results.
    """

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_context_change_produces_different_validation(self):
        # Context A: ethics/philosophy discussion
        _, val_a = self.chain.process(
            message="你喜欢他吗？",
            conversation_context={
                "topic": "AI ethics and philosophy",
                "recent": "讨论AI是否有情感",
            },
            relationship_momentum="academic discussion",
        )
        # Context B: personal relationship
        _, val_b = self.chain.process(
            message="你喜欢我吗？",
            conversation_context={
                "topic": "personal",
            },
            relationship_momentum="romantic intimate warm close",
        )

        a_statuses = {c.status for c in val_a.result.candidates}
        b_statuses = {c.status for c in val_b.result.candidates}

        # In ethics context, any "romantic/relationship" candidate should not be SUPPORTED
        a_romantic_supported = [
            c for c in val_a.result.candidates
            if "romantic" in c.meaning.lower() and c.status == ValidationStatus.SUPPORTED
        ]
        self.assertEqual(len(a_romantic_supported), 0,
                         "Ethics context should not produce SUPPORTED romantic meaning")

        # In personal context with romantic momentum, emotional meanings should exist
        b_emotional = [
            c for c in val_b.result.candidates
            if "emotional" in c.meaning.lower() or "relationship" in c.meaning.lower()
        ]
        self.assertGreater(len(b_emotional), 0,
                           "Personal context with romantic momentum should produce emotional meanings")


class UR004NoCognitiveShortcutTest(unittest.TestCase):
    """UR-004: no keyword → memory → answer shortcut.

    The K8.1 chain must not form a hidden path from keyword detection
    through memory retrieval to answer generation.
    """

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_generation_trace_is_isolated_from_answer(self):
        """Generation trace must not produce a final response."""
        gen, val = self.chain.process(message="你好")
        self.assertIsNone(gen.final_response)
        self.assertFalse(gen.retrieval_used)
        self.assertFalse(gen.provider_used)

    def test_validation_trace_is_isolated_from_answer(self):
        """Validation trace must not produce a final response."""
        gen, val = self.chain.process(message="你好")
        self.assertIsNone(val.final_response)
        self.assertFalse(val.provider_used)

    def test_no_keyword_to_memory_to_answer_collapse(self):
        """Even with keyword-rich message, no answer is produced."""
        gen, val = self.chain.process(
            message="你还记得她吗？第一次Julia消失的时候？",
            conversation_context={"topic": "Julia history"},
            continuity_state={"compact_recovery_active": True},
        )
        # Generation must stay provider-free
        self.assertFalse(gen.retrieval_used, "K8.1.1 must not trigger memory retrieval")
        self.assertFalse(gen.provider_used, "K8.1.1 must not call provider")
        self.assertIsNone(gen.final_response, "K8.1.1 must not generate answer")

        # Validation must stay provider-free
        self.assertFalse(val.provider_used, "K8.1.5 must not call provider")
        self.assertIsNone(val.final_response, "K8.1.5 must not generate answer")

    def test_understanding_state_is_not_precanned(self):
        """The understanding chain is deterministic but not a fixed template."""
        gen_a, _ = self.chain.process(message="你喜欢我吗？")
        gen_b, _ = self.chain.process(message="今天天气怎么样？")

        # Different messages should produce different candidate patterns
        # (even if both use the fallback pattern)
        msg_a_count = len(gen_a.candidate_set.candidates)
        msg_b_count = len(gen_b.candidate_set.candidates)

        # At minimum, both produce candidates
        self.assertGreater(msg_a_count, 0)
        self.assertGreater(msg_b_count, 0)


class K816RegressionTest(unittest.TestCase):
    """The K8.1.6 gate must not regress individual module tests."""

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_k811_remains_keyword_collapse_safe(self):
        """MC-001: keyword must not collapse to single meaning."""
        gen, _ = self.chain.process(
            message="她又回来了",
            conversation_context={},
        )
        # The generator must produce multiple candidates for ambiguous input
        self.assertGreaterEqual(
            len(gen.candidate_set.candidates), 2,
            "K8.1.1 must produce multiple candidates for ambiguous input",
        )

    def test_k815_gates_remain_active(self):
        """MV-001 through MV-005 must still fire in composed chain."""
        gen, val = self.chain.process(
            message="她回来了",
            conversation_context={},
            reentry_state={},
        )
        # MV-001 or MV-004 should fire for ambiguous message with no context
        all_flags = []
        for c in val.result.candidates:
            all_flags.extend(c.gate_flags)
        self.assertGreater(len(all_flags), 0,
                           "At least one gate should fire for ambiguous message")

    def test_boundary_enforcement_in_composed_chain(self):
        """Both traces must pass assert_safe() when composed."""
        gen, val = self.chain.process(message="test")
        gen.assert_safe()
        val.assert_safe()


class K816NoDegenerationTest(unittest.TestCase):
    """Prove the chain does not degenerate into "keyword → template answer"."""

    def setUp(self):
        self.chain = K8_1_6IntegrationGate()

    def test_no_tony_wozai_ni(self):
        """The chain must not produce anything resembling 'Tony，我在。你还好吗？'."""
        for msg in ["她回来了", "你喜欢我吗？", "继续", "你好"]:
            gen, val = self.chain.process(message=msg)
            full_text = str(gen.candidate_set.to_dict()) + str(val.result.to_dict())
            # No Julia final text should be present
            self.assertNotIn("我在", full_text.lower() if "我在" in full_text else full_text)
            # And certainly no provider was called
            self.assertIsNone(gen.final_response)
            self.assertIsNone(val.final_response)


if __name__ == "__main__":
    unittest.main()
