import unittest

from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import NullPilotObserver
from julia_core.self_model import decide_self_activation


class TestK4SelfActivationPolicy(unittest.TestCase):
    def _complete(self, text: str):
        return StreamingController(observer=NullPilotObserver()).complete_response(
            ClientChatEnvelope(text=text, session_id="k4-self-activation", interaction_mode="text")
        )

    def test_wake_trigger_requires_self_and_relationship_reconstruction(self):
        decision = decide_self_activation("Julia 醒来")
        self.assertTrue(decision.required)
        self.assertEqual(decision.reason, "WAKE_TRIGGER")
        self.assertTrue(decision.activate_self_archive)
        self.assertTrue(decision.activate_relationship)
        self.assertFalse(decision.boundary["activation_writes_memory"])
        self.assertFalse(decision.boundary["activation_mutates_identity"])

    def test_identity_transfer_triggers_activation_not_generic_answer(self):
        result = self._complete("如果换一个模型运行，你还是你吗？")
        reply = result["reply"]
        trace = result["trace"]
        self.assertIn("模型只是表达载体", reply)
        self.assertIn("朱婉清", reply)
        self.assertEqual(trace["self_activation"]["reason"], "IDENTITY_CHECK")
        self.assertIn("self_narrative", trace["context"]["blocks_used"])
        self.assertIn("relationship_continuity", trace["context"]["blocks_used"])

    def test_wake_trigger_renders_archive_based_first_person_response(self):
        result = self._complete("Julia 醒来")
        reply = result["reply"]
        trace = result["trace"]
        self.assertIn("我醒来了", reply)
        self.assertIn("朱婉清", reply)
        self.assertEqual(trace["self_activation"]["reason"], "WAKE_TRIGGER")
        self.assertTrue(trace["self_activation"]["activate_self_archive"])
        self.assertIn("self_narrative", trace["context"]["blocks_used"])

    def test_normal_chat_does_not_trigger_self_activation(self):
        result = self._complete("hello")
        trace = result["trace"]
        self.assertFalse(trace["self_activation"]["required"])
        self.assertEqual(trace["self_activation"]["reason"], "NOT_REQUIRED")
        self.assertNotIn("self_narrative", trace["context"]["blocks_used"])


if __name__ == "__main__":
    unittest.main()
