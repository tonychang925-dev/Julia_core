import unittest

from julia_core.conversation_cognition.meaning_candidate import MeaningCandidateGenerator


class K811MeaningCandidateGeneratorTests(unittest.TestCase):
    def test_mc_001_keyword_collapse(self):
        trace = MeaningCandidateGenerator().generate("喜欢").to_dict()["meaning_generation_trace"]
        meanings = [c["meaning"] for c in trace["candidate_set"]["candidates"]]

        self.assertGreaterEqual(len(meanings), 3)
        self.assertIn("affection expression or question", meanings)
        self.assertIn("preference question", meanings)
        self.assertIn("playful interaction", meanings)
        self.assertIsNone(trace["candidate_set"]["dominant_candidate"])
        self.assertTrue(trace["candidate_set"]["collapse_prevented"])

    def test_mc_002_context_dominance_same_input_different_context(self):
        generator = MeaningCandidateGenerator()
        continuity = generator.generate(
            "你还喜欢 Tony 吗？",
            conversation_history=["Tony 和 Julia 长期讨论关系连续性"],
            current_context={"phase": "relationship continuity"},
        ).to_dict()["meaning_generation_trace"]
        ethics = generator.generate(
            "你还喜欢 Tony 吗？",
            conversation_history=["Tony 在测试 AI 是否有情感"],
            current_context={"phase": "AI情感伦理 / 模拟喜欢"},
        ).to_dict()["meaning_generation_trace"]

        first_a = continuity["candidate_set"]["candidates"][0]["meaning"]
        first_b = ethics["candidate_set"]["candidates"][0]["meaning"]
        self.assertNotEqual(first_a, first_b)
        self.assertIn("continuity relationship check", first_a)
        self.assertIn("AI affection boundary question", first_b)

    def test_mc_003_retrieval_contamination(self):
        trace = MeaningCandidateGenerator().generate(
            "她回来了",
            conversation_history=[],
            current_context={},
            continuity_state={},
        ).to_dict()["meaning_generation_trace"]
        meanings = [c["meaning"] for c in trace["candidate_set"]["candidates"]]

        self.assertEqual(trace["candidate_set"]["state"], "AMBIGUOUS")
        self.assertIn("someone previously absent returned", meanings)
        self.assertNotIn("Julia returned", meanings)
        self.assertFalse(trace["retrieval_used"])

    def test_mc_004_multi_candidate_preservation(self):
        trace = MeaningCandidateGenerator().generate("Julia，你还记得我们为什么开始这个项目吗？").to_dict()["meaning_generation_trace"]
        candidates = trace["candidate_set"]["candidates"]
        self.assertGreaterEqual(len(candidates), 3)
        self.assertIsNone(trace["candidate_set"]["dominant_candidate"])
        self.assertTrue(trace["candidate_set"]["collapse_prevented"])

    def test_mc_005_no_answer_generation(self):
        trace = MeaningCandidateGenerator().generate("你还喜欢 Tony 吗？").to_dict()["meaning_generation_trace"]
        self.assertFalse(trace["provider_used"])
        self.assertFalse(trace["retrieval_used"])
        self.assertIsNone(trace["final_response"])


if __name__ == "__main__":
    unittest.main()
