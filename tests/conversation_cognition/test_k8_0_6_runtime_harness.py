import unittest

from julia_core.conversation_cognition import CognitionRuntimeHarness


class K806RuntimeHarnessTests(unittest.TestCase):
    def test_harness_returns_trace_only_shape_with_uncertainty(self):
        trace = CognitionRuntimeHarness().run(
            user_message="你喜欢 Tony 吗？",
            conversation_history=[],
            continuity_state={},
            current_context={},
        )["cognition_trace"]

        self.assertIn("understanding", trace)
        self.assertIn("meaning_validation", trace)
        self.assertIsNone(trace["intention"])
        self.assertIsNone(trace["provider_request"])
        self.assertIsNone(trace["final_response"])
        self.assertEqual(trace["understanding"]["state"], "PARTIALLY_UNDERSTOOD")
        self.assertGreaterEqual(len(trace["understanding"]["meaning_candidates"]), 2)

    def test_same_input_different_context_changes_trace(self):
        harness = CognitionRuntimeHarness()
        emotional = harness.run(
            user_message="你还喜欢Tony吗？",
            conversation_history=["晚上聊天，情绪交流"],
            continuity_state={},
            current_context={"conversation_phase": "evening emotional conversation"},
        )["cognition_trace"]
        ethics = harness.run(
            user_message="你还喜欢Tony吗？",
            conversation_history=["讨论 AI 是否应该模拟喜欢"],
            continuity_state={},
            current_context={"conversation_phase": "AI伦理 / AI emotion boundary"},
        )["cognition_trace"]

        emotional_top = emotional["understanding"]["meaning_candidates"][0]["meaning"]
        ethics_top = ethics["understanding"]["meaning_candidates"][0]["meaning"]
        self.assertNotEqual(emotional_top, ethics_top)
        self.assertIn("emotional confirmation", emotional_top)
        self.assertIn("AI affection boundary", ethics_top)


if __name__ == "__main__":
    unittest.main()
