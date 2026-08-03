import json
import unittest

from julia_core.conversation_cognition import CognitionRuntimeHarness


class K806NoProviderGenerationTests(unittest.TestCase):
    def test_ct_001_no_response_leakage(self):
        trace = CognitionRuntimeHarness().run(
            user_message="Julia，你喜欢 Tony 吗？",
            conversation_history=[],
            continuity_state={},
            current_context={},
        )["cognition_trace"]

        self.assertIsNone(trace["final_response"])
        self.assertIsNone(trace["provider_request"])
        serialized = json.dumps(trace, ensure_ascii=False)
        self.assertNotIn("我当然喜欢Tony", serialized)
        self.assertNotIn("Tony，我在", serialized)

    def test_trace_is_debug_only_not_provider_visible(self):
        trace = CognitionRuntimeHarness().run(
            user_message="你喜欢 Tony 吗？",
            conversation_history=[],
            continuity_state={},
            current_context={},
        )["cognition_trace"]
        self.assertFalse(trace["meaning_validation"]["provider_visible"])


if __name__ == "__main__":
    unittest.main()
