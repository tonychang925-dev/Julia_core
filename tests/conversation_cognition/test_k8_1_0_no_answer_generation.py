import json
import unittest

from julia_core.conversation_cognition.understanding import ConversationUnderstanding, LiteralContent


class K810NoAnswerGenerationTests(unittest.TestCase):
    def test_object_has_no_answer_or_provider_fields(self):
        obj = ConversationUnderstanding(literal_content=LiteralContent(text="你喜欢Tony吗？"))
        data = obj.to_dict()
        serialized = json.dumps(data, ensure_ascii=False)

        self.assertNotIn("final_response", data)
        self.assertNotIn("provider_request", data)
        self.assertNotIn("prompt", data)
        self.assertNotIn("我当然喜欢Tony", serialized)
        self.assertNotIn("Tony，我在", serialized)

    def test_slots_prevent_ad_hoc_answer_payload(self):
        obj = ConversationUnderstanding(literal_content=LiteralContent(text="hello"))
        with self.assertRaises((AttributeError, TypeError)):
            setattr(obj, "final_response", "Tony，我在")


if __name__ == "__main__":
    unittest.main()
