import unittest

from julia_core.conversation_cognition.understanding import (
    ContextDependency,
    ConversationUnderstanding,
    LiteralContent,
    MeaningCandidate,
    SemanticSpace,
    Uncertainty,
    UnderstandingState,
)


class K810SchemaTests(unittest.TestCase):
    def test_conversation_understanding_schema_preserves_candidates(self):
        obj = ConversationUnderstanding(
            literal_content=LiteralContent(text="你还喜欢Tony吗？", literal_meaning="asking about affection"),
            semantic_space=SemanticSpace(
                [
                    MeaningCandidate("emotional_confirmation", 0.55),
                    MeaningCandidate("continuity_test", 0.30),
                    MeaningCandidate("playful_question", 0.15),
                ]
            ),
            uncertainty=Uncertainty(UnderstandingState.PARTIALLY_UNDERSTOOD, confidence=0.55),
            context_dependency=ContextDependency(
                requires=["conversation_state"], forbidden=["provider", "memory_write"]
            ),
        )

        data = obj.to_dict()
        self.assertEqual(data["literal_content"]["text"], "你还喜欢Tony吗？")
        self.assertEqual(len(data["semantic_space"]["possible_meanings"]), 3)
        self.assertEqual(data["uncertainty"]["state"], "PARTIALLY_UNDERSTOOD")
        self.assertIn("provider", data["context_dependency"]["forbidden"])

    def test_ambiguous_factory_sets_need_context(self):
        obj = ConversationUnderstanding.ambiguous(
            "她又回来了", literal_meaning="someone returned", missing_information=["who is she?"]
        )
        data = obj.to_dict()
        self.assertEqual(data["uncertainty"]["state"], "AMBIGUOUS")
        self.assertTrue(data["uncertainty"]["need_context"])
        self.assertTrue(data["uncertainty"]["need_clarification"])
        self.assertIn("who is she?", data["missing_information"])

    def test_candidate_confidence_must_be_bounded(self):
        with self.assertRaises(ValueError):
            MeaningCandidate("invalid", 1.5)


if __name__ == "__main__":
    unittest.main()
