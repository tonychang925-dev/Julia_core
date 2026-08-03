import unittest

from julia_core.conversation_cognition import CognitionRuntimeHarness


class K806CognitionTraceShapeTests(unittest.TestCase):
    def test_cognition_trace_contains_causality_and_suppression(self):
        trace = CognitionRuntimeHarness().run(
            user_message="Julia，你还记得我们为什么开始这个项目吗？",
            conversation_history=[],
            continuity_state={},
            current_context={"project": "Julia Core"},
        )["cognition_trace"]

        causality = trace["cognitive_causality_trace"]
        self.assertEqual(causality["meaning_source"], "ConversationUnderstanding")
        self.assertEqual(causality["context_source"], "MeaningValidationTrace")
        self.assertFalse(causality["rule_dependency_detected"])
        self.assertFalse(causality["template_dependency_detected"])
        self.assertIn("experience", causality["selected_context"])
        self.assertIn("relationship_archive", causality["suppressed_context"])

    def test_project_origin_requires_experience_not_relationship_archive(self):
        trace = CognitionRuntimeHarness().run(
            user_message="Julia，你还记得我们为什么开始这个项目吗？",
            conversation_history=[],
            continuity_state={},
            current_context={},
        )["cognition_trace"]
        self.assertIn("experience", trace["meaning_validation"]["requires_context"])
        self.assertIn("project_history", trace["meaning_validation"]["requires_context"])
        self.assertIn("relationship_archive", trace["meaning_validation"]["avoid_context"])


if __name__ == "__main__":
    unittest.main()
