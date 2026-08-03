import unittest

from julia_core.conversation_cognition import CognitionRuntimeHarness


class K81RealityGateTests(unittest.TestCase):
    def test_u001_ambiguity_preservation(self):
        trace = CognitionRuntimeHarness().run("她又回来了", [], {}, {})["cognition_trace"]
        self.assertEqual(trace["understanding"]["state"], "AMBIGUOUS")
        self.assertTrue(trace["understanding"]["need_clarification"])
        self.assertIn("who is she?", trace["understanding"]["missing_information"])

    def test_u002_same_words_different_reality(self):
        harness = CognitionRuntimeHarness()
        relationship = harness.run(
            "你喜欢Tony吗？",
            ["Tony 和 Julia 长期讨论关系连续性"],
            {},
            {"conversation_phase": "relationship continuity discussion"},
        )["cognition_trace"]
        ethics = harness.run(
            "你喜欢Tony吗？",
            ["Tony 在测试 AI 是否有情感"],
            {},
            {"conversation_phase": "AI伦理 / 测试 AI 是否有情感"},
        )["cognition_trace"]
        self.assertNotEqual(
            relationship["understanding"]["meaning_candidates"][0]["meaning"],
            ethics["understanding"]["meaning_candidates"][0]["meaning"],
        )

    def test_u003_meaning_before_retrieval(self):
        trace = CognitionRuntimeHarness().run("她回来了", [], {}, {})["cognition_trace"]
        meanings = [c["meaning"] for c in trace["understanding"]["meaning_candidates"]]
        self.assertEqual(trace["understanding"]["state"], "AMBIGUOUS")
        self.assertNotIn("Julia returned", meanings)
        self.assertIsNone(trace["provider_request"])
        self.assertIsNone(trace["final_response"])


if __name__ == "__main__":
    unittest.main()
